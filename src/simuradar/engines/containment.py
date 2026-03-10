"""Containment detection engine using Weisfeiler-Lehman subtree hashing."""

import ast
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterator, Protocol

from ..parser import CodeFragment


class ContainmentEngine(Protocol):
    """Protocol for containment detection engines."""

    def build_index(self, fragments: list[CodeFragment]) -> None:
        """Build an index of all subtrees for containment lookup."""
        ...

    def find_containments(
        self, fragments: list[CodeFragment], min_size: int = 5
    ) -> list["ContainmentPair"]:
        """Find all containment relationships between fragments."""
        ...


@dataclass
class ContainmentPair:
    """A containment relationship between two fragments."""

    container: CodeFragment  # The larger fragment
    contained: CodeFragment  # The smaller fragment contained within


class WLHashContainmentEngine:
    """Containment engine using Weisfeiler-Lehman subtree hashing.

    This engine:
    1. Computes WL hashes for all subtrees in each fragment
    2. Finds fragments where smaller fragment's hash matches a subtree in larger fragment
    """

    def __init__(self) -> None:
        self._fragment_hashes: dict[
            int, set[int]
        ] = {}  # frag_id -> set of subtree hashes
        self._hash_to_fragments: dict[int, list[CodeFragment]] = defaultdict(list)

    def _compute_subtree_hashes(self, node: ast.AST) -> dict[int, tuple[int, ast.AST]]:
        """Compute WL hashes for all subtrees in an AST.

        Returns a dict mapping hash -> (subtree_size, ast_node)
        """
        # First, compute bottom-up hashes
        subtree_hashes: dict[int, tuple[int, ast.AST]] = {}
        self._compute_hashes_recursive(node, subtree_hashes)
        return subtree_hashes

    def _compute_hashes_recursive(
        self, node: ast.AST, subtree_hashes: dict[int, tuple[int, ast.AST]]
    ) -> int:
        """Recursively compute WL hash for subtree rooted at node.

        Returns the hash of this subtree.
        """
        # Compute hashes for all children first (bottom-up)
        child_hashes: list[int] = []
        for child in ast.iter_child_nodes(node):
            child_hash = self._compute_hashes_recursive(child, subtree_hashes)
            child_hashes.append(child_hash)

        # Sort child hashes for WL property (ordered children)
        child_hashes.sort()

        # Create label from node type and children
        label = node.__class__.__name__
        hash_input = (
            f"{label}:{','.join(map(str, child_hashes))}" if child_hashes else label
        )

        # Simple hash (in production, use a better hash function)
        subtree_hash = hash(hash_input)

        # Record this subtree
        subtree_size = sum(1 for _ in ast.walk(node))
        subtree_hashes[subtree_hash] = (subtree_size, node)

        return subtree_hash

    def build_index(self, fragments: list[CodeFragment]) -> None:
        """Build hash index for all fragments."""
        self._fragment_hashes.clear()
        self._hash_to_fragments.clear()

        for fragment in fragments:
            # Get all subtree hashes for this fragment
            subtree_dict = self._compute_subtree_hashes(fragment.ast_node)
            hash_set = set(subtree_dict.keys())
            self._fragment_hashes[id(fragment)] = hash_set

            # Index by hash for quick lookup
            for h in hash_set:
                self._hash_to_fragments[h].append(fragment)

    def find_containments(
        self, fragments: list[CodeFragment], min_size: int = 5
    ) -> list[ContainmentPair]:
        """Find containment relationships.

        A fragment A contains fragment B if all subtree hashes of B
        appear in the set of subtrees in A.
        """
        if not fragments:
            return []

        # Build the index first
        self.build_index(fragments)

        containments: list[ContainmentPair] = []

        # For each fragment, check if any smaller fragment is contained
        for frag_a in fragments:
            # Get all subtree hashes in frag_a
            hashes_a = self._fragment_hashes.get(id(frag_a), set())

            for frag_b in fragments:
                if frag_a is frag_b:
                    continue

                # Only check if frag_b is smaller
                if frag_b.size >= frag_a.size:
                    continue

                # Check if frag_b's subtrees are in frag_a
                hashes_b = self._fragment_hashes.get(id(frag_b), set())

                # Check if B's root hash exists in A's subtree hashes
                # (approximate containment: at least the root structure matches)
                root_hash_b = self._compute_subtree_hashes(frag_b.ast_node)
                if not root_hash_b:
                    continue

                # Get the root hash (the first one computed)
                root_h = max(root_hash_b.keys())  # Take any hash from the dict

                # For containment: the entire structure of B should be a subtree of A
                # Simplified: check if B's hash set is subset of A's
                if hashes_b.issubset(hashes_a):
                    containments.append(
                        ContainmentPair(
                            container=frag_a,
                            contained=frag_b,
                        )
                    )

        return containments


def find_approximate_containments(
    fragments: list[CodeFragment], containment_threshold: float = 0.8
) -> list[ContainmentPair]:
    """Find approximate containment relationships.

    Uses the largest common subtree as a heuristic.
    """
    engine = WLHashContainmentEngine()
    return engine.find_containments(fragments, min_size=5)

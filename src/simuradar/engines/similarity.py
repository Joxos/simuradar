"""Similarity detection engine using apted tree edit distance."""

import ast
from dataclasses import dataclass
from itertools import combinations
from typing import Protocol

from apted import APTED
from apted.helpers import Tree

from ..parser import CodeFragment
from ..normalizer import normalize_ast, ast_to_bracket_notation


class SimilarityEngine(Protocol):
    """Protocol for similarity detection engines."""

    def compute_similarity(
        self, fragment_a: CodeFragment, fragment_b: CodeFragment
    ) -> float:
        """Compute similarity between two fragments (0.0 to 1.0)."""
        ...

    def find_similar_pairs(
        self, fragments: list[CodeFragment], threshold: float
    ) -> list["SimilarityPair"]:
        """Find all pairs above the similarity threshold."""
        ...


@dataclass
class SimilarityPair:
    """A pair of similar code fragments."""

    fragment_a: CodeFragment
    fragment_b: CodeFragment
    similarity: float


class AptedSimilarityEngine:
    """Similarity engine using APTED tree edit distance."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], float] = {}

    def compute_similarity(
        self, fragment_a: CodeFragment, fragment_b: CodeFragment
    ) -> float:
        """Compute similarity using tree edit distance.

        Similarity = 1 - (ted / max(size_a, size_b))
        """
        # Normalize ASTs
        norm_a = normalize_ast(fragment_a.ast_node)
        norm_b = normalize_ast(fragment_b.ast_node)

        # Convert to bracket notation
        tree_a_str = ast_to_bracket_notation(norm_a)
        tree_b_str = ast_to_bracket_notation(norm_b)

        # Create apted trees
        tree_a = Tree.from_text(tree_a_str)
        tree_b = Tree.from_text(tree_b_str)

        # Compute tree edit distance
        apted = APTED(tree_a, tree_b)
        ted = apted.compute_edit_distance()

        # Normalize by max size
        max_size = max(fragment_a.size, fragment_b.size)
        if max_size == 0:
            return 0.0

        similarity = 1.0 - (ted / max_size)
        return max(0.0, min(1.0, similarity))

    def find_similar_pairs(
        self, fragments: list[CodeFragment], threshold: float
    ) -> list[SimilarityPair]:
        """Find all pairs of fragments with similarity above threshold."""
        pairs = []

        for frag_a, frag_b in combinations(fragments, 2):
            # Skip if different types
            if frag_a.fragment_type != frag_b.fragment_type:
                continue

            similarity = self.compute_similarity(frag_a, frag_b)

            if similarity >= threshold:
                pairs.append(
                    SimilarityPair(
                        fragment_a=frag_a, fragment_b=frag_b, similarity=similarity
                    )
                )

        return pairs


def group_similar_fragments(
    pairs: list[SimilarityPair],
) -> list[list[CodeFragment]]:
    """Group fragments by similarity connectivity.

    Uses Union-Find to group fragments that are similar to each other.
    """
    if not pairs:
        return []

    # Collect all unique fragments
    all_fragments = {}
    for pair in pairs:
        all_fragments[id(pair.fragment_a)] = pair.fragment_a
        all_fragments[id(pair.fragment_b)] = pair.fragment_b

    # Union-Find implementation
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Union all similar pairs
    for pair in pairs:
        union(id(pair.fragment_a), id(pair.fragment_b))

    # Group by root
    groups: dict[int, list[CodeFragment]] = {}
    for frag_id, fragment in all_fragments.items():
        root = find(frag_id)
        if root not in groups:
            groups[root] = []
        groups[root].append(fragment)

    return list(groups.values())

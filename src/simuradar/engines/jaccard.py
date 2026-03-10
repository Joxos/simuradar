"""Jaccard similarity engine using AST node sets."""

import ast
from dataclasses import dataclass
from itertools import combinations

from ..parser import CodeFragment


@dataclass
class SimilarityPair:
    """A pair of similar code fragments."""

    fragment_a: CodeFragment
    fragment_b: CodeFragment
    similarity: float


def _is_dataclass(node: ast.ClassDef) -> bool:
    """Check if a ClassDef is decorated with @dataclass."""
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name) and dec.id == "dataclass":
            return True
        if isinstance(dec, ast.Attribute) and dec.attr == "dataclass":
            return True
    return False


def _extract_dataclass_tokens(node: ast.ClassDef) -> set[str]:
    """Extract field name and type tokens from a dataclass.

    These tokens are injected into the feature set so that dataclasses
    with different field names are distinguished from each other.
    """
    tokens: set[str] = set()
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            tokens.add(f"field:{stmt.target.id}")
            # Top-level annotation name (int, str, MyType, ...)
            ann = stmt.annotation
            if isinstance(ann, ast.Name):
                tokens.add(f"fieldtype:{ann.id}")
            elif isinstance(ann, ast.Attribute):
                tokens.add(f"fieldtype:{ann.attr}")
            elif isinstance(ann, ast.Subscript) and isinstance(ann.value, ast.Name):
                # e.g. Optional[str], list[int]
                tokens.add(f"fieldtype:{ann.value.id}")
    return tokens


class JaccardSimilarityEngine:
    """Similarity engine using Jaccard similarity on AST node types.

    This engine extracts node types from AST and computes Jaccard similarity:
    J(A, B) = |A ∩ B| / |A ∪ B|

    Complexity: O(n) per fragment to extract features, O(n²) comparisons.
    Much faster than apted (O(n³)) for large codebases.
    """

    def __init__(self) -> None:
        self._cache: dict[int, frozenset[str]] = {}

    def _extract_node_types(self, node: ast.AST) -> frozenset[str]:
        """Extract a set of node types from AST.

        For dataclasses, also injects field name and type tokens so that
        structurally identical dataclasses with different fields are
        correctly distinguished.
        """
        types = set()
        for child in ast.walk(node):
            types.add(child.__class__.__name__)
            if isinstance(child, ast.ClassDef) and _is_dataclass(child):
                types.update(_extract_dataclass_tokens(child))
        return frozenset(types)

    def _get_features(self, fragment: CodeFragment) -> frozenset[str]:
        """Get cached features for a fragment."""
        frag_id = id(fragment)
        if frag_id not in self._cache:
            self._cache[frag_id] = self._extract_node_types(fragment.ast_node)
        return self._cache[frag_id]

    def compute_similarity(
        self, fragment_a: CodeFragment, fragment_b: CodeFragment
    ) -> float:
        """Compute Jaccard similarity between two fragments.

        Jaccard = |A ∩ B| / |A ∪ B|
        """
        features_a = self._get_features(fragment_a)
        features_b = self._get_features(fragment_b)

        if not features_a and not features_b:
            return 0.0

        intersection = len(features_a & features_b)
        union = len(features_a | features_b)

        if union == 0:
            return 0.0

        return intersection / union

    def find_similar_pairs(
        self, fragments: list[CodeFragment], threshold: float
    ) -> list[SimilarityPair]:
        """Find all pairs of fragments with similarity above threshold."""
        pairs = []

        # Clear cache for new analysis
        self._cache.clear()

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


class JaccardNormalizedEngine:
    """Enhanced Jaccard with subtree pattern matching.

    Uses both node types and common subtree patterns for better accuracy.
    """

    def __init__(self) -> None:
        self._cache: dict[int, tuple[frozenset[str], frozenset[str]]] = {}

    def _extract_features(self, node: ast.AST) -> tuple[frozenset[str], frozenset[str]]:
        """Extract node types and subtree patterns.

        Returns:
            - node_types: frozenset of node type names
            - patterns: frozenset of subtree patterns (type + child types)
        """
        node_types = set()
        patterns = set()

        for child in ast.walk(node):
            node_types.add(child.__class__.__name__)
            if isinstance(child, ast.ClassDef) and _is_dataclass(child):
                node_types.update(_extract_dataclass_tokens(child))
            # Create pattern from node and its immediate children
            child_types = tuple(
                c.__class__.__name__ for c in ast.iter_child_nodes(child)
            )
            patterns.add(f"{child.__class__.__name__}:{child_types}")

        return frozenset(node_types), frozenset(patterns)

    def _get_features(
        self, fragment: CodeFragment
    ) -> tuple[frozenset[str], frozenset[str]]:
        """Get cached features for a fragment."""
        frag_id = id(fragment)
        if frag_id not in self._cache:
            self._cache[frag_id] = self._extract_features(fragment.ast_node)
        return self._cache[frag_id]

    def compute_similarity(
        self, fragment_a: CodeFragment, fragment_b: CodeFragment
    ) -> float:
        """Compute combined Jaccard similarity.

        Combines node type similarity and pattern similarity.
        """
        types_a, patterns_a = self._get_features(fragment_a)
        types_b, patterns_b = self._get_features(fragment_b)

        # Jaccard for node types
        if types_a or types_b:
            type_jaccard = len(types_a & types_b) / len(types_a | types_b)
        else:
            type_jaccard = 0.0

        # Jaccard for patterns (weighted higher)
        if patterns_a or patterns_b:
            pattern_jaccard = len(patterns_a & patterns_b) / len(
                patterns_a | patterns_b
            )
        else:
            pattern_jaccard = 0.0

        # Weighted combination: patterns are more indicative of structure
        return 0.4 * type_jaccard + 0.6 * pattern_jaccard

    def find_similar_pairs(
        self, fragments: list[CodeFragment], threshold: float
    ) -> list[SimilarityPair]:
        """Find all pairs of fragments with similarity above threshold."""
        pairs = []
        self._cache.clear()

        for frag_a, frag_b in combinations(fragments, 2):
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

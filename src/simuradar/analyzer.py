"""Analysis orchestration - combines similarity and containment detection."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from .engines.similarity import AptedSimilarityEngine, group_similar_fragments
from .engines.jaccard import JaccardSimilarityEngine
from .engines.containment import WLHashContainmentEngine
from .parser import Parser


ProgressCallback = Callable[[str], None]


class SimilarityBackend(Enum):
    """Available similarity detection backends."""

    APTED = "apted"  # Tree edit distance (accurate, slow)
    JACCARD = "jaccard"  # Node set Jaccard (fast, approximate)


@dataclass
class FragmentInfo:
    """Serialized fragment information for reporting."""

    file: str
    type: str
    name: str
    lines: list[int]
    size: int


@dataclass
class SimilarityGroup:
    """A group of similar code fragments."""

    similarity: float
    fragments: list[FragmentInfo]


@dataclass
class AnalysisResult:
    """Complete analysis result."""

    analyzed_files: int
    total_fragments: int
    threshold: float
    duplicate_rate: float
    similarity_groups: list[SimilarityGroup]
    containment_pairs: list[dict]


class Analyzer:
    """Orchestrates similarity and containment detection."""

    def __init__(
        self,
        threshold: float = 0.8,
        min_size: int = 5,
        backend: SimilarityBackend = SimilarityBackend.JACCARD,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self.threshold = threshold
        self.min_size = min_size
        self.backend = backend
        self.progress_callback = progress_callback or (lambda x: None)
        self.parser = Parser()

        if backend == SimilarityBackend.APTED:
            self.similarity_engine = AptedSimilarityEngine()
        else:
            self.similarity_engine = JaccardSimilarityEngine()

        self.containment_engine = WLHashContainmentEngine()

    def analyze(self, path: Path) -> AnalysisResult:
        """Run complete analysis on a path."""
        self.progress_callback(f"Parsing files in {path}...")

        fragments = self.parser.collect_fragments(path, min_size=self.min_size)

        if not fragments:
            return AnalysisResult(
                analyzed_files=0,
                total_fragments=0,
                threshold=self.threshold,
                duplicate_rate=0.0,
                similarity_groups=[],
                containment_pairs=[],
            )

        analyzed_files = len(set(f.file_path for f in fragments))
        self.progress_callback(
            f"Found {len(fragments)} fragments in {analyzed_files} files. "
            f"Computing similarity ({self.backend.value})..."
        )

        similar_pairs = self.similarity_engine.find_similar_pairs(
            fragments, self.threshold
        )

        self.progress_callback(f"Found {len(similar_pairs)} similar pairs. Grouping...")

        similar_groups = group_similar_fragments(similar_pairs)

        similarity_groups = []
        for group in similar_groups:
            if len(group) < 2:
                continue

            max_sim = 0.0
            for pair in similar_pairs:
                if pair.fragment_a in group and pair.fragment_b in group:
                    max_sim = max(max_sim, pair.similarity)

            similarity_groups.append(
                SimilarityGroup(
                    similarity=max_sim,
                    fragments=[
                        FragmentInfo(
                            file=str(f.file_path),
                            type=f.fragment_type,
                            name=f.name,
                            lines=list(f.lines),
                            size=f.size,
                        )
                        for f in group
                    ],
                )
            )

        self.progress_callback(
            f"Found {len(similarity_groups)} similar groups. Checking containment..."
        )

        containment_pairs = self.containment_engine.find_containments(
            fragments, self.min_size
        )

        self.progress_callback(
            f"Found {len(containment_pairs)} containment pairs. Generating report..."
        )

        involved_fragments = set()
        for group in similarity_groups:
            for f in group.fragments:
                involved_fragments.add((f.file, f.name))

        for pair in containment_pairs:
            involved_fragments.add((str(pair.container.file_path), pair.container.name))
            involved_fragments.add((str(pair.contained.file_path), pair.contained.name))

        total_unique = len(set((f.file_path, f.name) for f in fragments))
        duplicate_rate = (
            len(involved_fragments) / total_unique if total_unique > 0 else 0.0
        )

        containment_output = [
            {
                "container": FragmentInfo(
                    file=str(pair.container.file_path),
                    type=pair.container.fragment_type,
                    name=pair.container.name,
                    lines=list(pair.container.lines),
                    size=pair.container.size,
                ),
                "contained": FragmentInfo(
                    file=str(pair.contained.file_path),
                    type=pair.contained.fragment_type,
                    name=pair.contained.name,
                    lines=list(pair.contained.lines),
                    size=pair.contained.size,
                ),
            }
            for pair in containment_pairs
        ]

        return AnalysisResult(
            analyzed_files=analyzed_files,
            total_fragments=len(fragments),
            threshold=self.threshold,
            duplicate_rate=duplicate_rate,
            similarity_groups=similarity_groups,
            containment_pairs=containment_output,
        )

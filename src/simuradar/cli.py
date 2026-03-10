"""CLI entry point for Simuradar."""

from pathlib import Path
from typing import Literal

import cyclopts
from rich.console import Console

from .analyzer import Analyzer, SimilarityBackend
from .report import OutputFormat, format_result


def main(
    path: Path,
    threshold: float = 0.8,
    min_size: int = 5,
    backend: Literal["apted", "jaccard"] = "jaccard",
    output: Path | None = None,
    format: Literal["text", "json"] = "text",
) -> None:
    """Analyze code for duplication and containment.

    Parameters
    ----------
    path
        Directory or Python file to analyze.
    threshold
        Similarity threshold (0.0 to 1.0). Fragments with similarity
        above this threshold are considered duplicates.
    min_size
        Minimum AST node count to consider a fragment.
    backend
        Similarity detection backend: 'apted' (accurate, slow) or
        'jaccard' (fast, approximate). Default: 'jaccard'.
    output
        Output file path. If not specified, prints to stdout.
    format
        Output format: 'text' for Rich formatted output, 'json' for JSON.
    """
    # Validate inputs
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")
    if min_size < 1:
        raise ValueError("min_size must be at least 1")

    # Setup console for progress output
    console = Console()

    def progress(msg: str) -> None:
        console.print(f"[dim]{msg}[/dim]")

    # Run analysis
    analyzer = Analyzer(
        threshold=threshold,
        min_size=min_size,
        backend=SimilarityBackend(backend),
        progress_callback=progress,
    )
    result = analyzer.analyze(path)

    # Output
    output_format = OutputFormat(format)
    output_console = Console(file=open(output, "w") if output else None)
    formatted = format_result(result, output_format, output_console)

    if formatted and output:
        output.write_text(formatted, encoding="utf-8")
    elif formatted:
        print(formatted)


def run() -> None:
    """Entry point for the CLI."""
    cyclopts.run(main)


if __name__ == "__main__":
    run()

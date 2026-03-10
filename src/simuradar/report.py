"""Report generation - JSON and Rich text output."""

import json
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .analyzer import AnalysisResult, SimilarityGroup


class OutputFormat(Enum):
    """Supported output formats."""

    TEXT = "text"
    JSON = "json"


def format_json(result: AnalysisResult) -> str:
    """Format analysis result as JSON."""
    data = {
        "meta": {
            "analyzed_files": result.analyzed_files,
            "total_fragments": result.total_fragments,
            "threshold": result.threshold,
            "duplicate_rate": f"{result.duplicate_rate:.2%}",
        },
        "similarity_groups": [
            {
                "similarity": f"{group.similarity:.2%}",
                "fragments": [
                    {
                        "file": f.file,
                        "type": f.type,
                        "name": f.name,
                        "lines": f.lines,
                        "size": f.size,
                    }
                    for f in group.fragments
                ],
            }
            for group in result.similarity_groups
        ],
        "containment_pairs": result.containment_pairs,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_text(result: AnalysisResult, console: Console) -> None:
    """Format and print analysis result using Rich."""
    # Summary panel
    console.print()
    console.print(
        Panel(
            f"[bold]Analyzed Files:[/bold] {result.analyzed_files}\n"
            f"[bold]Total Fragments:[/bold] {result.total_fragments}\n"
            f"[bold]Threshold:[/bold] {result.threshold:.0%}\n"
            f"[bold]Duplicate Rate:[/bold] [red]{result.duplicate_rate:.2%}[/red]",
            title="[bold cyan]Analysis Summary[/bold cyan]",
            border_style="cyan",
        )
    )

    # Similarity groups
    if result.similarity_groups:
        console.print()
        console.print(
            f"[bold yellow]Similarity Groups ({len(result.similarity_groups)})[/bold yellow]"
        )

        for i, group in enumerate(result.similarity_groups, 1):
            table = Table(
                title=f"Group {i}: {group.similarity:.1%} Similar",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("File", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Name", style="green")
            table.add_column("Lines", justify="right")
            table.add_column("Size", justify="right", style="dim")

            for f in group.fragments:
                table.add_row(
                    f.file,
                    f.type,
                    f.name,
                    f"{f.lines[0]}-{f.lines[1]}",
                    str(f.size),
                )

            console.print(table)
    else:
        console.print()
        console.print("[dim]No similar fragment groups found above threshold.[/dim]")

    # Containment pairs
    if result.containment_pairs:
        console.print()
        console.print(
            f"[bold yellow]Containment Pairs ({len(result.containment_pairs)})[/bold yellow]"
        )

        table = Table(
            title="Contained Fragments",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Container File", style="cyan")
        table.add_column("Container", style="green")
        table.add_column("Contained File", style="cyan")
        table.add_column("Contained", style="yellow")

        for pair in result.containment_pairs:
            container = pair["container"]
            contained = pair["contained"]
            table.add_row(
                container["file"],
                container["name"],
                contained["file"],
                contained["name"],
            )

        console.print(table)
    else:
        console.print()
        console.print("[dim]No containment relationships found.[/dim]")

    console.print()


def format_result(
    result: AnalysisResult,
    output_format: OutputFormat,
    console: Console | None = None,
) -> str | None:
    """Format analysis result based on output format.

    Returns the formatted string for JSON, or None for text (printed directly).
    """
    if output_format == OutputFormat.JSON:
        return format_json(result)
    else:
        if console is None:
            console = Console()
        format_text(result, console)
        return None

"""Viswall CLI output formatting."""

import json
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table


console = Console()


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    console.print_json(json.dumps(data, default=str))


def print_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> None:
    """Print list of dicts as a table."""
    if not data:
        console.print("[dim]No data.[/dim]")
        return

    if columns is None:
        columns = list(data[0].keys())

    table = Table(title=title, show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(str(col))

    for row in data:
        table.add_row(*[str(row.get(col, "")) for col in columns])

    console.print(table)


def print_result(data: Any, format: str = "table", columns: Optional[List[str]] = None) -> None:
    """Print result in specified format."""
    if format == "json":
        print_json(data)
    elif format == "table":
        if isinstance(data, list):
            print_table(data, columns=columns)
        else:
            print_json(data)
    else:
        console.print(str(data))


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}")

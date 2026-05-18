"""Terminal output formatting using rich.

All user-visible output from the CLI goes through this module so that
formatting decisions are centralised and check functions stay pure.
"""

from __future__ import annotations

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from preventdm_cli.checks import CheckResult

_console = Console(highlight=False)


def print_header(title: str) -> None:
    """Print a styled header panel with the tool name and the given title."""
    _console.print(
        Panel(
            f"[bold cyan]PreventDM CLI[/bold cyan]\n[dim]{title}[/dim]",
            border_style="cyan",
            expand=False,
        )
    )
    _console.print()


def print_check_result(result: CheckResult) -> None:
    """Print a single check result with a coloured indicator, timing, and message."""
    if result.passed:
        icon = "[bold green]PASS[/bold green]"
        name_style = "green"
    else:
        icon = "[bold red]FAIL[/bold red]"
        name_style = "red"

    elapsed_ms = result.elapsed_seconds * 1000
    _console.print(
        f"  {icon} [{name_style}]Check {result.number}[/{name_style}]"
        f" - {result.name}"
        f" [dim]({elapsed_ms:.0f} ms)[/dim]"
        f"  {result.message}"
    )


def print_summary(results: list[CheckResult], total_elapsed: float) -> None:
    """Print a summary table of all check results and an overall verdict."""
    _console.print()

    table = Table(title="Results", box=ROUNDED, show_lines=False)
    table.add_column("#", style="bold", width=3, justify="right")
    table.add_column("Check", min_width=28)
    table.add_column("Status", width=6, justify="center")
    table.add_column("ms", width=6, justify="right")
    table.add_column("Message")

    for r in results:
        if r.passed:
            status_cell = "[bold green]PASS[/bold green]"
        else:
            status_cell = "[bold red]FAIL[/bold red]"
        table.add_row(
            str(r.number),
            r.name,
            status_cell,
            f"{r.elapsed_seconds * 1000:.0f}",
            r.message,
        )

    _console.print(table)

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    if passed == total and total > 0:
        verdict = "[bold green]PASSED[/bold green]"
    else:
        verdict = "[bold red]FAILED[/bold red]"

    _console.print(
        f"\n  {passed}/{total} checks passed"
        f"  [dim]({total_elapsed:.2f}s total)[/dim]"
        f"  --  {verdict}\n"
    )


def print_service_health(service: str, url: str, healthy: bool, status_code: int) -> None:
    """Print the health status of one service for the health command."""
    label_style = "green" if healthy else "red"
    icon_markup = f"[bold {label_style}]{'OK  ' if healthy else 'FAIL'}[/bold {label_style}]"
    status_text = f"HTTP {status_code}" if status_code > 0 else "unreachable"
    label = "healthy" if healthy else "unhealthy"
    _console.print(
        f"  {icon_markup}  [{label_style}]{service:<16}[/{label_style}]"
        f"  {url}"
        f"  [dim][{status_text}][/dim]"
        f"  [{label_style}]{label}[/{label_style}]"
    )


def print_info(message: str) -> None:
    """Print a plain informational message."""
    _console.print(message)

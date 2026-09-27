"""Rich console rendering."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from conventionguardian.diff import unified_diff
from conventionguardian.models import BATCH_LABELS, Category, Finding, Severity, ToolProfile

console = Console()

_SEV_STYLE = {
    Severity.CRITICAL: "bold red",
    Severity.DRIFT: "yellow",
    Severity.OPTIONAL: "dim",
}

_CATEGORY_TITLES = {
    Category.STRUCTURE: "A. Project Structure",
    Category.NAMING: "B. Naming Conventions",
    Category.IMPORTS: "C. Imports & Module Organization",
    Category.FORMATTING: "D. Formatting & Pure Style",
    Category.DOCS: "E. Documentation Style",
    Category.TOOLING: "F. Configuration & Tooling",
    Category.MISC: "G. Additional Pure-Structure Issues",
}


def print_scan_table(profile: ToolProfile, target: str | None = None) -> None:
    table = Table(title="ConventionGuardian — project scan", show_header=False)
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    for k, v in profile.summary_rows():
        table.add_row(k, v)
    console.print(table)
    if target:
        console.print(f"Target convention set: [bold green]{target}[/bold green]")


def _finding_line(f: Finding) -> Text:
    sev = Text(f.severity.value, style=_SEV_STYLE.get(f.severity, ""))
    loc = f.path.name if f.path.is_file() else str(f.path)
    line = Text()
    line.append(f"{f.id}  ", style="bold cyan")
    line.append(sev)
    line.append(f"  {loc} — {f.message}")
    return line


def print_audit(findings: list[Finding]) -> None:
    """Print the full audit report grouped by category with diffs."""
    if not findings:
        console.print("[green]No convention findings. Clean project![/green]")
        return
    by_cat: dict[Category, list[Finding]] = {}
    for f in findings:
        by_cat.setdefault(f.category, []).append(f)

    for category in Category:
        group = by_cat.get(category)
        if not group:
            continue
        console.rule(f"[bold]{_CATEGORY_TITLES[category]}")
        for f in group:
            console.print(_finding_line(f))
            if f.current or f.recommended:
                console.print(
                    f"    current: {f.current!r} -> recommended: {f.recommended!r}",
                    style="dim",
                )
            console.print(f"    confidence: {f.conf}%  — {f.rationale}", style="dim")
            if f.conf == 100 and f.fix is not None:
                diff = _diff_for(f)
                if diff:
                    console.print(Syntax(diff, "diff", theme="ansi_dark", padding=0))

    applicable = [f for f in findings if f.conf == 100 and f.fix is not None]
    console.print()
    console.print(
        Panel(
            "Batches: " + ", ".join(f"[bold]{b}[/bold]" for b in BATCH_LABELS)
            + f"\nApplicable (auto-fixable): [green]{len(applicable)}[/green]"
            + f"   Manual review: [yellow]{len(findings) - len(applicable)}[/yellow]",
            title="Selectable batches",
        )
    )
    console.print(
        "[bold]Which batches or individual items shall I apply?[/bold] "
        '(e.g. "cg apply --batch formatting" or "cg apply --ids N-001,F-002")'
    )


def _diff_for(f: Finding) -> str | None:
    try:
        ch = f.materialize()
    except (OSError, ValueError):
        return None
    if ch is None or not ch.changed:
        return None
    return unified_diff(ch.old_content, ch.new_content, f.path)


def print_apply_result(result: dict) -> int:
    """Print apply outcome; returns process exit code."""
    if result.get("dry_run"):
        changes = result.get("changes", [])
        console.print(f"[bold]Dry run:[/bold] {len(changes)} file(s) would change:")
        for ch in changes:
            console.print(f"  - {ch.path}")
            console.print(
                Syntax(
                    unified_diff(ch.old_content, ch.new_content, ch.path),
                    "diff",
                    theme="ansi_dark",
                    padding=0,
                )
            )
        skipped = result.get("skipped", [])
        if skipped:
            console.print(f"[dim]{len(skipped)} finding(s) had no material change.[/dim]")
        return 0

    if result.get("reverted"):
        console.print("[bold red]Batch REVERTED — verification failed.[/bold red]")
        console.print(f"Reason: {result.get('reason')}")
        for fpath in result.get("files", []):
            console.print(f"  reverted: {fpath}")
        return 1

    applied = result.get("applied", [])
    branch = result.get("branch")
    console.print(f"[bold green]Applied {len(applied)} file change(s)"
                  + (f" on branch {branch}" if branch else "") + ".[/bold green]")
    for p in applied:
        console.print(f"  - {p}")
    verified = result.get("verified", [])
    if verified:
        console.print(f"Verification passed: {', '.join(verified)}")
    for f in result.get("review_only", []):
        console.print(f"[yellow]manual review only: {f.id} {f.path.name}[/yellow]")
    return 0

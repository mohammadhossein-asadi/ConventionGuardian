"""ConventionGuardian CLI (cg)."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from conventionguardian import (
    applier,
    audit as audit_mod,
    adopt as adopt_mod,
    checks,
    safety,
    scanner,
    styleguide,
)
from conventionguardian.config import TARGETS, load_config, save_config
from conventionguardian.models import BATCH_LABELS
from conventionguardian.reporters import console as rpt
from conventionguardian.reporters.markdown import write_markdown

app = typer.Typer(
    name="cg",
    help="Zero-logic-change convention auditing and pure-style fixing.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()





def _target_label(config) -> str:
    return TARGETS.get(config.target, config.target)


@app.command()
def scan(
    target: str = typer.Option(None, "--target", "-t", help="Target convention set"),
) -> None:
    """Detect project type, tooling, and conventions; write .cg.toml if missing."""
    root = scanner.find_root()
    profile = scanner.detect_profile(root)
    rpt.print_scan_table(profile, target=_target_label(load_config(root)))
    if target:
        if target not in TARGETS:
            console.print(f"[red]Unknown target '{target}'. Options: {', '.join(TARGETS)}[/red]")
            raise typer.Exit(2)
        path = save_config(root, target)
        console.print(f"Wrote {path}")
    elif not (root / ".cg.toml").is_file():
        path = save_config(root, "internal")
        console.print(f"Wrote default {path} (target: internal consistency only)")


@app.command()
def audit(
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output"),
    formatter: bool = typer.Option(
        True, "--formatter/--no-formatter",
        help="Delegate formatting to the project's own formatter when configured",
    ),
) -> None:
    """Run the full A-G audit and print the report (never writes code)."""
    root = scanner.find_root()
    findings, profile = audit_mod.audit(root, use_formatter=formatter)
    if json_out:
        import json

        console.print_json(json.dumps(_findings_payload(root, profile, findings)))
    else:
        rpt.print_scan_table(profile)
        rpt.print_audit(findings)
        _maybe_hint_adapters(profile)


def _maybe_hint_adapters(profile) -> None:
    """When JS/TS/Go/Rust files exist but adapters aren't installed, say how to enable."""
    from conventionguardian.adapters import adapters_available, available_languages

    langs = set(profile.languages)
    wanted = {"JavaScript": "javascript", "TypeScript": "typescript", "Go": "go", "Rust": "rust"}
    missing = [v for k, v in wanted.items() if k in langs]
    if not missing or adapters_available():
        return
    have = available_languages()
    if all(have.get(m) for m in missing):
        return
    console.print(
        f"[dim]Language adapters for {', '.join(missing)} are not active; "
        "install with: pip install 'convention-guardian[adapters]'[/dim]"
    )


def _findings_payload(root, profile, findings):
    return {
        "root": str(root),
        "profile": {
            "languages": profile.languages,
            "formatters": profile.formatters,
            "linters": profile.linters,
            "tests": profile.tests,
        },
        "findings": [
            {
                "id": f.id,
                "category": f.category.value,
                "severity": f.severity.value,
                "path": str(f.path),
                "message": f.message,
                "current": f.current,
                "recommended": f.recommended,
                "conf": f.conf,
                "fix_id": f.fix_id,
                "applicable": f.conf == 100 and f.fix is not None,
            }
            for f in findings
        ],
    }


@app.command()
def show(finding_id: str = typer.Argument(..., help="e.g. N-001")) -> None:
    """Show full file context around a finding."""
    root = scanner.find_root()
    findings, _profile = audit_mod.audit(root)
    match = [f for f in findings if f.id == finding_id.upper()]
    if not match:
        console.print(f"[red]No finding {finding_id}[/red]")
        raise typer.Exit(1)
    f = match[0]
    console.print(f"[bold]{f.id}[/bold] {f.severity.value} — {f.message}")
    console.print(f"File: {f.path}")
    if f.path.is_file():
        lines = f.path.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, ln in enumerate(lines, start=1):
            console.print(f"{i:4d} | {ln}")


@app.command()
def apply(
    batch: str = typer.Option(None, "--batch", "-b", help="Batch name (formatting, imports, safe, ...)"),
    ids: str = typer.Option(None, "--ids", help="Comma-separated finding IDs"),
    allow_dirty: bool = typer.Option(False, "--allow-dirty", help="Skip dirty-tree check"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show diffs without writing"),
    timeout_s: int = typer.Option(120, "--timeout", help="Per-check timeout seconds"),
) -> None:
    """Apply an approved batch or specific IDs (safety branch + verify + revert)."""
    root = scanner.find_root()
    findings, _profile = audit_mod.audit(root)
    id_list = [i.strip() for i in ids.split(",")] if ids else None
    if not batch and not id_list:
        console.print("[red]Specify --batch or --ids.[/red]")
        console.print(f"Available batches: {', '.join(BATCH_LABELS)}")
        raise typer.Exit(2)
    try:
        result = applier.apply_findings(
            root,
            findings,
            batch=batch,
            ids=id_list,
            allow_dirty=allow_dirty,
            dry_run=dry_run,
            timeout_s=timeout_s,
        )
    except (applier.ApplyError, safety.SafetyError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    code = rpt.print_apply_result(result)
    if code:
        raise typer.Exit(code)


@app.command()
def verify(timeout_s: int = typer.Option(120, "--timeout")) -> None:
    """Run fast checks only (compileall/pytest/tsc/go build/cargo check)."""
    root = scanner.find_root()
    profile = scanner.detect_profile(root)
    plan = checks.build_plan(root, profile)
    if not plan:
        console.print("[yellow]No fast checks available for this project.[/yellow]")
        return
    results = checks.run_checks(root, plan, timeout_s=timeout_s)
    ok = True
    for r in results:
        status = "[green]PASS[/green]" if r.ok else "[red]FAIL[/red]"
        console.print(f"{status}  {r.command} ({r.duration_s}s)")
        if not r.ok:
            ok = False
            console.print(r.output)
    raise typer.Exit(0 if ok else 1)


@app.command()
def log() -> None:
    """Show the running applied/reverted log (.cg/log.json)."""
    root = scanner.find_root()
    log = applier.load_log(root)
    entries = log.get("applied", [])
    if not entries:
        console.print("[dim]No apply history yet.[/dim]")
        return
    for e in entries:
        status = e.get("status", "?")
        style = "green" if status == "applied" else "red"
        console.print(f"[{style}]{status:>8}[/{style}] {e.get('ts','')} batch={e.get('batch','')!r} "
                      f"ids={','.join(e.get('ids', []))} files={len(e.get('files', []))}")


@app.command()
def report(
    out: Path = typer.Option(None, "--out", "-o", help="Output path (.md or .json)"),
) -> None:
    """Write a markdown (default report.md) or JSON report file."""
    root = scanner.find_root()
    findings, profile = audit_mod.audit(root)
    if out is None:
        out = Path("report.md")
    if out.suffix == ".json":
        from conventionguardian.audit import write_report_json

        write_report_json(out, root, profile, findings)
    else:
        write_markdown(out, root, profile, findings)
    console.print(f"Wrote {out}")


@app.command("init-styleguide")
def init_styleguide(
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
    json_out: bool = typer.Option(False, "--json", help="Machine-readable summary"),
    check: bool = typer.Option(
        False, "--check",
        help="No writes: verify committed artifacts match the current audit; exit 1 on drift",
    ),
) -> None:
    """Generate .editorconfig, pre-commit config, CI lint snippet and STYLEGUIDE.md
    derived from the current audit (skips existing files unless --force).

    With --check, regenerate in memory and compare against the git-tracked
    artifacts (CRLF and the generation date never count as drift). Exits 1 and
    prints diffs when a tracked artifact has drifted; missing or untracked
    artifacts are reported as "not armed" and do not fail the run."""
    root = scanner.find_root()
    findings, profile = audit_mod.audit(root)
    config = load_config(root)
    files = scanner.iter_files(root, config)
    plan = styleguide.build_styleguide(root, findings, profile, files)
    if check:
        rep = styleguide.check_styleguide(root, plan)
        if json_out:
            import json

            console.print_json(
                json.dumps(
                    {
                        "root": str(root),
                        "ok": rep.ok,
                        "drifted": rep.drifted,
                        "not_armed": rep.not_armed,
                    }
                )
            )
        else:
            for rel in rep.ok:
                console.print(f"[green]ok[/green] {rel}")
            for rel in rep.drifted:
                console.print(f"[red]drifted[/red] {rel}")
                console.print(rep.diffs[rel])
            for rel in rep.not_armed:
                console.print(f"[dim]not armed (untracked or missing)[/dim] {rel}")
            if rep.drifted:
                console.print(
                    "[dim]Re-run with --force to regenerate the drifted files, "
                    "then commit them.[/dim]"
                )
            elif rep.ok:
                console.print("[green]All armed styleguide artifacts are up to date.[/green]")
        raise typer.Exit(1 if rep.drifted else 0)
    written, skipped = styleguide.write_styleguide(root, plan, force=force)
    if json_out:
        import json

        console.print_json(
            json.dumps(
                {
                    "root": str(root),
                    "written": written,
                    "skipped": skipped,
                    "notes": plan.notes,
                }
            )
        )
        return
    for rel in written:
        console.print(f"[green]wrote[/green] {rel}")
    for rel in skipped:
        console.print(f"[yellow]skipped (exists; use --force)[/yellow] {rel}")
    for note in plan.notes:
        console.print(f"[dim]{note}[/dim]")
    if skipped:
        console.print("[dim]Re-run with --force to overwrite skipped files.[/dim]")


@app.command()
def adopt(
    force: bool = typer.Option(
        False, "--force", help="Scaffold even when the styleguide drift gate fails"
    ),
    allow_dirty: bool = typer.Option(False, "--allow-dirty", help="Skip dirty-tree check"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the plan without writing"),
    timeout_s: int = typer.Option(120, "--timeout", help="Per-check timeout seconds"),
) -> None:
    """One guided onboarding pass: apply the safe batch on a fresh branch, then
    scaffold the styleguide (converged) — with drift gate and verification."""
    root = scanner.find_root()
    try:
        res = adopt_mod.adopt(
            root,
            force=force,
            allow_dirty=allow_dirty,
            dry_run=dry_run,
            timeout_s=timeout_s,
        )
    except adopt_mod.AdoptError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    if dry_run:
        console.print("[bold]Dry run — nothing was written.[/bold]")
        console.print(
            f"Audit basis: {res.findings_total} findings "
            f"({res.findings_applicable} auto-fixable)."
        )
        console.print("Plan: apply `safe` batch on a fresh cg/convention-<ts> branch, then scaffold:")
        for rel in adopt_mod.ARTIFACT_ORDER:
            state = "exists (kept)" if rel in res.skipped_scaffold else "will be written"
            console.print(f"  {rel} — {state}")
        return
    if res.branch:
        console.print(f"[green]branch[/green] {res.branch}")
    if res.applied:
        console.print(f"[green]applied[/green] {len(res.applied)} file(s) via the safe batch")
    else:
        console.print("[dim]safe batch: nothing to apply[/dim]")
    if res.reverted:
        console.print(f"[red]safe batch reverted:[/red] {res.reason}")
    if res.verify:
        console.print(f"[green]verified[/green] {', '.join(res.verify)}")
    else:
        console.print("[dim]no fast checks available; nothing to verify[/dim]")
    for rel in res.written:
        console.print(f"[green]wrote[/green] {rel}")
    for rel in res.skipped_scaffold:
        console.print(f"[dim]kept existing[/dim] {rel}")
    console.print(
        "[dim]Next: review the branch, commit and merge. "
        "`cg init-styleguide --check` keeps the scaffold honest.[/dim]"
    )
    if not res.ok:
        raise typer.Exit(1)


def app_main() -> None:
    app()


if __name__ == "__main__":
    app_main()

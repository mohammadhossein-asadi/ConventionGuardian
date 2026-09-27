"""Guided onboarding (cg adopt): scaffold + safe batch + verify in one pass.

``cg adopt`` is the one-command entry point for a new project:

1. Audit and select the ``safe`` batch (confidence-100 findings only).
2. Apply it on a fresh safety branch with backups, verification, and
   auto-revert — the standard applier pipeline. Code changes come first so a
   failed verification leaves no scaffolding behind.
3. Scaffold the styleguide artifacts (.editorconfig, pre-commit config, CI
   snippet, STYLEGUIDE.md) with one convergence pass: arming .editorconfig
   resolves tooling findings, which shifts the STYLEGUIDE.md audit snapshot,
   so files created by this run are regenerated once against the post-arm
   audit. Artifacts that already exist are never touched.
4. Summarize every step; the caller renders it.

Refusals (AdoptError): non-git repo, dirty worktree (unless allow_dirty), or
a failed styleguide drift gate (unless force). dry_run=True audits, runs the
gate, and reports the plan without writing anything.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from conventionguardian import applier, audit as audit_mod, safety, scanner, styleguide


class AdoptError(RuntimeError):
    """Raised when adopt cannot run safely (dirty tree, failed gate, no git)."""


# Display order for scaffold artifacts in CLI output.
ARTIFACT_ORDER = (
    ".editorconfig",
    ".pre-commit-config.yaml",
    ".cg/ci-lint.yml",
    "STYLEGUIDE.md",
)


@dataclass
class AdoptResult:
    """Outcome of one ``cg adopt`` run."""

    branch: str | None = None
    applied: list[Path] = field(default_factory=list)
    reverted: bool = False
    reason: str = ""
    skipped_apply: str = ""  # "" = applied; "dry-run" in dry-run mode
    written: list[str] = field(default_factory=list)
    skipped_scaffold: list[str] = field(default_factory=list)
    drift_gate: list[str] = field(default_factory=list)
    verify: list[str] = field(default_factory=list)
    findings_total: int = 0
    findings_applicable: int = 0

    @property
    def ok(self) -> bool:
        return not self.reverted and not self.drift_gate


def _current_plan(root: Path) -> tuple[list, styleguide.StyleguidePlan]:
    findings, profile = audit_mod.audit(root)
    files = scanner.iter_files(root, None)
    plan = styleguide.build_styleguide(root, findings, profile, files)
    return findings, plan


def _write_scaffold(root: Path, result: AdoptResult) -> None:
    """Write artifacts, then one convergence pass over files THIS run created."""
    _findings, plan = _current_plan(root)
    pseudo = styleguide.StyleguidePlan(artifacts=plan.artifacts)
    written, skipped = styleguide.write_styleguide(root, pseudo)
    result.written.extend(written)
    result.skipped_scaffold.extend(skipped)
    if not written:
        return  # everything pre-existed: never touched, no convergence needed
    _findings2, plan2 = _current_plan(root)
    targets = {rel: c for rel, c in plan2.artifacts.items() if rel in set(written)}
    styleguide.write_styleguide(root, styleguide.StyleguidePlan(artifacts=targets), force=True)


def adopt(
    root: Path,
    *,
    force: bool = False,
    allow_dirty: bool = False,
    dry_run: bool = False,
    timeout_s: int = 120,
) -> AdoptResult:
    """Run the guided onboarding pass. See the module docstring for the flow."""
    root = Path(root).resolve()
    result = AdoptResult()

    if not safety.is_git_repo(root):
        raise AdoptError("Not a git repository; cg adopt needs git for its safety net.")
    dirty = safety.dirty_files(root)
    if dirty and not allow_dirty:
        raise AdoptError(
            "Working tree has uncommitted changes; commit or stash first "
            "(or use --allow-dirty)."
        )

    findings, profile = audit_mod.audit(root)
    result.findings_total = len(findings)
    result.findings_applicable = sum(1 for f in findings if not f.review_only())

    # Drift gate: refuse when armed styleguide artifacts no longer match the
    # current audit (they would be summarized inconsistently after the pass).
    _findings2, plan = _current_plan(root)
    rep = styleguide.check_styleguide(root, plan)
    result.drift_gate = list(rep.drifted)
    if rep.drifted and not force:
        raise AdoptError(
            "Styleguide drift gate failed for: "
            + ", ".join(rep.drifted)
            + ". Re-run with --force to scaffold over the drifted files."
        )

    if dry_run:
        result.skipped_apply = "dry-run"
        result.skipped_scaffold = [rel for rel in plan.artifacts if (root / rel).exists()]
        return result

    # Step 1: the safe batch on a fresh branch (code first — if verification
    # fails and the batch reverts, no scaffolding has been written yet).
    try:
        applied = applier.apply_findings(
            root,
            findings,
            batch="safe",
            allow_dirty=allow_dirty,
            timeout_s=timeout_s,
        )
    except (applier.ApplyError, safety.SafetyError) as exc:
        raise AdoptError(f"Safe batch failed: {exc}") from exc

    result.branch = applied["branch"]
    result.applied = [Path(p) for p in applied["applied"]]
    result.reverted = applied["reverted"]
    result.reason = applied.get("reason", "")
    result.verify = applied.get("verified", [])

    # Step 2: scaffold (converged). Runs even after a revert so the artifacts
    # are ready on the safety branch for the next attempt.
    _write_scaffold(root, result)
    return result

"""Apply approved findings with per-batch verification and auto-revert."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from pathlib import Path

from conventionguardian import checks, safety
from conventionguardian.audit import eligible_for_batch
from conventionguardian.models import FileChange, Finding
from conventionguardian.scanner import detect_profile


class ApplyError(RuntimeError):
    pass


def resolve_selection(
    findings: list[Finding], batch: str | None, ids: list[str] | None
) -> list[Finding]:
    """Resolve --batch and/or --ids into a deduplicated list of findings.

    Selecting one member of a multi-file fix group (e.g. a cross-file rename)
    automatically selects every other member, so partial groups are never
    applied — a partial rename would break callers and fail verification.
    """
    selected: list[Finding] = []
    if batch:
        selected.extend(eligible_for_batch(findings, batch))
    if ids:
        by_id = {f.id: f for f in findings}
        for i in ids:
            if i not in by_id:
                raise ApplyError(f"Unknown finding id: {i}")
            selected.append(by_id[i])

    # Expand coordinated fix groups only (e.g. cross-file renames): a partial
    # rename would break callers. Non-coordinated fixes (e.g. per-file import
    # ordering) are never expanded — only explicitly approved items are applied.
    selected_groups = {f.group for f in selected if f.group}
    if selected_groups:
        selected.extend(
            f for f in findings if f.group in selected_groups and f not in selected
        )

    unique: list[Finding] = []
    seen: set[str] = set()
    for f in selected:
        if f.id not in seen:
            seen.add(f.id)
            unique.append(f)
    return unique


def materialize_all(
    findings: list[Finding],
) -> tuple[list[FileChange], list[Finding]]:
    """Materialize applicable findings into FileChanges (dedup by path).

    Returns (changes, skipped): skipped covers review-only-style leftovers,
    no-op fixes, and second fixes targeting an already-changed file.
    """
    by_path: dict[Path, FileChange] = {}
    skipped: list[Finding] = []
    for f in findings:
        ch = f.materialize()
        if ch is None or not ch.changed:
            skipped.append(f)
        elif ch.path in by_path:
            skipped.append(f)
        else:
            by_path[ch.path] = ch
    return list(by_path.values()), skipped


def _backup_path(root: Path, ch: FileChange) -> Path:
    digest = hashlib.sha1(str(ch.path).encode("utf-8")).hexdigest()[:8]
    # fix_ids are free-form and may contain characters that are illegal in
    # filenames (e.g. the colon in "fn-rename:prepareData", which Windows
    # parses as an ADS separator and CopyFile2 rejects with WinError 87).
    safe_fix_id = re.sub(r"[^A-Za-z0-9._-]", "_", ch.fix_id)
    return root / ".cg" / "backup" / f"{ch.path.name}.{safe_fix_id}.{digest}.bak"


def write_changes(root: Path, changes: list[FileChange]) -> None:
    """Back up each file under .cg/backup, then write the new content."""
    backup_dir = root / ".cg" / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for ch in changes:
        shutil.copy2(ch.path, _backup_path(root, ch))
        ch.path.write_text(ch.new_content, encoding="utf-8", newline="")


def revert_changes(root: Path, changes: list[FileChange]) -> None:
    """Restore originals from backups, then remove the backups."""
    for ch in changes:
        backup = _backup_path(root, ch)
        if backup.is_file():
            shutil.copy2(backup, ch.path)
    delete_backups(root, changes)


def delete_backups(root: Path, changes: list[FileChange]) -> None:
    for ch in changes:
        backup = _backup_path(root, ch)
        if backup.is_file():
            backup.unlink()


def load_log(root: Path) -> dict:
    """Load .cg/log.json, returning {"applied": [...], "remaining": [...]}."""
    path = root / ".cg" / "log.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"applied": [], "remaining": []}


def save_log(root: Path, log: dict) -> None:
    path = root / ".cg" / "log.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=2), encoding="utf-8")


def apply_findings(
    root: Path,
    findings: list[Finding],
    batch: str | None = None,
    ids: list[str] | None = None,
    allow_dirty: bool = False,
    dry_run: bool = False,
    timeout_s: int = 120,
) -> dict:
    """Apply the selected batch/ids with safety net and verification.

    Flow: resolve selection -> materialize (no writes) -> safety branch ->
    write (with backups) -> verify -> revert on failure -> update log.
    In dry-run mode no writes occur and no branch is created.
    """
    root = Path(root).resolve()
    selected = resolve_selection(findings, batch, ids)
    review_only = [f for f in selected if f.review_only()]
    applicable = [f for f in selected if not f.review_only()]
    changes, skipped = materialize_all(applicable)

    if dry_run:
        return {
            "dry_run": True,
            "changes": changes,
            "skipped": skipped,
            "review_only": review_only,
        }

    if not changes:
        return {
            "applied": [],
            "branch": None,
            "reverted": False,
            "skipped": skipped,
            "review_only": review_only,
            "verified": [],
        }

    branch = safety.assert_safe(root, allow_dirty=allow_dirty)
    write_changes(root, changes)

    profile = detect_profile(root)
    plan = checks.build_plan(root, profile)
    results = checks.run_checks(root, plan, timeout_s=timeout_s)
    failed = [r for r in results if not r.ok]

    if failed:
        revert_changes(root, changes)
        log = load_log(root)
        log["applied"].append(
            {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "batch": batch or "",
                "ids": [f.id for f in applicable],
                "status": "reverted",
                "reason": f"verification failed: {failed[0].command}",
                "files": [str(ch.path) for ch in changes],
            }
        )
        save_log(root, log)
        return {
            "applied": [],
            "branch": branch,
            "reverted": True,
            "reason": f"verification failed: {failed[0].command}",
            "failed_checks": [r.command for r in failed],
            "files": [str(ch.path) for ch in changes],
            "skipped": skipped,
            "review_only": review_only,
        }

    delete_backups(root, changes)
    log = load_log(root)
    log["applied"].append(
        {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "batch": batch or "",
            "ids": [f.id for f in applicable],
            "status": "applied",
            "checks": [r.command for r in results],
            "files": [str(ch.path) for ch in changes],
        }
    )
    save_log(root, log)
    return {
        "applied": [ch.path for ch in changes],
        "branch": branch,
        "reverted": False,
        "verified": [r.command for r in results],
        "skipped": skipped,
        "review_only": review_only,
    }

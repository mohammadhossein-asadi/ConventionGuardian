"""Git safety net: dirty-tree check, safety branch, SafetyError."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from rich.console import Console

console = Console()


class SafetyError(RuntimeError):
    pass


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def is_git_repo(root: Path) -> bool:
    return _run_git(root, "rev-parse", "--is-inside-work-tree").returncode == 0


def dirty_files(root: Path) -> list[str]:
    res = _run_git(root, "status", "--porcelain")
    if res.returncode != 0:
        return []
    return [ln for ln in res.stdout.splitlines() if ln.strip()]


def assert_safe(root: Path, allow_dirty: bool = False) -> str:
    """Refuse to write unless the tree is clean; then create a safety branch.

    Returns the created branch name. Raises SafetyError when unsafe.
    """
    if not is_git_repo(root):
        raise SafetyError("Not a git repository; ConventionGuardian refuses to write.")
    if dirty_files(root) and not allow_dirty:
        raise SafetyError(
            "Working tree has uncommitted changes. "
            "Commit or stash them first (or use --allow-dirty)."
        )
    branch = f"cg/convention-{time.strftime('%Y%m%d-%H%M%S')}"
    res = _run_git(root, "switch", "-c", branch)
    if res.returncode != 0:
        res = _run_git(root, "checkout", "-b", branch)
    if res.returncode != 0:
        raise SafetyError(f"Could not create safety branch: {res.stderr.strip()}")
    console.print(f"[green]Created safety branch {branch}[/green]")
    return branch

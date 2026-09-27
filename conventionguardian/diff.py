"""Unified diff helpers."""

from __future__ import annotations

import difflib
from pathlib import Path


def unified_diff(old: str, new: str, path: Path | str, context: int = 3) -> str:
    """Return a unified diff between old and new content for the given path."""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    posix = Path(path).as_posix()
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{posix}",
        tofile=f"b/{posix}",
        n=context,
    )
    return "".join(diff)

"""Finding, ToolProfile and audit data models."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import hashlib


class Category(str, Enum):
    STRUCTURE = "structure"
    NAMING = "naming"
    IMPORTS = "imports"
    FORMATTING = "formatting"
    DOCS = "docs"
    TOOLING = "tooling"
    MISC = "misc"


class Severity(str, Enum):
    CRITICAL = "Critical inconsistency"
    DRIFT = "Style drift"
    OPTIONAL = "Optional improvement"


BATCH_LABELS = {
    "structure": "Batch Structure Moves",
    "naming": "Batch Naming",
    "imports": "Batch Import Order",
    "formatting": "Batch Formatting",
    "docs": "Batch Docs",
    "tooling": "Batch Config Alignment",
    "misc": "Batch Misc",
    "high-impact": "High-Impact Only",
    "safe": "All Safe Items",
}


class Source(str, Enum):
    SCAN = "scan"
    AUDIT = "audit"


class Action(str, Enum):
    APPLY = "apply"
    REVERT = "revert"
    FAIL = "fail"


@dataclass
class FileChange:
    """A materialized change to a single file, ready to write."""

    path: Path
    old_content: str
    new_content: str
    fix_id: str

    @property
    def changed(self) -> bool:
        return self.old_content != self.new_content


@dataclass
class Finding:
    """One audit observation.

    materialize() must return a byte-identical diff every call for a given
    (path, fix_id, conf) triple. Set conf to a value below 100 to mark the
    item as manual-review only (no diff, never applied).
    """

    category: Category
    severity: Severity
    path: Path
    message: str
    current: str = ""
    recommended: str = ""
    conf: int = 100
    rationale: str = ""
    fix_id: str = ""
    fix: Any = None
    id: str = ""
    group: str = ""  # non-empty only for coordinated cross-file fixes (e.g. renames)
    delegate: str = ""  # formatter name for tool-delegated fixes (e.g. "Ruff")

    def key(self) -> tuple:
        return (str(self.path), self.fix_id, self.conf, self.message)

    def stable_suffix(self) -> str:
        return hashlib.sha1(str(self.key()).encode("utf-8")).hexdigest()[:4]

    def review_only(self) -> bool:
        return self.conf < 100 or self.fix is None

    def materialize(self) -> FileChange | None:
        """Produce the FileChange for this finding, preserving original line endings.

        Content is processed with universal newlines and written back in the
        file's original dominant ending style — except the misc-crlf fix, whose
        explicit purpose is CRLF -> LF conversion.
        """
        if self.review_only():
            return None
        raw = Path(self.path).read_bytes()
        had_crlf = b"\r\n" in raw
        raw_text = raw.decode("utf-8", errors="replace")
        old_norm = raw_text.replace("\r\n", "\n")
        if self.fix_id == "misc-crlf":
            # The purpose of this fix IS newline conversion: run it on the raw
            # text, not the newline-normalized view (where it is a no-op), and
            # keep real endings in old/new so `changed` is truthful.
            new_lf = apply_fix(self.fix, raw_text)
            if new_lf == raw_text:
                return None
            return FileChange(
                path=self.path,
                old_content=raw_text,
                new_content=new_lf,
                fix_id=self.fix_id,
            )
        new_norm = apply_fix(self.fix, old_norm)
        if new_norm == old_norm:
            return None
        if had_crlf and self.fix_id != "misc-crlf" and not self.delegate:
            # Restore the file's dominant line endings — except for the CRLF
            # normalization fix and formatter-delegated fixes, whose output
            # line endings are the tool's own and must be preserved.
            new_final = new_norm.replace("\n", "\r\n")
            old_final = raw.decode("utf-8", errors="replace")
        else:
            new_final = new_norm
            old_final = old_norm
        return FileChange(
            path=self.path,
            old_content=old_final,
            new_content=new_final,
            fix_id=self.fix_id,
        )


@dataclass
class ToolProfile:
    """Detected languages, package managers, convention tooling, test framework."""

    root: Path = field(default_factory=Path.cwd)
    languages: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    configs: list[str] = field(default_factory=list)
    formatters: list[str] = field(default_factory=list)
    linters: list[str] = field(default_factory=list)
    monorepo: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    is_git: bool = False

    def summary_rows(self) -> list[tuple[str, str]]:
        join = lambda v: ", ".join(v) if v else "none"
        return [
            ("Root", str(self.root)),
            ("Languages", join(self.languages)),
            ("Package managers", join(self.package_managers)),
            ("Configs", join(self.configs)),
            ("Formatters", join(self.formatters)),
            ("Linters", join(self.linters)),
            ("Monorepo tools", join(self.monorepo)),
            ("Test frameworks", join(self.tests)),
            ("Git repo", "yes" if self.is_git else "no"),
        ]


def make_id(category: Category, findings: list[Finding]) -> str:
    """Next sequential ID within a category, e.g. N-004 for the fourth naming finding."""
    prefix = {"structure": "S", "naming": "N", "imports": "I", "formatting": "F",
              "docs": "D", "tooling": "T", "misc": "M"}[category.value]
    n = sum(1 for f in findings if f.category == category)
    return f"{prefix}-{n + 1:03d}"


def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def apply_fix(fix: Any, content: str) -> str:
    """Dispatch table for fix callables: each returns the new file content."""
    if callable(fix):
        return fix(content)
    if isinstance(fix, str):
        return fix
    if isinstance(fix, tuple) and len(fix) == 2:
        old, new = fix
        if old not in content:
            raise ValueError(f"Fix target {old!r} not found in content")
        return content.replace(old, new, 1)
    raise TypeError(f"Unsupported fix type: {type(fix)!r}")

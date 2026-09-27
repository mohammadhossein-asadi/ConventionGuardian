"""Project structure finder (category A).

Structure moves are the riskiest class of change (import paths shift), so all
items here are report-only recommendations (confidence 0, never auto-applied).
"""

from __future__ import annotations
from pathlib import Path

from conventionguardian.models import Category, Finding, Severity


def find_structure_issues(
    root: Path, files: list[Path], findings: list[Finding]
) -> None:
    """Collect project-level structure findings."""
    rel_files = [p.relative_to(root).as_posix() for p in files]
    py_files = [f for f in rel_files if f.endswith(".py")]
    root_py = [f for f in py_files if "/" not in f and f != "setup.py"]
    test_files = [f for f in py_files if f.startswith("tests/") or "/tests/" in f]

    # A1: source modules loose at the repo root
    if len(root_py) >= 5:
        findings.append(
            Finding(
                category=Category.STRUCTURE,
                severity=Severity.DRIFT,
                path=root,
                message=f"{len(root_py)} Python modules sit at the repository root",
                current="flat layout at repo root",
                recommended="src/ layout or a named package directory",
                conf=0,
                rationale="Moving modules changes import paths; needs coordinated manual move.",
                fix_id="struct-flat",
            )
        )

    # A2: tests missing entirely for a Python codebase
    if py_files and not test_files:
        findings.append(
            Finding(
                category=Category.STRUCTURE,
                severity=Severity.OPTIONAL,
                path=root,
                message="No tests directory detected",
                current="no tests/",
                recommended="tests/ directory with pytest discovery",
                conf=0,
                rationale="Advisory only.",
                fix_id="struct-tests",
            )
        )

    # A3: docs missing
    has_docs = any(f.startswith("docs/") for f in rel_files) or (root / "README.md").is_file()
    if py_files and not has_docs:
        findings.append(
            Finding(
                category=Category.STRUCTURE,
                severity=Severity.OPTIONAL,
                path=root,
                message="No docs directory or README",
                current="no docs/",
                recommended="docs/ directory or README.md",
                conf=0,
                rationale="Advisory only.",
                fix_id="struct-docs",
            )
        )

    # A4: root pollution — many top-level entries
    top_entries = [p for p in root.iterdir() if not p.name.startswith(".")]
    if len(top_entries) > 18:
        findings.append(
            Finding(
                category=Category.STRUCTURE,
                severity=Severity.OPTIONAL,
                path=root,
                message=f"{len(top_entries)} entries at repository root",
                current=f"{len(top_entries)} top-level entries",
                recommended="group configs into config/ or scripts/ subdirectories",
                conf=0,
                rationale="Advisory; moves can affect CI and tooling paths.",
                fix_id="struct-root-pollution",
            )
        )

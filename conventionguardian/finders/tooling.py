"""Configuration & tooling consistency finder (category F)."""

from __future__ import annotations

from pathlib import Path

from conventionguardian.models import Category, Finding, Severity


def find_tooling_issues(root: Path, files: list[Path], findings: list[Finding]) -> None:
    """Collect tooling/config findings."""
    names = {p.name for p in files} | {"README.md"}

    # F1: Python project without .editorconfig
    py = any(p.suffix == ".py" for p in files)
    if py and ".editorconfig" not in names:
        findings.append(
            Finding(
                category=Category.TOOLING,
                severity=Severity.OPTIONAL,
                path=root / ".editorconfig",
                message="No .editorconfig found for a Python project",
                current="missing .editorconfig",
                recommended="add .editorconfig (utf-8, lf, indent 4 spaces, trim trailing ws)",
                conf=0,
                rationale="Config content is advisory; generated only on request.",
                fix_id="tooling-editorconfig",
            )
        )

    # F2: formatter configured but not .editorconfig (misalignment hint)
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8", errors="replace")
        has_black = "[tool.black]" in text
        if has_black and ".editorconfig" not in names:
            findings.append(
                Finding(
                    category=Category.TOOLING,
                    severity=Severity.DRIFT,
                    path=pyproject,
                    message="Black configured but no .editorconfig to match",
                    current="Black without .editorconfig",
                    recommended="align .editorconfig with Black settings",
                    conf=0,
                    rationale="Advisory alignment item.",
                    fix_id="tooling-black-align",
                )
            )

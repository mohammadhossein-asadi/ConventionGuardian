"""Additional pure-structure finder (category G)."""

from __future__ import annotations
from pathlib import Path

from conventionguardian.models import Category, Finding, Severity

CRLF = "\r\n"


def find_misc_issues(
    tree: ast.AST, path: Path, findings: list[Finding]
) -> None:
    """Collect misc findings for one file."""
    if path.suffix == ".py":
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        if CRLF in text:
            findings.append(
                Finding(
                    category=Category.MISC,
                    severity=Severity.DRIFT,
                    path=path,
                    message="CRLF line endings in a Python source file",
                    current="CRLF",
                    recommended="LF",
                    conf=100,
                    rationale="Line-ending normalization; AST-equivalent.",
                    fix_id="misc-crlf",
                    fix=_to_lf,
                )
            )


def _to_lf(content: str) -> str:
    return content.replace("\r\n", "\n")


def find_test_naming_issues(
    root: Path, files: list[Path], findings: list[Finding]
) -> None:
    """Report test files not matching test_*.py pattern (report-only)."""
    testish = [
        p for p in files
        if p.name.endswith("_test.py") or (p.name.startswith("test") and not p.name.startswith("test_"))
    ]
    for p in testish:
        if p.name.endswith("_test.py"):
            findings.append(
                Finding(
                    category=Category.MISC,
                    severity=Severity.OPTIONAL,
                    path=p,
                    message="Test file naming deviates from test_*.py convention",
                    current=p.name,
                    recommended=f"test_{p.stem[:-len('_test')]}.py",
                    conf=0,
                    rationale="Renaming test modules can break discovery references.",
                    fix_id="misc-test-naming",
                )
            )

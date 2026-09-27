"""Documentation style finder (category E).

Non-behavioral only: never rewrites explanatory content. v1 reports public
functions/classes lacking docstrings as optional improvements (report-only).
Docstring reformatting is deferred to later versions.
"""

from __future__ import annotations
from pathlib import Path

import ast

from conventionguardian.models import Category, Finding, Severity


def find_docs_issues(tree: ast.AST, path: Path, findings: list[Finding]) -> None:
    """Report public defs without docstrings (report-only)."""
    missing = 0
    first: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | None = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            has_doc = (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            )
            if not has_doc:
                missing += 1
                if first is None:
                    first = node
    if missing and first is not None:
        findings.append(
            Finding(
                category=Category.DOCS,
                severity=Severity.OPTIONAL,
                path=path,
                message=f"{missing} public definition(s) lack a docstring "
                        f"(first: {first.name})",
                current="missing docstring",
                recommended="add docstrings",
                conf=0,
                rationale="Writing doc content is not a mechanical style fix.",
                fix_id="docs-missing",
            )
        )

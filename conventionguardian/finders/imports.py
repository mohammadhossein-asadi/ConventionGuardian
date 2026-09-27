"""Imports & module organization finder (category C)."""

from __future__ import annotations
from pathlib import Path

import ast

from conventionguardian.finders.fixers import sort_import_block
from conventionguardian.models import Category, Finding, Severity


def _make_local_roots_provider():
    """Module-level local-roots holder, set per audit run by audit()."""
    state = {"roots": ()}

    def set_roots(roots: tuple[str, ...]) -> None:
        state["roots"] = tuple(roots)

    def get_roots() -> tuple[str, ...]:
        return state["roots"]

    return set_roots, get_roots


_set_roots, _get_roots = _make_local_roots_provider()


def _remove_duplicate_import(content: str) -> str:
    """Delete later duplicate top-level single-name import lines."""
    tree = ast.parse(content)
    lines = content.split("\n")
    seen: set[str] = set()
    drop: set[int] = set()
    for node in tree.body:
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Import):
            if len(node.names) != 1:
                continue
            key = node.names[0].asname or node.names[0].name
        else:
            if len(node.names) != 1 or node.names[0].asname:
                continue
            key = f"{node.module}.{node.names[0].name}"
        if key in seen:
            drop.add(node.lineno - 1)
        else:
            seen.add(key)
    return "\n".join(ln for i, ln in enumerate(lines) if i not in drop)


def _regroup_imports(content: str) -> str:
    """Replace the leading contiguous top-level import block with grouped order."""
    tree = ast.parse(content)
    lines = content.split("\n")
    top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if not top:
        return content
    start = top[0].lineno - 1
    end = top[-1].end_lineno
    block = "\n".join(lines[start:end])
    new_block = sort_import_block(block, local_roots=_get_roots())
    if new_block == block:
        return content
    return "\n".join(lines[:start] + new_block.split("\n") + lines[end:])


def find_import_issues(
    tree: ast.AST, path: Path, findings: list[Finding], local_roots: tuple[str, ...] = ()
) -> None:
    """Collect import findings for one Python file.

    Records the project's local package roots so the regroup fix (which runs
    later, at apply time) classifies first-party imports correctly.
    """
    if local_roots:
        _set_roots(local_roots)
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]

    # C1: duplicate top-level imports
    seen: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Import):
            if len(node.names) != 1:
                continue
            key = node.names[0].asname or node.names[0].name
        else:
            if len(node.names) != 1 or node.names[0].asname:
                continue
            key = f"{node.module}.{node.names[0].name}"
        if key in seen:
            findings.append(
                Finding(
                    category=Category.IMPORTS,
                    severity=Severity.DRIFT,
                    path=path,
                    message=f"Duplicate import of '{key}'",
                    current=ast.get_source_segment(text, node) or key,
                    recommended="remove the redundant import line",
                    conf=100,
                    rationale="Removing a redundant import cannot change semantics.",
                    fix_id="imp-dup",
                    fix=_remove_duplicate_import,
                )
            )
            break
        seen.add(key)

    # C2: star imports (report-only)
    for node in imports:
        if isinstance(node, ast.ImportFrom) and any(
            a.name == "*" for a in node.names
        ):
            findings.append(
                Finding(
                    category=Category.IMPORTS,
                    severity=Severity.CRITICAL,
                    path=path,
                    message=f"Star import at line {node.lineno} (manual review only)",
                    current="from X import *",
                    recommended="explicit imports",
                    conf=0,
                    rationale="Expanding star imports requires scope analysis.",
                    fix_id="imp-star",
                )
            )
            break

    # C3: grouping/order of the leading top-level import block
    top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if len(top) >= 3:
        start = top[0].lineno - 1
        end = top[-1].end_lineno
        span_lines = lines[start:end]
        multi = any((n.end_lineno or n.lineno) > n.lineno for n in top)
        has_comments = any(ln.lstrip().startswith("#") for ln in span_lines)
        interleaved = any(
            not isinstance(n, (ast.Import, ast.ImportFrom)) and start <= n.lineno - 1 < end
            for n in tree.body
        )
        if multi or has_comments or interleaved:
            findings.append(
                Finding(
                    category=Category.IMPORTS,
                    severity=Severity.DRIFT,
                    path=path,
                    message="Import block ordering not verifiable automatically",
                    current="mixed import block",
                    recommended="stdlib -> third-party -> local",
                    conf=0,
                    rationale="Multi-line or commented import blocks need manual review.",
                    fix_id="imp-order",
                )
            )
        else:
            block = "\n".join(span_lines)
            sorted_block = sort_import_block(block, local_roots=local_roots)
            if sorted_block != block:
                findings.append(
                    Finding(
                        category=Category.IMPORTS,
                        severity=Severity.DRIFT,
                        path=path,
                        message="Import block is not grouped stdlib -> third-party -> local",
                        current=block[:200],
                        recommended="grouped order",
                        conf=100,
                        rationale="Pure reordering of top-level imports; same names bound.",
                        fix_id="imp-order",
                        fix=_regroup_imports,
                    )
                )

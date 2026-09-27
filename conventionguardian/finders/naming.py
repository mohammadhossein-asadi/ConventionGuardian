"""Naming conventions finder (category B).

Project-aware: a rename is only proposed when the same whole-word identifier
is renamed identically in every affected file, so callers and imports stay
consistent. Textual whole-word matching on non-definition lines is the
conservative superset of symbol uses (attribute uses like ``obj.name`` are
renamed too — safe for public API style-drift renames, which is the documented
v1 scope).
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path

from conventionguardian.finders.fixers import camel_to_snake, rename_identifier
from conventionguardian.models import Category, Finding, Severity


def _style_of(name: str) -> str:
    if name.startswith("_"):
        name = name[1:]
    if not name:
        return "other"
    if name.isupper() and len(name) > 1:
        return "screaming"
    if "_" in name:
        return "snake"
    if name[0].isupper():
        return "pascal"
    if name[0].islower():
        return "camel"
    return "other"


def find_project_naming_issues(
    root: Path, trees: dict[Path, ast.AST], findings: list[Finding]
) -> None:
    """Detect case-style drift in function names across the whole project."""
    # Count styles over all function defs.
    style_counts: Counter[str] = Counter()
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                style_counts[_style_of(node.name)] += 1

    if len(style_counts) < 2 or style_counts.get("snake", 0) < 1:
        return

    # Which files mention which candidate names (whole-word, textually)?
    file_texts: dict[Path, str] = {}
    for path in trees:
        try:
            file_texts[path] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            file_texts[path] = ""

    candidates: dict[str, list[Path]] = {}
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if _style_of(name) != "snake" and camel_to_snake(name) != name:
                    candidates.setdefault(name, []).append(path)

    for name, def_files in candidates.items():
        new = camel_to_snake(name)
        # Files that mention the identifier textually.
        affected = {
            p for p, text in file_texts.items()
            if re.search(rf"\b{re.escape(name)}\b", text)
        }
        if not affected:
            continue
        # One finding per affected file, all sharing fix_id = f"fn-rename:{name}".
        for path in sorted(affected):
            is_def = path in def_files
            findings.append(
                Finding(
                    category=Category.NAMING,
                    severity=Severity.DRIFT,
                    path=path,
                    message=(
                        f"Function '{name}' deviates from dominant snake_case style "
                        f"(cross-file rename to '{new}'"
                        + (", this file defines it" if is_def else ", this file uses it")
                        + ")"
                    ),
                    current=name,
                    recommended=new,
                    conf=100,
                    rationale=(
                        "Whole-word rename applied identically in every file that "
                        "mentions the identifier, keeping callers and imports consistent."
                    ),
                    fix_id=f"fn-rename:{name}",
                    group=f"fn-rename:{name}",
                    fix=lambda text, _o=name, _n=new: rename_identifier(text, _o, _n),
                )
            )

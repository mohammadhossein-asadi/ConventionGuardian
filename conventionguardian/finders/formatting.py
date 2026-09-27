"""Formatting & pure style finder (category D).

Text-only rules with zero-semantic-impact fixes. When the project has its own
formatter configured, callers may suppress this finder and run the formatter instead.
"""

from __future__ import annotations

import ast
from pathlib import Path

from conventionguardian.finders.fixers import (
    indent_tabs_to_spaces,
    normalize_final_newline,
)
from conventionguardian.models import Category, Finding, Severity

DEFAULT_MAX_LINE = 100


def _finding(
    path: Path,
    message: str,
    current: str,
    recommended: str,
    fix_id: str,
    fix: object,
    severity: Severity = Severity.DRIFT,
) -> Finding:
    return Finding(
        category=Category.FORMATTING,
        severity=severity,
        path=path,
        message=message,
        current=current,
        recommended=recommended,
        conf=100,
        rationale="Whitespace-only change; AST-equivalent source.",
        fix_id=fix_id,
        fix=fix,
    )


def find_formatting_issues(
    tree: ast.AST,
    path: Path,
    findings: list[Finding],
    max_line: int = DEFAULT_MAX_LINE,
) -> None:
    """Collect formatting findings for one Python file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    # D1: tab indentation while the file is otherwise space-indented
    tab_lines = [ln for ln in lines if ln.startswith("\t")]
    space_lines = [ln for ln in lines if ln.startswith(" ")]
    if tab_lines and len(tab_lines) <= len(space_lines):
        findings.append(
            _finding(
                path,
                f"Tab indentation on {len(tab_lines)} line(s) in a space-indented file",
                "tab indentation",
                "4-space indentation",
                "fmt-tabs",
                indent_tabs_to_spaces,
            )
        )

    # D2: missing final newline
    if text and not text.endswith("\n"):
        findings.append(
            _finding(
                path,
                "Missing final newline at EOF",
                "no trailing newline",
                "single trailing newline",
                "fmt-final-newline",
                normalize_final_newline,
            )
        )

    # D3: over-long lines (report only worst offender per file, with a fix
    # only when the line is a pure import that can be wrapped safely)
    long_lines = [(i + 1, ln) for i, ln in enumerate(lines) if len(ln) > max_line]
    if long_lines:
        findings.append(
            Finding(
                category=Category.FORMATTING,
                severity=Severity.DRIFT,
                path=path,
                message=f"{len(long_lines)} line(s) exceed {max_line} chars "
                        f"(first: line {long_lines[0][0]})",
                current=f"{len(long_lines[0][1])} chars",
                recommended=f"<={max_line} chars",
                conf=0,
                rationale="Line wrapping can alter string contents; manual review only.",
                fix_id="fmt-long-lines",
            )
        )

    # D4: quote-style consistency for simple string literals
    singles = doubles = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            src = ast.get_source_segment(text, node)
            if src is None:
                continue
            if src.startswith("'"):
                singles += 1
            elif src.startswith('"'):
                doubles += 1
    if singles and doubles and doubles >= singles:
        findings.append(
            _finding(
                path,
                f"Mixed quote styles ({singles} single vs {doubles} double)",
                "mixed quotes",
                "double quotes",
                "fmt-quotes",
                _normalize_quotes_to_double,
            )
        )
    elif singles and doubles:
        findings.append(
            _finding(
                path,
                f"Mixed quote styles ({singles} single vs {doubles} double)",
                "mixed quotes",
                "single quotes",
                "fmt-quotes",
                _normalize_quotes_to_single,
            )
        )


def _swap_simple_quotes(text: str, target: str) -> str:
    """Swap quote characters on simple single-line string literals only.

    A literal qualifies when it starts and ends with the same quote char, spans
    one line, and contains no backslashes. Docstrings and multi-line strings
    (triple quotes) are never touched.
    """
    out_lines = []
    for line in text.split("\n"):
        out_lines.append(_swap_line(line, target))
    return "\n".join(out_lines)


def _swap_line(line: str, target: str) -> str:
    if target not in ("'", '"'):
        return line
    other = "'" if target == '"' else '"'
    triple = target * 3
    if triple in line or (other * 3) in line:
        return line
    chars = list(line)
    i = 0
    n = len(chars)
    while i < n:
        c = chars[i]
        if c not in ("'", '"'):
            i += 1
            continue
        j = i + 1
        while j < n and chars[j] != c:
            if chars[j] == "\\":
                j += 2
            else:
                j += 1
        if j >= n:
            break
        seg = "".join(chars[i : j + 1])
        if len(seg) >= 2 and seg[0] == seg[-1] == other and "\\" not in seg:
            inner = seg[1:-1]
            if target not in inner:
                chars[i] = target
                chars[j] = target
        i = j + 1
    return "".join(chars)


def _normalize_quotes_to_double(text: str) -> str:
    return _swap_simple_quotes(text, '"')


def _normalize_quotes_to_single(text: str) -> str:
    return _swap_simple_quotes(text, "'")

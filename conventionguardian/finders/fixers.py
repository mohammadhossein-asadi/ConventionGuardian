"""Pure-style fixers. Every fix function takes file text and returns new text.

Fixes must be deterministic and side-effect free: same input, same output.
"""

from __future__ import annotations

import re

# --- Formatting (category D) -----------------------------------------------

# Matches any single inline comment, honoring the fact that "#" inside a
# string literal is not a comment. We only strip comments that are preceded
# by whitespace and followed by end-of-line, and the "#" must not be inside
# quotes: we approximate by counting quotes before it.
_INLINE_COMMENT = re.compile(r"(?P<code>.*?)(?P<ws>\s+)#\s*[^\n]*$", re.DOTALL)


def _hash_outside_quotes(code: str) -> bool:
    """True if "#" chars in code are all outside quotes (rough but safe check)."""
    return code.count('"') % 2 == 0 and code.count("'") % 2 == 0


def strip_inline_comment(content: str, count: int = 1) -> str:
    """Remove inline comments (keeping standalone comment lines) from Python files.

    Only removes trailing comments whose "#" is outside any string literal,
    and never removes "# type:" or "# noqa" markers.
    """
    lines = content.split("\n")
    removed = 0
    out: list[str] = []
    for line in lines:
        if removed < count and "#" in line and not line.lstrip().startswith("#"):
            m = _INLINE_COMMENT.match(line)
            if m:
                code = m.group("code")
                if _hash_outside_quotes(code) and not re.search(r"#\s*(type|noqa)", line):
                    out.append(code.rstrip())
                    removed += 1
                    continue
        out.append(line)
    return "\n".join(out)


def normalize_final_newline(content: str) -> str:
    """Ensure the file ends with exactly one newline (CRLF-safe)."""
    if not content:
        return content
    body = content.rstrip("\r\n")
    if not body:
        return "\n"
    return body + "\n"


def indent_tabs_to_spaces(content: str, width: int = 4) -> str:
    """Convert leading tabs to spaces (only line-leading whitespace)."""
    out = []
    for line in content.split("\n"):
        stripped = line.lstrip("\t")
        n_tabs = len(line) - len(stripped)
        out.append(" " * (n_tabs * width) + stripped)
    return "\n".join(out)


# --- Naming (category B) ----------------------------------------------------

_CAMEL1 = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL2 = re.compile(r"([a-z\d])([A-Z])")


def camel_to_snake(name: str) -> str:
    s1 = _CAMEL1.sub(r"\1_\2", name)
    s2 = _CAMEL2.sub(r"\1_\2", s1)
    return s2.replace("-", "_").lower()


def rename_identifier(content: str, old: str, new: str) -> str:
    """Whole-word rename of an identifier across the file."""
    pattern = re.compile(rf"\b{re.escape(old)}\b")
    return pattern.sub(new, content)


# --- Imports (category C) ---------------------------------------------------

def sort_import_block(block: str, local_roots: tuple[str, ...] = ()) -> str:
    """Regroup a block of 'import x' / 'from x import y' lines.

    Grouping: stdlib -> third-party -> local (isort-style, conservative).
    Blank lines inside the block are dropped and canonical single blanks are
    emitted between groups. `local_roots` carries the project's own top-level
    package names (derived from __init__.py layout and pyproject name) so
    first-party imports are classified correctly.
    """
    import_lines = [ln for ln in block.split("\n") if ln.strip()]
    stdlib, third_party, local, other = [], [], [], []
    known_stdlib = {
        "__future__",
        "os", "sys", "re", "json", "time", "math", "typing", "pathlib", "abc",
        "collections", "dataclasses", "enum", "functools", "hashlib", "itertools",
        "subprocess", "tomllib", "unittest", "io", "contextlib", "shutil", "glob",
    }
    fallback_local = ("tests", "app", "src", "lib")

    def bucket_for(line: str) -> str:
        if line.lstrip().startswith(("from .", "import .")):
            return "local"
        m = re.match(r"(?:from|import)\s+([\w.]+)", line)
        if not m:
            return "other"
        root = m.group(1).split(".")[0]
        if root in known_stdlib:
            return "stdlib"
        if root in local_roots or root in fallback_local:
            return "local"
        return "third_party"

    for line in import_lines:
        b = bucket_for(line)
        if b == "stdlib":
            stdlib.append(line)
        elif b == "third_party":
            third_party.append(line)
        elif b == "local":
            local.append(line)
        else:
            other.append(line)

    out: list[str] = []
    for group in (stdlib, third_party, local):
        if group:
            if out:
                out.append("")
            out.extend(sorted(group))
    if other:  # unexpected content: preserve it verbatim, never drop
        if out:
            out.append("")
        out.extend(other)
    return "\n".join(out)


# --- Docs (category E) -------------------------------------------------------

def docs_toc_sort(content: str) -> str:
    """Alphabetize a Markdown table of contents between <!-- TOC --> markers."""
    m = re.search(r"<!--\s*TOC\s*-->\n(.*?)<!--\s*/TOC\s*-->", content, re.DOTALL)
    if not m:
        return content
    toc_block = m.group(1)
    lines = toc_block.strip("\n").split("\n")
    sorted_lines = sorted(lines, key=lambda ln: ln.lower())
    new_block = "\n".join(sorted_lines) + "\n"
    return content[: m.start(1)] + new_block + content[m.end(1) :]

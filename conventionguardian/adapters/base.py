"""Language adapter registry (tree-sitter based).

Tree-sitter is an OPTIONAL dependency: the core package installs without it,
and adapters are only loadable when the grammars are present.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from conventionguardian.models import Category, Finding, Severity

TRY_GRAMMARS = {
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
    "go": "tree_sitter_go",
    "rust": "tree_sitter_rust",
}


def available_languages() -> dict[str, bool]:
    out: dict[str, bool] = {}
    for lang, mod_name in TRY_GRAMMARS.items():
        try:
            __import__(mod_name)
            out[lang] = True
        except ImportError:
            out[lang] = False
    return out


def adapters_available() -> bool:
    try:
        import tree_sitter  # noqa: F401

        return True
    except ImportError:
        return False


@dataclass
class AdapterContext:
    root: Path
    local_roots: tuple[str, ...] = ()
    max_line: int = 100


def _mk_finding(
    category: Category,
    severity: Severity,
    path: Path,
    message: str,
    current: str,
    recommended: str,
    fix_id: str,
    fix=None,
    conf: int = 100,
    rationale: str = "",
    group: str = "",
) -> Finding:
    return Finding(
        category=category,
        severity=severity,
        path=path,
        message=message,
        current=current,
        recommended=recommended,
        conf=conf,
        rationale=rationale or "Tree-sitter-verified pure-style change; AST-equivalent source.",
        fix_id=fix_id,
        fix=fix,
        group=group,
    )


class BaseAdapter:
    """Per-language syntax-tree adapter for categories B (naming), C (imports), D (formatting)."""

    extensions: tuple[str, ...] = ()
    language_name: str = ""

    def __init__(self, ctx: AdapterContext) -> None:
        self.ctx = ctx

    @staticmethod
    def load_language():
        raise NotImplementedError

    def find_issues(self, path: Path, findings: list[Finding]) -> None:
        """Parse the file and run naming, import, and formatting finders."""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        parser = self._parser_for(path)
        tree = parser.parse(text.encode("utf-8"))
        if tree.root_node.has_error:
            # Unparseable source: refuse to propose anything (zero-logic rule).
            findings.append(
                _mk_finding(
                    Category.FORMATTING,
                    Severity.DRIFT,
                    path,
                    "File has syntax errors; skipping all automatic fixes",
                    "unparseable",
                    "manual review",
                    f"{self.language_name}-parse-error",
                    conf=0,
                    rationale="Fixes are only proposed for files that parse cleanly.",
                )
            )
            return
        self.find_naming_issues(tree.root_node, text, path, findings)
        self.find_import_issues(tree.root_node, text, path, findings)
        self.find_formatting_issues(tree.root_node, text, path, findings)

    def _parser_for(self, path: Path):
        from tree_sitter import Parser

        return Parser(self.load_language())

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _find_all(root, node_type: str) -> list:
        return [n for n in _walk(root) if n.type == node_type]

    @staticmethod
    def _child_of_type(node, node_type: str):
        for ch in node.children:
            if ch.type == node_type:
                return ch
        return None

    @staticmethod
    def _child_text(node, node_type: str) -> str | None:
        ch = BaseAdapter._child_of_type(node, node_type)
        return None if ch is None else _text(ch)

    # -- per-language hooks -------------------------------------------------

    def find_naming_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        raise NotImplementedError

    def find_import_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        raise NotImplementedError

    def find_formatting_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        raise NotImplementedError


def _walk(root):
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(node.children))


def _text(node) -> str:
    return node.text.decode("utf-8", errors="replace")

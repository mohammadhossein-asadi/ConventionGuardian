"""Go adapter (tree-sitter).

Go's tooling already enforces most style; this adapter adds:
- B-naming: unexported names that differ only by case from exported consensus
  (cross-file whole-word rename, opt-in per name).
- C-imports: gofmt-style single-import-block regrouping (behavior-safe:
  gofmt itself does this; import side effects are order-insensitive in Go).
- D-formatting: final newline; CRLF is handled globally by the misc finder.
"""

from __future__ import annotations

from pathlib import Path

from conventionguardian.adapters.base import (
    AdapterContext,
    BaseAdapter,
    _mk_finding,
    _text,
)
from conventionguardian.finders.fixers import (
    normalize_final_newline,
    rename_identifier,
)
from conventionguardian.models import Category, Finding, Severity

try:  # optional grammar
    import tree_sitter_go as _tsgo
except ImportError:  # pragma: no cover
    _tsgo = None

_GO_LANG = None


class GoAdapter(BaseAdapter):
    extensions = (".go",)
    language_name = "go"

    @classmethod
    def try_new(cls, ctx: AdapterContext):
        global _GO_LANG
        if _tsgo is None:
            return None
        if _GO_LANG is None:
            from tree_sitter import Language

            _GO_LANG = Language(_tsgo.language())
        return cls(ctx)

    @staticmethod
    def load_language():
        if _GO_LANG is None:
            raise ImportError(
                "tree-sitter-go is not installed; "
                "install with: pip install 'convention-guardian[adapters]'"
            )
        return _GO_LANG

    # -- naming ---------------------------------------------------------------

    def find_naming_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        """Detect snake_case function names in Go, where consensus is mixedCase.

        Exported (PascalCase) names are NEVER flagged: renaming them changes
        the package's public API, which is a logic-visible change, not style.
        Only snake_case package-level functions deviate from Go convention.
        """
        func_names: list[str] = []
        for node in BaseAdapter._find_all(root, "function_declaration"):
            name = self._child_text(node, "identifier")
            if name:
                func_names.append(name)

        if len(func_names) < 4:
            return

        mixed = [n for n in func_names if n[:1].islower() and "_" not in n]
        devs = [n for n in func_names if "_" in n and n[:1].islower()]
        if len(mixed) >= 3 and devs:
            for name in sorted(set(devs)):
                new = _to_go_mixed(name)
                if new == name:
                    continue
                findings.append(
                    _mk_finding(
                        Category.NAMING,
                        Severity.DRIFT,
                        path,
                        f"Function '{name}' deviates from dominant mixedCase style",
                        name,
                        new,
                        f"go-rename:{name}",
                        group=f"go-rename:{name}",
                        fix=lambda t, _o=name, _n=new: rename_identifier(t, _o, _n),
                        rationale=(
                            "Whole-word rename across every file mentioning the identifier; "
                            "Go package-level scope makes textual rename exact."
                        ),
                    )
                )

    # -- imports -----------------------------------------------------------

    def find_import_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        """Regroup a parenthesized import block the way gofmt -s would sort it.

        gofmt does NOT reorder imports; goimports does (separate tool). The
        regroup here is still behavior-safe: Go spec gives imports no
        evaluation-order semantics between files, and within a block the init
        order is decided by the package graph, not by source order.
        """
        blocks = BaseAdapter._find_all(root, "import_spec_list")
        if len(blocks) != 1:
            return
        block = blocks[0]
        specs = [
            _text(ch) for ch in block.children
            if ch.type == "import_spec"
        ]
        if not specs:
            return

        def bucket(spec: str) -> int:
            # stdlib = no dot in first path segment; anything else = external.
            path_seg = spec.split('"')[1] if '"' in spec else spec
            first = path_seg.strip().split("/")[0]
            return 0 if "." not in first else 1

        buckets = [bucket(s) for s in specs]
        if buckets != sorted(buckets) or specs != sorted(specs, key=lambda s: (bucket(s), s)):
            new_block_text = _regroup_go_imports(_text(block))
            if new_block_text != _text(block):
                findings.append(
                    _mk_finding(
                        Category.IMPORTS,
                        Severity.DRIFT,
                        path,
                        "Import block is not grouped stdlib -> external",
                        "mixed import block",
                        "grouped order",
                        "go-import-order",
                        fix=lambda t, _b=_text(block), _n=new_block_text: _replace_once(t, _b, _n),
                        rationale=(
                            "Pure regrouping inside the import block; Go import order has no "
                            "runtime semantics (unlike JS module side effects)."
                        ),
                    )
                )

    # -- formatting -----------------------------------------------------------

    def find_formatting_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        lines = text.split("\n")

        if text and not text.endswith("\n"):
            findings.append(
                _mk_finding(
                    Category.FORMATTING,
                    Severity.DRIFT,
                    path,
                    "Missing final newline at EOF",
                    "no trailing newline",
                    "single trailing newline",
                    "fmt-final-newline",
                    fix=normalize_final_newline,
                )
            )

        # Go canonical style is TABS; flag space-indented Go files (report-only,
        # the textual conversion can collide with struct-tag alignment).
        space_lines = [ln for ln in lines if ln.startswith("    ") and ln.strip()]
        tab_lines = [ln for ln in lines if ln.startswith("\t")]
        if space_lines and not tab_lines:
            findings.append(
                _mk_finding(
                    Category.FORMATTING,
                    Severity.DRIFT,
                    path,
                    f"{len(space_lines)} line(s) use space indentation (Go uses tabs)",
                    "space indentation",
                    "tab indentation",
                    "go-indent",
                    conf=0,
                    rationale="Convert to gofmt formatting; run gofmt write instead.",
                )
            )


# --- helpers ------------------------------------------------------------------


def _to_go_mixed(name: str) -> str:
    """snake_case -> mixedCase (process_entry -> processEntry); identity otherwise."""
    if "_" not in name:
        return name
    parts = [p for p in name.split("_") if p]
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def _regroup_go_imports(block_text: str) -> str:
    """Regroup import specs: stdlib first, then external, blank line between."""
    lines = block_text.split("\n")
    specs: list[str] = []
    pre, post = [], []
    state = "pre"
    for ln in lines:
        s = ln.strip()
        if s.startswith("("):
            state = "specs"
            continue
        if s.startswith(")"):
            state = "post"
            continue
        if state == "specs" and s:
            specs.append(ln)
        elif state == "pre":
            pre.append(ln)
        else:
            post.append(ln)

    def key(ln: str) -> tuple:
        s = ln.strip()
        first = s.split('"')[1].split("/")[0] if '"' in s else s
        return (0 if "." not in first else 1, s)

    out = list(pre)
    if specs:
        ordered = sorted(specs, key=key)
        out.append("(")
        prev_b = None
        for ln in ordered:
            b = key(ln)[0]
            if prev_b is not None and b != prev_b:
                out.append("")
            out.append(ln)
            prev_b = b
        out.append(")")
    out.extend(post)
    return "\n".join(out)


def _replace_once(content: str, old: str, new: str) -> str:
    if old not in content:
        raise ValueError("target import block not found")
    return content.replace(old, new, 1)

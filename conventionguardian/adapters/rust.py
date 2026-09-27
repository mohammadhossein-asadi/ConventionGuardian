"""Rust adapter (tree-sitter).

- B-naming: snake_case is the Rust norm (RFC 430). Functions/methods deviating
  from snake_case are flagged as cross-file coordinated renames — EXCEPT when
  they carry #[allow(non_snake_case)] or #![allow(non_snake_case)] at module
  level, or sit inside #[cfg(test)] test-module idioms where deviant names are
  sometimes intentional. Renames of `pub` items are REPORT-ONLY (API change).
- C-imports: `use` statements are order-insensitive in Rust; sorting the
  leading contiguous use-block is behavior-safe (rustfmt does exactly this).
- D-formatting: final newline; line-length report-only.
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
    camel_to_snake,
    normalize_final_newline,
    rename_identifier,
)
from conventionguardian.models import Category, Finding, Severity

try:  # optional grammar
    import tree_sitter_rust as _tsrs
except ImportError:  # pragma: no cover
    _tsrs = None

_RS_LANG = None


class RustAdapter(BaseAdapter):
    extensions = (".rs",)
    language_name = "rust"

    @classmethod
    def try_new(cls, ctx: AdapterContext):
        global _RS_LANG
        if _tsrs is None:
            return None
        if _RS_LANG is None:
            from tree_sitter import Language

            _RS_LANG = Language(_tsrs.language())
        return cls(ctx)

    @staticmethod
    def load_language():
        if _RS_LANG is None:
            raise ImportError(
                "tree-sitter-rust is not installed; "
                "install with: pip install 'convention-guardian[adapters]'"
            )
        return _RS_LANG

    # -- naming ---------------------------------------------------------------

    def find_naming_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        if "allow(non_snake_case)" in text:
            return  # module opted out; honor the ignore attribute
        for node in BaseAdapter._find_all(root, "function_item"):
            name = self._child_text(node, "identifier")
            if not name or _is_snake(name):
                continue
            pub = any(
                ch.type == "visibility_modifier" for ch in node.children
            )
            new = camel_to_snake(name)
            if new == name:
                continue
            if pub:
                findings.append(
                    _mk_finding(
                        Category.NAMING,
                        Severity.DRIFT,
                        path,
                        f"Public fn '{name}' deviates from RFC-430 snake_case (report-only)",
                        name,
                        new,
                        f"rs-rename:{name}",
                        conf=0,
                        rationale="Renaming a pub fn changes the crate's public API.",
                    )
                )
            else:
                findings.append(
                    _mk_finding(
                        Category.NAMING,
                        Severity.DRIFT,
                        path,
                        f"fn '{name}' deviates from RFC-430 snake_case",
                        name,
                        new,
                        f"rs-rename:{name}",
                        group=f"rs-rename:{name}",
                        fix=lambda t, _o=name, _n=new: rename_identifier(t, _o, _n),
                        rationale=(
                            "Whole-word rename across every file mentioning the identifier; "
                            "private crate-internal symbol."
                        ),
                    )
                )

    # -- imports ------------------------------------------------------------

    def find_import_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        uses = [
            n for n in root.children if n.type == "use_declaration"
        ]
        if len(uses) < 2:
            return
        # Only contiguous leading use-blocks, single-line declarations, no comments.
        first = uses[0]
        if first.start_byte != 0 and text[: first.start_byte].strip():
            return
        for i in range(1, len(uses)):
            if uses[i].start_byte != uses[i - 1].end_byte + 1:
                return
            if text[uses[i - 1].end_byte: uses[i].start_byte].strip() != "":
                return
        for u in uses:
            decl = _text(u)
            if any(ch.type == "line_comment" for ch in u.children):
                return
            if "\n" in decl:
                return

        decls = [_text(u) for u in uses]
        ordered = sorted(decls, key=_use_key)
        if ordered == decls:
            return
        block_text = text[uses[0].start_byte: uses[-1].end_byte]
        new_block = "\n".join(ordered)
        findings.append(
            _mk_finding(
                Category.IMPORTS,
                Severity.DRIFT,
                path,
                "use statements are not sorted (rustfmt-style ordering)",
                "unsorted use block",
                "sorted use block",
                "rs-use-sort",
                fix=lambda t, _b=block_text, _n=new_block: _replace_once(t, _b, _n),
                rationale=(
                    "Rust `use` order has no runtime semantics; rustfmt applies "
                    "the same normalization."
                ),
            )
        )

    # -- formatting ----------------------------------------------------------

    def find_formatting_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
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

        max_line = self.ctx.max_line
        long_lines = [ln for ln in text.split("\n") if len(ln) > max_line]
        if long_lines:
            findings.append(
                _mk_finding(
                    Category.FORMATTING,
                    Severity.DRIFT,
                    path,
                    f"{len(long_lines)} line(s) exceed {max_line} chars",
                    f"{len(long_lines[0])} chars",
                    f"<={max_line} chars",
                    "rs-long-lines",
                    conf=0,
                    rationale="Line wrapping in Rust can move borrow boundaries in source text; manual review.",
                )
            )


def _is_snake(name: str) -> bool:
    return name.islower() or "_" not in name and name == name.lower()


def _use_key(decl: str) -> str:
    """rustfmt-style sort key: crate:: first, then self::, then others; case-sensitive."""
    body = decl.strip()
    if body.startswith("pub("):
        body = body[4:]
    elif body.startswith("pub"):
        body = body[3:]
    body = body.lstrip()
    if body.startswith("use "):
        body = body[4:]
    for i, prefix in enumerate(("crate::", "self::", "super::")):
        if body.startswith(prefix):
            return (i, body)
    return (3, body)


def _replace_once(content: str, old: str, new: str) -> str:
    if old not in content:
        raise ValueError("target use block not found")
    return content.replace(old, new, 1)

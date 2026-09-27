"""JavaScript/TypeScript adapter (tree-sitter).

Naming drift only fires on verified camelCase-consensus files. Import and
long-line findings are report-only (reordering JS imports can change
module-evaluation side effects). Whole-word rename fixes reuse the shared
rename machinery used by the Python finder.
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
    indent_tabs_to_spaces,
    normalize_final_newline,
    rename_identifier,
)
from conventionguardian.finders.formatting import (
    _normalize_quotes_to_double,
    _normalize_quotes_to_single,
)
from conventionguardian.models import Category, Severity

try:  # optional grammars
    import tree_sitter_javascript as _tsjs
except ImportError:  # pragma: no cover
    _tsjs = None
try:  # pragma: no cover
    import tree_sitter_typescript as _tsts
except ImportError:
    _tsts = None

_JS_LANG = None
_TS_LANG = None
_TSX_LANG = None


def _load_languages() -> bool:
    """Cache Language objects; returns True when the JS grammar is available."""
    global _JS_LANG, _TS_LANG, _TSX_LANG
    from tree_sitter import Language

    if _JS_LANG is None and _tsjs is not None:
        _JS_LANG = Language(_tsjs.language())
    if _tsts is not None:
        if _TS_LANG is None:
            _TS_LANG = Language(_tsts.language_typescript())
        if _TSX_LANG is None:
            _TSX_LANG = Language(_tsts.language_tsx())
    return _JS_LANG is not None


class JsTsAdapter(BaseAdapter):
    """One adapter instance handles .js/.mjs/.cjs, .ts, and .tsx via per-file grammar."""

    extensions = ()
    language_name = "js-ts"

    def __init__(self, ctx: AdapterContext) -> None:
        super().__init__(ctx)
        self.extensions = self._extensions()

    @staticmethod
    def _extensions() -> tuple[str, ...]:
        exts: list[str] = []
        if _JS_LANG is not None or _tsjs is not None:
            exts.extend([".js", ".jsx", ".mjs", ".cjs"])
        if _TS_LANG is not None:
            exts.append(".ts")
        if _TSX_LANG is not None:
            exts.append(".tsx")
        return tuple(exts)

    @classmethod
    def try_new(cls, ctx: AdapterContext):
        if _tsjs is None and _tsts is None:
            return None
        try:
            _load_languages()
        except ImportError:
            return None
        return cls(ctx)

    def _parser_for(self, path: Path):
        from tree_sitter import Parser

        if path.suffix == ".tsx" and _TSX_LANG is not None:
            return Parser(_TSX_LANG)
        if path.suffix == ".ts" and _TS_LANG is not None:
            return Parser(_TS_LANG)
        if _JS_LANG is None:
            raise ImportError(
                "tree-sitter-javascript is not installed; "
                "install with: pip install 'convention-guardian[adapters]'"
            )
        return Parser(_JS_LANG)

    # -- naming ------------------------------------------------------------

    def find_naming_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        decl_names: list[tuple[str, str]] = []  # (kind, name)
        for node in BaseAdapter._find_all(root, "variable_declarator"):
            ch = self._child_of_type(node, "identifier")
            if ch is not None:
                decl_names.append(("var", _text(ch)))
        for kind in ("function_declaration", "generator_function_declaration"):
            for node in BaseAdapter._find_all(root, kind):
                name = self._child_text(node, "identifier")
                if name:
                    decl_names.append(("function", name))
        for node in BaseAdapter._find_all(root, "class_declaration"):
            name = self._child_text(node, "identifier")
            if name:
                decl_names.append(("class", name))
        for node in BaseAdapter._find_all(root, "method_definition"):
            key = self._child_of_type(node, "property_identifier")
            if key is not None:
                decl_names.append(("function", _text(key)))

        funcs = [n for k, n in decl_names if k in ("function", "var")]
        classes = [n for k, n in decl_names if k == "class"]

        # PascalCase functions are the React-component convention and are NEVER
        # flagged: renaming a component to camelCase changes JSX semantics
        # (<Analytics /> becomes a DOM element lookup). Only snake_case names
        # deviate from JS/TS convention; a camelCase majority must exist.
        camel_funcs = [n for n in funcs if "_" not in n]
        devs = [n for n in funcs if "_" in n and not _is_screaming(n)]
        if len(camel_funcs) >= 3 and devs:
            for name in sorted(set(devs)):
                new = _camel_to_js(name)
                if new == name:
                    continue
                findings.append(
                    _mk_finding(
                        Category.NAMING,
                        Severity.DRIFT,
                        path,
                        f"Identifier '{name}' deviates from dominant camelCase style",
                        name,
                        new,
                        f"js-rename:{name}",
                        fix=lambda t, _o=name, _n=new: rename_identifier(t, _o, _n),
                        rationale="Whole-word rename applied textually; same-scope symbol rename.",
                    )
                )

        pascal_classes = [n for n in classes if n[:1].isupper()]
        bad_classes = [n for n in classes if not n[:1].isupper()]
        if len(pascal_classes) >= 2 and bad_classes:
            for name in sorted(set(bad_classes)):
                new = name[:1].upper() + name[1:]
                findings.append(
                    _mk_finding(
                        Category.NAMING,
                        Severity.DRIFT,
                        path,
                        f"Class '{name}' deviates from dominant PascalCase style",
                        name,
                        new,
                        f"js-rename:{name}",
                        fix=lambda t, _o=name, _n=new: rename_identifier(t, _o, _n),
                        rationale="Whole-word rename applied textually; same-scope symbol rename.",
                    )
                )

    # -- imports (report-only) ----------------------------------------------

    def find_import_issues(self, root, text: str, path: Path, findings: list[Finding]) -> None:
        imports = BaseAdapter._find_all(root, "import_statement")
        if len(imports) < 2:
            return
        kinds = []
        for node in imports:
            src = self._child_text(node, "string")
            if src is None:
                continue
            is_rel = src.startswith("'./") or src.startswith('"./') or src.startswith("'../") or src.startswith('"../')
            kinds.append(is_rel)
        # Report when relative imports appear before package imports (grouping drift).
        first_rel = kinds.index(True) if True in kinds else -1
        last_pkg = max((i for i, k in enumerate(kinds) if not k), default=-1)
        if first_rel != -1 and last_pkg > first_rel:
            findings.append(
                _mk_finding(
                    Category.IMPORTS,
                    Severity.DRIFT,
                    path,
                    "Relative imports appear before package imports (report-only)",
                    "mixed import order",
                    "package imports first, then relative",
                    "js-import-order",
                    conf=0,
                    rationale="Reordering JS imports can change module evaluation side effects.",
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

        tab_lines = [ln for ln in lines if ln.startswith("\t")]
        space_lines = [ln for ln in lines if ln.startswith(" ")]
        if tab_lines and len(tab_lines) <= len(space_lines):
            findings.append(
                _mk_finding(
                    Category.FORMATTING,
                    Severity.DRIFT,
                    path,
                    f"Tab indentation on {len(tab_lines)} line(s) in a space-indented file",
                    "tab indentation",
                    "4-space indentation",
                    "fmt-tabs",
                    fix=indent_tabs_to_spaces,
                )
            )

        max_line = self.ctx.max_line
        long_lines = [ln for ln in lines if len(ln) > max_line]
        if long_lines:
            findings.append(
                _mk_finding(
                    Category.FORMATTING,
                    Severity.DRIFT,
                    path,
                    f"{len(long_lines)} line(s) exceed {max_line} chars",
                    f"{len(long_lines[0])} chars",
                    f"<={max_line} chars",
                    "js-long-lines",
                    conf=0,
                    rationale="Line wrapping can alter template/string contents; manual review.",
                )
            )

        singles = doubles = 0
        for node in BaseAdapter._find_all(root, "string"):
            raw = _text(node)
            if raw.startswith("'"):
                singles += 1
            elif raw.startswith('"'):
                doubles += 1
        if singles and doubles:
            if doubles >= singles:
                fix, target = _normalize_quotes_to_double, "double"
            else:
                fix, target = _normalize_quotes_to_single, "single"
            findings.append(
                _mk_finding(
                    Category.FORMATTING,
                    Severity.DRIFT,
                    path,
                    f"Mixed quote styles ({singles} single vs {doubles} double)",
                    "mixed quotes",
                    f"{target} quotes",
                    "js-quotes",
                    fix=fix,
                    rationale="Quote swap on simple string literals only; escapes skipped.",
                )
            )


def _is_screaming(name: str) -> bool:
    return len(name) > 1 and name.isupper()


def _camel_to_js(name: str) -> str:
    """Transform a non-conforming identifier toward camelCase.

    snake_case -> camelCase (apply_discount -> applyDiscount);
    PascalCase -> camelCase (CalcTotal -> calcTotal); identity otherwise.
    """
    if "_" in name:
        parts = [p for p in name.split("_") if p]
        return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])
    if name[:1].isupper():
        return name[0].lower() + name[1:]
    return name

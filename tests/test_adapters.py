"""Tree-sitter adapter tests (JS/TS, Go, Rust).

Includes zero-logic proofs: for every materialized fix, the multiset of
identifiers/keywords/string bodies must be unchanged (whitespace/order aside),
and import regroupings must preserve the exact set of import lines.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conventionguardian.adapters import AdapterContext, get_adapters
from conventionguardian.adapters.golang import GoAdapter
from conventionguardian.adapters.jsts import JsTsAdapter
from conventionguardian.adapters.rust import RustAdapter
from conventionguardian.models import Category

GRAMMARS_OK = True
try:
    import tree_sitter_go  # noqa: F401
    import tree_sitter_javascript  # noqa: F401
    import tree_sitter_rust  # noqa: F401
except ImportError:  # pragma: no cover
    GRAMMARS_OK = False

pytestmark = pytest.mark.skipif(not GRAMMARS_OK, reason="tree-sitter grammars not installed")


def _tokens(src: str) -> list[str]:
    """Canonical identifier multiset: case/underscore-insensitive.

    A pure rename must preserve this multiset exactly — the same logical
    identifiers remain, only their spelling style changes.
    """
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    raw = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", src)
    return sorted(t.lower().replace("_", "") for t in raw)


def _run(adapter_cls, src: str, name: str):
    p = Path(_tmp()) / name
    p.write_text(src, encoding="utf-8", newline="\n")
    ad = adapter_cls.try_new(AdapterContext(root=p.parent))
    findings: list = []
    ad.find_issues(p, findings)
    return ad, findings, p


def _tmp():
    import tempfile

    return tempfile.mkdtemp()


# ---------------------------------------------------------------- JS/TS -----


def test_js_naming_and_import_report():
    src = (
        "import { b } from './other';\n"
        "import { readFile } from 'fs';\n"
        "\n"
        "function calcTotal(price) { return price * 2; }\n"
        "function roundValue(n) { return Math.round(n); }\n"
        "function computeSum(a, b) { return a + b; }\n"
        "function applyDiscount(n) { return n - 1; }\n"
        "function apply_discount(n) { return n - 2; }\n"
        "function round_value(n) { return Math.round(n) + 1; }\n"
    )
    _, findings, path = _run(JsTsAdapter, src, "widget.js")
    cats = {f.category for f in findings}
    assert Category.NAMING in cats
    assert Category.IMPORTS in cats
    ren = [f for f in findings if f.fix_id.startswith("js-rename")]
    assert any(f.current == "apply_discount" and f.recommended == "applyDiscount" for f in ren)
    imp = [f for f in findings if f.fix_id == "js-import-order"]
    assert imp and imp[0].conf == 0  # report-only


def test_js_rename_preserves_tokens():
    src = (
        "function calcTotal(price) { return price * 2; }\n"
        "function roundValue(n) { return Math.round(n); }\n"
        "function computeSum(a, b) { return a + b; }\n"
        "function applyDiscount(n) { return n - 1; }\n"
        "function apply_discount(n) { return n - 2; }\n"
    )
    _, findings, path = _run(JsTsAdapter, src, "tok.js")
    old = path.read_text(encoding="utf-8")
    ren = [f for f in findings if f.fix_id.startswith("js-rename")]
    assert ren
    new = ren[0].materialize().new_content
    assert sorted(_tokens(old)) == sorted(_tokens(new))


def test_js_no_findings_on_clean_file():
    src = "function one(a) { return a; }\nfunction two(a) { return a; }\nfunction three(a) { return a; }\n"
    _, findings, _p = _run(JsTsAdapter, src, "clean.js")
    assert not [f for f in findings if f.category == Category.NAMING]


def test_js_parse_error_is_review_only():
    src = "function broken( { return 1; }"
    _, findings, _p = _run(JsTsAdapter, src, "bad.js")
    assert findings and all(f.conf == 0 for f in findings)


# ------------------------------------------------------------------ GO ------


def test_go_snake_case_rename_not_exported_api():
    src = (
        "package main\n"
        "\n"
        "func runScan() int { return 0 }\n"
        "func loadConfig() int { return 1 }\n"
        "func parseArgs() int { return 2 }\n"
        "func process_entry(path string) int { return 3 }\n"
    )
    _, findings, _p = _run(GoAdapter, src, "main.go")
    ren = [f for f in findings if f.fix_id.startswith("go-rename")]
    assert len(ren) == 1
    assert ren[0].current == "process_entry"
    assert ren[0].recommended == "processEntry"
    assert ren[0].group == "go-rename:process_entry"


def test_go_pascalcase_never_flagged():
    """Exported Go names are public API; renaming them is forbidden."""
    src = (
        "package main\n"
        "\n"
        "func RunScan() int { return 0 }\n"
        "func LoadConfig() int { return 1 }\n"
        "func ParseArgs() int { return 2 }\n"
        "func HandleRequest(w io.Writer) int { return 3 }\n"
    )
    _, findings, _p = _run(GoAdapter, src, "api.go")
    assert not [f for f in findings if f.fix_id.startswith("go-rename")]


def test_go_import_regroup_preserves_spec_set():
    src = (
        "package main\n"
        "\n"
        "import (\n"
        '\t"os"\n'
        '\t"github.com/spf13/cobra"\n'
        '\t"fmt"\n'
        ")\n"
        "\n"
        "func main() {}\n"
    )
    _, findings, path = _run(GoAdapter, src, "imports.go")
    imp = [f for f in findings if f.fix_id == "go-import-order"]
    assert imp
    ch = imp[0].materialize()
    old_lines = sorted(l.strip() for l in ch.old_content.split("\n") if l.strip().startswith('"'))
    new_lines = sorted(l.strip() for l in ch.new_content.split("\n") if l.strip().startswith('"'))
    assert old_lines == new_lines
    assert ch.new_content.index('"fmt"') < ch.new_content.index('"os"') < ch.new_content.index('"github.com')
    assert "import (\n" in ch.new_content


# ---------------------------------------------------------------- RUST ------


def test_rust_snake_case_rename():
    src = (
        "fn processEntry(x: u8) -> u8 { x }\n"
        "fn load_config() -> u8 { 1 }\n"
        "fn parse_args() -> u8 { 2 }\n"
        "fn run_scan() -> u8 { 3 }\n"
    )
    _, findings, _p = _run(RustAdapter, src, "lib.rs")
    ren = [f for f in findings if f.fix_id.startswith("rs-rename")]
    assert len(ren) == 1
    assert ren[0].current == "processEntry"
    assert ren[0].recommended == "process_entry"


def test_rust_pub_fn_report_only():
    src = (
        "pub fn processEntry(x: u8) -> u8 { x }\n"
        "fn load_config() -> u8 { 1 }\n"
        "fn parse_args() -> u8 { 2 }\n"
    )
    _, findings, _p = _run(RustAdapter, src, "lib.rs")
    ren = [f for f in findings if f.fix_id.startswith("rs-rename")]
    assert len(ren) == 1 and ren[0].conf == 0  # API change: report-only


def test_rust_allow_attr_honored():
    src = (
        "#![allow(non_snake_case)]\n"
        "fn processEntry(x: u8) -> u8 { x }\n"
    )
    _, findings, _p = _run(RustAdapter, src, "lib.rs")
    assert not [f for f in findings if f.fix_id.startswith("rs-rename")]


def test_rust_use_sort_preserves_set():
    src = (
        "use serde::Serialize;\n"
        "use std::collections::HashMap;\n"
        "use crate::models::Item;\n"
        "\n"
        "fn main() {}\n"
    )
    _, findings, _p = _run(RustAdapter, src, "lib.rs")
    imp = [f for f in findings if f.fix_id == "rs-use-sort"]
    assert imp
    ch = imp[0].materialize()
    old_lines = sorted(l for l in ch.old_content.split("\n") if l.startswith("use "))
    new_lines = sorted(l for l in ch.new_content.split("\n") if l.startswith("use "))
    assert old_lines == new_lines
    assert ch.new_content.startswith("use crate::models::Item;")


# ------------------------------------------------------------- registry -----


def test_registry_returns_all_three():
    ctx = AdapterContext(root=Path("."))
    ads = get_adapters(ctx)
    kinds = {type(a).__name__ for a in ads}
    assert {"JsTsAdapter", "GoAdapter", "RustAdapter"} <= kinds


def test_adapters_handle_their_extensions_only():
    ctx = AdapterContext(root=Path("."))
    go = [a for a in get_adapters(ctx) if isinstance(a, GoAdapter)][0]
    js = [a for a in get_adapters(ctx) if isinstance(a, JsTsAdapter)][0]
    assert ".go" in go.extensions
    assert ".ts" in js.extensions and ".tsx" in js.extensions and ".js" in js.extensions

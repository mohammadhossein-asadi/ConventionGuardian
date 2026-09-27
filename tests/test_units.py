"""Unit tests for fixers, diff, config, scanner, applier internals."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conventionguardian.config import load_config, save_config
from conventionguardian.diff import unified_diff
from conventionguardian.finders.fixers import (
    camel_to_snake,
    normalize_final_newline,
    sort_import_block,
)
from conventionguardian import applier, scanner
from conventionguardian.models import Category, Finding, Severity, make_id


def test_camel_to_snake():
    assert camel_to_snake("prepareData") == "prepare_data"
    assert camel_to_snake("HTTPServer") == "http_server"
    assert camel_to_snake("already_snake") == "already_snake"


def test_normalize_final_newline():
    assert normalize_final_newline("a") == "a\n"
    assert normalize_final_newline("a\n\n") == "a\n"
    assert normalize_final_newline("") == ""


def test_sort_import_block_groups():
    block = (
        "import os\n"
        "import rich\n"
        "import sys\n"
        "from conventionguardian.models import Finding\n"
        "import json\n"
    )
    out = sort_import_block(block, local_roots=("conventionguardian",))
    assert out == (
        "import json\n"
        "import os\n"
        "import sys\n"
        "\n"
        "import rich\n"
        "\n"
        "from conventionguardian.models import Finding"
    )


def test_sort_import_block_future_is_stdlib():
    out = sort_import_block(
        "from __future__ import annotations\nimport os\nimport pytest\n"
    )
    lines = out.split("\n")
    assert lines[0] == "from __future__ import annotations"
    assert lines[1] == "import os"
    assert lines[3] == "import pytest"


def test_unified_diff_headers():
    diff = unified_diff("a\n", "a\nb\n", Path("x/y.py"))
    assert diff.startswith("--- a/x/y.py")
    assert "+++ b/x/y.py" in diff
    assert "+b" in diff


def test_config_roundtrip(tmp_path):
    save_config(tmp_path, "pep8")
    cfg = load_config(tmp_path)
    assert cfg.target == "pep8"
    assert ".venv" in cfg.excludes


def test_make_id_sequence():
    findings: list = []
    a = Finding(category=Category.NAMING, severity=Severity.DRIFT, path=Path("a.py"), message="m")
    a.id = make_id(Category.NAMING, findings)
    findings.append(a)
    b = Finding(category=Category.NAMING, severity=Severity.DRIFT, path=Path("b.py"), message="m")
    b.id = make_id(Category.NAMING, findings)
    assert (a.id, b.id) == ("N-001", "N-002")


def test_resolve_selection_unknown_id_raises():
    f = Finding(category=Category.MISC, severity=Severity.DRIFT, path=Path("a.py"), message="m", id="M-001")
    with pytest.raises(applier.ApplyError):
        applier.resolve_selection([f], None, ["NOPE-999"])


def test_resolve_selection_dedup(tmp_path):
    f = Finding(category=Category.MISC, severity=Severity.DRIFT, path=tmp_path / "a.py",
                message="m", id="M-001")
    out = applier.resolve_selection([f], None, ["M-001", "M-001"])
    assert len(out) == 1


def test_log_roundtrip(tmp_path):
    log = {"applied": [{"ts": "t", "ids": ["M-001"], "status": "applied", "files": []}],
           "remaining": []}
    applier.save_log(tmp_path, log)
    loaded = applier.load_log(tmp_path)
    assert loaded["applied"][0]["ids"] == ["M-001"]


def test_materialize_crlf_fix_converts(tmp_path):
    """Regression: misc-crlf must convert real CRLF bytes.

    materialize() used to run the CRLF fix on the newline-normalized view,
    where it is a no-op — every pure-CRLF file reported 0 material change.
    """
    p = tmp_path / "crlf.py"
    p.write_bytes(b"x = 1\r\ny = 2\r\n")
    f = Finding(
        category=Category.MISC, severity=Severity.DRIFT, path=p,
        message="CRLF line endings in a Python source file",
        current="CRLF", recommended="LF", conf=100,
        fix_id="misc-crlf", fix=lambda c: c.replace("\r\n", "\n"),
    )
    ch = f.materialize()
    assert ch is not None and ch.changed
    assert ch.old_content == "x = 1\r\ny = 2\r\n"
    assert ch.new_content == "x = 1\ny = 2\n"


def test_iter_files_honors_gitignore(tmp_path):
    """Regression: projects WITH a .gitignore must not crash the file walk.

    GitIgnoreSpec must be built from lines (from_lines), never from raw
    pattern objects; also verifies gitignored files are actually excluded.
    """
    (tmp_path / ".gitignore").write_text("secret\n*.log\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src" / "debug.log").write_text("noise\n", encoding="utf-8")
    (tmp_path / "secret").write_text("key\n", encoding="utf-8")
    files = scanner.iter_files(tmp_path)
    rels = {p.relative_to(tmp_path).as_posix() for p in files}
    assert "src/app.py" in rels
    assert "src/debug.log" not in rels
    assert "secret" not in rels

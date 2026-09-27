"""End-to-end tests on the golden mini-project."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conventionguardian import applier, audit as audit_mod, safety
from fixture_project import build_git_repo, git
from conventionguardian.models import Category


@pytest.fixture()
def mini_project(tmp_path: Path) -> Path:
    return build_git_repo(tmp_path)


def _audit(root: Path):
    findings, profile = audit_mod.audit(root)
    return findings, profile


def test_scan_detects_python_and_pytest(mini_project):
    findings, profile = _audit(mini_project)
    assert "Python" in profile.languages
    assert "pytest" in profile.tests
    assert profile.is_git


def test_audit_finds_expected_categories(mini_project):
    findings, _ = _audit(mini_project)
    cats = {f.category for f in findings}
    assert Category.FORMATTING in cats          # tabbed.py + import order
    assert Category.NAMING in cats              # prepareData
    assert all(f.id for f in findings)          # IDs assigned


def test_import_order_finding_has_diff(mini_project):
    findings, _ = _audit(mini_project)
    imp = [f for f in findings
           if f.category == Category.IMPORTS and f.fix_id == "imp-order"]
    assert imp, "expected import-order finding"
    ch = imp[0].materialize()
    assert ch is not None and ch.changed
    # The reorder must keep the same set of import lines.
    old_lines = sorted(l for l in ch.old_content.split("\n") if l.startswith(("import", "from")))
    new_lines = sorted(l for l in ch.new_content.split("\n") if l.startswith(("import", "from")))
    assert old_lines == new_lines


def test_apply_formatting_batch_passes_verify(mini_project):
    findings, _ = _audit(mini_project)
    result = applier.apply_findings(mini_project, findings, batch="formatting")
    assert result["reverted"] is False
    assert result["applied"], "expected at least one applied file"
    # Files must still parse after fixes.
    for p in mini_project.rglob("*.py"):
        compile(p.read_text(encoding="utf-8"), str(p), "exec")


def test_apply_preserves_runtime_behavior(mini_project):
    findings, _ = _audit(mini_project)
    applier.apply_findings(mini_project, findings, batch="safe")
    # Import the fixed modules and run the core functions (post-rename names).
    sys.path.insert(0, str(mini_project))
    try:
        from sample_app.loose import run
        assert run()["a"] == 2
        from sample_app.helpers import prepare_data
        assert prepare_data(1) == 2
    finally:
        sys.path.remove(str(mini_project))
        for m in [k for k in list(sys.modules) if k.startswith("sample_app")]:
            del sys.modules[m]


def test_renamed_function_updates_callers(mini_project):
    findings, _ = _audit(mini_project)
    renames = [f for f in findings if f.fix_id.startswith("fn-rename")]
    assert renames, "expected prepareData rename finding"
    applier.apply_findings(mini_project, findings, ids=[renames[0].id])
    text = (mini_project / "tests" / "test_helpers.py").read_text(encoding="utf-8")
    assert "prepare_data" in text


def test_misc_batch_converts_crlf_files(mini_project):
    """Regression: the misc batch must really convert CRLF -> LF on disk."""
    target = mini_project / "sample_app" / "crlf_style.py"
    target.write_bytes(b"def crlf_fn():\r\n    return 7\r\n")
    git(mini_project, "add", "-A")
    git(mini_project, "-c", "user.email=cg@example.com",
        "-c", "user.name=cg", "commit", "-m", "crlf file")

    findings, _ = _audit(mini_project)
    crlf = [f for f in findings if f.fix_id == "misc-crlf"]
    assert any(f.path == target for f in crlf), "expected CRLF finding for new file"

    result = applier.apply_findings(mini_project, findings, batch="misc")
    assert result["reverted"] is False
    assert any(Path(p) == target for p in result["applied"])
    raw = target.read_bytes()
    assert b"\r\n" not in raw
    assert b"return 7" in raw  # content otherwise intact


def test_apply_reverts_on_failing_check(mini_project):
    # Seed a broken test: after any change, pytest fails -> batch must revert.
    bad = mini_project / "tests" / "test_bad.py"
    bad.write_text("def test_always_fails():\n    assert False\n", encoding="utf-8")
    git(mini_project, "add", "-A")
    git(mini_project, "-c", "user.email=cg@example.com",
        "-c", "user.name=cg", "commit", "-m", "bad")

    findings, _ = _audit(mini_project)
    target = mini_project / "sample_app" / "tabbed.py"
    before = target.read_text(encoding="utf-8")
    result = applier.apply_findings(mini_project, findings, batch="formatting")
    assert result["reverted"] is True
    assert target.read_text(encoding="utf-8") == before, "file must be restored after revert"


def test_apply_refuses_dirty_tree(mini_project):
    (mini_project / "scratch.txt").write_text("dirty", encoding="utf-8")
    findings, _ = _audit(mini_project)
    with pytest.raises(safety.SafetyError):
        applier.apply_findings(mini_project, findings, batch="formatting")


def test_dry_run_writes_nothing(mini_project):
    findings, _ = _audit(mini_project)
    target = mini_project / "sample_app" / "tabbed.py"
    before = target.read_text(encoding="utf-8")
    result = applier.apply_findings(mini_project, findings, batch="formatting", dry_run=True)
    assert result["dry_run"] is True
    assert result["changes"]
    assert target.read_text(encoding="utf-8") == before

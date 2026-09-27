"""Formatter-delegation tests.

Uses fake specs for the delegation logic and real Ruff (when installed) for an
end-to-end check including a zero-logic proof on the delegated output.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conventionguardian import audit as audit_mod
from conventionguardian import applier, formatters
from fixture_project import FILES, git
from conventionguardian.models import Category, Finding, Severity

RUFF_OK = True
try:
    import subprocess as _sp

    _sp.run(["ruff", "--version"], capture_output=True, check=True)
except Exception:  # noqa: BLE001
    RUFF_OK = False


def _mk_repo(tmp_path: Path, extra_pyproject: str = "") -> Path:
    for rel, content in FILES.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    py = tmp_path / "pyproject.toml"
    py.write_text(
        py.read_text(encoding="utf-8") + "\n" + extra_pyproject, encoding="utf-8"
    )
    git(tmp_path, "init")
    git(tmp_path, "config", "core.autocrlf", "false")
    git(tmp_path, "add", "-A")
    git(tmp_path, "-c", "user.email=cg@example.com",
        "-c", "user.name=cg", "commit", "-m", "init")
    return tmp_path


def _fake_spec(name="FakeFmt", marker="[tool.fake]"):
    return formatters.FormatterSpec(
        name=name,
        cmd=("fake-fmt",),
        suffixes=(".py",),
        languages=("Python",),
        content_markers=(marker,),
    )


# ---------------------------------------------------------------- units -----


def test_delegate_replaces_builtin_and_emits_delegate(tmp_path, monkeypatch):
    root = _mk_repo(tmp_path, "[tool.fake]\n")
    findings, _ = audit_mod.audit(root)
    assert any(f.fix_id == "fmt-final-newline" for f in findings)

    spec = _fake_spec()
    monkeypatch.setattr(formatters, "detect_configured", lambda r, p: [spec])
    monkeypatch.setattr(
        formatters, "run_formatter",
        lambda s, r, text, suffix: text.upper() if "def run" in text else text,
    )

    out: list[Finding] = list(findings)
    n = formatters.delegate_formatting(root, sorted(root.rglob("*.py")), out, detect=lambda: [spec])
    assert n >= 1
    assert not any(f.fix_id in formatters.SUBSUMED_FIX_IDS for f in out)
    delegates = [f for f in out if f.delegate == "FakeFmt"]
    assert delegates
    assert delegates[0].conf == 100


def test_delegate_finds_suppresses_subsumed_only(tmp_path, monkeypatch):
    root = _mk_repo(tmp_path, "[tool.fake]\n")
    findings, _ = audit_mod.audit(root)
    before_imp = [f for f in findings if f.fix_id == "imp-order"]
    assert before_imp  # import ordering is NOT subsumed by plain formatters
    out = list(findings)
    spec = _fake_spec()
    monkeypatch.setattr(
        formatters, "run_formatter", lambda s, r, text, suffix: text  # no-op tool
    )
    formatters.delegate_formatting(root, sorted(root.rglob("*.py")), out, detect=lambda: [spec])
    assert any(f.fix_id == "imp-order" for f in out)


def test_fail_open_when_tool_errors(tmp_path, monkeypatch):
    root = _mk_repo(tmp_path, "[tool.fake]\n")
    findings, _ = audit_mod.audit(root)
    out = list(findings)
    spec = _fake_spec()
    monkeypatch.setattr(formatters, "run_formatter", lambda s, r, text, suffix: None)
    formatters.delegate_formatting(root, sorted(root.rglob("*.py")), out, detect=lambda: [spec])
    assert not [f for f in out if f.delegate]  # no delegates proposed
    # Built-in fixes survive (fail-open).
    assert any(f.fix_id == "fmt-final-newline" for f in out)


def test_detect_requires_config_and_binary(tmp_path, monkeypatch):
    """detect_configured iterates the real SPECS; gate on the Ruff spec."""
    from conventionguardian.models import ToolProfile

    profile = ToolProfile(languages=["Python"])
    # No [tool.ruff] marker -> not detected even with binary present.
    monkeypatch.setattr(formatters, "_resolve_binary", lambda r, s: ("fake",))
    assert formatters.detect_configured(tmp_path, profile) == []
    # Config present, binary missing -> not detected.
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    monkeypatch.setattr(formatters, "_resolve_binary", lambda r, s: None)
    assert formatters.detect_configured(tmp_path, profile) == []
    # Both present -> detected.
    monkeypatch.setattr(formatters, "_resolve_binary", lambda r, s: ("fake",))
    assert [s.name for s in formatters.detect_configured(tmp_path, profile)] == ["Ruff"]


def test_delegate_fix_rejects_stale_content(tmp_path, monkeypatch):
    root = _mk_repo(tmp_path, "[tool.fake]\n")
    spec = _fake_spec()
    monkeypatch.setattr(
        formatters, "run_formatter", lambda s, r, text, suffix: text + "\n# formatted\n"
    )
    out: list[Finding] = []
    formatters.delegate_formatting(root, sorted(root.rglob("*.py")), out, detect=lambda: [spec])
    delegates = [f for f in out if f.delegate]
    assert delegates
    f = delegates[0]
    # Tamper: file changed since audit -> materialize must raise, not mis-write.
    f.path.write_text("# totally different\n", encoding="utf-8")
    with pytest.raises(ValueError):
        f.materialize()


# ----------------------------------------------------------- real Ruff ------


@pytest.mark.skipif(not RUFF_OK, reason="ruff not installed")
def test_real_ruff_delegation_end_to_end(tmp_path):
    extra = "[tool.ruff]\nline-length = 88\n"
    root = _mk_repo(tmp_path, extra)
    messy = root / "sample_app" / "messy.py"
    messy.write_text(
        "import os\n\n\ndef calc( a,b ) :\n\treturn a+b\n",
        encoding="utf-8",
    )
    git(root, "add", "-A")
    git(root, "-c", "user.email=cg@example.com",
        "-c", "user.name=cg", "commit", "-m", "messy")

    findings, _ = audit_mod.audit(root, use_formatter=True)
    delegates = [f for f in findings if f.delegate == "Ruff"]
    assert delegates, "expected delegated Ruff formatting finding for messy.py"
    assert not any(
        f.fix_id in formatters.SUBSUMED_FIX_IDS and f.path.suffix == ".py"
        for f in findings
    )

    # Zero-logic proof: delegation must be format-only (same AST).
    import ast

    delegate = [f for f in delegates if f.path == messy][0]
    ch = delegate.materialize()
    old_ast = ast.dump(ast.parse(ch.old_content))
    new_ast = ast.dump(ast.parse(ch.new_content))
    assert old_ast == new_ast

    # Apply the delegated batch: verification must pass, change must land.
    result = applier.apply_findings(root, findings, batch="formatting")
    assert result["reverted"] is False
    assert any(str(messy) in str(p) for p in result["applied"])
    assert "\t" not in messy.read_text(encoding="utf-8")

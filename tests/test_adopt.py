"""Tests for cg adopt: guided onboarding (safe batch + converged scaffold)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conventionguardian import adopt as adopt_mod
from conventionguardian import applier, safety, styleguide
from fixture_project import build_git_repo, git


@pytest.fixture()
def mini_project(tmp_path: Path) -> Path:
    return build_git_repo(tmp_path)


def _plan_of(root: Path):
    from conventionguardian import audit as audit_mod, scanner

    findings, profile = audit_mod.audit(root)
    files = scanner.iter_files(root, None)
    return styleguide.build_styleguide(root, findings, profile, files)


def _arm(root: Path) -> None:
    """Commit the scaffold (two passes) so the drift gate is armed and clean."""
    for _ in range(2):
        styleguide.write_styleguide(root, _plan_of(root), force=True)
        _commit(root, "arm styleguide")


def _commit(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "-c", "user.email=cg@example.com",
        "-c", "user.name=cg", "commit", "-m", message)


def test_adopt_happy_path_applies_and_scaffolds(mini_project):
    res = adopt_mod.adopt(mini_project)
    assert res.ok and not res.reverted
    assert res.branch and res.branch.startswith("cg/convention-")
    assert res.applied, "safe batch should have applied fixes"
    assert sorted(res.written) == sorted(adopt_mod.ARTIFACT_ORDER)
    assert not res.skipped_scaffold
    # Convergence: the on-disk STYLEGUIDE.md matches the post-arm audit.
    rep = styleguide.check_styleguide(mini_project, _plan_of(mini_project))
    assert not rep.drifted, "STYLEGUIDE must not be stale right after adopt"
    # Tab-indentation fix really landed (safe batch).
    tabbed = (mini_project / "sample_app" / "tabbed.py").read_text(encoding="utf-8")
    assert "\t" not in tabbed


def test_adopt_is_idempotent_second_run(mini_project):
    adopt_mod.adopt(mini_project)
    _commit(mini_project, "adopt")  # real usage commits between runs
    res2 = adopt_mod.adopt(mini_project)
    assert res2.ok
    assert not res2.applied, "second run: safe batch has nothing left"
    assert not res2.written, "second run: scaffold already exists"
    assert sorted(res2.skipped_scaffold) == sorted(adopt_mod.ARTIFACT_ORDER)


def test_adopt_dry_run_writes_nothing(mini_project):
    before_tabbed = (mini_project / "sample_app" / "tabbed.py").read_bytes()
    res = adopt_mod.adopt(mini_project, dry_run=True)
    assert res.skipped_apply == "dry-run"
    assert res.applied == [] and res.written == []
    assert (mini_project / "sample_app" / "tabbed.py").read_bytes() == before_tabbed
    assert not (mini_project / ".editorconfig").exists()


def test_adopt_refuses_dirty_tree(mini_project):
    (mini_project / "scratch.txt").write_text("dirty", encoding="utf-8")
    with pytest.raises(adopt_mod.AdoptError, match="uncommitted"):
        adopt_mod.adopt(mini_project)


def test_adopt_drift_gate_blocks_stale_scaffold(mini_project):
    _arm(mini_project)
    ec = mini_project / ".editorconfig"
    ec.write_text(ec.read_text(encoding="utf-8") + "\n# hand edit\n", encoding="utf-8", newline="\n")
    _commit(mini_project, "hand edit")  # commit so only the drift gate fires
    with pytest.raises(adopt_mod.AdoptError, match="drift gate"):
        adopt_mod.adopt(mini_project)
    # force scaffolds over the drift.
    res = adopt_mod.adopt(mini_project, force=True)
    assert ".editorconfig" in res.written
    assert styleguide.check_styleguide(mini_project, _plan_of(mini_project)).clean


def test_adopt_revert_leaves_no_new_scaffold_until_after_apply(mini_project):
    """On verification failure, code reverts and scaffold is still written."""
    (mini_project / "tests" / "test_bad.py").write_text(
        "def test_always_fails():\n    assert False\n", encoding="utf-8"
    )
    git(mini_project, "add", "-A")
    git(mini_project, "-c", "user.email=cg@example.com",
        "-c", "user.name=cg", "commit", "-m", "bad")
    res = adopt_mod.adopt(mini_project)
    assert res.reverted
    assert not res.ok
    assert res.applied == []
    assert sorted(res.written) == sorted(adopt_mod.ARTIFACT_ORDER), (
        "scaffold written after revert so the next attempt starts documented"
    )
    tabbed = (mini_project / "sample_app" / "tabbed.py").read_text(encoding="utf-8")
    assert "\t" in tabbed, "code must be back to pre-apply state"


def test_adopt_never_overwrites_existing_artifacts(mini_project):
    (mini_project / ".editorconfig").write_text("# mine\n", encoding="utf-8")
    _commit(mini_project, "existing editorconfig")
    res = adopt_mod.adopt(mini_project)
    assert ".editorconfig" in res.skipped_scaffold
    assert (mini_project / ".editorconfig").read_text(encoding="utf-8") == "# mine\n"


def test_adopt_non_git_repo_refuses(tmp_path):
    from fixture_project import build

    build(tmp_path)
    with pytest.raises(adopt_mod.AdoptError, match="git"):
        adopt_mod.adopt(tmp_path)


def test_adopt_log_records_safe_batch(mini_project):
    adopt_mod.adopt(mini_project)
    log = applier.load_log(mini_project)
    assert log["applied"], "apply must be recorded in .cg/log.json"
    assert log["applied"][-1]["status"] == "applied"


def test_cli_adopt_exit_codes(mini_project, monkeypatch):
    from typer.testing import CliRunner

    from conventionguardian import cli, scanner

    monkeypatch.setattr(scanner, "find_root", lambda: mini_project)

    (mini_project / "scratch.txt").write_text("dirty", encoding="utf-8")
    dirty = CliRunner().invoke(cli.app, ["adopt"])
    assert dirty.exit_code == 1 and "uncommitted" in dirty.output

    ok = CliRunner().invoke(cli.app, ["adopt", "--allow-dirty"])
    assert ok.exit_code == 0, ok.output
    assert "wrote" in ok.output and "verified" in ok.output

    _commit(mini_project, "adopt")  # commit between runs, like real usage
    again = CliRunner().invoke(cli.app, ["adopt"])
    assert again.exit_code == 0 and "kept existing" in again.output

    dry = CliRunner().invoke(cli.app, ["adopt", "--dry-run"])
    assert dry.exit_code == 0 and "Dry run" in dry.output

"""Tests for cg init-styleguide artifact generation."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conventionguardian import audit as audit_mod
from conventionguardian import scanner, styleguide
from conventionguardian.models import ToolProfile
from fixture_project import build, build_git_repo, git


@pytest.fixture()
def mini_project(tmp_path: Path) -> Path:
    return build_git_repo(tmp_path)


def _plan(root: Path):
    findings, profile = audit_mod.audit(root)
    files = scanner.iter_files(root, None)
    return styleguide.build_styleguide(root, findings, profile, files), findings, profile


def test_generates_all_four_artifacts(mini_project):
    plan, _, _ = _plan(mini_project)
    assert set(plan.artifacts) == {
        ".editorconfig", ".pre-commit-config.yaml", ".cg/ci-lint.yml", "STYLEGUIDE.md",
    }
    assert all(c.strip() for c in plan.artifacts.values())
    assert not any(plan.existed.values())  # fresh repo: nothing pre-exists


def test_editorconfig_reflects_fixture_conventions(mini_project):
    plan, _, _ = _plan(mini_project)
    ec = plan.artifacts[".editorconfig"]
    assert "root = true" in ec
    assert "end_of_line = lf" in ec
    assert "insert_final_newline = true" in ec
    assert "[*.py]" in ec and "indent_size = 4" in ec
    assert "max_line_length = 100" in ec


def test_precommit_default_is_hygiene_only(mini_project):
    plan, _, _ = _plan(mini_project)
    pc = plan.artifacts[".pre-commit-config.yaml"]
    assert "trailing-whitespace" in pc
    assert "end-of-file-fixer" in pc
    # Fixture configures no Python formatter -> explicit guidance, no ruff hook.
    assert "no Python formatter detected" in pc
    assert "\n      - id: ruff" not in pc  # commented example must not read as a hook


def test_precommit_pins_detected_formatter(mini_project, monkeypatch):
    profile = ToolProfile(
        languages=["Python"], formatters=["Ruff"], linters=["Ruff"], tests=["pytest"]
    )
    monkeypatch.setattr(styleguide, "_detect_version", lambda tool: "0.16.7")
    pc = styleguide._precommit(mini_project, profile, list(mini_project.rglob("*.py")))
    assert "astral-sh/ruff-pre-commit" in pc
    assert "rev: v0.16.7  # detected ruff 0.16.7" in pc
    assert "ruff-format" in pc


def test_ci_snippet_matches_stack(monkeypatch):
    profile = ToolProfile(
        languages=["Python"],
        formatters=["Ruff"],
        linters=["Ruff", "mypy"],
        tests=["pytest"],
    )
    ci = styleguide._ci(profile, [])
    assert '"on":' in ci  # quoted so YAML parses it as a key, not a bool
    assert "ruff format --check ." in ci
    assert "mypy ." in ci
    assert "pytest -q" in ci
    assert "cg verify" in ci

    go = styleguide._ci(ToolProfile(languages=["Go"], tests=["go test"]), [])
    assert 'gofmt -l .' in go
    assert "go vet ./..." in go


def test_styleguide_md_has_snapshot_and_drift(mini_project):
    plan, findings, _ = _plan(mini_project)
    md = plan.artifacts["STYLEGUIDE.md"]
    assert md.startswith("# Style Guide —")
    assert "## Audit snapshot" in md
    # Data rows: | category | findings | auto | manual |
    rows = re.findall(r"^\| \*{0,2}(\w+)\*{0,2} \| (\d+) \| (\d+) \| (\d+) \|$", md, re.M)
    assert rows, "expected category table rows"
    total = [r for r in rows if r[0] == "total"][0]
    cats = [r for r in rows if r[0] != "total"]
    assert int(total[1]) == sum(int(r[1]) for r in cats)
    assert int(total[2]) == sum(int(r[2]) for r in cats)
    # Fixture has tab-indentation drift -> the guide must call it out.
    assert "tab indentation" in md
    assert str(len(findings)) in md  # audit basis line cites the finding count


def test_write_skips_existing_unless_force(mini_project):
    plan, _, _ = _plan(mini_project)
    written, skipped = styleguide.write_styleguide(mini_project, plan)
    assert sorted(written) == sorted(plan.artifacts)
    assert not skipped
    # Idempotent second run: everything exists -> everything skipped.
    written2, skipped2 = styleguide.write_styleguide(mini_project, plan)
    assert not written2 and sorted(skipped2) == sorted(plan.artifacts)
    # --force overwrites anyway.
    written3, skipped3 = styleguide.write_styleguide(mini_project, plan, force=True)
    assert sorted(written3) == sorted(plan.artifacts) and not skipped3


def test_written_files_use_lf_and_trailing_newline(mini_project):
    plan, _, _ = _plan(mini_project)
    styleguide.write_styleguide(mini_project, plan)
    raw = (mini_project / ".editorconfig").read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")


def _arm(root: Path) -> None:
    """Write artifacts and commit them so they count as armed.

    Two passes: arming .editorconfig resolves the tooling finding, which
    shifts the STYLEGUIDE.md snapshot — the second pass regenerates against
    the post-arm audit, so the committed files are a fixed point.
    """
    for _ in range(2):
        findings, profile = audit_mod.audit(root)
        files = scanner.iter_files(root, None)
        plan = styleguide.build_styleguide(root, findings, profile, files)
        styleguide.write_styleguide(root, plan, force=True)
        git(root, "add", "-A")
        git(root, "-c", "user.email=cg@example.com",
            "-c", "user.name=cg", "commit", "-m", "arm styleguide")


def test_check_clean_after_arm_and_converge(mini_project):
    _arm(mini_project)
    findings, profile = audit_mod.audit(mini_project)
    files = scanner.iter_files(mini_project, None)
    plan = styleguide.build_styleguide(mini_project, findings, profile, files)
    rep = styleguide.check_styleguide(mini_project, plan)
    assert rep.clean
    assert sorted(rep.ok) == sorted(plan.artifacts)
    assert not rep.not_armed


def test_check_reports_drift_with_diff(mini_project):
    _arm(mini_project)
    editorconfig = mini_project / ".editorconfig"
    editorconfig.write_text(
        editorconfig.read_text(encoding="utf-8") + "\n# tampered rule\n",
        encoding="utf-8", newline="\n",
    )
    findings, profile = audit_mod.audit(mini_project)
    files = scanner.iter_files(mini_project, None)
    plan = styleguide.build_styleguide(mini_project, findings, profile, files)
    rep = styleguide.check_styleguide(mini_project, plan)
    assert not rep.clean
    assert rep.drifted == [".editorconfig"]
    assert ".editorconfig" in rep.diffs and "tampered rule" in rep.diffs[".editorconfig"]
    assert set(rep.ok) == set(plan.artifacts) - {".editorconfig"}


def test_check_ignores_crlf_checkout(mini_project):
    _arm(mini_project)
    ec = mini_project / ".editorconfig"
    ec.write_bytes(ec.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
    findings, profile = audit_mod.audit(mini_project)
    files = scanner.iter_files(mini_project, None)
    plan = styleguide.build_styleguide(mini_project, findings, profile, files)
    assert styleguide.check_styleguide(mini_project, plan).clean


def test_check_ignores_generation_date(mini_project):
    _arm(mini_project)
    md = mini_project / "STYLEGUIDE.md"
    md.write_text(
        md.read_text(encoding="utf-8").replace("on 2026-09-26", "on 2001-01-01"),
        encoding="utf-8", newline="\n",
    )
    findings, profile = audit_mod.audit(mini_project)
    files = scanner.iter_files(mini_project, None)
    plan = styleguide.build_styleguide(mini_project, findings, profile, files)
    assert styleguide.check_styleguide(mini_project, plan).clean


def test_check_untracked_artifacts_are_not_armed(mini_project):
    styleguide.write_styleguide(mini_project, _plan(mini_project)[0])
    # Files exist on disk but are untracked -> not armed, no failure.
    findings, profile = audit_mod.audit(mini_project)
    files = scanner.iter_files(mini_project, None)
    plan = styleguide.build_styleguide(mini_project, findings, profile, files)
    rep = styleguide.check_styleguide(mini_project, plan)
    assert rep.clean
    assert sorted(rep.not_armed) == sorted(plan.artifacts)
    assert not rep.ok and not rep.drifted


def test_check_non_git_repo_compares_on_disk(tmp_path):
    build(tmp_path)  # no git init
    findings, profile = audit_mod.audit(tmp_path)
    files = scanner.iter_files(tmp_path, None)
    plan = styleguide.build_styleguide(tmp_path, findings, profile, files)
    styleguide.write_styleguide(tmp_path, plan)
    rep = styleguide.check_styleguide(tmp_path, plan)
    assert rep.clean and not rep.not_armed  # no arming concept: compare directly


def test_cli_check_exit_codes(mini_project, monkeypatch):
    from typer.testing import CliRunner

    from conventionguardian import cli

    monkeypatch.setattr(scanner, "find_root", lambda: mini_project)
    _arm(mini_project)
    ok = CliRunner().invoke(cli.app, ["init-styleguide", "--check"])
    assert ok.exit_code == 0, ok.output
    assert "up to date" in ok.output

    ec = mini_project / ".editorconfig"
    ec.write_text(ec.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8", newline="\n")
    bad = CliRunner().invoke(cli.app, ["init-styleguide", "--check"])
    assert bad.exit_code == 1
    assert "drifted" in bad.output and ".editorconfig" in bad.output


def test_mask_stamp_covers_md_and_yaml_forms():
    md = "_Generated by ConventionGuardian (`cg init-styleguide`) on 2026-09-26. Derived..._"
    yml = "# Generated by ConventionGuardian (cg init-styleguide). Review before committing."
    assert "2026-09-26" not in styleguide._mask_stamp(md)
    assert "on <date>" in styleguide._mask_stamp(md)
    # Bare form has no date suffix: masking must leave it intact.
    assert styleguide._mask_stamp(yml) == yml


def test_generated_yaml_parses(mini_project):
    """The two generated YAML artifacts must be valid YAML (quoted 'on:' etc.)."""
    yaml = pytest.importorskip("yaml")
    plan, _, _ = _plan(mini_project)
    for rel in (".pre-commit-config.yaml", ".cg/ci-lint.yml"):
        data = yaml.safe_load(plan.artifacts[rel])
        assert isinstance(data, dict), rel
    ci = yaml.safe_load(plan.artifacts[".cg/ci-lint.yml"])
    assert "on" in ci  # not parsed as boolean True


def test_cli_init_styleguide_writes_files(mini_project, monkeypatch):
    from typer.testing import CliRunner

    from conventionguardian import cli

    monkeypatch.setattr(scanner, "find_root", lambda: mini_project)
    result = CliRunner().invoke(cli.app, ["init-styleguide"])
    assert result.exit_code == 0, result.output
    assert (mini_project / ".editorconfig").is_file()
    assert (mini_project / "STYLEGUIDE.md").is_file()
    assert (mini_project / ".cg" / "ci-lint.yml").is_file()
    assert "wrote" in result.output

"""Audit pipeline: run all finders, assign IDs, build batches."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

from conventionguardian import formatters

from conventionguardian import scanner
from conventionguardian.adapters import AdapterContext, get_adapters
from conventionguardian.config import Config, load_config
from conventionguardian.finders import (
    docs_style,
    formatting,
    imports,
    misc,
    naming,
    structure,
    tooling,
)
from conventionguardian.models import BATCH_LABELS, Category, Finding, Severity, ToolProfile, make_id


def derive_local_roots(root: Path, files: list[Path]) -> tuple[str, ...]:
    """Top-level package names belonging to THIS project (not third parties).

    Derived from __init__.py layout and the pyproject project name. Passed to
    the import grouper so first-party imports land in the local bucket.
    """
    roots: set[str] = set()
    for p in files:
        if p.name != "__init__.py":
            continue
        parts = p.relative_to(root).parts
        if len(parts) >= 2:
            roots.add(parts[0])
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        m = re.search(r'^name\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            roots.add(m.group(1).replace("-", "_"))
    return tuple(sorted(roots))


def audit(
    root: Path, config: Config | None = None, use_formatter: bool = False
) -> tuple[list[Finding], ToolProfile]:
    """Run every finder over the project and return findings plus the tool profile.

    With use_formatter=True and a configured+installed formatter, built-in
    formatting fixes are replaced by delegated tool runs.
    """
    root = Path(root).resolve()
    config = config or load_config(root)
    profile = scanner.detect_profile(root)
    files = scanner.iter_files(root, config)
    local_roots = derive_local_roots(root, files)
    findings: list[Finding] = []

    structure.find_structure_issues(root, files, findings)

    trees: dict[Path, ast.AST] = {}
    for path in files:
        if path.suffix == ".py":
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(text)
            except SyntaxError:
                continue
            trees[path] = tree
            imports.find_import_issues(tree, path, findings, local_roots=local_roots)
            formatting.find_formatting_issues(tree, path, findings, max_line=100)
            docs_style.find_docs_issues(tree, path, findings)
            misc.find_misc_issues(tree, path, findings)

    naming.find_project_naming_issues(root, trees, findings)
    tooling.find_tooling_issues(root, files, findings)

    # Tree-sitter adapters: JS/TS, Go, Rust (categories B, C, D).
    ctx = AdapterContext(root=root, local_roots=local_roots, max_line=100)
    by_ext: dict[str, list] = {}
    for adapter in get_adapters(ctx):
        for ext in adapter.extensions:
            by_ext.setdefault(ext, []).append(adapter)
    for path in files:
        adapters = by_ext.get(path.suffix)
        if adapters:
            for adapter in adapters:
                adapter.find_issues(path, findings)

    # Formatter delegation: when the project configures its own formatter and
    # it is installed, suppress built-in formatting fixes it would subsume and
    # propose running the tool instead (via stdin->stdout diff, never writing).
    if use_formatter:
        formatters.delegate_formatting(
            root, files, findings,
            detect=lambda: formatters.detect_configured(root, profile),
        )

    # Assign IDs and sort into stable category order.
    id_findings: list[Finding] = []
    for category in Category:
        group = [f for f in findings if f.category == category]
        for f in group:
            f.id = make_id(category, id_findings)
            id_findings.append(f)
    return id_findings, profile


def _batch_of(f: Finding) -> str:
    return f.category.value


def build_batches(findings: list[Finding]) -> dict[str, list[Finding]]:
    """Group findings into selectable batches."""
    batches: dict[str, list[Finding]] = {}
    for f in findings:
        batches.setdefault(_batch_of(f), []).append(f)
    return batches


def eligible_for_batch(findings: list[Finding], batch: str) -> list[Finding]:
    """Findings selectable for a given batch name or category value."""
    if batch in BATCH_LABELS:
        if batch == "high-impact":
            return [f for f in findings if f.severity == Severity.CRITICAL]
        if batch == "safe":
            return [f for f in findings if f.conf == 100]
        return [f for f in findings if f.category.value == batch]
    return []


def find_git_repos_under(root: Path) -> list[Path]:
    """Find nested git repos (used to detect vendored sub-projects)."""
    found: list[Path] = []
    for p in sorted(root.rglob(".git")):
        if p.is_dir():
            found.append(p.parent)
    return found


def _git_ls_files(root: Path) -> list[Path]:
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if res.returncode != 0:
        return []
    return [root / ln for ln in res.stdout.splitlines() if ln.strip()]


def write_report_json(path: Path, root: Path, profile: ToolProfile, findings: list[Finding]) -> None:
    """Serialize an audit report as JSON."""
    data = {
        "root": str(root),
        "profile": {
            "languages": profile.languages,
            "package_managers": profile.package_managers,
            "configs": profile.configs,
            "formatters": profile.formatters,
            "linters": profile.linters,
            "monorepo": profile.monorepo,
            "tests": profile.tests,
            "is_git": profile.is_git,
        },
        "findings": [
            {
                "id": f.id,
                "category": f.category.value,
                "severity": f.severity.value,
                "path": str(f.path),
                "message": f.message,
                "current": f.current,
                "recommended": f.recommended,
                "conf": f.conf,
                "rationale": f.rationale,
                "fix_id": f.fix_id,
                "applicable": f.conf == 100 and f.fix is not None,
            }
            for f in findings
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

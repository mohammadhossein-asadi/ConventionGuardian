"""Project detection: languages, package managers, convention tooling, test frameworks.

Also provides the ignore-aware file walk used by the audit pipeline.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

from pathspec import GitIgnoreSpec

from conventionguardian.config import BUILTIN_IGNORE_FILES, Config, load_config
from conventionguardian.models import ToolProfile


def find_root(start: Path | None = None) -> Path:
    """Prefer git root; fall back to the start directory."""
    start = Path(start or Path.cwd()).resolve()
    p = start
    while True:
        if (p / ".git").exists():
            return p
        if p.parent == p:
            return start
        p = p.parent


def _has_any(root: Path, patterns: tuple[str, ...]) -> bool:
    return any(root.glob(p) for p in patterns)


def detect_profile(root: Path) -> ToolProfile:
    profile = ToolProfile(root=root)
    languages: list[str] = []

    if _has_any(root, ("pyproject.toml", "setup.py", "setup.cfg", "Pipfile")) or any(
        root.glob("*.py")
    ):
        languages.append("Python")
    if root.joinpath("package.json").is_file():
        if root.joinpath("tsconfig.json").is_file() or _has_any(root, ("**/*.ts", "**/*.tsx")):
            languages.append("TypeScript")
        if _has_any(root, ("**/*.js", "**/*.mjs", "**/*.cjs", "**/*.jsx")):
            languages.append("JavaScript")
    if root.joinpath("go.mod").is_file():
        languages.append("Go")
    if root.joinpath("Cargo.toml").is_file():
        languages.append("Rust")
    if _has_any(root, ("pom.xml", "build.gradle", "build.gradle.kts")):
        languages.append("Java")
    profile.languages = languages

    managers: list[str] = []
    if root.joinpath("package-lock.json").is_file():
        managers.append("npm")
    if root.joinpath("yarn.lock").is_file():
        managers.append("yarn")
    if root.joinpath("pnpm-lock.yaml").is_file():
        managers.append("pnpm")
    if _has_any(root, ("poetry.lock", "Pipfile.lock", "uv.lock", "requirements*.txt")):
        managers.append("pip/poetry/uv")
    if root.joinpath("Cargo.lock").is_file():
        managers.append("cargo")
    if root.joinpath("go.sum").is_file():
        managers.append("go modules")
    profile.package_managers = managers

    configs: list[str] = []
    for name in (
        ".editorconfig",
        "pyproject.toml",
        "setup.cfg",
        "package.json",
        "Makefile",
        "tox.ini",
    ):
        if root.joinpath(name).is_file():
            configs.append(name)
    profile.configs = configs

    formatters: list[str] = []
    if _has_any(root, (".prettierrc*", "prettier.config.*")):
        formatters.append("Prettier")
    if root.joinpath("biome.json").is_file():
        formatters.append("Biome")
    if root.joinpath("rustfmt.toml").is_file() or root.joinpath(".rustfmt.toml").is_file():
        formatters.append("rustfmt")
    if root.joinpath(".clang-format").is_file():
        formatters.append("clang-format")
    if "Python" in languages and root.joinpath("pyproject.toml").is_file():
        text = root.joinpath("pyproject.toml").read_text(encoding="utf-8", errors="replace")
        if "[tool.black]" in text:
            formatters.append("Black")
        if "[tool.ruff]" in text or "[tool.ruff.lint]" in text:
            formatters.append("Ruff")
        if "[tool.isort]" in text:
            formatters.append("isort")
    if "Go" in languages:
        formatters.append("gofmt")
    profile.formatters = formatters

    linters: list[str] = []
    if _has_any(root, (".eslintrc*", "eslint.config.*")):
        linters.append("ESLint")
    if "Python" in languages and root.joinpath("pyproject.toml").is_file():
        text = root.joinpath("pyproject.toml").read_text(encoding="utf-8", errors="replace")
        if "[tool.ruff]" in text or "[tool.ruff.lint]" in text:
            linters.append("Ruff")
        if "[tool.mypy]" in text:
            linters.append("mypy")
        if "[tool.flake8]" in text or root.joinpath(".flake8").is_file():
            linters.append("flake8")
    if root.joinpath(".golangci.yml").is_file() or root.joinpath(".golangci.yaml").is_file():
        linters.append("golangci-lint")
    if "Rust" in languages:
        linters.append("Clippy")
    profile.linters = linters

    monorepo: list[str] = []
    for name, label in (
        ("nx.json", "Nx"),
        ("turbo.json", "Turborepo"),
        ("lerna.json", "Lerna"),
        ("pnpm-workspace.yaml", "pnpm workspace"),
        ("rush.json", "Rush"),
    ):
        if root.joinpath(name).is_file():
            monorepo.append(label)
    if _has_any(root, ("WORKSPACE", "WORKSPACE.bazel", "MODULE.bazel")):
        monorepo.append("Bazel")
    profile.monorepo = monorepo

    tests: list[str] = []
    pyproject = root.joinpath("pyproject.toml")
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8", errors="replace")
        if "[tool.pytest" in text:
            tests.append("pytest")
    if _has_any(root, ("jest.config.*",)):
        tests.append("Jest")
    if _has_any(root, ("vitest.config.*",)):
        tests.append("Vitest")
    if "Go" in languages:
        tests.append("go test")
    if "Rust" in languages:
        tests.append("cargo test")
    profile.tests = tests
    profile.is_git = root.joinpath(".git").exists()
    return profile


def _ignore_spec(root: Path) -> GitIgnoreSpec:
    lines: list[str] = []
    for name in BUILTIN_IGNORE_FILES:
        p = root / name
        if p.is_file():
            lines.extend(
                p.read_text(encoding="utf-8", errors="replace").splitlines()
            )
    return GitIgnoreSpec.from_lines("gitignore", lines)


def _excluded(rel: str, config: Config) -> bool:
    parts = Path(rel).parts
    for part in parts[:-1]:
        if part in config.excludes:
            return True
    name = parts[-1] if parts else rel
    for e in config.excludes:
        if fnmatch.fnmatch(name, e):
            return True
    return False


def iter_files(root: Path, config: Config | None = None) -> list[Path]:
    """All audit-worthy files under root, honoring excludes, .gitignore, .cgignore."""
    config = config or load_config(root)
    spec = _ignore_spec(root)
    files: list[Path] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if _excluded(rel, config):
            continue
        if spec.match_file(rel):
            continue
        files.append(p)
    return files

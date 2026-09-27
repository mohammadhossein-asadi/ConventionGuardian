"""Local config (.cg.toml): target convention set, include/exclude, ignore patterns."""

from __future__ import annotations

import tomllib
from pathlib import Path

DEFAULT_EXCLUDES = [
    "node_modules",
    "vendor",
    "dist",
    "build",
    "out",
    "__pycache__",
    ".venv",
    "venv",
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "target",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "coverage",
    "htmlcov",
    "site-packages",
    ".cg",
    "*.min.js",
    "*.min.css",
]

CONFIG_NAME = ".cg.toml"

BUILTIN_IGNORE_FILES = (".gitignore", ".cgignore")

TARGETS = {
    "internal": "Enforce internal consistency only",
    "pep8": "PEP 8 + Black + isort / Ruff (Python)",
    "airbnb": "Google/Airbnb + Prettier + ESLint (JS/TS)",
    "gofmt": "Standard Go (gofmt + golangci-lint)",
    "rustfmt": "Rustfmt + Clippy",
    "custom": "Company / team style guide (see style_guide_file)",
}

DEFAULT_TARGET = "internal"


class Config:
    """Loaded .cg.toml settings."""

    def __init__(self, root: Path, data: dict) -> None:
        self.root = root
        self.data = data
        self.target: str = data.get("target", DEFAULT_TARGET)
        self.excludes: list[str] = list(DEFAULT_EXCLUDES)
        self.excludes.extend(data.get("exclude", []))
        self.includes: list[str] = list(data.get("include", []))
        self.style_guide_file: str | None = data.get("style_guide_file")

    def exclude_globs(self) -> list[str]:
        return [f"**/{e}" if "/" not in e else e for e in self.excludes]


def load_config(root: Path) -> Config:
    """Load .cg.toml from root if present; otherwise defaults."""
    path = root / CONFIG_NAME
    data: dict = {}
    if path.is_file():
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    return Config(root=root, data=data)


def save_config(root: Path, target: str) -> Path:
    """Write a minimal .cg.toml; returns the path written."""
    path = root / CONFIG_NAME
    lines = [
        f'target = "{target}"',
        "",
        "# include = []   # extra globs to audit",
        "# exclude = []   # extra globs to skip",
        '# style_guide_file = "STYLE.md"',
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

"""Formatter/linter integration.

When the project already configures a formatter (Ruff, Black, Prettier, gofmt,
rustfmt), the formatting batch should defer to that tool instead of built-in
fixes: the project's own formatter is the source of truth for its style.

Mechanics: run the formatter in "diff mode" (stdin -> stdout, never writing)
over each file, and propose the resulting transformation as a delegate
finding. If the tool is missing or errors, delegation is skipped entirely and
the built-in passes apply as usual.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from conventionguardian.models import Finding, Severity, ToolProfile


@dataclass(frozen=True)
class FormatterSpec:
    """One supported formatter tool."""

    name: str
    cmd: tuple[str, ...]
    suffixes: tuple[str, ...]
    languages: tuple[str, ...]
    config_patterns: tuple[str, ...] = ()
    content_markers: tuple[str, ...] = ()
    parser_map: dict[str, str] = field(default_factory=dict)


SPECS: tuple[FormatterSpec, ...] = (
    FormatterSpec(
        name="Ruff",
        cmd=("ruff", "format", "-"),
        suffixes=(".py",),
        languages=("Python",),
        config_patterns=("ruff.toml", ".ruff.toml"),
        content_markers=("[tool.ruff]",),
    ),
    FormatterSpec(
        name="Black",
        cmd=("black", "--quiet", "-"),
        suffixes=(".py",),
        languages=("Python",),
        content_markers=("[tool.black]",),
    ),
    FormatterSpec(
        name="Prettier",
        cmd=("prettier", "--parser", "{parser}"),
        suffixes=(".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".css", ".scss",
                  ".less", ".html", ".json", ".md", ".yaml", ".yml"),
        languages=("JavaScript", "TypeScript"),
        config_patterns=(".prettierrc*", "prettier.config.*"),
        parser_map={
            ".js": "babel", ".jsx": "babel", ".mjs": "babel", ".cjs": "babel",
            ".ts": "typescript", ".tsx": "typescript",
            ".css": "css", ".scss": "scss", ".less": "less",
            ".html": "html", ".json": "json", ".md": "markdown",
            ".yaml": "yaml", ".yml": "yaml",
        },
    ),
    FormatterSpec(
        name="gofmt",
        cmd=("gofmt",),
        suffixes=(".go",),
        languages=("Go",),
    ),
    FormatterSpec(
        name="rustfmt",
        cmd=("rustfmt", "--emit", "stdout"),
        suffixes=(".rs",),
        languages=("Rust",),
        config_patterns=("rustfmt.toml", ".rustfmt.toml"),
    ),
)


def _config_present(root: Path, spec: FormatterSpec) -> bool:
    if not spec.config_patterns and not spec.content_markers:
        # No config concept (e.g. gofmt): the language itself decides.
        return True
    for pattern in spec.config_patterns:
        if any(root.glob(pattern)):
            return True
    pyproject = root / "pyproject.toml"
    if spec.content_markers and pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False
        return any(m in text for m in spec.content_markers)
    return False


def _resolve_binary(root: Path, spec: FormatterSpec) -> tuple[str, ...] | None:
    """Prefer the tool on PATH, then project-local venv / node_modules installs."""
    found = shutil.which(spec.cmd[0])
    if found:
        return (found, *spec.cmd[1:])
    candidates = (
        root / ".venv" / "Scripts" / spec.cmd[0],
        root / ".venv" / "Scripts" / f"{spec.cmd[0]}.exe",
        root / ".venv" / "bin" / spec.cmd[0],
        root / "node_modules" / ".bin" / spec.cmd[0],
        root / "node_modules" / ".bin" / f"{spec.cmd[0]}.cmd",
    )
    for cand in candidates:
        if cand.is_file():
            return (str(cand), *spec.cmd[1:])
    return None


def detect_configured(root: Path, profile: ToolProfile) -> list[FormatterSpec]:
    """Formatters that are (a) configured for this project, (b) installed."""
    langs = set(profile.languages)
    out: list[FormatterSpec] = []
    for spec in SPECS:
        if not langs & set(spec.languages):
            continue
        if not _config_present(root, spec):
            continue
        if _resolve_binary(root, spec) is None:
            continue
        out.append(spec)
    return out


def handles(spec: FormatterSpec, path: Path) -> bool:
    return path.suffix in spec.suffixes


def run_formatter(spec: FormatterSpec, root: Path, text: str, suffix: str) -> str | None:
    """Run the formatter over `text` via stdin/stdout; returns formatted text.

    Returns None when the tool is missing, errors, or times out — the caller
    must then treat the file as NOT delegated (fail-open to built-in passes).
    """
    cmd = list(spec.cmd)
    if "{parser}" in cmd:
        parser = spec.parser_map.get(suffix, "babel")
        cmd = [c.replace("{parser}", parser) for c in cmd]
    binary = _resolve_binary(root, spec)
    if binary is None:
        return None
    try:
        res = subprocess.run(
            binary,
            cwd=str(root),
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if res.returncode != 0:
        return None
    return res.stdout.decode("utf-8", errors="replace")


# Built-in formatting fixes that a project formatter subsumes: if the project's
# own tool would normalize these, proposing our own version is style drift.
# Import REORDERING (imp-order) is intentionally NOT subsumed: formatters like
# `ruff format` and gofmt do not sort imports (that is isort/goimports/ruff I001).
SUBSUMED_FIX_IDS = {
    "fmt-tabs",
    "fmt-final-newline",
    "fmt-quotes",
    "js-quotes",
    "go-indent",
}


def delegate_formatting(root, files, findings, detect) -> int:
    """Replace subsumed built-in formatting fixes with delegated formatter runs.

    For every file a configured formatter handles: trial-run the tool via
    stdin->stdout (never writing). If it would change the file, emit a delegate
    finding whose fix reproduces that exact output at apply time. If the tool
    is missing/errors, the file keeps its built-in findings (fail-open).

    `detect` is a zero-arg callable returning the configured FormatterSpecs.
    Returns the number of delegate findings created.
    """
    from conventionguardian.models import Category

    specs = detect()
    if not specs:
        return 0

    # Trial-run the tool per handled file. None means the tool is missing or
    # failed: that file must KEEP its built-in findings (fail-open).
    trials: dict[Path, tuple[str, str | None]] = {}
    for path in files:
        spec = next((s for s in specs if handles(s, path)), None)
        if spec is None:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not text.strip():
            continue  # nothing meaningful to format; avoid degenerate delegates
        trials[path] = (text, run_formatter(spec, root, text, path.suffix))

    # Suppress subsumed built-ins ONLY where the tool verifiably ran.
    findings[:] = [
        f for f in findings
        if not (
            f.fix_id in SUBSUMED_FIX_IDS
            and f.category.value == "formatting"
            and f.path in trials
            and trials[f.path][1] is not None
        )
    ]

    created = 0
    for path, (text, formatted) in trials.items():
        if formatted is None or formatted == text:
            continue
        spec = next(s for s in specs if handles(s, path))

        def _apply(text_in: str, _old=text, _new=formatted, _name=spec.name) -> str:
            if _old not in text_in:
                raise ValueError(f"{_name}: file changed since audit; re-run cg audit")
            return text_in.replace(_old, _new, 1)

        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
        findings.append(
            Finding(
                category=Category.FORMATTING,
                severity=Severity.DRIFT,
                path=path,
                message=f"Delegated to {spec.name} format (project's own formatter)",
                current=f"pre-{spec.name} formatting",
                recommended=f"{spec.name}-formatted",
                conf=100,
                rationale=(
                    f"{spec.name} is configured for this project and produced this "
                    "transformation in diff mode; the tool is the style source of truth."
                ),
                fix_id=f"delegate-{spec.name.lower()}",
                fix=_apply,
                delegate=spec.name,
            )
        )
        created += 1
    return created

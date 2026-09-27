# ConventionGuardian (cg)

**Full-project convention & structure audit with zero-logic-change pure-style fixes.**

ConventionGuardian scans a codebase, reports convention violations grouped into selectable batches, and applies **only** fixes you explicitly approve — each fix is a minimal unified diff and every batch is verified (fast checks: compile, type-check, unit tests) and auto-reverted if verification fails.

---

## The Zero-Logic-Change Guarantee

Every proposed fix carries a `confidence` value that the fix is purely stylistic. Fixes are only ever proposed when confidence is 100%. Lower-confidence observations are reported as **manual review** items (no diff, never applied by the tool). Batches are verified after application with type-checks/compile/tests when available and cheap; any failure reverts the whole batch.

---

## Quick Start

```bash
# 1. Clone and set up
git clone https://github.com/mohammadhossein-asadi/ConventionGuardian
cd ConventionGuardian
python -m venv .venv
.venv/Scripts/pip install -e .[dev]      # Windows
# .venv/bin/pip install -e .[dev]        # POSIX

# 2. Scan your project
cg scan

# 3. See the full audit
cg audit

# 4. Apply a batch (on a fresh safety branch, verified, auto-revert on fail)
cg apply --batch formatting

# 5. Generate styleguide artifacts from the audit
cg init-styleguide --force
```

---

## Install

### From PyPI (when published)
```bash
pip install convention-guardian
```

### Development Install
```bash
python -m venv .venv
.venv/Scripts/pip install -e .[dev]      # Windows
# .venv/bin/pip install -e .[dev]        # POSIX
```

### Optional: Tree-sitter Language Adapters
```bash
pip install -e .[adapters]   # adds tree-sitter + JS/TS, Go, Rust grammars
```

---

## Commands

| Command | Description |
|---------|-------------|
| `cg scan` | Detect languages, package managers, configs, formatters, linters, test frameworks. Writes `.cg.toml` if missing. |
| `cg audit` | Full A–G report with per-finding IDs, diffs, confidence, and rationale. |
| `cg audit --json` | Machine-readable audit output. |
| `cg show <ID>` | Show full file context around a finding. |
| `cg apply --batch <name>` | Apply an approved batch (git safety branch + verify + auto-revert on fail). |
| `cg apply --ids <ID,...>` | Apply specific findings only. |
| `cg apply --dry-run` | Materialize diffs without touching the working tree. |
| `cg verify` | Run fast checks only (compileall, pytest, tsc, go build, cargo check). |
| `cg log` | Show running applied/remaining log (`.cg/log.json`). |
| `cg report -o report.md` | Write markdown report (default `report.md`). |
| `cg report --json -o report.json` | Write JSON report. |
| `cg init-styleguide` | Generate `.editorconfig`, `.pre-commit-config.yaml`, `.cg/ci-lint.yml`, `STYLEGUIDE.md` from current audit. |
| `cg init-styleguide --check` | CI gate: regenerate and compare against git-tracked artifacts; exits 1 on drift. |

---

## Batches

Findings are grouped into selectable batches:

| Batch | Categories | Description |
|-------|------------|-------------|
| `structure` | A | Project layout, root pollution, test/docs placement |
| `naming` | B | Variables, functions, classes, types, enums, constants |
| `imports` | C | Import ordering (stdlib → third-party → local), grouping, duplicates |
| `formatting` | D | Indentation, line length, quotes, trailing commas, final newline, tabs |
| `docs` | E | Docstring/JSDoc/godoc/rustdoc format consistency (report-only) |
| `tooling` | F | `.editorconfig`, linter/formatter/CI config alignment |
| `misc` | G | Line endings, license headers, generated code markers, test naming |
| `high-impact` | — | Critical inconsistencies only |
| `safe` | — | All safe (confidence-100) items across categories |

---

## Language Adapters (Tree-sitter, Optional)

Beyond the built-in Python passes, optional tree-sitter adapters extend naming, import, and formatting categories to JavaScript/TypeScript, Go, and Rust:

```bash
pip install -e .[adapters]     # adds tree-sitter + the four grammars
```

### Adapter Guarantees

- **Parse failures**: Files that fail to parse produce a review-only finding and suppress every automatic fix for that file.
- **JavaScript/TypeScript**: Import order and long lines are report-only (module side-effect semantics); quote-style, tabs, and final newline are fixed. React-component PascalCase names are never flagged (renaming `<Feed />` would change JSX semantics — a logic change).
- **Go**: Import regrouping follows goimports-style (stdlib → external); exported (PascalCase) names are never renamed — that's an API change.
- **Rust**: `use` sorting is rustfmt-equivalent; `#[allow(non_snake_case)]` is honored; `pub` items are report-only.
- **Cross-file coordination**: Every rename is a coordinated fix group — callers and imports are renamed in the same batch, or nothing is applied.

---

## Plan → Approve → Build Flow

- **`audit` never writes** — it only reports.
- **Only `apply` writes**, and only what you explicitly named.
- Each `apply` creates a fresh git safety branch (`cg/convention-<ts>` or `--branch <name>`), backs up files, applies changes, runs verification, and auto-reverts on failure.
- **Safety net**: Refuses on dirty worktree (use `--allow-dirty` to override). Returns non-zero exit codes for CI use.

---

## Formatter Integration (Project's Own Tool is Source of Truth)

If a configured formatter is detected — **Ruff or Black** (`[tool.*]` in `pyproject.toml` / `ruff.toml`), **Prettier** (`.prettierrc*`), **gofmt**, or **rustfmt** (`rustfmt.toml`) — `cg audit` proposes running the project's own formatter over each file it handles, in diff mode (stdin → stdout, never writing). Each changed file becomes one delegated finding.

- Built-in style fixes the tool subsumes (tabs, quotes, final newline, indentation) are **suppressed**.
- Import ordering stays built-in (formatters like `ruff format` don't sort imports; that's `isort`/`goimports`/`ruff I001`).
- On by default; pass `--no-formatter` for built-in fixes only.
- If the tool is missing or errors, delegation fails open to built-in fixes.
- Binary resolution: PATH → `.venv/Scripts` → `node_modules/.bin`.

---

## Ignores

`.gitignore`, `.cgignore`, `node_modules`, `vendor`, `dist`, `build`, `__pycache__`, `.venv` and similar are skipped by default. Generated code, vendored dependencies, build artifacts, lockfiles, and binary files are auto-detected and excluded.

---

## cg init-styleguide

Generates a starter convention toolkit **derived from the current audit**, so the documented rules match observed reality instead of generic defaults:

| Artifact | Purpose |
|----------|---------|
| `.editorconfig` | Editor-level whitespace rules per detected language (LF, final newline, Python 4-space / JS 2-space / Go tabs), with drift counts from the audit. |
| `.pre-commit-config.yaml` | Hygiene hooks (trailing whitespace, EOF newline, mixed line endings) plus the project's detected formatter hook, with version pinned when the tool is on PATH (Ruff, Black, Prettier, gofmt, rustfmt). |
| `.cg/ci-lint.yml` | GitHub Actions lint job matching the stack (ruff check / `ruff format --check`, mypy, eslint, prettier --check, gofmt, clippy, tests) ending with `cg audit` + `cg verify`; copy into `.github/workflows/` to arm it. |
| `STYLEGUIDE.md` | Short human-readable guide with per-category audit snapshot table and explicit drift counts ("6 files still CRLF", "3 files with mixed quotes"). |

**Existing files are never overwritten** (re-run with `--force` to replace them). Written files use LF endings and end with a newline.

### CI Gate: `cg init-styleguide --check`

Regenerates artifacts in memory and compares against **git-tracked** copies:
- Committing (or staging) an artifact **arms** it for checking.
- Missing or untracked ones are reported as "not armed" and never fail the run.
- Any other difference marks the file as **drifted**, prints a unified diff, and exits 1 — suitable as a CI gate.
- CRLF checkouts (`core.autocrlf`) and the `STYLEGUIDE.md` generation date never count as drift.

---

## Configuration

`.cg.toml` (created by `cg scan`):

```toml
target = "internal"              # internal | pep8 | airbnb | gofmt | rustfmt | custom
# include = []                   # extra globs to audit
# exclude = []                   # extra globs to skip
# style_guide_file = "STYLE.md"  # path to team style guide (custom target)
```

### Target Convention Sets

| Target | Description |
|--------|-------------|
| `internal` | Enforce internal consistency only (default) |
| `pep8` | PEP 8 + Black + isort / Ruff (Python) |
| `airbnb` | Google/Airbnb + Prettier + ESLint (JS/TS) |
| `gofmt` | Standard Go (gofmt + golangci-lint) |
| `rustfmt` | Rustfmt + Clippy (style lints only) |
| `custom` | Company/team style guide (see `style_guide_file`) |

---

## Example Workflow

```bash
# 1. Scan and configure
cg scan

# 2. Review the audit
cg audit

# 3. Apply safe batch (all confidence-100 items)
cg apply --batch safe

# 4. Or apply specific batches
cg apply --batch imports
cg apply --batch formatting

# 5. Generate styleguide artifacts
cg init-styleguide --force

# 6. Arm for CI
cp .cg/ci-lint.yml .github/workflows/cg-lint.yml
# Add .editorconfig, .pre-commit-config.yaml, STYLEGUIDE.md to git

# 7. CI will run: formatter checks + linters + tests + cg audit + cg verify
```

---

## CI Integration

Add to `.github/workflows/cg-lint.yml`:

```yaml
name: cg-lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - run: pip install convention-guardian
      - run: cg audit
      - run: cg verify
```

Or use the generated `.cg/ci-lint.yml` which includes formatter/linter steps for your stack.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Verification failed / drift detected / user error |
| 2 | Safety error (not a git repo, dirty tree, branch creation failed) |

---

## Project Structure

```
conventionguardian/
├── __init__.py
├── cli.py              # Typer CLI entry point
├── audit.py            # Audit pipeline (A–G finders)
├── applier.py          # Apply + verify + revert
├── scanner.py          # Language/tooling detection + file walk
├── config.py           # .cg.toml config
├── models.py           # Finding, ToolProfile, Category, Severity
├── safety.py           # Git safety net (dirty check, branch)
├── checks.py           # Fast verification (compileall, pytest, tsc, etc.)
├── diff.py             # Unified diff helpers
├── adopt.py            # Guided onboarding (safe batch + scaffold)
├── styleguide.py       # Artifact generators
├── formatters.py       # Formatter delegation (Ruff, Black, Prettier, gofmt, rustfmt)
├── finders/            # A–G finders (imports, formatting, naming, etc.)
├── adapters/           # Tree-sitter adapters (JS/TS, Go, Rust)
└── reporters/          # Console + Markdown output
```

---

## Contributing

1. Fork and create a feature branch
2. Make changes with `cg audit` clean
3. Run `cg verify` (compile + tests)
4. Submit PR

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Credits

Built with:
- [Typer](https://typer.tiangolo.com/) — CLI framework
- [Rich](https://rich.readthedocs.io/) — Terminal rendering
- [pathspec](https://github.com/cpburnz/python-pathspec) — Gitignore matching
- [tree-sitter](https://tree-sitter.github.io/) — Language parsing (optional)
- [LibCST](https://libcst.readthedocs.io/) — Python AST manipulation (optional)

---

**ConventionGuardian** — making convention enforcement safe, deterministic, and zero-logic-change.
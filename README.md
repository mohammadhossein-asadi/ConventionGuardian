# ConventionGuardian (cg)

Full-project convention & structure audit with **zero-logic-change** pure-style fixes.

ConventionGuardian scans a codebase, reports convention violations grouped into selectable
batches, and applies **only** fixes you explicitly approve — each fix is a minimal unified
diff and every batch is verified (fast checks) and auto-reverted if verification fails.

## The zero-logic-change guarantee

Every proposed fix carries a `confidence` value that the fix is purely stylistic. Fixes are
only ever proposed when confidence is 100. Lower-confidence observations are reported as
**manual review** items (no diff, never applied by the tool). Batches are verified after
application with type-checks/compile/tests when available and cheap; any failure reverts the
whole batch.

## Install (dev)

```bash
python -m venv .venv
.venv/Scripts/pip install -e .[dev]      # Windows
# .venv/bin/pip install -e .[dev]        # POSIX
```

## Usage

```bash
cg scan                       # detect languages, tooling, configs; write .cg.toml if missing
cg audit                      # full A–G report with per-finding IDs and diffs
cg audit --json               # machine-readable audit
cg show N-001                 # full file context around a finding
cg apply --batch formatting   # apply an approved batch (git safety branch + verify + revert on fail)
cg apply --ids N-001,S-003    # apply specific findings only
cg apply --dry-run            # materialize diffs without touching the working tree
cg verify                     # run fast checks only
cg log                        # running applied/remaining log (.cg/log.json)
cg report -o report.md        # markdown report
cg report --json -o report.json
```

## Batches

Findings are grouped into batches: `structure`, `naming`, `imports`, `formatting`,
`docs`, `tooling`, `misc`, plus `high-impact` and `safe` (all safe items).

## Language adapters (tree-sitter, optional)

Beyond the built-in Python passes, optional tree-sitter adapters extend the
naming, import, and formatting categories to JavaScript/TypeScript, Go, and Rust:

```bash
pip install -e .[adapters]     # adds tree-sitter + the four grammars
```

Adapter guarantees:

- Files that fail to parse produce a review-only finding and suppress every
  automatic fix for that file.
- JS/TS import order and long lines are report-only (JS import order has
  module side-effect semantics); quote-style, tabs, and final newline are fixed.
- Go import regrouping follows goimports-style grouping (stdlib -> external);
  exported (PascalCase) Go names are never renamed — that is an API change.
- Rust `use` sorting is rustfmt-equivalent; `#[allow(non_snake_case)]` is
  honored; `pub` items are report-only.
- React-component PascalCase names are never flagged (renaming `<Feed />` to
  lowercase would change JSX semantics — a logic change).
- Every rename is a coordinated cross-file fix group: callers and imports are
  renamed in the same batch, or nothing is applied.

## Commands the master prompt requires

- Plan → Approve → Build flow: `audit` never writes; only `apply` writes, and only what you
  named, on a fresh git branch (`cg/convention-<ts>`, or `--branch <name>`).
- Safety net: refuses on dirty worktree (use `--allow-dirty` to override), reverts failed
  batches automatically, and returns non-zero exit codes for CI use.
- Formatter integration: if a configured formatter is detected — Ruff or Black
  (`[tool.*]` in pyproject.toml / ruff.toml), Prettier (`.prettierrc*`), gofmt,
  or rustfmt (`rustfmt.toml`) — `cg audit` proposes running the project's own
  formatter over each file it handles, in diff mode (stdin -> stdout, never
  writing). Each changed file becomes one delegated finding; built-in style
  fixes the tool subsumes (tabs, quotes, final newline, indentation) are
  suppressed, while import ordering stays built-in. On by default; pass
  `--no-formatter` for built-in fixes only. If the tool is missing or errors,
  delegation fails open to built-in fixes. Binary resolution: PATH, then
  `.venv/Scripts`, then `node_modules/.bin`.
- Ignores: `.gitignore`, `.cgignore`, `node_modules`, `vendor`, `dist`, `build`, `__pycache__`,
  `.venv` and similar are skipped by default.

## cg init-styleguide

Generates a starter convention toolkit **derived from the current audit**, so the
documented rules match observed reality instead of generic defaults:

- `.editorconfig` — editor-level whitespace rules per detected language (LF, final
  newline, Python 4-space / JS 2-space / Go tabs), with drift counts from the audit.
- `.pre-commit-config.yaml` — hygiene hooks (trailing whitespace, EOF newline, mixed
  line endings) plus the project's detected formatter hook, with the version pinned
  when the tool is on PATH (Ruff, Black, Prettier, gofmt, rustfmt).
- `.cg/ci-lint.yml` — a GitHub Actions lint job matching the stack (ruff check /
  `ruff format --check`, mypy, eslint, prettier --check, gofmt, clippy, tests) and
  ending with `cg audit` + `cg verify`; copy it into `.github/workflows/` to arm it.
- `STYLEGUIDE.md` — a short human-readable guide with a per-category audit snapshot
  table and explicit drift counts ("6 files still CRLF", "3 files with mixed quotes").

Existing files are never overwritten (re-run with `--force` to replace them);
written files use LF endings and end with a newline.

`cg init-styleguide --check` regenerates the artifacts in memory and compares
them against the **git-tracked** copies: committing (or staging) an artifact
arms it for checking, while missing or untracked ones are reported as "not
armed" and never fail the run. Any other difference between the committed
file and the current audit marks the file as drifted, prints a unified diff,
and exits 1 — suitable as a CI gate. CRLF checkouts (`core.autocrlf`) and the
STYLEGUIDE.md generation date never count as drift.

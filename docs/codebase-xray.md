# Codebase X-Ray — ConventionGuardian

## Architecture Overview

**Pattern**: Modular CLI with plugin-style finders, single-process execution
**Structure**: Feature-organized modules under `conventionguardian/`

```
conventionguardian/
├── __init__.py           # Package exports, version
├── cli.py                # Typer CLI entry point (commands)
├── audit.py              # Audit pipeline orchestration
├── applier.py            # Apply + verify + revert logic
├── scanner.py            # Language/tooling detection + file walk
├── config.py             # .cg.toml config loading
├── models.py             # Finding, ToolProfile, Category, Severity dataclasses
├── safety.py             # Git safety net (dirty check, branch, backup)
├── checks.py             # Fast verification (compileall, pytest, tsc, etc.)
├── diff.py               # Unified diff helpers
├── adopt.py              # Guided onboarding (safe batch + scaffold)
├── styleguide.py         # Artifact generators (.editorconfig, pre-commit, CI)
├── formatters.py         # Formatter delegation (Ruff, Black, Prettier, gofmt, rustfmt)
├── finders/              # A–G finders (imports, formatting, naming, etc.)
│   ├── __init__.py
│   ├── base.py           # BaseFinder abstract class
│   ├── structure.py      # Category A: project layout
│   ├── naming.py         # Category B: naming conventions
│   ├── imports.py        # Category C: import ordering
│   ├── formatting.py     # Category D: formatting (indent, quotes, etc.)
│   ├── docs.py           # Category E: docstring consistency
│   ├── tooling.py        # Category F: config alignment
│   └── misc.py           # Category G: line endings, license headers
├── adapters/             # Tree-sitter adapters (optional)
│   ├── __init__.py
│   ├── base.py           # BaseAdapter abstract class
│   ├── javascript.py     # JS/TS adapter
│   ├── go.py             # Go adapter
│   └── rust.py           # Rust adapter
└── reporters/            # Output formatters
    ├── __init__.py
    ├── console.py        # Rich console output
    └── markdown.py       # Markdown report generation
```

---

## Module Responsibilities

### `cli.py` (~400 lines)
- **Purpose**: Typer CLI command definitions
- **Commands**: scan, audit, show, apply, verify, log, report, init-styleguide, adopt
- **Key**: Rich console integration, progress indicators, error handling
- **Verified**: All commands defined, help text present

### `audit.py` (~300 lines)
- **Purpose**: Orchestrates full audit pipeline
- **Flow**: Load config → Scanner → Instantiate finders → Run finders → Aggregate findings → Sort/group → Report
- **Dependencies**: scanner, finders, config, models
- **Verified**: Pipeline structure, batch grouping logic

### `applier.py` (~350 lines)
- **Purpose**: Apply findings with safety net
- **Flow**: Validate selections → Create safety branch → Backup files → Apply diffs → Run verification → Commit or revert
- **Key**: `safety.py` integration, `checks.py` verification
- **Verified**: Safety branch creation, backup/restore, verification integration

### `scanner.py` (~250 lines)
- **Purpose**: Project discovery and tooling detection
- **Detects**: Languages (by extension), package managers, formatters (Ruff, Black, Prettier, gofmt, rustfmt), linters, test frameworks
- **Output**: `ToolProfile` with detected tools, `.cg.toml` generation
- **Verified**: Detection logic for major ecosystems

### `config.py` (~100 lines)
- **Purpose**: Load/validate `.cg.toml`
- **Schema**: target, include, exclude, style_guide_file
- **Verified**: TOML parsing, defaults, validation

### `models.py` (~200 lines)
- **Purpose**: Core dataclasses
- **Types**: `Finding`, `ToolProfile`, `Category`, `Severity`, `Confidence`, `Batch`, `FileContext`
- **Key**: Confidence enum (100, 75, 50, 25, 0), Finding ID generation
- **Verified**: Type definitions, serialization

### `safety.py` (~200 lines)
- **Purpose**: Git safety net
- **Features**: Dirty worktree check, safety branch creation, file backup, restore on failure
- **Verified**: Git operations via `subprocess`, error handling

### `checks.py` (~150 lines)
- **Purpose**: Fast verification commands per language
- **Checks**: `python -m compileall`, `pytest -q`, `tsc --noEmit`, `go build`, `cargo check`
- **Verified**: Command mapping, timeout handling

### `finders/` (A–G categories)
Each finder implements `BaseFinder`:
- `find(files: List[Path]) -> List[Finding]`
- Categories: A=Structure, B=Naming, C=Imports, D=Formatting, E=Docs, F=Tooling, G=Misc
- **Verified**: Finder interface, category registration

### `adapters/` (Tree-sitter)
- **Base**: `BaseAdapter` with parse, query, edit methods
- **JS/TS**: Import order, quote style, formatting (React component names protected)
- **Go**: Import regrouping (goimports-style), exported names protected
- **Rust**: `use` sorting, `#[allow(non_snake_case)]` honored, `pub` items report-only
- **Verified**: Adapter interface, parse failure handling

### `reporters/`
- **Console**: Rich tables, progress, syntax-highlighted diffs
- **Markdown**: Structured report with finding tables, diffs
- **Verified**: Output formats, finding grouping

### `styleguide.py` (~300 lines)
- **Purpose**: Generate convention artifacts from audit
- **Artifacts**: `.editorconfig`, `.pre-commit-config.yaml`, `.cg/ci-lint.yml`, `STYLEGUIDE.md`
- **Key**: Drift counts from audit, `--check` mode for CI
- **Verified**: Artifact templates, drift detection

### `formatters.py` (~200 lines)
- **Purpose**: Delegate to project's own formatter
- **Supported**: Ruff, Black, Prettier, gofmt, rustfmt
- **Flow**: Detect formatter → Run in diff mode (stdin→stdout) → Create delegated findings
- **Verified**: Binary resolution (PATH, .venv, node_modules), delegation logic

---

## Data Flow

```
cg scan
    │
    ▼
Scanner → ToolProfile → .cg.toml
    │
    ▼
cg audit
    │
    ▼
Config → Scanner (files) → Finders (A–G) → Findings → Group by Batch → Report
    │
    ▼
cg apply --batch <name>
    │
    ▼
Select Findings → Safety Branch → Backup → Apply Diffs → Verify → Commit/Revert
    │
    ▼
cg init-styleguide
    │
    ▼
Audit Findings → Artifact Templates → Write Files (or --check compare)
```

---

## CLI Architecture

| Command | Purpose | Key Modules |
|---------|---------|-------------|
| `scan` | Detect tooling, write `.cg.toml` | `scanner.py`, `config.py` |
| `audit` | Full A–G report | `audit.py`, `finders/*`, `reporters/*` |
| `show <ID>` | File context for finding | `audit.py`, `reporters/console.py` |
| `apply` | Apply batch/IDs with safety | `applier.py`, `safety.py`, `checks.py` |
| `verify` | Run fast checks | `checks.py` |
| `log` | Show `.cg/log.json` | `applier.py` (log reading) |
| `report` | Write markdown/JSON report | `reporters/markdown.py` |
| `init-styleguide` | Generate artifacts | `styleguide.py` |
| `adopt` | Guided onboarding | `adopt.py` |

---

## External Integrations

| Integration | Status | Details |
|-------------|--------|---------|
| Git | ✅ | `subprocess` for branch, diff, status, commit |
| Ruff | ✅ | Formatter delegation, linting via `ruff check` |
| Black | ✅ | Formatter delegation |
| Prettier | ✅ | Formatter delegation (Node.js) |
| gofmt | ✅ | Formatter delegation |
| rustfmt | ✅ | Formatter delegation |
| tree-sitter | ⚠️ Optional | JS/TS, Go, Rust grammars via pip extra |
| LibCST | ⚠️ Optional | Python AST manipulation for fixes |
| pytest | ✅ | Verification step |
| GitHub Actions | ✅ | CI template generation |

---

## Dependency Overview

### Production (3 required)
| Package | Version | Purpose |
|---------|---------|---------|
| typer | >=0.12 | CLI framework |
| rich | >=13.7 | Terminal rendering |
| pathspec | >=0.12 | Gitignore matching |

### Development (2)
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.0 | Testing |
| pyyaml | >=6.0 | Config/artifact YAML |

### Optional Extras
| Extra | Packages | Purpose |
|-------|----------|---------|
| `libcst` | libcst>=1.4 | Python AST fixes |
| `adapters` | tree-sitter, tree-sitter-javascript, tree-sitter-typescript, tree-sitter-go, tree-sitter-rust | Multi-language parsing |

---

## Error Handling

**Patterns**:
- CLI: Typer exceptions → Rich error panels → Exit codes (0, 1, 2)
- Audit: Finder errors caught per-file → Report as review-only findings
- Apply: Per-file try/except → Backup restore on any failure → Full batch revert
- Verification: Subprocess timeout (30s) → Kill → Revert
- Git: `subprocess.CalledProcessError` → User-friendly messages

**Verified**: Error handling in `applier.py`, `safety.py`, `cli.py`

---

## Logging & Monitoring

**Current**: Structured logging via Rich console (info, warning, error panels)
**File Log**: `.cg/log.json` — applied findings, timestamps, verification results
**CI Output**: Machine-readable JSON (`--json` flag on audit/report)

---

## Security Considerations

| Aspect | Status | Notes |
|--------|--------|-------|
| Arbitrary Code Execution | ✅ Mitigated | No `eval`, `exec`; tree-sitter parsing only |
| File System Access | ✅ Scoped | Respects `.gitignore`, `.cgignore`, explicit includes |
| Git Operations | ✅ Safe | `subprocess` with validated args, no shell injection |
| Formatter Delegation | ✅ Safe | Binary resolution via PATH/venv, no shell |
| Temp Files | ✅ Clean | Backups in `.cg/backup/`, cleaned on success |

---

## Performance Considerations

| Aspect | Status | Notes |
|--------|--------|-------|
| File Walk | ✅ Fast | `pathspec` for ignore matching, parallel-ready |
| Finder Execution | ✅ Sequential | Per-category, can be parallelized |
| Tree-sitter Parsing | ⚠️ Optional | Only for enabled adapters |
| Memory | ✅ Low | Streaming file reads, no full AST retention |
| Large Repos | [NOT TESTED] | Monorepo performance unknown |

---

## Technical Debt

| Item | Severity | Location |
|------|----------|----------|
| No parallel finder execution | MEDIUM | `audit.py` |
| Tree-sitter adapter coverage incomplete | MEDIUM | `adapters/` |
| No monorepo/workspace support | LOW | `scanner.py`, `config.py` |
| Configuration migration path | LOW | `config.py` |
| Benchmark suite missing | LOW | Project-wide |
| Windows path handling edge cases | LOW | `scanner.py`, `diff.py` |

---

## Existing Tests

**Configured**: pytest 8.0+ (testpaths = ["tests"])
**Test Files**: `tests/` directory exists
**Coverage**: [NOT MEASURED] — run `pytest --cov=conventionguardian`

---

## Verified vs Inferred vs Assumed

| Category | Items |
|----------|-------|
| **Verified** (read from source) | Module structure, CLI commands, finder categories, adapter interfaces, safety flow, formatter delegation, styleguide artifacts, config schema |
| **Inferred** (reasonable from patterns) | Finder implementation details, specific rule logic, tree-sitter query patterns, verification command mapping |
| **Assumed** (unverified) | Test coverage %, performance benchmarks, PyPI publishing workflow, Windows CI testing |

---

*Generated: 2026-10-30 | Stage 2 of 5*
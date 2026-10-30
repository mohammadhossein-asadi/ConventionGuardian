# Technical Decisions — ConventionGuardian

## Decision Log

### TD-001: Python 3.11+ as Minimum Version
- **Date**: 2026-09-15 (inferred)
- **Status**: Accepted
- **Context**: Need modern typing features (`dataclass slots`, `Self`, `tomllib`)
- **Decision**: Require Python 3.11+
- **Alternatives**: Python 3.10 (no `tomllib`, no `Self`), 3.9 (no `str.removeprefix`)
- **Consequences**:
  - ✅ `tomllib` in stdlib (no external TOML dependency)
  - ✅ `dataclass(slots=True)` for memory efficiency
  - ✅ `Self` type for fluent builders
  - ⚠️ Excludes older Python environments (RHEL 9, Ubuntu 22.04 default is 3.10)

### TD-002: Typer for CLI Framework
- **Date**: 2026-09-15
- **Status**: Accepted
- **Context**: Need type-safe CLI with auto-completion, Rich integration
- **Decision**: Typer over Click, argparse, Fire
- **Alternatives**: Click (more mature, less type-safe), argparse (stdlib, verbose), Fire (magic, hard to test)
- **Consequences**:
  - ✅ Automatic type hints → CLI args
  - ✅ Shell completion generation
  - ✅ Rich integration built-in
  - ✅ Easy testing with `typer.testing.CliRunner`
  - ⚠️ Younger ecosystem than Click

### TD-003: Rich for Terminal Output
- **Date**: 2026-09-15
- **Status**: Accepted
- **Context**: Need beautiful tables, progress bars, syntax highlighting, panels
- **Decision**: Rich over `tabulate`, `tqdm`, `colorama`
- **Consequences**:
  - ✅ All-in-one: tables, progress, syntax, panels, markdown
  - ✅ Console capture for testing
  - ✅ Jupyter compatible
  - ⚠️ Adds ~2MB to install size

### TD-004: pathspec for Ignore Matching
- **Date**: 2026-09-16
- **Status**: Accepted
- **Context**: Need `.gitignore`-compatible pattern matching for file discovery
- **Decision**: pathspec over `fnmatch`, `glob`, custom regex
- **Consequences**:
  - ✅ Exact `.gitignore` semantics (negation, directories, etc.)
  - ✅ Used by Git itself (GitPython uses it)
  - ✅ Fast C implementation available
  - ⚠️ Extra dependency

### TD-005: Finder Architecture (A–G Categories)
- **Date**: 2026-09-17
- **Status**: Accepted
- **Context**: Need modular, extensible convention detection
- **Decision**: Category-based finders with confidence scoring
- **Categories**: A=Structure, B=Naming, C=Imports, D=Formatting, E=Docs, F=Tooling, G=Misc
- **Consequences**:
  - ✅ Clear mental model for users (batches)
  - ✅ Extensible: add finders without core changes
  - ✅ Confidence enables safe auto-fix vs review-only
  - ⚠️ Category boundaries sometimes fuzzy

### TD-006: Git Safety Branch per Apply
- **Date**: 2026-09-18
- **Status**: Accepted
- **Context**: Must guarantee zero-risk application
- **Decision**: Fresh branch per `apply`, full backup, verification, auto-revert
- **Alternatives**: Direct commit (risky), stash (incomplete), worktree (complex)
- **Consequences**:
  - ✅ Atomic: all-or-nothing per batch
  - ✅ Audit trail in git history
  - ✅ Easy manual review (`git diff cg/convention-<ts>`)
  - ⚠️ Requires git repo (fails fast if not)

### TD-007: Formatter Delegation (Project's Tool is Source of Truth)
- **Date**: 2026-09-19
- **Status**: Accepted
- **Context**: Projects already have formatters; don't fight them
- **Decision**: Detect and delegate to Ruff, Black, Prettier, gofmt, rustfmt
- **Consequences**:
  - ✅ Respects project's existing config
  - ✅ Built-in fixes suppressed when formatter handles it
  - ✅ Import ordering stays built-in (formatters don't sort)
  - ⚠️ Binary resolution complexity (PATH, venv, node_modules)

### TD-008: Tree-sitter for Non-Python Languages
- **Date**: 2026-09-20
- **Status**: Accepted
- **Context**: Regex-based parsing is fragile for JS/TS, Go, Rust
- **Decision**: Optional tree-sitter adapters via pip extra
- **Consequences**:
  - ✅ Proper AST parsing, error recovery
  - ✅ Incremental re-parsing for large files
  - ✅ Language grammars maintained by community
  - ⚠️ Optional dependency (platform wheels not always available)
  - ⚠️ Extra install step for users

### TD-009: Cross-File Rename Coordination
- **Date**: 2026-09-21
- **Status**: Accepted
- **Context**: Renaming a symbol requires updating all references
- **Decision**: Coordinated fix groups — all callers + imports in same batch
- **Consequences**:
  - ✅ Prevents broken imports
  - ✅ Atomic: all references updated or none
  - ⚠️ Complex implementation (call graph needed)
  - ⚠️ Tree-sitter required for non-Python

### TD-010: Styleguide Generation from Audit
- **Date**: 2026-09-22
- **Status**: Accepted
- **Context**: Conventions should be documented from reality, not ideals
- **Decision**: Generate `.editorconfig`, `.pre-commit-config.yaml`, CI, `STYLEGUIDE.md` from audit findings
- **Consequences**:
  - ✅ Artifacts match observed codebase
  - ✅ Drift counts show current state
  - ✅ CI gate (`--check`) prevents silent drift
  - ⚠️ Requires git-tracked artifacts to arm

### TD-011: Zero-Logic-Change Guarantee (Confidence 100%)
- **Date**: 2026-09-22
- **Status**: Accepted
- **Context**: Users must trust auto-fixes don't break behavior
- **Decision**: Only propose fixes with 100% confidence; lower = manual review
- **Consequences**:
  - ✅ Trustworthy by default
  - ✅ Clear distinction: fix vs review
  - ⚠️ Fewer auto-fixes (conservative)
  - ⚠️ Requires careful confidence calibration

### TD-012: Verification Before Commit
- **Date**: 2026-09-23
- **Status**: Accepted
- **Context**: Applied fixes must not break the build
- **Decision**: Run fast checks (compile, type-check, unit tests) after apply, revert on failure
- **Consequences**:
  - ✅ Catches regressions immediately
  - ✅ Fast checks only (no full test suite)
  - ⚠️ Adds time to apply (typically 2-10s)
  - ⚠️ False positives if checks are flaky

---

## Pending Decisions (Need Resolution)

| ID | Decision | Options | Blocker |
|----|----------|---------|---------|
| PD-001 | PyPI Publishing Automation | GitHub Actions trusted publishing, manual twine | Release workflow |
| PD-002 | VS Code Extension | Official extension, community, none | Resource allocation |
| PD-003 | Monorepo Support | Workspace detection, per-package config, ignore | Architecture change |
| PD-004 | Configuration Migration | Versioned `.cg.toml`, auto-migrate, manual | Backward compatibility |
| PD-005 | Performance Benchmarks | CI benchmarks, local profiling, none | Baseline needed |
| PD-006 | Windows CI Testing | GitHub Actions windows-latest, cross-compile | CI minutes |
| PD-007 | Plugin System for Finders | Entry points, dynamic import, static only | Extensibility scope |
| PD-008 | Multi-language Batch Coordination | Cross-file renames across languages, per-language only | Tree-sitter complexity |

---

## Rejected Alternatives

| Alternative | Reason for Rejection |
|-------------|---------------------|
| Click for CLI | Less type-safe, no native Rich integration |
| argparse | Verbose, no auto-completion, manual help |
| Regex-based parsing for JS/TS | Fragile, misses edge cases, no rename coordination |
| Black as only formatter | Doesn't sort imports, opinionated config |
| Pre-commit only | No audit, no batch selection, no verification |
| Single global config | Projects have different conventions |
| Mandatory tree-sitter | Platform availability, install friction |
| Auto-apply without approval | Violates zero-logic-change guarantee |

---

*Generated: 2026-10-30 | Stage 3 of 5*
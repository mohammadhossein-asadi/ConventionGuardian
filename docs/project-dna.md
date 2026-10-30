# Project DNA — ConventionGuardian (cg)

## Project Identity

| Field | Value |
|-------|-------|
| **Project Name** | ConventionGuardian (cg) |
| **Repository** | `ConventionGuardian` |
| **Type** | CLI Tool (Python) — Convention Audit & Auto-Fix |
| **Primary Language** | Python 3.11+ |
| **Package Manager** | pip / setuptools (pyproject.toml) |
| **CLI Framework** | Typer |
| **Terminal UI** | Rich |

---

## Purpose & Problem Statement

**Problem**: Codebases accumulate convention drift (formatting, naming, imports, structure) over time. Existing tools either:
- Enforce opinionated defaults (Black, Prettier) without project-specific context
- Require manual configuration and don't verify fixes don't break logic
- Apply changes without safety nets (no verification, no auto-revert)

**Solution**: A convention audit tool that:
1. **Scans** the full project to detect languages, tools, and existing conventions
2. **Reports** findings grouped into selectable batches (A–G categories) with confidence scores
3. **Applies** only explicitly approved batches on a git safety branch
4. **Verifies** each batch with fast checks (compile, type-check, tests) and auto-reverts on failure
5. **Generates** styleguide artifacts (.editorconfig, pre-commit, CI, STYLEGUIDE.md) from observed reality

**Core Philosophy**: Zero-logic-change guarantee. Every fix carries 100% confidence of being purely stylistic. Lower-confidence observations are manual-review only.

---

## Target Users

- **Primary**: Development teams wanting safe, automated convention enforcement
- **Secondary**: Solo developers maintaining multi-language projects
- **Tertiary**: CI/CD pipelines needing convention drift detection

---

## Core Features (Implemented)

| Feature | Status | Description |
|---------|--------|-------------|
| Project Scanner (`cg scan`) | ✅ Implemented | Detects languages, package managers, formatters, linters, test frameworks; writes `.cg.toml` |
| Full Audit (`cg audit`) | ✅ Implemented | A–G category findings with IDs, diffs, confidence, rationale; JSON output support |
| Batch Application (`cg apply`) | ✅ Implemented | Apply by batch name or finding IDs; git safety branch; verification + auto-revert |
| Verification (`cg verify`) | ✅ Implemented | Fast checks: compileall, pytest, tsc, go build, cargo check |
| Styleguide Generation (`cg init-styleguide`) | ✅ Implemented | Generates .editorconfig, .pre-commit-config.yaml, CI config, STYLEGUIDE.md |
| CI Gate (`cg init-styleguide --check`) | ✅ Implemented | Regenerates artifacts in-memory, compares against git-tracked copies |
| Formatter Delegation | ✅ Implemented | Delegates to project's own formatter (Ruff, Black, Prettier, gofmt, rustfmt) |
| Tree-sitter Adapters (Optional) | ✅ Implemented | JS/TS, Go, Rust naming/import/formatting via tree-sitter grammars |
| Safety Net | ✅ Implemented | Dirty worktree check, git branch backup, non-zero exit codes for CI |
| Cross-file Rename Coordination | ✅ Implemented | Coordinated fix groups for callers + imports in same batch |

---

## Technical Requirements

| Requirement | Detail |
|-------------|--------|
| **Runtime** | Python 3.11+ |
| **CLI Framework** | Typer 0.12+ |
| **Terminal Rendering** | Rich 13.7+ |
| **Gitignore Matching** | pathspec 0.12+ |
| **Testing** | pytest 8.0+ |
| **Optional: AST Manipulation** | LibCST 1.4+ (for Python fixes) |
| **Optional: Tree-sitter** | tree-sitter 0.24+ + language grammars |
| **Optional: YAML** | PyYAML 6.0+ (for config/artifacts) |

---

## Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| FR-01 | Scan project and detect tooling conventions | ✅ |
| FR-02 | Audit with A–G category findings + confidence | ✅ |
| FR-03 | Apply fixes by batch with git safety branch | ✅ |
| FR-04 | Verify batch with fast checks + auto-revert | ✅ |
| FR-05 | Generate styleguide artifacts from audit | ✅ |
| FR-06 | CI gate for artifact drift detection | ✅ |
| FR-07 | Delegate to project's own formatter | ✅ |
| FR-08 | Tree-sitter adapters for JS/TS, Go, Rust | ✅ |
| FR-09 | Cross-file coordinated renames | ✅ |
| FR-10 | Machine-readable JSON output | ✅ |
| FR-11 | Configuration via `.cg.toml` | ✅ |
| FR-12 | Ignore patterns (.gitignore, .cgignore) | ✅ |

---

## Non-Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| NFR-01 | Zero logic changes (confidence 100% for fixes) | ✅ Designed |
| NFR-02 | Safety: never write without explicit approval | ✅ |
| NFR-03 | Verification before commit | ✅ |
| NFR-04 | Auto-revert on verification failure | ✅ |
| NFR-05 | Fast scans (< 5s for typical projects) | [NOT VERIFIED] |
| NFR-06 | Cross-platform (Windows, Linux, macOS) | ✅ Designed |
| NFR-07 | Extensible finder architecture | ✅ |
| NFR-08 | Comprehensive test coverage | [PARTIAL] |

---

## Business/Technical Objectives

- [ ] Publish to PyPI as `convention-guardian`
- [ ] Achieve 80%+ test coverage
- [ ] Add GitHub Action marketplace entry
- [ ] Support more language adapters (Java, C#, etc.)
- [ ] Add VS Code extension for inline findings
- [ ] Benchmark performance on large monorepos

---

## Known Limitations

1. **Python-only core fixes** — Built-in finders focus on Python; other languages need tree-sitter adapters
2. **No semantic analysis** — Cannot detect logic changes, only syntactic patterns
3. **Tree-sitter optional** — Adapters require extra install; not available on all platforms
4. **Single-project scope** — No multi-repo/monorepo coordination yet
5. **Configuration learning** — `.cg.toml` target conventions require manual selection
6. **Generated code handling** — Heuristic-based, may need manual exclude patterns

---

## Confirmed Decisions

| Decision | Rationale |
|----------|-----------|
| Typer for CLI | Modern, type-safe, auto-completion, Rich integration |
| Rich for terminal output | Beautiful tables, progress, syntax highlighting |
| pathspec for ignores | Git-compatible pattern matching |
| Finder architecture (A–G) | Modular, extensible, category-based reporting |
| Git safety branch per apply | Atomic, reversible, audit trail |
| Formatter delegation | Respects project's existing tool choices |
| Tree-sitter for non-Python | Proper parsing vs regex heuristics |
| Cross-file rename groups | Prevents broken imports after renames |
| PyPI package name: convention-guardian | Descriptive, available |

---

## Unknown Information / Needs Confirmation

| Question | Priority |
|----------|----------|
| Will PyPI publishing be automated (CI)? | HIGH |
| Are there plans for a VS Code extension? | MEDIUM |
| Should there be a hosted SaaS version? | LOW |
| What is the target test coverage %? | MEDIUM |
| Are there enterprise features planned (RBAC, policies)? | LOW |
| Will there be a configuration migration path for `.cg.toml`? | LOW |

---

*Generated: 2026-10-30 | Stage 1 of 5 | [NEEDS CONFIRMATION] on unknowns*
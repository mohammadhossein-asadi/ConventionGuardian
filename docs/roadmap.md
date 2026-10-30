# Roadmap — ConventionGuardian

## Vision

Make convention enforcement safe, deterministic, and zero-logic-change for every codebase — from solo projects to enterprise monorepos.

---

## Phase 0: Foundation (Current) — v0.1.x

**Status**: ✅ Core CLI complete, all commands functional
**Timeline**: 2026-Q3

| Milestone | Status |
|-----------|--------|
| Core CLI (scan, audit, apply, verify) | ✅ Done |
| Finder architecture (A–G) | ✅ Done |
| Git safety net (branch, backup, revert) | ✅ Done |
| Verification pipeline (compile, test, lint) | ✅ Done |
| Styleguide generation (.editorconfig, pre-commit, CI, STYLEGUIDE.md) | ✅ Done |
| Formatter delegation (Ruff, Black, Prettier, gofmt, rustfmt) | ✅ Done |
| Tree-sitter adapters (JS/TS, Go, Rust) | ✅ Done |
| Cross-file rename coordination | ✅ Done |
| CI gate (`--check`) | ✅ Done |
| Comprehensive README | ✅ Done |

**Exit Criteria**: All commands work end-to-end on real projects

---

## Phase 1: Polish & Harden — v0.2.x

**Timeline**: 2026-Q4

### 1.1 Test Coverage & Quality
- [ ] **TASK-001**: Achieve 80% unit test coverage (pytest-cov)
- [ ] **TASK-002**: Add integration tests with real project fixtures
- [ ] **TASK-003**: Add CLI contract tests (exit codes, output formats)
- [ ] **TASK-004**: Property-based testing for finders (hypothesis)
- [ ] **TASK-005**: Benchmark suite (scan/audit/apply on 1k, 10k, 100k files)

### 1.2 Windows & Cross-Platform
- [ ] **TASK-006**: GitHub Actions Windows CI (windows-latest)
- [ ] **TASK-007**: Fix path separator issues in diffs/backups
- [ ] **TASK-008**: Test tree-sitter wheels on Windows
- [ ] **TASK-009**: Validate formatter binary resolution on Windows

### 1.3 Configuration & UX
- [ ] **TASK-010**: `.cg.toml` schema validation with helpful errors
- [ ] **TASK-011**: `cg scan --interactive` for guided target selection
- [ ] **TASK-012**: Configuration migration path for future versions
- [ ] **TASK-013**: Shell completion (bash, zsh, fish, PowerShell)

### 1.4 Documentation
- [ ] **TASK-014**: API documentation (pdoc/mkdocstrings)
- [ ] **TASK-015**: Contributor guide (architecture, adding finders/adapters)
- [ ] **TASK-016**: Video demo / GIFs for README

---

## Phase 2: Ecosystem & Distribution — v0.3.x

**Timeline**: 2027-Q1

### 2.1 PyPI Release
- [ ] **TASK-017**: Trusted publishing via GitHub Actions (no API tokens)
- [ ] **TASK-018**: Version bump strategy (semver, changelog automation)
- [ ] **TASK-019**: PyPI package metadata (classifiers, description, README)
- [ ] **TASK-020**: Install verification script

### 2.2 GitHub Integration
- [ ] **TASK-021**: GitHub Action marketplace entry (`convention-guardian/action`)
- [ ] **TASK-022**: `cg init-styleguide --github` creates workflow file directly
- [ ] **TASK-023**: Dependabot/renovate config for generated CI
- [ ] **TASK-024**: Status check integration (required status on PRs)

### 2.3 IDE Support
- [ ] **TASK-025**: VS Code extension (inline findings, quick fixes)
- [ ] **TASK-026**: Language Server Protocol (LSP) integration
- [ ] **TASK-027**: Neovim plugin (via null-ls or native)

---

## Phase 3: Scale & Enterprise — v0.4.x

**Timeline**: 2027-Q2

### 3.1 Monorepo Support
- [ ] **TASK-028**: Workspace detection (npm workspaces, pnpm, cargo, go work)
- [ ] **TASK-029**: Per-package `.cg.toml` with inheritance
- [ ] **TASK-030**: Cross-package rename coordination
- [ ] **TASK-031**: Aggregate audit across workspace

### 3.2 Advanced Features
- [ ] **TASK-032**: Custom finder plugin system (entry points)
- [ ] **TASK-033**: Rule packs (company presets, security, accessibility)
- [ ] **TASK-034**: SARIF output for GitHub Code Scanning
- [ ] **TASK-035**: Baseline/allowlist for existing violations
- [ ] **TASK-036**: Incremental audit (only changed files)

### 3.3 Language Expansion
- [ ] **TASK-037**: Java adapter (tree-sitter-java)
- [ ] **TASK-038**: C# adapter (tree-sitter-c-sharp)
- [ ] **TASK-039**: Python LibCST-based fixes (beyond formatting)
- [ ] **TASK-040**: SQL adapter (tree-sitter-sql)

---

## Phase 4: Intelligence — v1.0.x

**Timeline**: 2027-Q3+

### 4.1 ML-Assisted Conventions
- [ ] **TASK-041**: Learn conventions from codebase (unsupervised)
- [ ] **TASK-042**: Suggest target convention set from audit
- [ ] **TASK-043**: Anomaly detection for outliers

### 4.2 Platform Features
- [ ] **TASK-044**: Hosted dashboard (audit history, trends, team insights)
- [ ] **TASK-045**: Organization policies (enforce across repos)
- [ ] **TASK-046**: API for CI/CD integration
- [ ] **TASK-047**: Webhook notifications (Slack, Teams, email)

---

## Release Cadence

| Version | Type | Target Date | Focus |
|---------|------|-------------|-------|
| 0.1.x | Alpha | 2026-Q3 | Core functionality |
| 0.2.x | Beta | 2026-Q4 | Polish, tests, Windows |
| 0.3.x | RC | 2027-Q1 | PyPI, GitHub, IDE |
| 0.4.x | Stable | 2027-Q2 | Monorepo, plugins, languages |
| 1.0.x | GA | 2027-Q3 | Intelligence, platform |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| PyPI downloads/month | 10,000+ | PyPI stats |
| GitHub stars | 1,000+ | GitHub |
| VS Code extension installs | 5,000+ | Marketplace |
| Projects using in CI | 100+ | GitHub search |
| Test coverage | 80%+ | Codecov |
| Median audit time (10k files) | < 5s | Benchmark suite |
| Windows CI pass rate | 100% | GitHub Actions |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tree-sitter wheel availability | MEDIUM | HIGH | Fallback to built-in finders; document install |
| Windows path edge cases | HIGH | MEDIUM | Dedicated Windows CI, pathlib everywhere |
| Scope creep (feature requests) | HIGH | MEDIUM | Strict phase gates, community RFC process |
| Performance on huge monorepos | MEDIUM | HIGH | Incremental audit, parallel finders, profiling |
| PyPI name squatting | LOW | HIGH | Reserve name early, trademark if needed |
| Maintainer burnout | MEDIUM | HIGH | Document contributor guide, seek co-maintainers |

---

*Generated: 2026-10-30 | Stage 4 of 5*
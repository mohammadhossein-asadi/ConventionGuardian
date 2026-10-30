# Architecture — ConventionGuardian

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Entry (Typer)                        │
│  scan | audit | show | apply | verify | log | report | styleguide │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Audit Pipeline                              │
│  Config → Scanner → Finders (A–G) → Aggregator → Reporter       │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
       │  Findings   │ │  Batches    │ │  Artifacts  │
       │  (A–G cat)  │ │  (safe,     │ │  (.editor-  │
       │  +confidence│ │   formatting,│ │  config,    │
       │  +diffs)    │ │   imports..)│ │  pre-commit,│
       └─────────────┘ └─────────────┘ │  CI, STYLE) │
                                      └─────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
       │  Applier    │ │  Safety     │ │  Checks     │
       │  (git branch│ │  (dirty     │ │  (compile,  │
       │  + backup)  │ │   check,    │ │   test,     │
       │             │ │   branch)   │ │   lint)     │
       └─────────────┘ └─────────────┘ └─────────────┘
```

---

## Component Relationships

### CLI Layer (`cli.py`)
```
cli.py (Typer App)
├── scan_cmd()        → scanner.scan()
├── audit_cmd()       → audit.run_audit()
├── show_cmd()        → audit.show_finding()
├── apply_cmd()       → applier.apply_batch()
├── verify_cmd()      → checks.run_checks()
├── log_cmd()         → applier.read_log()
├── report_cmd()      → reporters.write_report()
├── styleguide_cmd()  → styleguide.generate()
└── adopt_cmd()       → adopt.run_onboarding()
```

### Audit Pipeline (`audit.py`)
```
run_audit(config)
    ├── scanner.discover_files()          → List[Path]
    ├── instantiate_finders(config)       → List[BaseFinder]
    ├── for finder in finders:            → List[Finding]
    │     finder.find(files)
    ├── aggregate_findings()              → Dict[Batch, List[Finding]]
    └── reporter.render(findings)         → Console/Markdown/JSON
```

### Finder Architecture (`finders/`)
```
BaseFinder (ABC)
    ├── find(files) → List[Finding]
    ├── category: Category (A–G)
    └── confidence_threshold: Confidence

StructureFinder (A)     → Project layout, root pollution
NamingFinder (B)        → Variables, functions, classes, types
ImportsFinder (C)       → Import ordering, grouping, duplicates
FormattingFinder (D)    → Indent, line length, quotes, trailing comma
DocsFinder (E)          → Docstring/JSDoc/godoc format
ToolingFinder (F)       → .editorconfig, linter/formatter/CI config
MiscFinder (G)          → Line endings, license headers, test naming
```

### Adapter Architecture (`adapters/`)
```
BaseAdapter (ABC)
    ├── parse(file) → Tree
    ├── query(tree, pattern) → List[Match]
    └── edit(tree, match, fix) → Tree

JavaScriptAdapter    → tree-sitter-javascript + typescript
GoAdapter            → tree-sitter-go
RustAdapter          → tree-sitter-rust
```

### Safety & Verification (`safety.py`, `checks.py`, `applier.py`)
```
apply_batch(findings, batch_name)
    ├── safety.check_clean_worktree()
    ├── safety.create_branch("cg/convention-<ts>")
    ├── safety.backup_files(findings)
    ├── for finding in findings:
    │     diff.apply(finding.diff)
    ├── checks.run_verification(languages)
    │     ├── python: compileall + pytest
    │     ├── js/ts: tsc --noEmit
    │     ├── go: go build
    │     └── rust: cargo check
    ├── if verification_passed:
    │     git commit + return success
    │ else:
    │     safety.restore_backups()
    │     git checkout -f
    │     return failure
```

---

## Technology Choices

| Layer | Choice | Version | Rationale |
|-------|--------|---------|-----------|
| Language | Python | 3.11+ | Wide adoption, rich ecosystem, typing support |
| CLI Framework | Typer | 0.12+ | Type-safe, auto-completion, Rich integration |
| Terminal UI | Rich | 13.7+ | Tables, progress, syntax highlighting, panels |
| Ignore Matching | pathspec | 0.12+ | Git-compatible `.gitignore` semantics |
| Config | TOML | stdlib (`tomllib`) | Human-readable, structured |
| Testing | pytest | 8.0+ | Fixtures, parametrize, fast |
| Optional: AST | LibCST | 1.4+ | Safe Python AST manipulation |
| Optional: Parsing | tree-sitter | 0.24+ | Incremental, error-tolerant parsing |
| Optional: YAML | PyYAML | 6.0+ | Config/artifact serialization |

---

## Existing Coding Conventions

### File Naming
- Modules: `snake_case.py` (`cli.py`, `audit.py`, `scanner.py`)
- Finders: `<category>.py` (`structure.py`, `naming.py`)
- Adapters: `<language>.py` (`javascript.py`, `go.py`)
- Tests: `test_<module>.py`

### Class/Function Naming
- Classes: PascalCase (`BaseFinder`, `Finding`, `ToolProfile`)
- Functions: snake_case (`run_audit`, `apply_batch`, `discover_files`)
- Constants: UPPER_SNAKE_CASE (`DEFAULT_TARGET`, `MAX_FILE_SIZE`)

### Type Hints
- Full type annotations on all public APIs
- `dataclasses` for data models (`@dataclass`, `slots=True`)
- `Protocol` for interfaces (`BaseFinder`, `BaseAdapter`)
- Generics for type-safe collections

### Error Handling
```python
# Custom exceptions
class CGError(Exception): pass
class SafetyError(CGError): pass
class VerificationError(CGError): pass

# Result pattern for fallible operations
@dataclass
class Result:
    success: bool
    value: T | None = None
    error: str | None = None
```

### CLI Patterns
```python
@app.command()
def audit(
    json: bool = typer.Option(False, "--json", help="Machine-readable output"),
    batch: str | None = typer.Option(None, "--batch", help="Filter by batch"),
):
    # Implementation with Rich console
    console = Console()
    # ...
```

---

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `cli.py`, `styleguide.py` |
| Classes | PascalCase | `BaseFinder`, `JavaScriptAdapter` |
| Functions | snake_case | `run_audit`, `generate_artifacts` |
| Methods | snake_case | `find`, `parse`, `apply_batch` |
| Constants | UPPER_SNAKE_CASE | `CATEGORY_A_STRUCTURE` |
| Dataclasses | PascalCase | `Finding`, `ToolProfile` |
| Enums | PascalCase | `Category`, `Severity`, `Confidence` |
| CLI Commands | kebab-case | `init-styleguide`, `cg scan` |
| Config Keys | snake_case | `target`, `style_guide_file` |

---

## Module Boundaries

| Module | Public API | Internal |
|--------|------------|----------|
| `cli.py` | `app` (Typer) | Command implementations |
| `audit.py` | `run_audit()`, `show_finding()` | Finder orchestration |
| `applier.py` | `apply_batch()`, `apply_ids()` | Git operations, verification |
| `scanner.py` | `discover_files()`, `detect_tooling()` | File walk, ignore logic |
| `config.py` | `load_config()`, `Config` dataclass | TOML parsing |
| `models.py` | All dataclasses/enums | — |
| `safety.py` | `check_clean()`, `create_branch()`, `backup()`, `restore()` | Git subprocess |
| `checks.py` | `run_verification()` | Subprocess commands |
| `finders/*` | `BaseFinder`, category finders | Rule implementations |
| `adapters/*` | `BaseAdapter`, language adapters | Tree-sitter queries |
| `reporters/*` | `render_console()`, `render_markdown()`, `render_json()` | Format logic |
| `styleguide.py` | `generate_artifacts()`, `check_drift()` | Templates |
| `formatters.py` | `delegate_to_formatter()` | Binary resolution |
| `adopt.py` | `run_onboarding()` | Interactive prompts |

---

## Error Handling Standards

### CLI Level
```python
try:
    result = run_audit(config)
except CGError as e:
    console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(code=1)
except SafetyError as e:
    console.print(f"[red]Safety:[/red] {e}")
    raise typer.Exit(code=2)
```

### Finder Level
```python
def find(self, files: List[Path]) -> List[Finding]:
    findings = []
    for file in files:
        try:
            findings.extend(self._find_in_file(file))
        except Exception as e:
            # Report as review-only, never crash
            findings.append(Finding(
                id=f"F-{self.category}-{file.name}-ERR",
                category=self.category,
                severity=Severity.REVIEW,
                confidence=Confidence.ZERO,
                message=f"Parse error: {e}",
                file=file,
            ))
    return findings
```

### Applier Level
```python
# Atomic batch: all or nothing
with safety.transaction():
    safety.backup(files)
    for finding in batch:
        apply_diff(finding.diff)
    if not checks.verify():
        raise VerificationError("Verification failed")
# Success: commit happens in transaction context
```

---

## Logging Standards

**Console**: Rich `Console` with structured panels
```python
console = Console()
console.print(Panel("Audit Complete", style="green"))
console.print(Table(...))
console.print(Syntax(diff, "diff"))
```

**File Log**: `.cg/log.json`
```json
{
  "timestamp": "2026-10-30T14:30:00Z",
  "command": "apply",
  "batch": "formatting",
  "findings_applied": 42,
  "verification": "passed",
  "duration_ms": 1250
}
```

**JSON Output**: `--json` flag for CI integration

---

## Security Standards

| Rule | Implementation |
|------|----------------|
| No shell injection | `subprocess.run(args_list, shell=False)` |
| Path traversal protection | `Path.resolve()`, validate within project root |
| Git argument validation | Allowlist git subcommands, sanitize branch names |
| Formatter binary resolution | PATH → `.venv/Scripts` → `node_modules/.bin` (no shell) |
| Temp file cleanup | `tempfile` module, explicit cleanup in `finally` |
| Generated code exclusion | Heuristic detection + `.cgignore` |

---

## Testing Strategy

| Layer | Tool | Coverage Target | Status |
|-------|------|-----------------|--------|
| Unit | pytest | 80% | [NOT MEASURED] |
| Integration | pytest + temp repos | 60% | [NOT MEASURED] |
| CLI | pytest + Typer testing | 70% | [NOT MEASURED] |
| Adapters | pytest + tree-sitter | 50% | [NOT MEASURED] |

**Priority Tests Needed**:
1. `test_scanner.py` — file discovery, ignore patterns, tool detection
2. `test_finders.py` — each category A–G with fixture files
3. `test_applier.py` — safety branch, backup, verify, revert
4. `test_adapters.py` — parse, query, edit for each language
5. `test_styleguide.py` — artifact generation, drift detection
6. `test_cli.py` — command parsing, exit codes, output formats

---

## Performance Expectations

| Metric | Target | Current |
|--------|--------|---------|
| Scan (10k files) | < 3s | [NOT MEASURED] |
| Audit (10k files) | < 10s | [NOT MEASURED] |
| Apply (100 findings) | < 5s | [NOT MEASURED] |
| Memory (peak) | < 200MB | [NOT MEASURED] |
| Startup (cold) | < 500ms | [NOT MEASURED] |

---

## CLI Conventions

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Verification failed / drift detected / user error |
| 2 | Safety error (not git repo, dirty tree, branch failed) |

### Output Modes
- **Default**: Rich console (tables, panels, syntax highlighting)
- **`--json`**: Machine-readable JSON (audit, report, show)
- **`--quiet`**: Minimal output (errors only)

### Common Options
```bash
--config PATH       # Custom .cg.toml
--include GLOB      # Extra files to include
--exclude GLOB      # Extra files to exclude
--target TARGET     # Convention target (internal|pep8|airbnb|...)
--no-formatter      # Disable formatter delegation
--allow-dirty       # Override safety check (CI only)
--branch NAME       # Custom safety branch name
```

---

## Configuration Conventions

### `.cg.toml`
```toml
target = "internal"              # internal | pep8 | airbnb | gofmt | rustfmt | custom
include = []                     # Extra globs to audit
exclude = []                     # Extra globs to skip
style_guide_file = "STYLE.md"    # Custom target style guide
```

### Target Convention Sets
| Target | Description |
|--------|-------------|
| `internal` | Enforce internal consistency only (default) |
| `pep8` | PEP 8 + Black + isort/Ruff (Python) |
| `airbnb` | Google/Airbnb + Prettier + ESLint (JS/TS) |
| `gofmt` | Standard Go (gofmt + golangci-lint) |
| `rustfmt` | Rustfmt + Clippy (style lints only) |
| `custom` | Company/team style guide |

---

## Deployment Architecture

| Environment | Method |
|-------------|--------|
| Development | `pip install -e .[dev]` |
| Testing | `pytest` (with optional `adapters` extra) |
| PyPI Release | `python -m build` → `twine upload dist/*` |
| GitHub Action | Generated via `cg init-styleguide` → `.cg/ci-lint.yml` |
| Docker | Not yet defined |

**Environment Variables**:
```env
# Optional
CG_CONFIG_PATH=          # Custom config path
CG_NO_FORMATTER=1        # Disable formatter delegation
CG_VERBOSE=1             # Verbose logging
```

---

*Generated: 2026-10-30 | Stage 3 of 5*
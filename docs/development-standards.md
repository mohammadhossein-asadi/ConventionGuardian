# Development Standards — ConventionGuardian

## Code Style

### Python Version
- **Target**: Python 3.11+
- **Features Used**: `tomllib`, `dataclass(slots=True)`, `Self`, `str.removeprefix()`, `exception.add_note()`

### Formatting
- **Formatter**: Ruff (line-length=100, target-version=py311)
- **Import Order**: Ruff I001 (stdlib → third-party → local)
- **Quotes**: Double quotes (Ruff default)
- **Line Endings**: LF (enforced via `.editorconfig`)

### Type Hints
- **Coverage**: 100% on public APIs
- **Style**: PEP 484 + PEP 585 (built-in generics) + PEP 604 (union `|`)
- **Dataclasses**: `@dataclass(slots=True, frozen=True)` for immutable models
- **Protocols**: For interfaces (`BaseFinder`, `BaseAdapter`, `Reporter`)

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `cli.py`, `styleguide.py` |
| Packages | snake_case | `finders`, `adapters` |
| Classes | PascalCase | `BaseFinder`, `JavaScriptAdapter` |
| Functions/Methods | snake_case | `run_audit`, `apply_batch` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_TARGET`, `CATEGORY_A` |
| Dataclasses | PascalCase | `Finding`, `ToolProfile` |
| Enums | PascalCase | `Category`, `Severity`, `Confidence` |
| Type Variables | PascalCase + `_T` | `Finding_T`, `Config_T` |
| Private | `_leading_underscore` | `_parse_file`, `_internal_cache` |

### Docstrings
- **Style**: Google/NumPy hybrid (compatible with `pdoc`, `mkdocstrings`)
- **Required**: All public classes, functions, methods
- **Format**:
```python
def run_audit(config: Config) -> AuditResult:
    """Run the full audit pipeline.

    Args:
        config: Loaded configuration from .cg.toml

    Returns:
        AuditResult with findings grouped by batch.

    Raises:
        CGError: If scanner or finders fail critically.
    """
```

### Imports
```python
# 1. Standard library
import subprocess
from pathlib import Path
from dataclasses import dataclass

# 2. Third-party
import typer
from rich.console import Console

# 3. Local (relative for same package)
from .models import Finding, Category
from .finders.base import BaseFinder
```

---

## Architecture Patterns

### Finder Interface
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

class BaseFinder(ABC):
    category: Category
    confidence_threshold: Confidence = Confidence.HIGH

    @abstractmethod
    def find(self, files: List[Path]) -> List[Finding]:
        """Find convention violations in the given files."""
        ...

    def _create_finding(self, **kwargs) -> Finding:
        """Helper to create Finding with common fields."""
        return Finding(
            category=self.category,
            confidence=self.confidence_threshold,
            **kwargs,
        )
```

### Adapter Interface
```python
class BaseAdapter(ABC):
    language: str
    extensions: List[str]

    @abstractmethod
    def parse(self, content: str) -> Tree:
        """Parse source code into tree-sitter Tree."""
        ...

    @abstractmethod
    def query(self, tree: Tree, pattern: str) -> List[Match]:
        """Run tree-sitter query pattern."""
        ...

    def edit(self, tree: Tree, match: Match, fix: str) -> Tree:
        """Apply edit to tree (default: not implemented)."""
        raise NotImplementedError
```

### Result Pattern for Fallible Operations
```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    success: bool
    value: Optional[T] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        return cls(success=True, value=value)

    @classmethod
    def err(cls, error: str) -> "Result[T]":
        return cls(success=False, error=error)
```

### CLI Command Pattern
```python
@app.command()
def audit(
    json: bool = typer.Option(False, "--json", help="Machine-readable output"),
    batch: Optional[str] = typer.Option(None, "--batch", help="Filter by batch name"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Custom config"),
) -> None:
    """Run full convention audit."""
    console = Console()
    try:
        config = load_config(config_path)
        result = run_audit(config, batch_filter=batch)
        if json:
            console.print_json(data=result.to_json())
        else:
            render_console(result, console)
    except CGError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
```

---

## Error Handling

### Exception Hierarchy
```python
class CGError(Exception):
    """Base exception for ConventionGuardian."""
    pass

class SafetyError(CGError):
    """Git safety net violations (dirty tree, not a repo, branch failure)."""
    pass

class VerificationError(CGError):
    """Verification checks failed after apply."""
    pass

class ConfigError(CGError):
    """Configuration loading/validation errors."""
    pass

class AdapterError(CGError):
    """Tree-sitter adapter errors (parse failure, missing grammar)."""
    pass
```

### Handling Rules
1. **Never use bare `except:`** — Always specify exception type
2. **Finder errors** → Catch per-file, emit review-only Finding, continue
3. **Applier errors** → Full batch revert, restore backups, raise VerificationError
4. **CLI errors** → Rich error panel, appropriate exit code (1 or 2)
5. **Subprocess** → `shell=False`, validate args, timeout (30s default)

---

## Logging Standards

### Console Output (Rich)
```python
console = Console()

# Info panel
console.print(Panel("Scan Complete", style="green"))

# Structured table
table = Table("Category", "Findings", "Confidence")
table.add_row("A Structure", "5", "100%")
console.print(table)

# Syntax highlighted diff
console.print(Syntax(diff_text, "diff", theme="monokai"))

# Progress
with console.status("Scanning..."):
    files = scanner.discover_files()
```

### File Log (`.cg/log.json`)
```json
{
  "timestamp": "2026-10-30T14:30:00Z",
  "command": "apply",
  "batch": "formatting",
  "findings_applied": 42,
  "verification": "passed",
  "duration_ms": 1250,
  "branch": "cg/convention-20261030-143000"
}
```

---

## Testing Standards

### Test Organization
```
tests/
├── unit/
│   ├── test_scanner.py
│   ├── test_finders/
│   │   ├── test_structure.py
│   │   ├── test_naming.py
│   │   └── ...
│   ├── test_applier.py
│   ├── test_adapters/
│   │   ├── test_javascript.py
│   │   ├── test_go.py
│   │   └── test_rust.py
│   ├── test_styleguide.py
│   └── test_formatters.py
├── integration/
│   ├── test_audit_pipeline.py
│   ├── test_apply_flow.py
│   └── test_styleguide_generation.py
├── cli/
│   └── test_commands.py
├── fixtures/
│   ├── python_project/
│   ├── js_project/
│   └── go_project/
└── conftest.py
```

### Test Patterns
```python
# Unit test with fixtures
def test_structure_finder_detects_root_pollution(tmp_path):
    # Arrange
    (tmp_path / "random_file.txt").write_text("content")
    (tmp_path / "src").mkdir()
    finder = StructureFinder()

    # Act
    findings = finder.find([tmp_path])

    # Assert
    assert any(f.category == Category.A for f in findings)
    assert any("root pollution" in f.message.lower() for f in findings)

# CLI test with CliRunner
def test_audit_command_json_output(tmp_path, runner):
    result = runner.invoke(app, ["audit", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "findings" in data

# Parametrized test for multiple languages
@pytest.mark.parametrize("language,ext", [
    ("python", ".py"),
    ("javascript", ".js"),
    ("typescript", ".ts"),
])
def test_scanner_detects_language(tmp_path, language, ext):
    (tmp_path / f"file{ext}").write_text("code")
    profile = scanner.detect_tooling(tmp_path)
    assert language in profile.languages
```

### Fixtures
- **Minimal**: Smallest possible test case
- **Realistic**: Real project structures (fixtures/python_project/)
- **Edge Cases**: Empty files, symlinks, unicode, huge files

---

## Security Standards

| Rule | Implementation |
|------|----------------|
| No `eval`/`exec` | Prohibited; use `ast.literal_eval` if needed |
| Subprocess safety | `shell=False`, args as list, validate paths |
| Path traversal | `Path.resolve()`, check `is_relative_to(project_root)` |
| Temp files | `tempfile.mkstemp()`, explicit cleanup in `finally` |
| Git args | Allowlist subcommands, sanitize branch names |
| Binary resolution | PATH → `.venv/Scripts` → `node_modules/.bin` (no shell) |

---

## Git Workflow Standards

### Branch Naming
- Safety branches: `cg/convention-<timestamp>` (e.g., `cg/convention-20261030-143000`)
- Feature branches: `feat/<short-description>`
- Fix branches: `fix/<short-description>`

### Commit Messages
- **Format**: Conventional Commits (`type(scope): description`)
- **Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`
- **Examples**:
  - `feat(finders): add import ordering for Go`
  - `fix(applier): handle empty diff edge case`
  - `docs(styleguide): update artifact templates`

### Pre-commit Hooks (Generated)
```yaml
# .pre-commit-config.yaml (generated by cg init-styleguide)
repos:
  - repo: local
    hooks:
      - id: cg-audit
        name: cg audit
        entry: cg audit
        language: system
        pass_filenames: false
      - id: cg-verify
        name: cg verify
        entry: cg verify
        language: system
        pass_filenames: false
```

---

## CI/CD Standards

### GitHub Actions (Generated Template)
```yaml
# .cg/ci-lint.yml (copy to .github/workflows/cg-lint.yml)
name: cg-lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install convention-guardian[adapters]
      - run: cg audit
      - run: cg verify
```

### Required Checks
1. `cg audit` — No new findings (or approved baseline)
2. `cg verify` — Fast checks pass
3. `pytest` — Unit/integration tests pass
4. `ruff check` — Linting (if Python project)
5. `ruff format --check` — Formatting (if Python project)

---

## Documentation Standards

### Code Documentation
- **Module docstring**: Every `.py` file
- **Class docstring**: Every public class
- **Function docstring**: Every public function/method
- **Type hints**: 100% on public APIs

### User Documentation
- **README.md**: Quick start, commands, architecture overview
- **STYLEGUIDE.md**: Generated, per-category audit snapshot
- **CHANGELOG.md**: Keep a changelog (manual or generated)

### Architecture Documentation
- **docs/architecture.md**: System architecture, component relationships
- **docs/technical-decisions.md**: Decision log (accepted/pending/rejected)
- **docs/development-standards.md**: This file

---

## Performance Standards

| Operation | Target | Measurement |
|-----------|--------|-------------|
| CLI startup | < 500ms | `time cg --help` |
| Scan (10k files) | < 3s | `cg scan` |
| Audit (10k files) | < 10s | `cg audit` |
| Apply (100 findings) | < 5s | `cg apply --batch safe` |
| Memory peak | < 200MB | `memory_profiler` |

### Optimization Guidelines
- Use `pathspec` for ignore matching (C-optimized)
- Stream file reads (don't load entire file for simple checks)
- Lazy-load tree-sitter grammars (only when adapters enabled)
- Batch subprocess calls (single `pytest` run vs per-file)
- Profile before optimizing

---

## Dependency Management

### Adding Dependencies
1. Add to `pyproject.toml` under `[project.dependencies]` or `[project.optional-dependencies]`
2. Pin minimum version, allow compatible updates (`>=x.y,<z`)
3. Run `pip install -e .[dev]` to update lockfile
4. Update `uv.lock` if using uv

### Updating Dependencies
- **Security**: `pip-audit` in CI, update immediately
- **Features**: Quarterly review, test thoroughly
- **Breaking**: Major version updates require migration plan

### Optional Dependencies
- `dev`: pytest, pyyaml
- `libcst`: Python AST manipulation
- `adapters`: tree-sitter + grammars (JS/TS, Go, Rust)

---

*Generated: 2026-10-30 | Stage 3 of 5*
# ConventionGuardian report

Root: `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian`

## Environment

| Key | Value |
|---|---|
| Root | C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian |
| Languages | Python, Java |
| Package managers | pip/poetry/uv |
| Configs | pyproject.toml |
| Formatters | Prettier |
| Linters | ESLint |
| Monorepo tools | Bazel |
| Test frameworks | pytest, Jest, Vitest |
| Git repo | no |

## Findings

### Imports

#### I-001 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\_repro_dry.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-002 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\base.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from conventionguardian.models import Category, Finding, Severity
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-003 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\golang.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-004 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\jsts.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-005 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\rust.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-006 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adopt.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from conventionguardian import applier, audit as audit_mod, safety, scanner, styleguide
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-007 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\applier.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from pathlib import Path

from conventionguardian import checks, safety
from conventionguardian.audit
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-008 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\audit.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-009 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\checks.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from conventionguardian.models import ToolProfile
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-010 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\cli.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-011 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\config.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import tomllib
from pathlib import Path
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-012 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\diff.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import difflib
from pathlib import Path
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-013 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\docs_style.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import ast
from pathlib import Path

from conventionguardian.models import Category, Finding, Severity
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-014 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\formatting.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-015 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\imports.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import ast
from pathlib import Path

from conventionguardian.finders.fixers import sort_import_block
from conventionguardian.models import Category, Finding, Severi
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-016 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\misc.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

from pathlib import Path

from conventionguardian.models import Category, Finding, Severity
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-017 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\naming.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path

from conventionguardian.finders.fixers import camel_to_snake, rename_identifier
from 
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-018 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\structure.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

from pathlib import Path

from conventionguardian.models import Category, Finding, Severity
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-019 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\tooling.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

from pathlib import Path

from conventionguardian.models import Category, Finding, Severity
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-020 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\formatters.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from conventionguardian.models import Finding, Severity, ToolProf
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-021 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\models.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-022 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\reporters\console.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text i
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-023 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\reporters\markdown.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

from pathlib import Path

from conventionguardian.models import Category, Finding, ToolProfile
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-024 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\safety.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import subprocess
import time
from pathlib import Path

from rich.console import Console
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-025 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\scanner.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import fnmatch
from pathlib import Path

from pathspec import GitIgnoreSpec

from conventionguardian.config import BUILTIN_IGNORE_FILES, Config, load_config
from co
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-026 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\styleguide.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Pat
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-027 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\fixture_project.py`
- **Message:** Import block is not grouped stdlib -> third-party -> local
- **Current:** from __future__ import annotations

import subprocess
from pathlib import Path
- **Recommended:** grouped order
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Pure reordering of top-level imports; same names bound.

#### I-028 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_adapters.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-029 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_adopt.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-030 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_e2e.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-031 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_formatters.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-032 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_styleguide.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

#### I-033 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_units.py`
- **Message:** Import block ordering not verifiable automatically
- **Current:** mixed import block
- **Recommended:** stdlib -> third-party -> local
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Multi-line or commented import blocks need manual review.

### Formatting

#### F-001 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\golang.py`
- **Message:** Mixed quote styles (5 single vs 52 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-002 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\jsts.py`
- **Message:** 1 line(s) exceed 100 chars (first: line 184)
- **Current:** 119 chars
- **Recommended:** <=100 chars
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Line wrapping can alter string contents; manual review only.

#### F-003 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\jsts.py`
- **Message:** Mixed quote styles (5 single vs 66 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-004 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\rust.py`
- **Message:** 1 line(s) exceed 100 chars (first: line 187)
- **Current:** 112 chars
- **Recommended:** <=100 chars
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Line wrapping can alter string contents; manual review only.

#### F-005 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\rust.py`
- **Message:** Mixed quote styles (2 single vs 37 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-006 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\audit.py`
- **Message:** 2 line(s) exceed 100 chars (first: line 25)
- **Current:** 101 chars
- **Recommended:** <=100 chars
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Line wrapping can alter string contents; manual review only.

#### F-007 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\cli.py`
- **Message:** 3 line(s) exceed 100 chars (first: line 145)
- **Current:** 105 chars
- **Recommended:** <=100 chars
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Line wrapping can alter string contents; manual review only.

#### F-008 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\cli.py`
- **Message:** Mixed quote styles (12 single vs 113 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-009 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\config.py`
- **Message:** Mixed quote styles (1 single vs 56 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-010 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\fixers.py`
- **Message:** Mixed quote styles (1 single vs 69 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-011 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\formatting.py`
- **Message:** Mixed quote styles (7 single vs 35 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-012 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\imports.py`
- **Message:** Mixed quote styles (1 single vs 36 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-013 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\misc.py`
- **Message:** 1 line(s) exceed 100 chars (first: line 46)
- **Current:** 104 chars
- **Recommended:** <=100 chars
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Line wrapping can alter string contents; manual review only.

#### F-014 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\misc.py`
- **Message:** Mixed quote styles (1 single vs 20 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-015 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\naming.py`
- **Message:** Mixed quote styles (2 single vs 19 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-016 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\reporters\console.py`
- **Message:** Mixed quote styles (2 single vs 42 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-017 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\safety.py`
- **Message:** Mixed quote styles (1 single vs 16 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-018 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\styleguide.py`
- **Message:** 8 line(s) exceed 100 chars (first: line 277)
- **Current:** 105 chars
- **Recommended:** <=100 chars
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Line wrapping can alter string contents; manual review only.

#### F-019 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\styleguide.py`
- **Message:** Mixed quote styles (9 single vs 279 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-020 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_adapters.py`
- **Message:** 2 line(s) exceed 100 chars (first: line 104)
- **Current:** 107 chars
- **Recommended:** <=100 chars
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Line wrapping can alter string contents; manual review only.

#### F-021 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_adapters.py`
- **Message:** Mixed quote styles (5 single vs 67 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-022 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_adopt.py`
- **Message:** 1 line(s) exceed 100 chars (first: line 86)
- **Current:** 101 chars
- **Recommended:** <=100 chars
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Line wrapping can alter string contents; manual review only.

#### F-023 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_styleguide.py`
- **Message:** Mixed quote styles (2 single vs 108 double)
- **Current:** mixed quotes
- **Recommended:** double quotes
- **Confidence:** 100% (auto-applicable: yes)
- **Rationale:** Whitespace-only change; AST-equivalent source.

#### F-024 — Style drift

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_units.py`
- **Message:** 1 line(s) exceed 100 chars (first: line 91)
- **Current:** 108 chars
- **Recommended:** <=100 chars
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Line wrapping can alter string contents; manual review only.

### Docs

#### D-001 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\_repro_dry.py`
- **Message:** 2 public definition(s) lack a docstring (first: run)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-002 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\base.py`
- **Message:** 3 public definition(s) lack a docstring (first: available_languages)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-003 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\golang.py`
- **Message:** 1 public definition(s) lack a docstring (first: GoAdapter)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-004 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\adapters\rust.py`
- **Message:** 1 public definition(s) lack a docstring (first: RustAdapter)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-005 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\applier.py`
- **Message:** 3 public definition(s) lack a docstring (first: ApplyError)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-006 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\checks.py`
- **Message:** 3 public definition(s) lack a docstring (first: CheckResult)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-007 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\cli.py`
- **Message:** 1 public definition(s) lack a docstring (first: app_main)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-008 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\finders\fixers.py`
- **Message:** 1 public definition(s) lack a docstring (first: camel_to_snake)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-009 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\formatters.py`
- **Message:** 1 public definition(s) lack a docstring (first: handles)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-010 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\models.py`
- **Message:** 5 public definition(s) lack a docstring (first: Category)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-011 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\reporters\console.py`
- **Message:** 1 public definition(s) lack a docstring (first: print_scan_table)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-012 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\reporters\markdown.py`
- **Message:** 2 public definition(s) lack a docstring (first: render_markdown)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-013 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\safety.py`
- **Message:** 3 public definition(s) lack a docstring (first: SafetyError)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-014 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\conventionguardian\scanner.py`
- **Message:** 1 public definition(s) lack a docstring (first: detect_profile)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-015 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\fixture_project.py`
- **Message:** 2 public definition(s) lack a docstring (first: build)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-016 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_adapters.py`
- **Message:** 12 public definition(s) lack a docstring (first: test_js_naming_and_import_report)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-017 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_adopt.py`
- **Message:** 10 public definition(s) lack a docstring (first: mini_project)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-018 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_e2e.py`
- **Message:** 10 public definition(s) lack a docstring (first: mini_project)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-019 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_formatters.py`
- **Message:** 5 public definition(s) lack a docstring (first: test_delegate_replaces_builtin_and_emits_delegate)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-020 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_styleguide.py`
- **Message:** 18 public definition(s) lack a docstring (first: mini_project)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

#### D-021 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\tests\test_units.py`
- **Message:** 10 public definition(s) lack a docstring (first: test_camel_to_snake)
- **Current:** missing docstring
- **Recommended:** add docstrings
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Writing doc content is not a mechanical style fix.

### Tooling

#### T-001 — Optional improvement

- **Location:** `C:\Users\MohammadHossein\Desktop\projects\ConventionGuardian\.editorconfig`
- **Message:** No .editorconfig found for a Python project
- **Current:** missing .editorconfig
- **Recommended:** add .editorconfig (utf-8, lf, indent 4 spaces, trim trailing ws)
- **Confidence:** 0% (auto-applicable: no)
- **Rationale:** Config content is advisory; generated only on request.

## Batches

- Auto-fixable findings: 35
- Manual-review findings: 44

Apply with `cg apply --batch <batch>` or `cg apply --ids <id,...>`.

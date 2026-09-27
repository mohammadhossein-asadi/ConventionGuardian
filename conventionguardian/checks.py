"""Fast verification: type-check / compile / unit tests with a time budget."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from conventionguardian.models import ToolProfile


@dataclass
class CheckResult:
    command: str
    ok: bool
    output: str
    duration_s: float


@dataclass
class CheckPlan:
    commands: list[list[str]] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.commands)


def build_plan(root: Path, profile: ToolProfile) -> CheckPlan:
    """Pick fast, already-present checks from the detected tool profile."""
    plan = CheckPlan()
    if "Python" in profile.languages:
        plan.commands.append(
            ["python", "-m", "compileall", "-q",
             "-x", r"(\.git|\.venv|venv|__pycache__|\.cg|node_modules|build|dist)",
             str(root)]
        )
        plan.labels.append("python compileall")
    if "pytest" in profile.tests:
        plan.commands.append(["python", "-m", "pytest", "-x", "-q", str(root)])
        plan.labels.append("pytest")
    if "TypeScript" in profile.languages and root.joinpath("tsconfig.json").is_file():
        plan.commands.append(["npx", "--no-install", "tsc", "--noEmit"])
        plan.labels.append("tsc --noEmit")
    if "Go" in profile.languages:
        plan.commands.append(["go", "build", "./..."])
        plan.labels.append("go build")
    if "Rust" in profile.languages:
        plan.commands.append(["cargo", "check", "--quiet"])
        plan.labels.append("cargo check")
    if "Node" in profile.languages or "JavaScript" in profile.languages:
        pkg = Path(root) / "package.json"
        if pkg.is_file() and "\"tsc\"" in pkg.read_text(encoding="utf-8", errors="replace"):
            plan.commands.append(["npx", "--no-install", "tsc", "--noEmit"])
            plan.labels.append("tsc --noEmit")
    return plan


def run_checks(root: Path, plan: CheckPlan, timeout_s: int = 120) -> list[CheckResult]:
    results: list[CheckResult] = []
    for cmd, label in zip(plan.commands, plan.labels):
        started = time.perf_counter()
        try:
            res = subprocess.run(
                cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s,
            )
            ok = res.returncode == 0
            out = (res.stdout or "") + (res.stderr or "")
        except FileNotFoundError:
            ok = True
            out = f"{cmd[0]} not found on PATH; check skipped"
        except subprocess.TimeoutExpired:
            ok = False
            out = f"{label} timed out after {timeout_s}s"
        results.append(
            CheckResult(
                command=" ".join(cmd),
                ok=ok,
                output=out[-4000:],
                duration_s=round(time.perf_counter() - started, 2),
            )
        )
    return results

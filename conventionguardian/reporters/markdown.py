"""Markdown report output."""

from __future__ import annotations

from pathlib import Path

from conventionguardian.models import Category, Finding, ToolProfile


def render_markdown(root: Path, profile: ToolProfile, findings: list[Finding]) -> str:
    lines: list[str] = []
    lines.append("# ConventionGuardian report")
    lines.append("")
    lines.append(f"Root: `{root}`")
    lines.append("")
    lines.append("## Environment")
    lines.append("")
    lines.append("| Key | Value |")
    lines.append("|---|---|")
    for k, v in profile.summary_rows():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    if not findings:
        lines.append("No convention findings. Clean project!")
        return "\n".join(lines) + "\n"

    by_cat: dict[Category, list[Finding]] = {}
    for f in findings:
        by_cat.setdefault(f.category, []).append(f)

    for category in Category:
        group = by_cat.get(category)
        if not group:
            continue
        lines.append(f"### {category.value.title()}")
        lines.append("")
        for f in group:
            applicable = "yes" if (f.conf == 100 and f.fix is not None) else "no"
            lines.append(f"#### {f.id} — {f.severity.value}")
            lines.append("")
            lines.append(f"- **Location:** `{f.path}`")
            lines.append(f"- **Message:** {f.message}")
            if f.current or f.recommended:
                lines.append(f"- **Current:** {f.current}")
                lines.append(f"- **Recommended:** {f.recommended}")
            lines.append(f"- **Confidence:** {f.conf}% (auto-applicable: {applicable})")
            lines.append(f"- **Rationale:** {f.rationale}")
            lines.append("")

    applicable = [f for f in findings if f.conf == 100 and f.fix is not None]
    lines.append("## Batches")
    lines.append("")
    lines.append(f"- Auto-fixable findings: {len(applicable)}")
    lines.append(f"- Manual-review findings: {len(findings) - len(applicable)}")
    lines.append("")
    lines.append("Apply with `cg apply --batch <batch>` or `cg apply --ids <id,...>`.")
    return "\n".join(lines) + "\n"


def write_markdown(
    path: Path, root: Path, profile: ToolProfile, findings: list[Finding]
) -> None:
    path.write_text(render_markdown(root, profile, findings), encoding="utf-8")

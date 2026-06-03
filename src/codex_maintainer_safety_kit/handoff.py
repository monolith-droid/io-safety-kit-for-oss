from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_report(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected report JSON object in {path}")
    return data


def render_handoff(report: dict[str, Any]) -> str:
    lines = [
        "# Maintainer Handoff",
        "",
        f"- Job: `{report.get('job_id', 'unknown')}`",
        f"- Repository: `{report.get('repository', '')}`",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated at: `{report.get('generated_at', '')}`",
        f"- Dry run: `{report.get('dry_run', True)}`",
        f"- Execution allowed: `{report.get('execution_allowed', False)}`",
        f"- Command executed: `{report.get('command_executed', False)}`",
        "",
        "## Blockers",
        "",
    ]

    blockers = report.get("blockers") or []
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- None")

    lines.extend(["", "## Warnings", ""])
    warnings = report.get("warnings") or []
    if warnings:
        lines.extend(f"- `{warning}`" for warning in warnings)
    else:
        lines.append("- None")

    lines.extend(["", "## Steps", ""])
    steps = report.get("steps") or []
    if not steps:
        lines.append("- No steps recorded")
    else:
        for step in steps:
            lines.append(
                f"- {step.get('index', '?')}: `{step.get('name', '')}` "
                f"manifest=`{step.get('manifest', '')}` "
                f"would_execute=`{step.get('would_execute', False)}`"
            )

    lines.append("")
    return "\n".join(lines)


def write_handoff(markdown: str, output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8", newline="\n")
    return output

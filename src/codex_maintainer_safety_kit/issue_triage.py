from __future__ import annotations

from pathlib import Path
from typing import Any

from .approval import evaluate_gate


def _list_or_none(items: list[str]) -> list[str]:
    if items:
        return [f"- `{item}`" for item in items]
    return ["- None"]


def _render_target(target: dict[str, Any], index: int) -> str:
    locator = target.get("url") or target.get("path") or target.get("ref") or ""
    purpose = target.get("purpose") or "triage target"
    target_type = target.get("type") or "target"
    return f"- {index}. `{target_type}`: {locator} ({purpose})"


def render_issue_triage(manifest: dict[str, Any]) -> str:
    gate = evaluate_gate(manifest, operation="issue_triage")
    gate_data = gate.to_dict()

    blockers = list(gate.blockers)
    warnings = list(gate.warnings)
    targets = manifest.get("targets") if isinstance(manifest.get("targets"), list) else []
    actions = (
        manifest.get("allowed_actions")
        if isinstance(manifest.get("allowed_actions"), list)
        else []
    )
    command = manifest.get("command") if isinstance(manifest.get("command"), dict) else {}

    lines = [
        "# Issue Triage Report",
        "",
        f"- Repository: `{manifest.get('repository', '')}`",
        f"- Operation: `{manifest.get('operation', '')}`",
        f"- Gate status: `{gate_data.get('status', '')}`",
        f"- Approval status: `{gate_data.get('approval_status', '')}`",
        f"- Risk level: `{manifest.get('risk_level', '')}`",
        "- Mode: `report_only`",
        "- Execution allowed: `False`",
        "- Command executed: `False`",
        "- GitHub mutation performed: `False`",
        "- Labels mutated: `False`",
        "- Comments posted: `False`",
        "",
        "## Scope",
        "",
        f"- Requested by: `{manifest.get('requested_by', '')}`",
        f"- Reason: {manifest.get('reason', '')}",
        f"- Command preview: {command.get('preview', '')}",
        "",
        "## Targets",
        "",
    ]

    if targets:
        for index, target in enumerate(targets, start=1):
            if isinstance(target, dict):
                lines.append(_render_target(target, index))
            else:
                lines.append(f"- {index}. Invalid target entry")
    else:
        lines.append("- None")

    lines.extend(["", "## Allowed Actions", ""])
    lines.extend(_list_or_none([str(action) for action in actions]))

    lines.extend(["", "## Draft Triage Policy", ""])
    lines.extend(
        [
            "- Label suggestions are drafts for maintainer review.",
            "- Priority and duplicate notes must be checked before use.",
            "- Do not mutate labels, milestones, assignments, or comments from this report.",
        ]
    )

    lines.extend(["", "## Blockers", ""])
    lines.extend(_list_or_none(blockers))

    lines.extend(["", "## Warnings", ""])
    lines.extend(_list_or_none(warnings))

    lines.extend(["", "## Maintainer Next Steps", ""])
    if gate.passed:
        lines.extend(
            [
                "- Review the issue query and draft triage notes locally.",
                "- Apply labels, priorities, or comments manually after maintainer review.",
                "- Keep issue mutation disabled until a separate approval model exists.",
            ]
        )
    else:
        lines.extend(
            [
                "- Resolve blockers before using agent output for issue triage.",
                "- Ask for explicit maintainer approval when approval is missing or expired.",
                "- Keep the workflow report-only until the gate passes.",
            ]
        )

    lines.append("")
    return "\n".join(lines)


def write_issue_triage(markdown: str, output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)
    return output

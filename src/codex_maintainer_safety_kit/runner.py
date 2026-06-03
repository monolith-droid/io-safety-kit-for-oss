from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def load_job(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected job JSON object in {path}")
    return data


def build_run_report(job: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    job_id = job.get("job_id") or "unnamed-job"
    steps = job.get("steps")
    if not isinstance(steps, list) or not steps:
        blockers.append("steps_must_be_non_empty_list")
        steps = []

    rendered_steps: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            blockers.append(f"step_not_object:{index}")
            continue
        name = step.get("name") or f"step-{index + 1}"
        manifest = step.get("manifest")
        if not manifest:
            blockers.append(f"step_missing_manifest:{name}")
        rendered_steps.append(
            {
                "index": index,
                "name": name,
                "manifest": manifest,
                "mode": "report_only",
                "would_execute": False,
                "command_executed": False,
                "notes": step.get("notes", ""),
            }
        )

    if job.get("execute") is True:
        blockers.append("job_execution_not_supported_in_mvp")

    if not job.get("repository"):
        warnings.append("job_repository_not_set")

    passed = not blockers
    return {
        "generated_at": now_iso(),
        "mode": "codex_maintainer_safety_kit_report_only_v1",
        "job_id": job_id,
        "repository": job.get("repository", ""),
        "status": "job_plan_ready" if passed else "job_plan_blocked",
        "passed": passed,
        "dry_run": True,
        "execution_allowed": False,
        "command_executed": False,
        "blockers": blockers,
        "warnings": warnings,
        "step_count": len(rendered_steps),
        "steps": rendered_steps,
    }


def write_report(report: dict[str, Any], output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output

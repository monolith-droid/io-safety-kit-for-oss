---
name: oss-maintenance
description: Use this skill to run report-only AI-assisted OSS maintainer workflows with approval manifests and fail-closed checks.
---

# OSS Maintenance Skill

Use this skill when a maintainer wants help with pull request review, issue
triage, release preparation, dependency review, or handoff generation.

## Workflow

1. Create or select an approval manifest under `examples/` or a project-local
   maintainer workflow directory.
2. Run `iosk validate --manifest <path> --json`.
3. Run `iosk gate --manifest <path> --json`.
4. If the gate passes, produce only report-only output.
5. Never execute commands, read secrets, merge pull requests, change repository
   settings, publish releases, or mutate labels unless a separate explicit
   project policy and approval layer exists.

## Output

Prefer concise reports with:

- scope,
- allowed actions,
- blockers,
- warnings,
- maintainer next steps,
- whether human review is required.

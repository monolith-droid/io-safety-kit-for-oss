# Codex Maintainer Safety Kit

[![CI](https://github.com/monolith-droid/codex-maintainer-safety-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/monolith-droid/codex-maintainer-safety-kit/actions/workflows/ci.yml)

Codex Maintainer Safety Kit is a small, fail-closed operations layer for open
source maintainers who want to use coding agents for pull request review, issue
triage, release work, and security checks without losing control of side
effects.

The current MVP is intentionally report-only. It validates approval manifests,
checks whether a requested maintainer workflow is inside the approved scope, and
produces auditable JSON/Markdown reports. It does not execute shell commands,
read secrets, change repository settings, merge pull requests, or publish
anything.

## Why This Exists

AI coding agents are useful for OSS maintenance, but the risky part is often not
the code suggestion. It is the surrounding workflow: which repository is in
scope, which action is authorized, whether a task is dry-run or executable, and
how a maintainer can reconstruct what happened later.

This project gives maintainers a compact pattern:

1. Describe a task with an approval manifest.
2. Validate the manifest.
3. Pass it through a fail-closed gate.
4. Run only report-only maintainer workflow plans.
5. Store the output as reviewable evidence.

## Quick Start

```bash
python -m pip install -e .
cmsk validate --manifest examples/pr-review-manifest.json --json
cmsk gate --manifest examples/pr-review-manifest.json --json
cmsk run --job examples/maintainer-job.json --json
cmsk handoff --report examples/sample-run-report.json --out reports/handoff.md
```

You can also run the module directly:

```bash
python -m codex_maintainer_safety_kit validate --manifest examples/pr-review-manifest.json
```

## What The Gate Checks

- Required manifest fields are present.
- The operation is one of the supported maintainer workflows.
- The approval is explicit, unexpired, and tied to a concrete scope.
- Requested actions avoid blocked high-risk verbs such as secret access,
  repository visibility changes, destructive cleanup, or protected-branch
  mutation.
- The command runner remains dry-run/report-only in this MVP.

## Example Workflows

- `examples/pr-review-manifest.json`: scope a Codex-assisted PR review.
- `examples/issue-triage-manifest.json`: classify and prioritize issues.
- `examples/release-checklist-manifest.json`: prepare release notes and checks.
- `examples/security-audit-manifest.json`: demonstrate a pending approval that
  must fail closed.
- `examples/maintainer-job.json`: report-only job plan using those manifests.

## Project Status

This repository is being prepared as a public OSS project for maintainers who
want auditable Codex-assisted workflows. The immediate goal is a clean v0.1.0
release with examples, CI, issue templates, and a small set of maintainer
automation recipes.

See:

- [Security model](docs/security-model.md)
- [Maintainer workflows](docs/maintainer-workflows.md)
- [Codex for OSS application draft](docs/codex_for_oss_application_draft.md)

## Non-Goals

- This is not a replacement for GitHub permissions or branch protection.
- This is not a secret scanner or vulnerability scanner.
- This MVP does not execute commands.
- This MVP does not grant authorization by itself; it only verifies that a
  manifest says authorization exists and reports whether the gate would allow
  the workflow.

## License

MIT

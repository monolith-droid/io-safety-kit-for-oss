# Publication Checklist

Use this checklist before making the repository public or submitting the Codex
for OSS application.

## Local Readiness

- Run `python -m unittest discover -s tests`.
- Run `python -m compileall -q src tests`.
- Run `cmsk validate --manifest examples/pr-review-manifest.json --json`.
- Run `cmsk gate --manifest examples/pr-review-manifest.json --json`.
- Run `cmsk promotion-check --candidate examples/promotion-candidate.json --json`.
- Run `cmsk run --job examples/maintainer-job.json --json`.
- Confirm `docs/codex_for_oss_strategy.md` stays local and ignored.

## GitHub Setup

- Create public repository: `monolith-droid/codex-maintainer-safety-kit`.
- Push the initial commit.
- Confirm the CI badge resolves.
- Create labels: `bug`, `workflow`, `safety`, `good first issue`.
- Open 3 to 5 public issues for the v0.1.0 roadmap.
- Close 1 to 2 issues through small PRs before applying, if time allows.
- Tag `v0.1.0` after README, examples, CI, and docs are stable.

## Suggested First Issues

- Add JSON Schema validation as an optional dependency.
- Add a GitHub issue triage report renderer.
- Add a PR review report renderer.
- Add safe output promotion checks for private-to-public OSS extraction.
- Add signed approval manifest design notes.
- Add eval fixtures for blocked action behavior.

## Submission

- Use `docs/codex_for_oss_application_draft.md` for the form copy.
- Submit only after the repository is public.
- Select API credits and Codex Security only if the repository is public and
  authorization/control is clear.

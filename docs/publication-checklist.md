# Publication Checklist

Use this checklist before public releases or before promoting downstream
findings into public OSS artifacts.

## Local Readiness

- Run `python -m unittest discover -s tests`.
- Run `python -m compileall -q src tests`.
- Run `iosk validate --manifest examples/pr-review-manifest.json --json`.
- Run `iosk gate --manifest examples/pr-review-manifest.json --json`.
- Run `iosk promotion-check --candidate examples/promotion-candidate.json --json`.
- Run `iosk run --job examples/maintainer-job.json --json`.
- Confirm local planning notes stay ignored and outside public commits.

## GitHub Setup

- Confirm the public repository URL and CI badge resolve.
- Push the initial commit.
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

## Public Promotion

- Promote only synthetic examples, generic fixtures, and public documentation.
- Keep private planning notes and local adapter details out of the public
  repository.
- Keep report-only defaults unless a separate design issue defines a stronger
  approval model.

# Changelog

## Unreleased

- Generalize the public project name to I/O Safety Kit for OSS.
- Position Codex as the first reference workflow rather than the project
  boundary.
- Add `iosk` as the preferred console command while retaining `msk` and `cmsk`
  for v0.1.x compatibility.
- Update public example schema versions to the `iosk.*` namespace.
- Remove the application-form draft from the public documentation set.

## v0.1.3

- Add `cmsk promotion-check` for privacy-safe public promotion candidates.
- Add safe output promotion loop docs, example candidate, and issue template.
- Add tests for ready and blocked promotion candidates.

## v0.1.2

- Add a report-only PR review Markdown renderer and CLI command.
- Add deterministic PR review renderer tests and sample output.
- Document downstream dogfooding as the project loop for turning private
  maintainer workflows into generic, privacy-safe public improvements.

## v0.1.1

- Add blocked-action regression fixtures for secret reads, force pushes,
  repository visibility changes, and branch protection changes.
- Convert blocked-action tests to table-driven fixture coverage.
- Add a README fail-closed sample output.

## v0.1.0

- Initial public MVP.
- Add approval manifest validation and fail-closed gate evaluation.
- Add report-only maintainer job planning and handoff rendering.
- Add PR review, issue triage, release checklist, and security audit examples.
- Add GitHub Actions CI, issue templates, and contribution docs.

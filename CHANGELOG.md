# Changelog

## Unreleased

- Add a public-safe evidence bundle example for promotion candidates.

## v0.3.0

- Add optional JSON Schema validation for promotion candidates.

## v0.2.6

- Add machine-readable review evidence summaries to promotion check output.

## v0.2.5

- Add public-safe review evidence checks for safe output promotion candidates.

## v0.2.4

- Refresh CI for the Windows 2025 VS 2026 runner label and signed-policy smoke
  checks.

## v0.2.3

- Add provider-neutral trust policy fixtures and `iosk trust-policy-check`.

## v0.2.2

- Add signed approval manifest digest verification fixtures and
  `iosk signature-check`.

## v0.2.1

- Add a synthetic maintainer workflow case study.

## v0.2.0

- Add a dogfooding-to-public issue template for safe public promotion.

## v0.1.7

- Add a signed approval manifest design note.

## v0.1.6

- Add optional JSON Schema validation for approval manifests via
  `iosk validate --schema`.

## v0.1.5

- Add a report-only issue triage Markdown renderer and CLI command.

## v0.1.4

- Generalize the public project name to I/O Safety Kit for OSS.
- Position Codex as the first reference workflow rather than the project
  boundary.
- Add `iosk` as the preferred console command while retaining `msk` and `cmsk`
  for v0.1.x compatibility.
- Update public example schema versions to the `iosk.*` namespace.
- Rename the public repository slug to `io-safety-kit-for-oss` and update
  repository URLs in docs, examples, and schemas.
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

# I/O Safety Kit for OSS

[![CI](https://github.com/monolith-droid/io-safety-kit-for-oss/actions/workflows/ci.yml/badge.svg)](https://github.com/monolith-droid/io-safety-kit-for-oss/actions/workflows/ci.yml)

I/O Safety Kit for OSS is a small, fail-closed operations layer for open source
maintainers who want to control both sides of AI-assisted maintenance: what
coding agents are allowed to take in, and what workflow output is safe to
publish.

The project is agent-agnostic by design. Codex workflows are the first concrete
reference use case, while the manifest, gate, report, and promotion patterns are
intended for OSS maintenance with coding agents more broadly.

The current release line is intentionally report-only. It validates approval
manifests, checks whether a requested maintainer workflow is inside the approved
scope, and produces auditable JSON/Markdown reports. It does not execute shell
commands, read secrets, change repository settings, merge pull requests, or
publish anything.

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

## I/O Model

Input safety means the agent workflow starts from a declared scope: repository,
operation, targets, approval state, allowed actions, and blocked high-risk
verbs. The core workflow does not read secrets, scan unrelated repositories, or
execute commands.

Output safety means the generated workflow result stays reviewable before it
becomes public. Reports remain local by default, GitHub mutation is disabled,
and `promotion-check` fails closed when private context, local paths, personal
data, or non-synthetic examples remain in a candidate.

## Quick Start

```bash
python -m pip install -e .
iosk validate --manifest examples/pr-review-manifest.json --json
iosk gate --manifest examples/pr-review-manifest.json --json
iosk pr-review --manifest examples/pr-review-manifest.json --out reports/pr-review.md
iosk issue-triage --manifest examples/issue-triage-manifest.json --out reports/issue-triage.md
iosk promotion-check --candidate examples/promotion-candidate.json --json
iosk signature-check --manifest examples/signed-pr-review-manifest.json --json
iosk trust-policy-check \
  --manifest examples/signed-pr-review-manifest.json \
  --policy examples/trust-policy.json \
  --json
iosk run --job examples/maintainer-job.json --json
iosk handoff --report examples/sample-run-report.json --out reports/handoff.md
```

The `iosk` command is the primary supported CLI name. The older `msk` and
`cmsk` commands remain compatibility aliases for early examples and adapters,
but new public docs and automation should use `iosk`. See
[V1 stability notes](docs/v1-stability.md).

You can also run the module directly:

```bash
python -m io_safety_kit validate --manifest examples/pr-review-manifest.json
```

## Optional JSON Schema Validation

The default validators use only the Python standard library. For stricter
manifest and promotion candidate shape checks, install the optional schema extra
and pass `--schema`:

```bash
python -m pip install -e ".[schema]"
iosk validate --manifest examples/pr-review-manifest.json --schema --json
iosk promotion-check --candidate examples/promotion-candidate.json --schema --json
```

When `jsonschema` is installed, schema errors are reported as fail-closed
`schema_error:*` blockers. When it is not installed, `--schema` falls back to
the standard validator and emits the warning
`jsonschema_not_installed_schema_validation_skipped`.

## Fail-Closed Example

High-risk actions remain blocked even when a fixture claims approval:

```bash
iosk gate --manifest tests/fixtures/blocked_actions/read_secret.json --json
```

```json
{
  "approval_status": "approved",
  "blockers": [
    "blocked_action:read_secret_values"
  ],
  "operation": "security_audit",
  "passed": false,
  "repository": "monolith-droid/io-safety-kit-for-oss",
  "risk_level": "high",
  "status": "gate_blocked_fail_closed",
  "warnings": [
    "high_risk_operation_requires_extra_maintainer_review"
  ]
}
```

## What The Gate Checks

- Required manifest fields are present.
- The operation is one of the supported maintainer workflows.
- The approval is explicit, unexpired, and tied to a concrete scope.
- Requested actions avoid blocked high-risk verbs such as secret access,
  repository visibility changes, destructive cleanup, or protected-branch
  mutation.
- The command runner remains dry-run/report-only in the core workflow.

## Example Workflows

- `examples/pr-review-manifest.json`: scope an AI-assisted PR review.
- `examples/pr-review-report.md`: sample report-only PR review output.
- `examples/issue-triage-manifest.json`: classify and prioritize issues.
- `examples/issue-triage-report.md`: sample report-only issue triage output.
- `examples/release-checklist-manifest.json`: prepare release notes and checks.
- `examples/security-audit-manifest.json`: demonstrate a pending approval that
  must fail closed.
- `examples/signed-pr-review-manifest.json`: demonstrate provider-neutral
  signed manifest digest metadata.
- `examples/trust-policy.json`: define synthetic trusted signature identities
  for repository, operation, and risk checks.
- `examples/maintainer-job.json`: report-only job plan using those manifests.
- `examples/promotion-candidate.json`: check whether private/downstream output
  is safe to promote publicly.

## PR Review Renderer

Render a deterministic local Markdown report without posting to GitHub:

```bash
iosk pr-review --manifest examples/pr-review-manifest.json --out reports/pr-review.md --json
```

The report summarizes scope, allowed actions, gate status, blockers, warnings,
and maintainer next steps. It keeps `GitHub mutation performed` set to `False`.

## Issue Triage Renderer

Render a deterministic local Markdown report without mutating labels, milestones,
assignments, or comments:

```bash
iosk issue-triage --manifest examples/issue-triage-manifest.json --out reports/issue-triage.md --json
```

The report summarizes scope, allowed actions, gate status, draft triage policy,
blockers, warnings, and maintainer next steps. It keeps `Labels mutated` and
`Comments posted` set to `False`.

## Safe Output Promotion

AI-assisted development needs not only safe input, but safe output. I/O Safety
Kit for OSS can check whether useful private or downstream workflow findings
are ready to become public OSS artifacts:

```bash
iosk promotion-check --candidate examples/promotion-candidate.json --out reports/promotion.md --json
```

The check fails closed when secrets, personal data, local paths, private context,
non-synthetic examples, or missing review evidence remain in the candidate.
Review evidence must be public-safe and synthetic; it should describe what was
checked without quoting private records. JSON output includes an evidence
summary with check counts, check ids, failed ids, and missing evidence notes so
CI and maintainers can review the record without parsing private logs. See
[Safe output promotion loop](docs/safe-output-promotion-loop.md).

When the optional schema extra is installed, `promotion-check --schema` also
validates the candidate structure against
`schemas/promotion-candidate.schema.json`.
Promotion candidates may also include a public-safe `evidence_bundle` that
groups docs, examples, tests, issues, pull requests, releases, or CI records
without requiring private logs.
See [Evidence bundle review](docs/evidence-bundle-review.md) for the maintainer
checklist.

## Signed Manifest Digest Check

Signed approval manifest support starts with the provider-neutral part: checking
that public signature metadata still matches the canonical approval manifest
payload.

```bash
iosk signature-check --manifest examples/signed-pr-review-manifest.json --json
```

The fixture intentionally does not include private keys, signing services, or
provider-specific credentials. The command verifies the canonical SHA-256 payload
digest and reports `cryptographic_signature_verified` as `False` until a future
provider integration is added. See
[Signed approval manifests](docs/signed-approval-manifests.md).

## Trust Policy Check

A signed manifest can say who claims to have signed it, but a project policy
decides whether that identity is trusted for a repository, operation, and risk
level:

```bash
iosk trust-policy-check \
  --manifest examples/signed-pr-review-manifest.json \
  --policy examples/trust-policy.json \
  --json
```

The fixture uses only public, synthetic identity metadata. The check first
requires the signed manifest digest metadata to pass, then verifies the identity,
key reference, allowed operations, repository, and maximum risk level. It does
not read private keys or call signing services.

## Project Status

This repository is a public OSS project for maintainers who want auditable
AI-assisted workflows. The current focus is a small active release line with
examples, CI, issue templates, blocked-action regression fixtures,
signed-manifest digest and trust-policy fixtures, and maintainer automation
recipes.

The project is developed through a dogfooding loop: private downstream adapters
can use the public core in report-only mode, then promote only generic,
privacy-safe improvements back into this repository as issues, tests, docs, or
small PRs. This keeps the OSS core reusable without exposing local operations,
secrets, private paths, or organization-specific policy.

See:

- [Security model](docs/security-model.md)
- [Maintainer workflows](docs/maintainer-workflows.md)
- [Downstream dogfooding](docs/downstream-dogfooding.md)
- [Safe output promotion loop](docs/safe-output-promotion-loop.md)
- [Evidence bundle review](docs/evidence-bundle-review.md)
- [Synthetic maintainer workflow case study](docs/synthetic-maintainer-case-study.md)
- [Signed approval manifests](docs/signed-approval-manifests.md)
- [V1 stability notes](docs/v1-stability.md)

## Non-Goals

- This is not a replacement for GitHub permissions or branch protection.
- This is not a secret scanner or vulnerability scanner.
- The core workflow does not execute commands.
- This project does not grant authorization by itself; it only verifies that a
  manifest says authorization exists and reports whether the gate would allow
  the workflow.

## License

MIT

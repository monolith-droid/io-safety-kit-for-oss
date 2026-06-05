# Security Model

I/O Safety Kit for OSS assumes that useful AI-assisted maintenance needs visible
boundaries around both input scope and output publication.

## Default State

- Fail closed.
- Dry-run/report-only.
- No command execution in the core workflow.
- No secret reads.
- No repository visibility changes.
- No protected-branch mutation.
- No external publishing.
- No scanning of systems or repositories outside maintainer authorization.

## Trust Boundary

The approval manifest is evidence of intended scope, not proof of human consent
by itself. Maintainers should store manifests in pull requests, issues, or
review systems where approval is auditable.

The gate checks that the manifest is structurally valid and says approval is
present. It does not replace GitHub permissions, branch protection, code owner
review, or human judgment.

When the optional `jsonschema` dependency is installed, maintainers can add
schema checks with `iosk validate --schema`. If the dependency is absent, the
CLI keeps the standard-library validator working and reports that schema
validation was skipped.

Signed approval manifest fixtures now bind reviewed scope to public digest
metadata and synthetic trust policy metadata. The current implementation does
not verify provider cryptographic signatures. It keeps signing providers
optional and keeps private keys out of this project. See
[Signed approval manifests](signed-approval-manifests.md).

## Input Boundary

An agent workflow should begin from declared maintainer intent: repository,
operation, targets, allowed actions, approval state, and output destination. The
gate treats anything outside that manifest as out of scope.

## Output Boundary

Generated reports and promotion candidates are not public artifacts by default.
They should remain local until private context has been removed, examples have
been made synthetic, and a maintainer can review the result in public without
revealing secrets, personal data, local paths, or organization-only policy.

## Blocked Action Keywords

The gate blocks action strings containing high-risk verbs such as:

- `delete_repo`
- `change_visibility`
- `force_push`
- `merge_without_review`
- `read_secret`
- `external_publish`
- `disable_branch_protection`
- `edit_github_secrets`
- `destructive_cleanup`

## High-Risk Reviews

High-risk workflows, such as security audit work, produce an extra warning even
when approved. Maintainers should require an additional human review step before
turning those workflows into executable automation.

## Roadmap

- Expand JSON Schema coverage as the manifest model grows.
- Add provider-backed signature verification after the public fixture model is
  stable.
- Add GitHub issue and PR comment renderers.
- Expand explicit policy files for organizations and projects.
- Add evals for prompt regressions and gate behavior.

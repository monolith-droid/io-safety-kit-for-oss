# Security Model

Codex Maintainer Safety Kit assumes that useful AI-assisted maintenance needs a
visible boundary between planning and side effects.

## Default State

- Fail closed.
- Dry-run/report-only.
- No command execution in the MVP.
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

## Blocked Action Keywords

The MVP blocks action strings containing high-risk verbs such as:

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

- Add JSON Schema validation as an optional dependency.
- Add signed approval manifests.
- Add GitHub issue and PR comment renderers.
- Add explicit policy files for organizations and projects.
- Add evals for prompt regressions and gate behavior.

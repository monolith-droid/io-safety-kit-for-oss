# Maintainer Workflows

This project is designed around everyday open source maintainer tasks where an
AI coding agent can help, but should remain inside a visible authorization
boundary.

Codex is the first concrete reference workflow for these examples. The core
pattern is broader: manifest-scoped work, fail-closed gates, report-only output,
and human maintainer application.

For stricter manifest checks, install the optional `schema` extra and run:

```bash
iosk validate --manifest examples/pr-review-manifest.json --schema --json
```

If `jsonschema` is not installed, the CLI keeps the standard validator working
and reports that schema validation was skipped.

## Pull Request Review

Use an approval manifest to scope the repository, pull request URL, allowed
read-only actions, and output location. The gate should allow only local review
reports and draft comments. It should not merge, approve, request changes, push
commits, or edit branch protection.

Render the report locally:

```bash
iosk pr-review --manifest examples/pr-review-manifest.json --out reports/pr-review.md
```

The PR review renderer summarizes scope, allowed actions, blockers, warnings,
and maintainer next steps. It is deterministic enough for tests and does not
post comments or mutate GitHub state.

## Issue Triage

Issue triage can classify open issues, propose labels, identify duplicates, and
draft maintainer notes. The MVP treats label mutation as outside scope; it
produces a report that a maintainer can apply manually.

Render the report locally:

```bash
iosk issue-triage --manifest examples/issue-triage-manifest.json --out reports/issue-triage.md
```

The issue triage renderer summarizes the issue query, allowed actions, draft
triage policy, blockers, warnings, and maintainer next steps. It does not apply
labels, edit milestones, assign issues, or post comments.

## Release Checklist

Release work can ask an AI coding agent to summarize merged PRs, draft release
notes, and prepare a readiness checklist. Creating a tag, publishing a release,
or changing package distribution settings should remain a separate explicit
approval.

## Security And Dependency Review

Security review must be limited to repositories the maintainer owns or is
authorized to administer. The MVP supports report-only review of dependency
files and workflow configuration. It does not probe external systems, read
secrets, or scan repositories outside the manifest.

## Suggested Agent Workflow Use

Useful report-only AI-assisted workflows include:

- summarizing pull request diffs and review risks,
- classifying issues and suggesting maintainer follow-up,
- drafting release notes and changelog sections,
- reviewing CI failures and dependency incidents,
- creating handoff reports between maintenance sessions,
- evaluating prompts and manifests against a small regression suite.

When using Codex, these are the reference workflows this project is built to
exercise first.

For an end-to-end synthetic example, see
[Synthetic maintainer workflow case study](synthetic-maintainer-case-study.md).

## Downstream Adapters

Maintainers can use this project from private downstream adapters without
publishing the adapter itself. The public core should remain generic: validate
the manifest, fail closed on risky actions, and produce reports. Local adapters
can add project-specific paths, storage, or review rituals, but those details
should stay outside this repository unless they can be safely generalized.

See [Downstream dogfooding](downstream-dogfooding.md) for the promotion
checklist used to decide which private findings should become public issues,
fixtures, docs, or PRs.

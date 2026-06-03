# Maintainer Workflows

This project is designed around everyday open source maintainer tasks where an
AI coding agent can help, but should remain inside a visible authorization
boundary.

## Pull Request Review

Use an approval manifest to scope the repository, pull request URL, allowed
read-only actions, and output location. The gate should allow only local review
reports and draft comments. It should not merge, approve, request changes, push
commits, or edit branch protection.

## Issue Triage

Issue triage can classify open issues, propose labels, identify duplicates, and
draft maintainer notes. The MVP treats label mutation as outside scope; it
produces a report that a maintainer can apply manually.

## Release Checklist

Release work can ask Codex to summarize merged PRs, draft release notes, and
prepare a readiness checklist. Creating a tag, publishing a release, or changing
package distribution settings should remain a separate explicit approval.

## Security And Dependency Review

Security review must be limited to repositories the maintainer owns or is
authorized to administer. The MVP supports report-only review of dependency
files and workflow configuration. It does not probe external systems, read
secrets, or scan repositories outside the manifest.

## Suggested API Credit Use

If selected for the Codex for OSS program, API credits would be used for:

- summarizing pull request diffs and review risks,
- classifying issues and suggesting maintainer follow-up,
- drafting release notes and changelog sections,
- reviewing CI failures and dependency incidents,
- creating handoff reports between maintenance sessions,
- evaluating prompts and manifests against a small regression suite.

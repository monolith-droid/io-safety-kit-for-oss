# Cross-Platform Dogfooding

This guide shows how a maintainer can use I/O Safety Kit for OSS from two
different downstream lanes without publishing private operational details.

The examples are synthetic. They describe reusable workflow shapes, not a real
machine, synced folder, private approval record, or local adapter.

## Why Split The Lanes

Downstream dogfooding tends to reveal two different kinds of lessons:

- an implementation lane, where a maintainer builds or refactors adapter logic,
  handoff files, and review reports;
- an operations lane, where a maintainer runs scheduled or repeated workflows
  and needs safe degraded reports when the local runner cannot execute.

Both lanes can improve the public project, but neither should copy private
state into this repository.

## Implementation Lane

Use this lane for Mac or Unix-like adapter work such as local script design,
handoff drafting, fixture shaping, and public-safe workflow extraction.

Recommended public-safe behavior:

- keep real synced folders, vault notes, host names, and account details out of
  public examples;
- use synthetic paths and synthetic repository names;
- keep adapter write tests candidate-only until the maintainer approves the
  exact target and rollback condition;
- record whether writes, external sends, scheduler changes, worker dispatch, and
  secret reads were performed;
- promote only the generic adapter lesson as a doc, fixture, test, or issue.

## Operations Lane

Use this lane for Windows or other operational hosts where a maintainer runs
repeatable report-only jobs, wrapper scripts, scheduled checks, or handoff
generation.

Recommended public-safe behavior:

- keep the public core report-only even if the private adapter uses a local
  scheduler;
- preserve `blockers`, `warnings`, and similar fields as arrays when wrapping
  `iosk --json` output;
- treat runner startup failures as observable workflow facts, not as proof that
  downstream checks ran;
- record degraded status without claiming fresh diagnostics;
- avoid reboot, driver update, registry edit, destructive cleanup, repository
  mutation, or external publishing in public examples.

## Shared Promotion Rules

Before turning either lane into a public contribution, check that:

- another OSS maintainer can understand the generalized problem;
- the example uses synthetic repositories, paths, approvals, and reports;
- side effects remain false or clearly outside the public core;
- private logs, transcripts, account details, approval IDs, service names, and
  local absolute paths are removed;
- the resulting artifact can be reviewed in CI as a doc, example, schema,
  fixture, or test.

Use `iosk promotion-check` for promoted findings that started in private
downstream work.

## Synthetic Report

The public fixture lives at:

- `examples/cross-platform-dogfooding-report.json`

It records two synthetic lanes:

- `implementation_lane`: adapter design and handoff extraction;
- `operations_lane`: report-only operations and degraded-runner handling.

Both lanes keep command execution, external publishing, scheduler mutation,
worker dispatch, and secret reads outside the public core. This makes the
dogfooding story reviewable without leaking private operational context.

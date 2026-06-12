# V1 Stability Notes

This page describes the stability boundary for the `v1.x` release line of I/O
Safety Kit for OSS.

## Primary CLI

`iosk` is the primary supported command name. New documentation, examples,
automation, and issue reports should use `iosk`.

Supported command surface:

- `iosk validate`
- `iosk gate`
- `iosk pr-review`
- `iosk issue-triage`
- `iosk promotion-check`
- `iosk signature-check`
- `iosk trust-policy-check`
- `iosk run`
- `iosk handoff`

The commands remain report-only by default through the v1 line.

## Legacy Aliases

`msk` and `cmsk` are compatibility aliases for early adopters and older local
adapters. They call the same implementation as `iosk`.

Compatibility expectations:

- Existing `msk` and `cmsk` invocations should keep working in the v1 line.
- New public docs, examples, and tests should use `iosk`.
- Any future removal of a legacy alias should require a later major release and
  a migration note.

## Safety Promise

The stable v1 safety model is:

- fail closed,
- report-only by default,
- no shell command execution from the core workflow,
- no secret reads,
- no repository mutation,
- no external publishing,
- no provider-specific signing service requirement,
- public examples must be synthetic and runnable from a fresh checkout.

Commands may render local JSON or Markdown reports. They should not merge pull
requests, post comments, apply labels, push branches, change repository
settings, tag releases, or publish generated output.

## Compatibility Promise

Within the v1 line, maintainers should be able to rely on:

- approval manifest validation and fail-closed gate semantics,
- blocked high-risk action fixtures,
- report-only PR review and issue triage rendering,
- promotion candidate privacy and evidence checks,
- signed manifest digest metadata checks,
- trust policy checks over public synthetic metadata,
- run report and handoff rendering,
- optional JSON Schema validation remaining optional.
- downstream adapters preserving machine-readable JSON fields such as blockers
  and warnings as arrays when wrapping `iosk --json` output.
- downstream dogfooding examples that keep implementation-lane and
  operations-lane lessons public-safe and synthetic.

The schema extra may provide stricter shape checks, but the standard-library
validators must continue to work without `jsonschema`.

## Non-Promises

The v1 line does not promise:

- automatic GitHub mutation,
- command execution,
- private signing provider integration,
- secret scanning,
- vulnerability scanning,
- downstream adapter support inside the public repository.

Those capabilities require separate design work and should preserve the same
fail-closed and report-only boundary unless a future major version explicitly
changes it.

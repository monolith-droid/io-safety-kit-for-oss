# Downstream Dogfooding

I/O Safety Kit for OSS is intended to be useful in real maintainer
workflows without requiring private projects to publish their internal
automation. The recommended pattern is a downstream adapter: a local wrapper
that uses this public core, stores local evidence, and keeps private policy
outside the OSS repository.

## Loop

1. Use the public `iosk` CLI from a private or organization-specific adapter.
2. Keep the adapter report-only unless a separate project policy explicitly
   allows execution.
3. Store local reports where the maintainer can review them.
4. Turn generic findings into public issues or tests.
5. Keep private paths, secrets, approval IDs, service names, and local operating
   details out of public artifacts.
6. Run `iosk promotion-check` before public promotion when the finding came from
   private or downstream work.

This lets maintainers improve the public tool from real work while preserving a
clear boundary between reusable OSS infrastructure and private operations.

## Adapter Boundary

A downstream adapter should not grant authority by itself. It should call the
public gate, record the result, and make the side-effect boundary obvious.

Recommended defaults:

- no shell command execution,
- no secret reads,
- no repository visibility changes,
- no protected branch mutation,
- no external publishing,
- no scheduled task changes,
- no worker dispatch,
- no implicit access to files outside the manifest scope.

If a local project needs stronger behavior, add it in the local adapter first,
then promote only the generic, well-tested part back to this repository.

## Adapter JSON Shape

Downstream adapters often wrap `iosk --json` output in a local report. Preserve
the public JSON shape when doing that. Fields such as `blockers`, `warnings`,
`check_ids`, `failed_check_ids`, `invalid_reference_targets`, and
`missing_reference_item_ids` should remain arrays even when they are empty.

This matters for CI and handoff tooling: an empty array means "checked and no
items were found"; `null` or an object-like value can make a wrapper report look
ambiguous.

For Windows PowerShell wrappers, normalize possibly empty values before
re-serializing:

```powershell
function New-JsonArray {
    param([object]$Value)

    if ($null -eq $Value) {
        return ,([object[]]@())
    }
    return ,([object[]]@($Value))
}

$upstream = iosk gate --manifest examples/pr-review-manifest.json --json |
    ConvertFrom-Json

$report = [ordered]@{
    status = $upstream.status
    passed = [bool]$upstream.passed
    blockers = New-JsonArray -Value $upstream.blockers
    warnings = New-JsonArray -Value $upstream.warnings
    command_executed = $false
}

$report | ConvertTo-Json -Depth 8
```

The adapter can add local metadata, but it should not change the meaning of the
core report fields. Keep local-only paths, approval records, and private policy
out of any public example derived from the adapter.

## Promotion Checklist

Before turning a downstream improvement into a public contribution, check that
it can be described without private context:

- Can the problem be understood by another OSS maintainer?
- Can the behavior be represented as a manifest, fixture, schema rule, renderer,
  or documentation page?
- Does the example avoid tokens, private transcripts, local absolute paths,
  organization names, and service-specific operations?
- Can CI verify the behavior?
- Does the change preserve report-only and fail-closed defaults?
- Does the promotion candidate include public-safe review evidence instead of
  private records?

When the answer is yes, open a public issue with the
`Dogfooding to public` issue template. The template asks for the public problem,
the generalized finding, the proposed artifact, safe extraction checks, and the
categories that must stay private.

Good promotion candidates:

- blocked-action fixtures,
- clearer gate warnings,
- schema validation improvements,
- report rendering for PR review or issue triage,
- handoff output formatting,
- public examples based on synthetic repositories.

Poor promotion candidates:

- private approval IDs,
- local runtime-state formats,
- organization-specific escalation rules,
- service credentials or token handling,
- adapter code that only makes sense in one private environment.

## Maintainer Signal

The goal of downstream dogfooding is not to claim broad adoption before it
exists. The goal is to show that the public OSS core is being exercised by real
maintenance workflows, with the resulting improvements converted into public,
reviewable issues, tests, documentation, and releases.

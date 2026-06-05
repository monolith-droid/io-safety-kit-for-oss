# Safe Output Promotion Loop

AI-assisted development needs not only safe input, but safe output.

I/O Safety Kit for OSS treats publication as a maintainer workflow.
Useful ideas can start in private downstream adapters, local automation, or
real project operations, but only the generic and privacy-safe part should
become public OSS.

## Loop

1. Discover a useful pattern in a real workflow.
2. Strip private context: secrets, tokens, personal details, local paths,
   approval IDs, transcripts, service names, and organization-specific policy.
3. Replace real data with synthetic examples or fixtures.
4. Check that another maintainer can understand the problem without private
   context.
5. Promote the output as a public issue, test, doc, example, schema, or small PR.
6. Release the generalized improvement.
7. Dogfood the public core again from downstream adapters.

This is the inverse of dependency intake. Instead of asking only "is this safe
to use?", the maintainer also asks "is this safe to publish?"

## CLI

Evaluate a promotion candidate:

```bash
iosk promotion-check --candidate examples/promotion-candidate.json --json
```

Render a local Markdown report:

```bash
iosk promotion-check --candidate examples/promotion-candidate.json --out reports/promotion.md
```

Add optional JSON Schema validation:

```bash
python -m pip install -e ".[schema]"
iosk promotion-check --candidate examples/promotion-candidate.json --schema --json
```

The command is report-only. It does not create issues, publish releases, push
branches, call external services, or inspect secret values.

## Promotion Candidate

A candidate should describe:

- where the idea came from,
- why it is useful to other maintainers,
- which public artifacts will be created,
- which privacy checks passed,
- which public-safe review evidence supports the decision,
- how it will be promoted through public review.

The candidate is ready only when private context has been removed and the
remaining artifact can be reviewed in a public issue or pull request.

For findings that came from downstream dogfooding, use the `Dogfooding to
public` issue template before opening a PR. The form keeps the public issue
focused on the generalized maintainer problem and the safety checks that made
the output publishable.

## Review Evidence

Review evidence is a small public-safe record of what the maintainer checked
before promotion. It should use roles and synthetic descriptions, not personal
names, private approval IDs, local paths, transcripts, or raw service records.

Each evidence check should have:

- an `id`,
- a `status` of `passed`,
- a short `evidence` note that another maintainer can read in public.

`promotion-check` fails closed when review evidence is missing, malformed,
empty, or marked as failed.

JSON output includes a `review_evidence` summary so maintainers and CI can see
the public-safe evidence record without parsing Markdown or exposing private
logs. The summary reports the evidence status, reviewed role, check count,
passed count, check ids, failed ids, missing evidence notes, missing id
positions, and malformed check count.

Promotion candidates can also include an optional `evidence_bundle`. A bundle
groups public-safe docs, examples, tests, schemas, issues, pull requests,
releases, or CI records into a portable review record. Bundle references should
point to public repository-relative paths or public URLs, not local absolute
paths, private approval records, transcripts, secrets, or provider credentials.
When a bundle is present, `promotion-check` reports bundle status, item count,
reference count, item ids, and invalid private-looking references.

When `--schema` is used and `jsonschema` is installed, JSON output also includes
`schema_validation` details for the public promotion candidate shape. The schema
checks structure only; the semantic promotion checks still enforce privacy,
generalization, report-only, and fail-closed rules.

## Blockers

The promotion check fails closed when a candidate still contains or depends on:

- secrets, tokens, passwords, or credentials,
- personal identity details,
- private transcripts,
- local absolute paths,
- private approval IDs,
- service-specific operations,
- organization-only policy,
- real data that should be synthetic,
- missing or failed public-safe review evidence,
- external publishing as part of the check itself.

## Maintainer Rule

If the output cannot be explained with synthetic examples and public context, do
not publish it yet. Keep it downstream, extract the general idea, and try again
with a smaller candidate.

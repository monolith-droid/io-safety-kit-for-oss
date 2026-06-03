# Safe Output Promotion Loop

AI-assisted development needs not only safe input, but safe output.

Codex Maintainer Safety Kit treats publication as a maintainer workflow. Useful
ideas can start in private downstream adapters, local automation, or real
project operations, but only the generic and privacy-safe part should become
public OSS.

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
cmsk promotion-check --candidate examples/promotion-candidate.json --json
```

Render a local Markdown report:

```bash
cmsk promotion-check --candidate examples/promotion-candidate.json --out reports/promotion.md
```

The command is report-only. It does not create issues, publish releases, push
branches, call external services, or inspect secret values.

## Promotion Candidate

A candidate should describe:

- where the idea came from,
- why it is useful to other maintainers,
- which public artifacts will be created,
- which privacy checks passed,
- how it will be promoted through public review.

The candidate is ready only when private context has been removed and the
remaining artifact can be reviewed in a public issue or pull request.

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
- external publishing as part of the check itself.

## Maintainer Rule

If the output cannot be explained with synthetic examples and public context, do
not publish it yet. Keep it downstream, extract the general idea, and try again
with a smaller candidate.

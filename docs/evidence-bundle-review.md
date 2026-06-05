# Evidence Bundle Review

Evidence bundles make safe output promotion portable. They group the public
docs, examples, tests, schemas, issues, pull requests, releases, or CI records
that support a promotion candidate without requiring private logs.

Use this guide before opening a public issue or pull request from downstream
dogfooding or other private maintainer work.

## Review Steps

1. Run the promotion check:

   ```bash
   iosk promotion-check --candidate examples/promotion-candidate.json --schema --json
   ```

2. Confirm the candidate passes with `status` set to
   `promotion_candidate_ready`.
3. Confirm `evidence_bundle.status` is `evidence_bundle_ready`.
4. Confirm every bundle item has a stable `id`, supported `kind`, short
   `summary`, and at least one public reference.
5. Check that every reference target is either a public URL or a repository
   relative path.
6. Check that the bundle supports the artifact being promoted: doc, example,
   test, schema, issue, pull request, release, or CI record.
7. Confirm the promotion remains report-only. The check must not create issues,
   push branches, tag releases, call external services, or publish output.

## Public-Safe References

Good references:

- `docs/safe-output-promotion-loop.md`
- `examples/promotion-candidate.json`
- `tests/test_promotion.py`
- `https://github.com/example-org/example-repo/pull/123`
- `https://github.com/example-org/example-repo/actions/runs/123456`

Do not include:

- local absolute paths,
- private approval IDs,
- private chat transcripts,
- raw service logs,
- secret names or values,
- provider credentials,
- organization-only policy,
- unpublished downstream adapter details.

## CI-Friendly Fields

Maintainers and CI should be able to inspect bundle readiness without parsing
private records. The JSON output exposes:

- `evidence_bundle.status`
- `evidence_bundle.bundle_id`
- `evidence_bundle.item_count`
- `evidence_bundle.reference_count`
- `evidence_bundle.item_ids`
- `evidence_bundle.invalid_references`

If `invalid_references` is not empty, do not publish the candidate. Rewrite the
bundle with public paths, public URLs, or synthetic fixtures and run the check
again.

## Review Outcome

Approve public promotion only when the bundle is understandable by another OSS
maintainer from public context alone. If the evidence still depends on private
state, keep it downstream and promote a smaller, safer artifact.

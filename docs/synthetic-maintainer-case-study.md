# Synthetic Maintainer Workflow Case Study

This case study shows how a maintainer can use I/O Safety Kit for OSS in an
AI-assisted maintenance loop without granting the agent write authority.

The repository, issues, pull requests, approvals, and outputs below are
synthetic. They are meant to demonstrate the workflow shape, not to document a
real project or private adapter.

## Scenario

An OSS maintainer of `example-org/synthetic-package` wants help with a routine
maintenance pass:

- review one pull request,
- triage a small set of open issues,
- prepare a release checklist,
- decide whether a downstream finding is safe to promote publicly.

The maintainer wants AI assistance for summaries and drafts, but does not want
the workflow to merge code, post comments, mutate labels, read secrets, or
publish anything automatically.

## Step 1: Declare Input Scope

The maintainer starts with approval manifests that describe the allowed scope.
For example:

- `examples/pr-review-manifest.json`
- `examples/issue-triage-manifest.json`
- `examples/release-checklist-manifest.json`

Each manifest describes the repository, operation, targets, allowed actions,
risk level, and approval state. Anything outside the manifest is out of scope.

Validate a manifest with the standard validator:

```bash
iosk validate --manifest examples/pr-review-manifest.json --json
```

Optionally add JSON Schema checks:

```bash
iosk validate --manifest examples/pr-review-manifest.json --schema --json
```

Then evaluate the fail-closed gate:

```bash
iosk gate --manifest examples/pr-review-manifest.json --json
```

## Step 2: Produce Report-Only Output

The maintainer asks for local reports, not GitHub mutation.

Render a PR review report:

```bash
iosk pr-review --manifest examples/pr-review-manifest.json --out reports/pr-review.md --json
```

Render an issue triage report:

```bash
iosk issue-triage --manifest examples/issue-triage-manifest.json --out reports/issue-triage.md --json
```

Both reports are deterministic local Markdown artifacts. They summarize scope,
allowed actions, blockers, warnings, and maintainer next steps. They do not post
comments, apply labels, assign issues, edit milestones, merge pull requests, or
push commits.

## Step 3: Run A Maintainer Job Plan

The maintainer can group report-only steps into a local job plan:

```bash
iosk run --job examples/maintainer-job.json --json
```

The job plan records what would be reviewed and which manifests are involved.
It keeps `command_executed` and `execution_allowed` false. This gives the
maintainer evidence for handoff and review without giving the tool execution
authority.

## Step 4: Keep Unsafe Actions Blocked

High-risk actions should fail closed even if a fixture claims approval. For
example:

```bash
iosk gate --manifest tests/fixtures/blocked_actions/read_secret.json --json
```

The gate reports a blocker for secret access. Similar fixtures cover force
pushes, repository visibility changes, and branch protection changes.

## Step 5: Promote Only Safe Public Output

Suppose the maintainer learns something useful from downstream dogfooding: a
report warning could be clearer for other OSS maintainers. Before opening a
public issue or PR, the maintainer strips private context and describes only the
generic pattern.

Check a promotion candidate:

```bash
iosk promotion-check --candidate examples/promotion-candidate.json --json
```

The candidate must avoid secrets, personal data, local paths, private approval
IDs, private transcripts, service-specific operations, organization-only policy,
real data that should be synthetic, and missing public-safe review evidence.

When the generalized finding is ready for public discussion, the maintainer can
open an issue with the `Dogfooding to public` issue template. That form asks for
the public problem, generalized finding, artifact type, proposed work, safe
extraction checks, and categories that must stay private.

## Result

The maintainer gets useful AI-assisted maintenance output while preserving the
project boundaries:

- input scope starts from explicit manifests,
- output remains local and reviewable,
- risky side effects fail closed,
- private downstream findings are generalized before publication,
- public improvements become issues, docs, fixtures, examples, or small PRs.

This is the intended loop for the public core: safe input, report-only output,
safe public promotion, and continued dogfooding without exposing private
operations.

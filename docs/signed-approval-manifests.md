# Signed Approval Manifests

This note sketches how I/O Safety Kit for OSS can support signed approval
manifests without making the core workflow depend on a specific signing
provider, secret store, or key format.

The current approval manifest is still treated as scope evidence, not as proof
of authorization by itself. A future signed manifest path should make that
evidence easier to verify while preserving the existing fail-closed behavior.

## Goals

- Let maintainers verify that the reviewed manifest is the same manifest an
  agent workflow used.
- Keep private keys, signing tokens, and provider credentials outside this
  repository and outside generated reports.
- Allow several signing backends later, such as Sigstore, GPG, SSH signing, or a
  project-specific approval service.
- Fail closed when a required signature is missing, malformed, expired,
  untrusted, or detached from the manifest content.

## What Is Signed

The signed payload is the approval manifest after canonicalization. The payload
should include at least:

- `schema_version`
- `operation`
- `repository`
- `requested_by`
- `reason`
- `risk_level`
- `allowed_actions`
- `targets`
- `command`, when present
- `approval`

The signature must bind the exact operation scope, allowed actions, targets,
approval status, approval time window, and repository identity. Verification
must fail if any signed field changes after approval.

Fields produced by report renderers, such as generated timestamps, report paths,
or local output locations, are not part of the signed manifest unless a future
schema version explicitly adds them.

## Where Signatures Live

The core workflow should avoid embedding private signing details in the
manifest. A future schema can support either of these public metadata shapes:

```json
{
  "signature": {
    "type": "detached",
    "algorithm": "provider-defined",
    "identity": "maintainer@example.com",
    "key_id": "public-key-or-certificate-reference",
    "payload_digest": "sha256:...",
    "signature_path": "approvals/pr-review-manifest.sig"
  }
}
```

```json
{
  "signature": {
    "type": "inline",
    "algorithm": "provider-defined",
    "identity": "maintainer@example.com",
    "key_id": "public-key-or-certificate-reference",
    "payload_digest": "sha256:...",
    "signature": "base64-or-provider-defined-public-signature"
  }
}
```

Detached signatures are preferred for repository workflows because the manifest
can remain readable and diffs stay small. Inline signatures can be useful for
single-file approvals, but they must still avoid secrets.

## Verification Flow

Verification starts as a separate report-only command:

```bash
iosk signature-check --manifest examples/signed-pr-review-manifest.json --json
iosk trust-policy-check \
  --manifest examples/signed-pr-review-manifest.json \
  --policy examples/trust-policy.json \
  --json
```

The current command verifies the provider-neutral portion of the design:
canonical payload generation, SHA-256 payload digest comparison, required public
signature metadata, and existing manifest validation. It does not verify a
cryptographic provider signature yet, and reports that explicitly.

The trust policy command checks the next provider-neutral layer: whether the
public signature identity and key reference are trusted for the repository,
operation, and risk level. A future provider-backed implementation can extend
this sequence:

1. Load and validate the approval manifest.
2. Canonicalize the signed subset of manifest fields.
3. Compute the payload digest.
4. Load the public signature metadata.
5. Resolve trusted public identity material from maintainer-configured policy.
6. Verify that the signature matches the digest and trusted identity.
7. Check approval status, expiry, operation match, blocked actions, and target
   scope with the existing fail-closed gate.

If signature verification is required by policy and cannot be completed, the
gate must block the workflow. If signatures are optional for a project, the CLI
may emit a warning while keeping the current unsigned manifest behavior.

## Trust Policy

Trust policy should stay outside the manifest. A signed manifest can say who
claims to have signed it, but a project policy decides whether that identity is
trusted for the requested operation.

A future policy file might define:

- trusted public identities or key references,
- operations each identity can approve,
- maximum approval lifetime,
- required number of signatures for high-risk operations,
- whether unsigned manifests are allowed for low-risk report-only workflows.

The current public fixture lives in `examples/trust-policy.json` and uses only
synthetic identity metadata. It does not contain private keys, tokens,
certificates, signing service URLs, or organization-specific policy.

## Fail-Closed Rules

Signed manifest support must block when:

- a signature is required but absent,
- the signature cannot be parsed,
- the payload digest does not match the manifest,
- the signing identity is not trusted by policy,
- the approval has expired,
- the manifest operation does not match the requested operation,
- the manifest includes blocked actions,
- a signed field was changed after approval.

The verifier should never read private keys or secrets. It should only consume
public signatures, public certificates or key references, local policy, and the
manifest content.

## Current Public Fixture

`examples/signed-pr-review-manifest.json` demonstrates detached signature
metadata without private key material. The manifest records:

- `type`: `detached`
- `algorithm`: `sha256-canonical-json-v1`
- `identity`: a synthetic maintainer identity
- `key_id`: a synthetic public fixture key
- `payload_digest`: the canonical approval manifest payload digest
- `signature_path`: a relative path to a synthetic `.sig` placeholder

The digest covers the approved manifest fields and intentionally excludes the
`signature` metadata itself. If a signed field such as `reason`, `targets`,
`allowed_actions`, or `approval` changes after approval, `iosk signature-check`
fails closed with `signature_payload_digest_mismatch`.

`examples/trust-policy.json` demonstrates the first policy layer. It permits the
synthetic `maintainer@example.invalid` identity and
`synthetic-public-fixture-key` key reference to approve selected low- or
medium-risk maintainer operations for this repository. `iosk trust-policy-check`
fails closed when:

- the manifest digest check fails,
- the repository does not match the policy,
- the signature identity or key id is not trusted,
- the operation is outside `allowed_operations`,
- the manifest risk level exceeds `max_risk_level`.

## Non-Goals

- This design does not choose a signing provider.
- This design does not introduce private keys, tokens, or signing services.
- This design does not make the core workflow execute approved commands.
- This design does not replace GitHub permissions, branch protection, code owner
  review, or maintainer judgment.

## Open Questions

- Should provider-backed signature verification live in `signature-check`,
  `trust-policy-check`, an option on `iosk gate`, or a combination of them?
- Should high-risk operations require multiple trusted signatures?
- How much richer can project policy become without making simple local use too
  heavy?

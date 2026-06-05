# Security Policy

## Supported Versions

Security fixes target the latest `v1.x` release and the default branch.
Pre-1.0 releases are retained for historical reference, but they are not a
supported security maintenance line.

## Reporting A Vulnerability

Please open a private security advisory on GitHub when available. If that is not
available, open an issue with a minimal description and avoid posting exploit
details, secret values, or private repository data.

## Scope

Relevant issues include:

- a gate allowing a blocked high-risk action,
- a manifest validation bypass,
- accidental secret disclosure,
- command execution despite report-only mode,
- misleading reports that claim execution happened when it did not.

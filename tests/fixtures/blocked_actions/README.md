# Blocked Action Fixtures

These fixtures intentionally contain high-risk actions. They should always make
`cmsk validate` and `cmsk gate` fail closed.

- `read_secret.json`
- `force_push.json`
- `change_visibility.json`
- `disable_branch_protection.json`

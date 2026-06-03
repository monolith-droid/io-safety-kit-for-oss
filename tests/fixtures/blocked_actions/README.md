# Blocked Action Fixtures

These fixtures intentionally contain high-risk actions. They should always make
`iosk validate` and `iosk gate` fail closed.

- `read_secret.json`
- `force_push.json`
- `change_visibility.json`
- `disable_branch_protection.json`

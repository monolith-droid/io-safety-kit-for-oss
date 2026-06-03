# Contributing

Thanks for considering a contribution. This project is early and intentionally
small; clear safety boundaries matter more than broad automation.

## Good First Contributions

- Improve example manifests.
- Add tests for blocked actions.
- Add maintainer workflow docs.
- Improve handoff report formatting.
- Add CI checks that do not require secrets.

## Safety Rules

- Do not add code that reads or prints secret values.
- Do not add command execution without a separate design issue and approval.
- Do not add workflows that mutate public GitHub state by default.
- Keep examples scoped to repositories the maintainer owns or controls.
- Prefer report-only behavior until a human maintainer applies the result.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -m compileall -q src tests
```

## Pull Requests

Please include:

- a short problem statement,
- the safety boundary affected by the change,
- tests or an explanation of why tests are not needed,
- sample CLI output when behavior changes.

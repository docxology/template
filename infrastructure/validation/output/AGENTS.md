# infrastructure/validation/output/ - Output Validation Documentation

## Purpose

The `infrastructure/validation/output/` package contains pipeline output validation and no-mock enforcement helpers.

## Files

- `validator.py` - output validation
- `pipeline.py` - pipeline output validation
- `no_mock_enforcer.py` - mock-usage checks (line-based scan; one-line `"""..."""` / `'''...'''` docstrings are skipped so policy docs can name forbidden APIs)

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)

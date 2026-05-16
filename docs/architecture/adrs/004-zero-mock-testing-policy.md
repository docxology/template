# ADR 004: Zero-Mock Testing Policy

## Status

Accepted

## Context

Testing research code with mocks hides bugs in data handling, file I/O, and integration boundaries. The template's goal is to ensure that passing tests mean the code actually works end-to-end with real data.

## Decision

**All tests must use real execution, temporary files, and pytest-httpserver. Mocking is forbidden.**

This policy applies to both `infrastructure/` and `projects/*/tests/` code.

### Alternatives Considered

| Approach | Verdict |
|----------|---------|
| Allow mocks for external APIs | Rejected — hides integration bugs; use pytest-httpserver instead |
| Allow mocks for slow computations | Rejected — use real data with pytest markers for slow tests |
| Allow `unittest.mock` in conftest only | Rejected — confuses test intent; fixture functions should return real data |

## Enforcement

- `scripts/verify_no_mocks.py` scans for `mock`, `MagicMock`, `patch`, `unittest.mock` in test files
- Reviewer checklist in `rules/AGENTS.md` includes "no mocks" verification
- Tests use `pytest-httpserver` for HTTP endpoints and `tempfile.TemporaryDirectory` for file I/O

## Consequences

### Positive

- Tests are realistic and catch integration issues
- Confidence in test results translates to confidence in production behavior
- No test drift between mocked and real behavior

### Negative

- Tests are more realistic but may be slower
- Requires real data fixtures or HTTP test fixtures
- Some tests may need network access (marked with `@pytest.mark.net`)

## References

- [`development/testing/`](../../development/testing/) — Test infrastructure utilities
- [`scripts/verify_no_mocks.py`](../../../scripts/verify_no_mocks.py) — Mock detection script
- [`development/testing/testing-guide.md`](../../development/testing/testing-guide.md) — Testing standards
- [`rules/AGENTS.md`](../../rules/AGENTS.md) — Development rules with no-mock clause
# Real Codebases

> Shallow-cloned GitHub repos used as integration test fixtures

## Contents

| Directory | Source Repository | Included Path |
|-----------|-------------------|---------------|
| `requests/` | [psf/requests](https://github.com/psf/requests) | `src/requests/` |
| `fastapi/` | [tiangolo/fastapi](https://github.com/tiangolo/fastapi) | `fastapi/` |

## Setup

```bash
python scripts/fixtures/download_real_codebases.py
```

Uses `--depth=1` and git sparse-checkout to minimize download size. Idempotent — skips already-downloaded repos.

Required before running integration tests marked `external_fixture` (see [`tests/integration/test_codebase_real.py`](../../integration/test_codebase_real.py)).

## See Also

- [Download Script](../../../scripts/fixtures/download_real_codebases.py) — How fixtures are fetched
- [Test Fixtures](../) — All fixture directories
- [Test Suite](../../README.md) — Full test documentation

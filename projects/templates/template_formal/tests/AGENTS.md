# `tests/` — Agent Guide

278 tests, one subdirectory per `src/template_formal/` subpackage. See
[`README.md`](README.md) for the full directory-to-responsibility map, the
mypy-oracle harness mechanics, and measured xdist timing.

## Contracts agents must honor

- **No mocks, ever.** No `MagicMock`/`mocker.patch`/`unittest.mock` anywhere
  in this directory. Real SQLite (`tmp_path`, never `:memory:` except through
  the explicitly test-only `storage.db.open_fast_test_database`), real
  `mypy --strict` subprocess calls, real `matplotlib` PNGs on disk.
- **New type-safety claim in `src/` → new mypy fixture.** If you add a claim
  of the form "mypy --strict rejects X" or "...accepts Y", add a
  `tests/mypy_fixtures/bad_*.py`/`good_*.py` fixture, and — for `bad_*.py` —
  a matching entry in `test_mypy_oracle.py`'s
  `_EXPECTED_BAD_FIXTURE_SUBSTRINGS` bound to the *literal* substring mypy
  emits (captured by actually running mypy against the fixture, not
  predicted). A `bad_*.py` fixture with no map entry raises `KeyError` by
  design — this is intentional, not a bug to silence.
- **Coverage floor is 90%, currently ~95.5%.** Run
  `uv run pytest tests -q --cov=src/template_formal --cov-report=term-missing`
  before treating a change as complete; a merge that drops coverage below
  90% fails CI.
- **The two heavy sweep test files are sequential by design.**
  `test_colony_convergence_statistics.py` and
  `test_colony_experiments_extended.py` each run hundreds of real trials in
  one test function. Do not try to "fix" their runtime by reaching for
  `pytest-xdist` — xdist parallelizes across test functions, not iterations
  inside one, so it cannot split these; see `README.md`'s xdist section for
  the actual measured numbers (not a projected/assumed speedup) and the one
  observed CPU-contention flake on the former wall-clock benchmark; the gate
  now measures process CPU time so scheduler contention is not a false failure.
- **A red run under `-n auto`/`-n 4` is not automatically a real failure.**
  Re-run serially before escalating — see `README.md` for why.

## Running tests

```bash
# From the project directory
uv run pytest tests -q

# With coverage
uv run pytest tests -q --cov=src/template_formal --cov-report=term-missing

# From the monorepo root (equivalent, see root CLAUDE.md)
uv run pytest projects/templates/template_formal/tests/ --cov=projects/templates/template_formal/src --cov-fail-under=90
```

## See also

- [`../src/template_formal/AGENTS.md`](../src/template_formal/AGENTS.md) —
  the honesty-line discipline these tests exist to enforce.
- [`../ISA.md`](../ISA.md) — ISC numbers cited throughout this suite's
  docstrings (ISC-1..92).

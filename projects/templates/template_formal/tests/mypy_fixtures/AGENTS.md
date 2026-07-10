# `tests/mypy_fixtures/` — Agent Guide

Fixture corpus for the mypy-as-oracle harness ([`../test_mypy_oracle.py`](../test_mypy_oracle.py)).
Files here are **never imported or executed** — they exist only to be
handed to `mypy --strict` as a subprocess target. See
[`README.md`](README.md) for the full fixture-to-ISC table and rationale.

## Contract

- **Naming is the discovery mechanism.** `test_mypy_oracle.py` globs
  `bad_*.py` and `good_*.py` — there is no manifest file to update. Get the
  prefix right or the fixture is invisible to the harness.
- **`bad_*.py` needs a dict entry, or it's a hard failure, not a silent
  pass.** Add the new file's expected error substring to
  `_EXPECTED_BAD_FIXTURE_SUBSTRINGS` in `test_mypy_oracle.py`, keyed by
  filename, captured from a real `mypy --strict` run against that exact
  file — never invented or copied from a similar-looking error.
- **`good_*.py` needs nothing extra** — `test_known_good_fixture_is_accepted_by_mypy_strict`
  picks it up automatically and requires exit code 0.
- **One illegal state per `bad_*.py` file.** Keep each fixture minimal and
  focused so the bound error substring can't drift onto an unrelated
  mypy complaint elsewhere in the same file.
- **Every fixture's module docstring must state the ISC it binds to**, and
  whether it has a paired runtime-guard test elsewhere in `tests/` (most
  `bad_*.py` fixtures do — grep for the fixture's filename across
  `tests/storage/`, `tests/agent/`, `tests/protocol/` before assuming one
  doesn't exist).
- **Do not add a fixture that only proves what `src/`'s own mypy run
  already proves.** The three `good_*.py` fixtures each close a specific,
  named blind spot (a generic type parameter or `Protocol` conformance
  `src/` never instantiates concretely) — a new `good_*.py` should state,
  in its docstring, which blind spot it closes, per that same pattern.

## When you touch `src/`

If a refactor changes which line first triggers a fixture's mypy error
(even without changing the underlying illegal-state claim), update the
bound substring in `_EXPECTED_BAD_FIXTURE_SUBSTRINGS` — don't loosen the
assertion to a generic `"error:"` check to make the test pass again. That
substring binding is the entire point of this harness (see the module
docstring in `test_mypy_oracle.py` and the repo-wide gotcha it encodes:
`gotcha-python-replace-silent-nomatch-unverified` — a check that can't fail
specifically isn't proving anything specifically).

## Running just this corpus

```bash
uv run pytest projects/templates/template_formal/tests/test_mypy_oracle.py -v
```

# Testing Philosophy: The Zero-Mock Standard

The Generalized Research Template strictly forbids mocking in
scientific/editorial validation. The prose-project test suite exemplifies
the standard: every check, every figure, every variable, and every script
is exercised against real Markdown, real BibTeX, real `tmp_path`
directories, and real subprocess invocation.

## Why Zero Mocks?

The prose project owns no algorithm of its own. Every line of `src/` is
either pure (config parsing, figure rendering, variable derivation, report
assembly) or a thin shell over `infrastructure/prose/` and
`infrastructure/reference/citation/`, which are themselves pure. There is
nothing legitimate to mock: tests can always pass real text and assert on
real outputs.

If you find yourself wanting to mock something, treat it as a signal: the
work probably belongs in `infrastructure/`, not in `src/`. Move it and
test the boundary directly.

## The Validation Suite

Files (`projects/template_prose_project/tests/`):

- `test_config.py` — covers `src/config.py` typed YAML loader (approximately 5 tests).
- `test_figures.py` — covers `src/figures.py` matplotlib renderers (approximately 6 tests).
- `test_manuscript_variables.py` — covers `src/manuscript_variables.py`
  substitution (approximately 9 tests).
- `test_pipeline.py` — covers `src/pipeline.py` checks and
  `run_prose_pipeline` (approximately 35 tests across `TestRunProsePipeline`,
  `TestCheckGradeLevel`, `TestCheckCitationDensity`, `TestBibliographyConsistency`,
  `TestCheckHeadings`, `TestCheckResult`, `TestLongSentenceThresholdWired`).
- `test_pipeline_integration.py` — runs the bundled `manuscript/` end-to-end
  against `run_prose_pipeline` (approximately 1 test).
- `test_report.py` — covers `src/report.py::write_review_report`
  (approximately 7 tests).
- `test_scripts.py` — invokes the three orchestrator scripts via
  `subprocess.run` (approximately 3 tests).

**Total: 66 collected tests** (run `pytest projects/template_prose_project/tests/
--collect-only -q | tail -1` for the live count).

Conftest: `projects/template_prose_project/tests/conftest.py` (sets
`MPLBACKEND=Agg`, adds `src/` to `sys.path`).
Configuration: `projects/template_prose_project/pyproject.toml`
(`fail_under = 70` locally; the root pipeline gates at 90).

## Coverage

The test suite achieves **100% line and branch coverage** on
`projects/template_prose_project/src/`:

```
Name                                                          Stmts   Miss Branch BrPart    Cover
-----------------------------------------------------------------------------------------------------------
projects/template_prose_project/src/__init__.py                   7      0      0      0  100.00%
projects/template_prose_project/src/config.py                    46      0      2      0  100.00%
projects/template_prose_project/src/figures.py                  102      0     14      0  100.00%
projects/template_prose_project/src/manuscript_variables.py      59      0     12      0  100.00%
projects/template_prose_project/src/pipeline.py                  81      0     14      0  100.00%
projects/template_prose_project/src/report.py                    67      0     28      0  100.00%
-----------------------------------------------------------------------------------------------------------
TOTAL                                                           362      0     70      0  100.00%
```

Run with full coverage report:

```bash
uv run pytest projects/template_prose_project/tests/ \
    --cov=projects/template_prose_project/src \
    --cov-report=term-missing \
    --cov-fail-under=90
```

The current 100% means there is a 10% buffer before the 90% gate is hit.
Do not consume the buffer unnecessarily. Do not delete tests to make a
coverage number work — fix the gap.

## Real Inputs, Real Outputs

Every test uses real artefacts:

- **Real Markdown.** Tests write `.md` files to `tmp_path` and pass them
  through `infrastructure.prose.analyze_manuscript`. No string-faking, no
  pre-built `ManuscriptReport` objects in production-path tests.
- **Real BibTeX.** Tests covering `_check_bibliography_consistency` write
  small but valid `.bib` files and parse them through
  `infrastructure.reference.citation.parse_bibfile`. This catches
  parser-level breakage that a mocked `BibDatabase` would hide.
- **Real `tmp_path`.** No test writes into the project's own `output/`
  tree; every filesystem operation is contained in pytest's
  `tmp_path` fixture.
- **Real subprocess.** `tests/test_scripts.py` invokes
  `scripts/run_prose_pipeline.py` and `scripts/y_generate_prose_figures.py`
  via `subprocess.run`, with real argparse, real exit codes, and real
  output-file existence checks.

## Integration Test

`tests/test_pipeline_integration.py::test_bundled_manuscript_runs` is the
end-to-end fixture: it copies the project's own `manuscript/` directory
into a temporary location, runs `run_prose_pipeline` against it, and
verifies that `manuscript_report.json`, `checks.json`, `review_report.md`,
and `run_summary.json` all land in the expected locations. The assertion
target is structural — file existence and shape — rather than exact value,
so the test is stable across editorial revisions of the bundled manuscript.

## Zero-Mock Checklist

Before submitting any test, verify all boxes are checked:

- [ ] Test uses real Markdown strings or `.md` files written to `tmp_path`.
- [ ] Test calls `src/` functions with real `ManuscriptReport`,
  `BibDatabase`, or `ProjectConfig` objects produced by infrastructure
  or by `src/config.py::load_project_config`.
- [ ] Test asserts on properties (passed/failed checks, file existence,
  field values), not on call counts.
- [ ] No `unittest.mock`, `MagicMock`, `create_autospec`, `@patch`, or
  `monkeypatch` used as a mock factory.
- [ ] Subprocess tests assert on exit codes and on the contents of files
  written by the script.

## Structural Rule: If You Need a Mock, Move the Code

The zero-mock constraint is self-enforcing when the architecture is correct:

- **`src/config.py`, `src/manuscript_variables.py`, `src/figures.py`,
  `src/report.py`** — pure modules → testable with real data.
- **`src/pipeline.py`** — orchestrates `infrastructure.prose` and
  `infrastructure.reference.citation` → testable with real Markdown and
  real BibTeX in `tmp_path`.
- **`scripts/*.py`** — CLI shims → tested via `subprocess.run` in
  `tests/test_scripts.py`.

If you find yourself wanting to mock `analyze_manuscript`, `parse_bibfile`,
or any I/O inside a test, stop. Either pass it real data, or move the
work behind a configuration knob and test both branches with real inputs.

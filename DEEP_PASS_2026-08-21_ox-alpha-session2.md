# Deep Assessment + Improvement Pass — session 2 (ox-alpha, 2026-08-21)

Independent second-pass assessment executed in a checkout already carrying
several same-day deep-pass reports. This report records only what **this
session** measured and changed. All commands were run with `uv run` on
macOS 26.6.2 / Python 3.14 / TeX Live 2026.

## Executive summary

Repository health is strong. Every static gate measured clean this session:

| Gate | Result |
| --- | --- |
| `ruff check infrastructure/ scripts/` | pass (all checks passed) |
| `mypy` on `public_scope source-paths` | pass — 0 issues in 1,559 files |
| `bandit -c bandit.yaml -r infrastructure/ scripts/` | pass — no findings |
| `verify_no_mocks.py` | pass — 25 test roots, 1,189 files, no prohibited mocks |
| `check_tracked_all.py` (projects/fonds/rules/tools) | clean |
| `check_tracked_generated_artifacts.py` | pass |
| `check_tracked_secrets.py` | pass — no high-confidence credentials in tracked blobs |
| `lint_docs.py` cross-links / consistency / doc-pairs | 0 / 0 / 0 issues |
| `infrastructure.skills check` | ok |
| `check_template_drift.py --strict` | no drift |
| `pytest tests/infra_tests/core/` | 1,830 passed, 2 failed (timeout flakes; independently re-verified green) |
| `pytest tests/infra_tests/rendering/ -m "not requires_latex"` | 1,350 passed, 3 failed (2 environment, 1 timeout bug — fixed) |

TODO debt: no unresolved TODO/FIXME/XXX markers in `infrastructure/` or
`scripts/` source (all grep hits are docstrings or the repo's own backlog
tooling).

## Findings and dispositions

### Minor

**M1. Test-mode xelatex timeout too tight (FIXED — this session).**
`infrastructure/rendering/_pdf_latex_pipeline.py:241` hard-capped xelatex at
8 s under `PYTEST_CURRENT_TEST`. On this machine a bare xelatex cold run takes
~3.7 s, so the real pandoc-to-bibtex-to-multipass bibliography pipeline
(`test_pdf_renderer_fixes.py::TestCitationProcessing::test_render_combined_includes_bibliography`,
whose own class budget is `@pytest.mark.timeout(90)`) exceeded 8 s
deterministically, even in isolation. Fix: raise the pytest-mode ceiling to
60 s (production unchanged at 600 s), with a comment explaining the bound.
Verified: the failing test alone now passes (27.3 s real render).

**M2. Mermaid test/doc failures were local-environment breakage (FIXED in
environment, no repo change needed).** `mmdc` could not launch anywhere:
puppeteer's pinned Chrome 131.0.6778.204 was missing from
`~/.cache/puppeteer`. This produced 8 doc-lint "mermaid failed (exit 124)"
lines in `.github/README.md` and 2 test failures in
`tests/infra_tests/rendering/test_mermaid_figure.py` (90 s timeouts). After
`npx puppeteer browsers install chrome-headless-shell@131.0.6778.204`, all 5
mermaid tests pass (62 s); the mermaid syntax itself was never at fault.
Note for future sessions: mermaid failures that time out (rather than error
on syntax) should first be checked against `~/.cache/puppeteer` state.

**M3. Concurrent-suite resource contention inflates subprocess timeouts
(observed, no code change).** Running the core and rendering suites
simultaneously on one machine caused cross-timeouts in both. The two
`test_cli.py` subprocess failures seen in the combined run had already been
fixed by another session (commit `ea45a1935` plus uncommitted `test_cli.py`
edits raising budgets to 300 s / class timeout 700 s). This session
independently verified: `TestCLISubprocess` — 4 passed in 16.4 s.

### Medium

**MED1. `counts.py --check` reports stale coverage provenance for
`template_active_inference` (source hash changed; rerun its coverage gate,
then refresh provenance).** Not fixed here: refreshing requires re-running
the project's coverage gate, and the checkout's
`projects/templates/template_active_inference/output/` tree carries
uncommitted changes from another active session. Deferred to avoid racing
that work; the check correctly fails closed.

### Major (scoped, not implemented)

**MAJ1. Per-test default `timeout = 10` in `pyproject.toml` is below the
real cost of many legitimate subprocess tests.** Individual suites work
around it with per-class `@pytest.mark.timeout(...)` overrides (60-700 s),
which is fragile: any new subprocess test silently inherits a 10 s ceiling.
Approach: raise the default via a tiered scheme (e.g. 60 s default, explicit
marks for long lanes), sweep existing per-class overrides for contradictions,
and run the full infra suite serially plus under `-n 2`. Effort: ~0.5-1 day
including the sweep. Risks: masking genuinely hung tests; slower CI feedback
on real hangs. Acceptance: full `tests/infra_tests/` passes serially and with
`-n 2`; no test's effective budget is reduced;
`scripts/maintenance/benchmark_tests.py` manifests stay green.

**MAJ2. Rendering test suite wall time (~15 min for one package) makes the
full gate expensive locally.** The rendering package alone took 900 s
unloaded. Approach: profile the slowest renders (the durations report already
surfaces them), split LaTeX-heavy tests into a marked lane with the same
opt-in discipline as `requires_ollama`, and cache pandoc intermediates where
determinism permits. Effort: 1-2 days. Risks: reduced default-lane coverage;
cache invalidation bugs. Acceptance: rendering suite median wall time halved
with zero change in selection semantics; coverage floor unchanged.

## What this session changed

- `infrastructure/rendering/_pdf_latex_pipeline.py` - pytest-mode xelatex
  timeout 8 s -> 60 s (M1).
- `DEEP_PASS_2026-08-21_ox-alpha-session2.md` - this report.
- Environment (not committed): installed puppeteer chrome-headless-shell
  131.0.6778.204 to repair `mmdc`.

## Verification record

- `pytest tests/infra_tests/rendering/test_mermaid_figure.py -q` -> 5 passed.
- `pytest "tests/infra_tests/rendering/test_pdf_renderer_fixes.py::TestCitationProcessing" -q` -> 1 passed (27.3 s).
- `pytest "tests/infra_tests/core/test_cli.py::TestCLISubprocess" -q --timeout=800` -> 4 passed (16.4 s).
- All static gates in the table above, measured this session, exit 0.

## Handoff notes

- The checkout is shared: several other deep-pass sessions committed during
  this one (e.g. `cb1db305b`, `ea45a1935`). This session's commits are
  path-scoped to their own files only; the dirty
  `projects/templates/template_active_inference/output/` and
  `docs/_generated/coverage_snapshot.json` changes belong to another session
  and were not touched.
- MED1 (stale coverage provenance) should be closed by whichever session owns
  the active_inference rerun.

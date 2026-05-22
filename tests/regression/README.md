# `tests/regression/` — pinned numerical outputs for manuscript claims

> Created 2026-05-20. See [`docs/maintenance/regression-testing.md`](../../docs/maintenance/regression-testing.md) for the full philosophy and rationale.

## TL;DR

Every quantitative claim in a manuscript — coefficient, p-value, effect size, count, percentage, ratio — has a corresponding pinned regression test here that:

1. Re-derives the value from the deterministic pipeline (same code, same data, same seed)
2. Compares against a pinned ground-truth value in [`pinned_values/`](pinned_values/)
3. Fails loudly if the value drifts beyond documented tolerance

This is **different from coverage** — coverage tells you "the code ran"; regression tests tell you "the science is still the science."

## Layout

```
tests/regression/
├── README.md                          (this file)
├── __init__.py
├── conftest.py                        (shared fixtures)
├── projects/
│   ├── template_code_project/
│   │   ├── __init__.py
│   │   ├── figures/                   (one test file per manuscript figure)
│   │   └── tables/                    (one test file per manuscript table)
│   └── template_prose_project/
│       ├── __init__.py
│       ├── figures/
│       └── tables/
└── pinned_values/                     (committed ground-truth values)
    ├── template_code_project.json
    └── template_prose_project.json
```

## Running

```bash
# Run all regression tests
uv run pytest tests/regression/ -v

# Run regression tests for one project
uv run pytest tests/regression/projects/template_code_project/ -v

# Run a specific figure or table
uv run pytest tests/regression/projects/template_code_project/figures/test_figure_03_panel_b.py -v
```

These tests are deliberately **not gated by the 90% coverage floor** — they are a *separate* signal. The coverage floor checks code execution; these check scientific claim integrity. Both matter; neither replaces the other.

## Adding a new regression case

1. Identify the value in the manuscript.
2. Trace it to its producing function in `projects/<name>/src/` or `.../scripts/`.
3. Re-run the pipeline with `--deterministic`; capture the output value.
4. Add the entry to `pinned_values/<project>.json`.
5. Write the test file (see template below).
6. Open a PR. CI will fail until the new test passes.

## Test file template

See [`projects/template_code_project/figures/test_figure_TEMPLATE.py`](projects/template_code_project/figures/test_figure_TEMPLATE.py) for a worked example.

## Pinned-values JSON schema

```json
{
  "<unique_id>": {
    "manuscript_section": "<file>.md / <section> / <figure or table ref>",
    "claim_text": "<the actual sentence from the manuscript that names the value>",
    "value": <number>,
    "abs_tolerance": <number>,        (use abs_tolerance OR rel_tolerance, not both)
    "rel_tolerance": <number>,
    "verifier_function": "<dotted.path.to.function>",
    "verifier_args": {<kwargs>},
    "pinned_on": "YYYY-MM-DD",
    "pinned_by": "<name>",
    "pinned_at_commit": "<git hash>"
  }
}
```

## Status

**Scaffold only as of 2026-05-20.** No pinned cases yet. See [`STATUS.md`](../../STATUS.md) row "Regression tests" — health 🔴.

Next step: pin the quantitative claims in both canonical exemplar manuscripts.

## Related

- [`docs/maintenance/regression-testing.md`](../../docs/maintenance/regression-testing.md) — full philosophy
- [`docs/maintenance/stage-10-executable-bundle.md`](../../docs/maintenance/stage-10-executable-bundle.md) — the executable-bundle manifest reads from `pinned_values/`
- [`MAINTAINERS.md`](../../MAINTAINERS.md) — `tests/regression/` owner

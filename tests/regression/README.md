# `tests/regression/` — pinned numerical outputs for manuscript claims

> Created 2026-05-20. See [`docs/maintenance/regression-testing.md`](../../docs/maintenance/regression-testing.md) for the full philosophy and rationale.

## TL;DR

Every quantitative claim in a manuscript that is eligible for deterministic
regression binding — coefficient, p-value, effect size, count, percentage, or
ratio — is either represented by a pinned regression test here or explicitly
classified in `claim_bindings.json` as `not_applicable` or `external_data`.
Bound claims:

1. Re-derives the value from the deterministic pipeline (same code, same data, same seed)
2. Compares against a pinned ground-truth value in [`pinned_values/`](pinned_values/)
3. Fails loudly if the value drifts beyond documented tolerance

This is **different from coverage** — coverage tells you "the code ran"; regression tests tell you "the science is still the science."

`claim_bindings.json` is the roster-level receipt consumed by
`scripts/audit/check_claim_bindings.py`. Every canonical public exemplar must
declare `bound`, `external_data`, or `not_applicable`; omission is a gate
failure. Bound pins carry manuscript location, verifier producer,
inputs/configuration, tolerance, revision, date, and a provenance rationale.
The explicit non-bound states prevent a scaffold or external-data lane from
being promoted by an accidental empty collection.

## Layout

```
tests/regression/
├── README.md                          (this file)
├── __init__.py
├── conftest.py                        (shared fixtures)
├── projects/
│   ├── template_code_project/
│   │   └── tables/test_optimization_results_claims.py
│   └── ...                             (one isolated lane per bound exemplar)
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

See [`tests/regression/projects/template_code_project/figures/test_figure_TEMPLATE.py`](./projects/template_code_project/figures/test_figure_TEMPLATE.py) for a worked example.

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

## Current status

The roster-level inventory is complete for the 24 canonical public exemplars.
It currently records 15 bound lanes and 9 explicit `not_applicable` lanes;
there are no `external_data` lanes. Re-derive the live result with:

```bash
uv run pytest tests/regression/ --collect-only -q --no-cov
uv run pytest tests/regression/ -q --no-cov
uv run python scripts/audit/check_claim_bindings.py --json
```

The inventory is intentionally separate from coverage. A project can remain
`not_applicable` while its structural, provenance, or visual claims are tested
by its own project suite; promoting it to `bound` requires a source-derived
pin, producer, manuscript location, tolerance, revision, and mutation control.

## Related

- [`docs/maintenance/regression-testing.md`](../../docs/maintenance/regression-testing.md) — full philosophy
- [`docs/maintenance/stage-10-executable-bundle.md`](../../docs/maintenance/stage-10-executable-bundle.md) — the executable-bundle manifest reads from `pinned_values/`
- [`MAINTAINERS.md`](../../MAINTAINERS.md) — `tests/regression/` owner

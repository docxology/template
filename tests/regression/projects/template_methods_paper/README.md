# `tests/regression/projects/template_methods_paper/` — regression suite

> Pinned numerical regression tests for `template_methods_paper`
> manuscript values. Loads ground truth from
> [`../../pinned_values/template_methods_paper.json`](../../pinned_values/template_methods_paper.json).

## Layout

- `tables/` — one test file per manuscript table/section (currently the
  compiled-plan summary, validation-gate tally, and provenance-chain
  claims in `03_results.md`)

Each value is re-derived by calling the real `src/methods_dsl`
functions (`compile_method`, `run_all_gates`, `demo_chain_report`) on
the two shipped worked example methods — never copied from the
manuscript. See [`../../README.md`](../../README.md) for the philosophy.

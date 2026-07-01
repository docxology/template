# `tests/regression/projects/template_active_inference/` — regression suite

> Pinned numerical regression tests for `template_active_inference`
> manuscript values. Loads ground truth from
> [`../../pinned_values/template_active_inference.json`](../../pinned_values/template_active_inference.json).

## Layout

- `tables/` — one test file per manuscript claim group (currently the
  analytical mutual-information sweep and free-energy claims in
  `10_results_mi_sweep.md`, `11_results_free_energy.md`, and
  `05_methods_analytical.md`)

## Scope note

The exemplar is multi-track (analytical + pymdp + sheaf +
Lean/GNN/ontology). The pins here bind the **analytical** track only —
the closed-form Bernoulli/Ising toy that needs numpy + scipy but not
`jax`/`pymdp` — so the tests re-derive from source under the repo root
`.venv` (which does not carry `jax`/`pymdp`) and pass together with the
other exemplars' regression tests. See
[`../../README.md`](../../README.md) for the philosophy.

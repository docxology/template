# `tests/regression/projects/template_template/` — regression suite

> Pinned numerical regression tests for `template_template`
> manuscript values. Loads ground truth from
> [`../../pinned_values/template_template.json`](../../pinned_values/template_template.json).

## Layout

- `tables/` — one test file per manuscript claim group (currently the
  self-introspection metrics injected across the abstract, introduction,
  architecture, results, and appendix sections: the frozen `pipeline.yaml`
  DAG stage counts, the confidentiality-invariant public exemplar roster
  count, and the live `infrastructure/` module count)

This exemplar is the autopoietic meta-template: it introspects the LIVE
repository and injects the numbers into its own manuscript as `${token}`
values. The pins therefore split into two stability tiers — frozen
structural counts (pipeline DAG, roster) at tolerance 0, and the live
`module_count` at an `abs_tolerance` band that tolerates organic repo
growth while still failing on a broken discovery.

See [`../../README.md`](../../README.md) for the philosophy.

# `template_active_inference` — analytical-track regression tests

> One file per manuscript claim group. Re-derives each value via the
> project's deterministic closed-form Bernoulli/Ising analytical track
> (`src/analytical/*`, numpy + scipy, no sampling) and compares to the
> pinned ground truth in
> [`../../../pinned_values/template_active_inference.json`](../../../pinned_values/template_active_inference.json).

Claims pinned: MI-sweep grid size, `lambda_max`, saturation mutual
information, closed-form-vs-total-correlation agreement residual, and
the free-energy argmin `lambda` — all from
`10_results_mi_sweep.md`, `11_results_free_energy.md`, and
`05_methods_analytical.md`.

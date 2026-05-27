# Limitations and extensions

<!-- sheaf-track:prose -->

**Limitations.** The Bernoulli–Ising toy and T-maze harness are pedagogical — they validate pipeline wiring, not empirical claims about biological agents. Default pymdp mode is `state_inference` with planning horizon 2; full policy inference remains an opt-in extension.

**Sheaf audit.** The coverage heatmap and appendix 9-track proof make binding state auditable: 42 present / 42 bound / 0 missing cells across 16 manifest rows. Strict compose validation fails on gray cells so downstream PDF rendering inherits an honest matrix.

**Extensions.** Opt-in pipeline extensions in `tracks.yaml` `extension_tracks` (belief GIF via `render_animation.py`, graph-world SI stub) add artifacts outside the default analysis DAG. The default IMRAD manifest already binds an `animation` **sheaf fragment** on the appendix row; extension scripts are for richer media, not extra manifest rows. Promote a private project by copying the sheaf manifest pattern under `manuscript/sections/imrad/`.

<!-- sheaf-track:simulation -->

Measured pymdp rollout (`state_inference`, config hash `ea4b126a9c22f22f`): mean belief entropy 0.3251 nats over 2 steps; goal reached flag 1; action diversity 2.

Analytical sweep residual RMSE 0 nats (max residual 0). Coverage audit: 42 present / 42 bound / 0 missing cells on the IMRAD matrix.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `coverage_semantics` → **Coverage matrix semantics**
- `pedagogical_scope` → **Pedagogical scope**
- `state_inference_mode` → **State inference harness**


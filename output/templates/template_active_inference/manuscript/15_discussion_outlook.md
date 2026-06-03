```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Discussion}
\section*{Discussion}
```

# Limitations and outlook {#sec:discussion_outlook}

<!-- sheaf-track:prose -->

## What this demonstrates

The result of this manuscript is a *discipline*, not a domain claim: across three toy models every reported number is hydrated from a generated artifact, 6 sheaf axioms are machine-checked before composition, and 22 negative controls keep each failure path live. No statistic, figure, or cross-track claim here can drift from its artifact without failing a gate before the PDF is built.

## Limitations

The Bernoulli–Ising toy, T-maze harness, and sheaf composition model are pedagogical. They validate analytical consistency, artifact wiring, renderer dispatch, and manuscript hydration—not empirical claims about biological agents. Default pymdp mode is `state_inference` with planning horizon 2; the policy-comparison artifact exposes policy-inference rows without changing the default rollout ([@sec:methods_pymdp]).

## Sheaf audit and outlook

[@sec:sheaf_coverage] and [@sec:appendix_full_sheaf] make binding state auditable under strict compose validation ([@sec:methods_sheaf]). Pipeline extensions in `tracks.yaml` `extension_tracks` now write deterministic artifacts: a belief GIF via `render_animation.py` and graph-world SI summary/trace via `simulate_si_graph_world.py`. The appendix row already binds an `animation` sheaf fragment without new manifest rows.

Sweep RMSE 0 nats and SI goal reached 1 summarize measured agreement on the declared grids and rollout. Future work includes full expected-free-energy policy selection, richer graph-world rollouts, and expanded Lean proofs beyond the boundary witnesses in [@sec:methods_lean].

The discussion ontology binds `coverage_semantics` to the audit matrix in [@sec:sheaf_coverage], `pedagogical_scope` to the non-empirical scope of the toy models, and `state_inference_mode` to the pymdp harness contract in [@sec:methods_pymdp].

<!-- sheaf-track:simulation -->

Measured pymdp rollout (`state_inference`, config hash `81eb061f43b7bfd7`): mean belief entropy 0.3251 nats over 2 steps; goal reached flag 1; action diversity 2.

Analytical sweep residual RMSE 0 nats (max residual 0). Coverage audit: 90 present / 90 bound / 0 missing cells on the IMRAD matrix.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `coverage_semantics` → **Coverage matrix semantics**
- `pedagogical_scope` → **Pedagogical scope**
- `state_inference_mode` → **State inference harness**


<!-- sheaf-track:release_notes -->

### Release notes evidence track

The `release_notes` track keeps release-language claims source-backed by
validation, semantic, and bundle artifacts. Its evidence artifact is
`output/reports/release_notes_evidence.json`: it currently records
3 rows, with source-backed status
`true`.

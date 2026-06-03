```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Discussion}
\section*{Discussion}
```

# Limitations and outlook {#sec:discussion_outlook}

<!-- sheaf-track:prose -->

## What this demonstrates

The result of this manuscript is a *discipline*, not a domain claim: across three toy models every reported number is hydrated from a generated artifact, {{sheaf_law_count}} sheaf axioms are machine-checked before composition, and {{counterexample_count}} negative controls keep each failure path live. No statistic, figure, or cross-track claim here can drift from its artifact without failing a gate before the PDF is built.

## Limitations

The Bernoulli–Ising toy, T-maze harness, and sheaf composition model are pedagogical. They validate analytical consistency, artifact wiring, renderer dispatch, and manuscript hydration—not empirical claims about biological agents. Default pymdp mode is `{{pymdp_mode}}` with planning horizon {{si_tmaze_policy_len}}; full policy inference remains an opt-in extension ([@sec:methods_pymdp]).

## Sheaf audit and outlook

[@sec:sheaf_coverage] and [@sec:appendix_full_sheaf] make binding state auditable under strict compose validation ([@sec:methods_sheaf]). Opt-in pipeline extensions in `tracks.yaml` `extension_tracks` (belief GIF via `render_animation.py`, graph-world SI stub) add artifacts outside the default analysis DAG; the appendix row already binds an `animation` sheaf fragment without new manifest rows.

Sweep RMSE {{sweep_rmse_mi}} nats and SI goal reached {{si_goal_reached}} summarize measured agreement on the declared grids and rollout. Future work includes full expected-free-energy policy selection, richer graph-world rollouts, and expanded Lean proofs beyond the boundary witnesses in [@sec:methods_lean].

The discussion ontology binds `coverage_semantics` to the audit matrix in [@sec:sheaf_coverage], `pedagogical_scope` to the non-empirical scope of the toy models, and `state_inference_mode` to the pymdp harness contract in [@sec:methods_pymdp].

<!-- sheaf-track:simulation -->

Measured pymdp rollout (`{{pymdp_mode}}`, config hash `{{pymdp_config_hash}}`): mean belief entropy {{si_tmaze_mean_belief_entropy_formatted}} nats over {{si_tmaze_steps}} steps; goal reached flag {{si_goal_reached}}; action diversity {{si_action_diversity}}.

Analytical sweep residual RMSE {{sweep_rmse_mi}} nats (max residual {{sweep_max_residual}}). Coverage audit: {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing cells on the IMRAD matrix.

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
{{release_notes_row_count}} rows, with source-backed status
`{{release_notes_source_backed}}`.

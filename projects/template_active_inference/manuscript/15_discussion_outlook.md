# Limitations and extensions

<!-- sheaf-track:prose -->

**Limitations.** The Bernoulli–Ising toy and T-maze harness are pedagogical — they validate pipeline wiring, not empirical claims about biological agents. Default pymdp mode is `{{pymdp_mode}}` with planning horizon {{si_tmaze_policy_len}}; full policy inference remains an opt-in extension.

**Sheaf audit.** The coverage heatmap and appendix {{appendix_sheaf_track_count}}-track proof make binding state auditable: {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing cells across {{imrad_manifest_rows}} manifest rows. Strict compose validation fails on gray cells so downstream PDF rendering inherits an honest matrix.

**Extensions.** Opt-in pipeline extensions in `tracks.yaml` `extension_tracks` (belief GIF via `render_animation.py`, graph-world SI stub) add artifacts outside the default analysis DAG. The default IMRAD manifest already binds an `animation` **sheaf fragment** on the appendix row; extension scripts are for richer media, not extra manifest rows. Promote a private project by copying the sheaf manifest pattern under `manuscript/sections/imrad/`.

<!-- sheaf-track:simulation -->

Measured pymdp rollout (`{{pymdp_mode}}`, config hash `{{pymdp_config_hash}}`): mean belief entropy {{si_tmaze_mean_belief_entropy_formatted}} nats over {{si_tmaze_steps}} steps; goal reached flag {{si_goal_reached}}; action diversity {{si_action_diversity}}.

Analytical sweep residual RMSE {{sweep_rmse_mi}} nats (max residual {{sweep_max_residual}}). Coverage audit: {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing cells on the IMRAD matrix.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `coverage_semantics` → **Coverage matrix semantics**
- `pedagogical_scope` → **Pedagogical scope**
- `state_inference_mode` → **State inference harness**


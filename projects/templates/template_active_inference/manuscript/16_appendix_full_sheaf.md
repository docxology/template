```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Appendix}
\section*{Appendix}
```

# Appendix: full track coverage {#sec:appendix_full_sheaf}

<!-- sheaf-track:prose -->

This section is the **composability proof** for the manifest-indexed sheaf model: all {{appendix_sheaf_track_count}} appendix-bound fragment tracks render into one flat manuscript section without section-specific compose branches. The registry defines {{sheaf_track_count}} composable types; optional `layers` is methods-only and excluded from this row. The `animation` fragment is bound here as an optional registry type alongside prose, formalism, simulation, pymdp, visualization, lean, gnn, and ontology tracks.

The proof is a publication-systems check ([@eq:appendix_track_count]). It demonstrates that heterogeneous fragments share one registry, manifest, renderer dispatch path, coverage matrix, and hydration boundary; it does not assert that every track carries equal scientific weight.

<!-- sheaf-track:formalism -->

For each track $t \in \mathcal{T}_{\mathrm{Full}}$, the appendix row binds a fragment path $f(t)$ and the composer emits `<!-- sheaf-track:t -->` before the rendered body. Generated renderers such as `section_figures` and markdown renderers pass through the same `resolve_track_body()` dispatch, so the appendix exercises the common compose interface rather than a bespoke appendix path.

$$
|\mathcal{T}_{\mathrm{Full}}| = {{appendix_sheaf_track_count}}
$$ {#eq:appendix_track_count}

The fragment registry defines {{sheaf_track_count}} composable track types; optional `layers` is bound on the methods sheaf section only. Optional `animation` is bound in this appendix proof; the opt-in GIF extension in `tracks.yaml` `extension_tracks` is separate from this fragment slot.

Because this appendix binds every non-optional track plus both optional tracks, it is the maximal stalk of the coverage presheaf and exercises every renderer through the common `resolve_track_body()` dispatch. The same compose path is gated by the {{sheaf_law_count}} sheaf laws verified in [@sec:methods_sheaf] ({{sheaf_laws_verified}}/{{sheaf_law_count}} satisfied): the appendix section glues to a unique output (separation), occupies the terminal position of the linear extension under its own `appendix` group row (poset and gluing), binds only well-typed fragments (typing), and owns every fragment path it references (compositionality). No count in this appendix is hand-written; all are injected from the registry-backed oracle.

<!-- sheaf-track:simulation -->

Analytical sweep artifacts feed [@sec:results_mi_sweep] and [@sec:results_invariants]; simulation invariants merge after [@sec:results_si_tmaze]. No additional path listing is required beyond those Results sections.

<!-- sheaf-track:pymdp -->

pymdp harness summary: `output/data/si_tmaze_summary.json` (mean belief entropy, action trace). Full log: `output/logs/pymdp_runs.jsonl`.

<!-- sheaf-track:visualization -->

![Two-panel plot of mutual information versus coupling strength lambda for the symmetric Bernoulli-Ising toy. Left panel shows closed-form curve (solid dark line) and Monte Carlo estimates (dashed blue line) with lambda on the x-axis and mutual information in nats on the y-axis. Right panel shows Monte Carlo minus closed-form residuals versus lambda with a zero reference line.](../output/figures/ising_mi_curve.png){width=90%}

*Figure A1 (appendix). Closed-form and Monte Carlo mutual information I(λ) for the symmetric Bernoulli-Ising toy across {{param_sweep_grid_points}} grid points up to λ_max = {{lambda_max}}; grid maximum {{ising_mi_saturation}} nats on the measured sweep.*

![Step plot of discrete action index versus timestep for the pymdp sophisticated-inference T-maze rollout. Actions change at each timestep with light fill under the step trace; policy depth is {{si_tmaze_policy_len}} steps.](../output/figures/si_tmaze_actions.png){width=90%}

*Figure A2 (appendix). Discrete action index over time for the pymdp T-maze rollout (policy length {{si_tmaze_policy_len}}).*

![Heatmap matrix of IMRAD manuscript rows versus {{sheaf_track_count}} sheaf fragment track columns. Black cells mean the track is bound and the fragment file exists; white cells mean the track is not bound; gray cells mean bound but missing. Rows are grouped by IMRAD block with indented subsection labels; column headers list track ids.](../output/figures/sheaf_coverage_heatmap.png){width=95%}

*Figure 4. Sheaf track coverage matrix: {{imrad_manifest_rows}} IMRAD rows × {{sheaf_track_count}} fragment columns. Black = present (P), white = absent (—), gray = missing (M). Counts: {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing.*

<!-- sheaf-track:lean -->

Lean modules under `lean/TemplateActiveInference/` declare horizon and coupling witnesses. Build with `lake build` in `lean/`; [@fig:lean_boundary_status] summarizes proved versus deferred statements for this boundary fragment.

<!-- sheaf-track:gnn -->

GNN declarations: `gnn/bernoulli_toy.gnn.md` and `gnn/si_tmaze.gnn.md`. [@fig:gnn_ontology_concordance] and [@sec:methods_analytical] document ontology concordance for the Bernoulli toy; SI notation extends the same pattern under [@sec:methods_pymdp].

<!-- sheaf-track:ontology -->

### Ontology bindings

- `belief_entropy` → **BeliefEntropy**
- `expected_free_energy` → **ExpectedFreeEnergy**
- `location` → **HiddenState**
- `observation` → **ObservationLikelihood**
- `policy` → **PolicyPosterior**
- `sheaf_track` → **SheafFragment**


<!-- sheaf-track:animation -->

Animation is an **extension** sheaf track (optional GIF via `scripts/render_animation.py`). This appendix row documents the track binding only; default publication uses static SI figures ([@sec:results_si_tmaze], [@fig:si_tmaze_actions]) rather than embedding motion assets unless explicitly promoted.

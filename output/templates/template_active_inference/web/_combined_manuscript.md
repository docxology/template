```{=latex}
\thispagestyle{empty}
\setlength{\parskip}{0pt}
\setlength{\itemsep}{0pt}
\begin{samepage}
\scriptsize
```

```{=latex}
\section*{BEGINNING OF TRANSMISSION}\label{beginning-of-transmission}
```

**State:** unpublished / pending pairing

**Pairing:** pending — unresolved:
- ✗ GitHub release URL: `pending`
- ✗ PDF SHA-256: `pending`

```{=latex}
\subsubsection*{Release metadata}
```

| Field | Value |
| --- | --- |
| Title | Active Inference Multi-Track Exemplar |
| Version | 0.3.0 |
| Concept DOI | 10.5281/zenodo.20417021 |
| Version DOI | 10.5281/zenodo.20420352 |
| GitHub | docxology/template_active_inference |
| Zenodo | [https://zenodo.org/records/20417021](https://zenodo.org/records/20417021) |
| SHA-256 | pending |
| SHA-512 | pending |

```{=latex}
\subsubsection*{How to verify}
```

- Scan **Integrity** QR and compare the embedded SHA-256 prefix to the table above.
- Scan **Zenodo** / **GitHub** QR codes and confirm they resolve to this release pairing.
- Full hashes and structured fields: `../data/transmission_manifest.json`.

![Integrity QR strip](../figures/transmission_integrity_strip.png){width=98%}

Structured manifest: `../data/transmission_manifest.json`

![Publication pairing flow](../figures/transmission_pairing.png){width=35%}

**Stego:** off | overlays text | barcodes on | XMP on | manifest on → `./secure_run.sh`

```{=latex}
\end{samepage}
\newpage
```


<!-- BEGINNING OF TRANSMISSION -->



---



# Sheaf Track Coverage {#sec:sheaf_coverage}

This page summarizes which **sheaf fragment tracks** are bound for each IMRAD row in `manuscript/sheaf/manifest.yaml`. The matrix is regenerated at compose time.

**Totals:** 47 present / 47 bound / 0 missing (gray).

| Color | Meaning |
| --- | --- |
| Black | Track **present** (bound and fragment exists) |
| White | **Absent** (not bound for this row) |
| Gray | **Missing** (bound but fragment file absent) |

## Introduction

- **Introduction** *(group)*
-   **Motivation and scope**
-   **Contributions**
## Methods

- **Methods** *(group)*
-   **Bernoulli–Ising analytical model**
-   **pymdp simulation harness**
-   **Lean formalization boundary**
-   **Sheaf composition**
## Results

- **Results** *(group)*
-   **Mutual-information parameter sweep**
-   **Free-energy decomposition**
-   **T-maze sophisticated inference**
-   **Validation invariants**
## Discussion

- **Discussion** *(group)*
-   **Limitations and outlook**
## Appendix

-   **Appendix: full track coverage**

![Heatmap matrix of IMRAD manuscript rows versus 10 sheaf fragment track columns. Black cells mean the track is bound and the fragment file exists; white cells mean the track is not bound; gray cells mean bound but missing. Rows are grouped by IMRAD block with indented subsection labels; column headers list track ids.](../figures/sheaf_coverage_heatmap.png){#fig:sheaf_coverage_heatmap width=95%}

*Coverage overview. Sheaf track coverage matrix: 16 IMRAD rows × 10 fragment columns. Black = present (P), white = absent (—), gray = missing (M). Counts: 47 present / 47 bound / 0 missing.*

Appendix row `16_appendix_full_sheaf.md` binds 9 fragment track types as a composability proof (registry defines 10 types; optional `layers` is methods-only).



---



# Abstract {#sec:abstract}

We study a minimal Active Inference stack on toy models: a Bernoulli–Ising analytical oracle, a pymdp T-maze rollout, and a sheaf-indexed compose contract that binds 10 fragment tracks into 12 flat IMRAD sections. Claims are limited to those models and their generated artifacts.

[@sec:sheaf_coverage] reports a 16-row coverage matrix (4 IMRAD group headers) regenerated from the live manifest at compose time. [@sec:methods_pymdp] documents the T-maze harness aligned with [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference).

[@sec:results_invariants] records 12 / 12 invariant checks passed. SI planning horizon: 2 steps. Sweep RMSE 0 nats bounds analytical–empirical agreement on the coupling grid.



---



```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Introduction}
\section*{Introduction}
```

# Motivation and scope {#sec:intro_motivation}

<!-- sheaf-track:prose -->

## Scientific scope

This manuscript couples three tracks on toy Active Inference models: a Bernoulli–Ising analytical oracle, a pymdp T-maze rollout, and a sheaf-indexed assembly contract that binds 10 optional fragment tracks under an IMRAD outline. The scientific claims stay within those models and their generated artifacts; they are not empirical statements about biological agents.

## Manuscript structure

Three **scientific tracks** (analytical, pymdp, sheaf composition) map onto 10 **composable fragment types** and 7 pipeline gates ([@fig:multi_track_architecture]). [@sec:sheaf_coverage] summarizes which fragment tracks bind to each manifest row. [@sec:methods_sheaf] documents the compose pipeline, coverage semantics ([@eq:coverage_cell]), and strict validation gates.

The pymdp track follows the [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference) with a minimal T-maze and planning horizon `policy_len = 2`. Other sections cite [@sec:methods_pymdp] instead of repeating that reference.



---



# Contributions {#sec:intro_contributions}

<!-- sheaf-track:prose -->

## Scientific contributions

1. **Analytical oracle** ([@sec:methods_analytical]): closed-form mutual information and free-energy decomposition on a symmetric Bernoulli–Ising toy with Monte Carlo cross-checks ([@sec:results_mi_sweep], [@sec:results_free_energy]).
2. **Sophisticated-inference harness** ([@sec:methods_pymdp]): deterministic pymdp T-maze rollout with logged beliefs, actions, and merged invariant gates ([@sec:results_si_tmaze], [@sec:results_invariants]).
3. **Sheaf-indexed composition** ([@sec:methods_sheaf]): 10 optional fragment types bind to 16 manifest rows under [@eq:coverage_cell], with a 9-track appendix composability proof ([@sec:appendix_full_sheaf]).

[@fig:multi_track_architecture] maps the three scientific tracks to 7 pipeline gates and 10 composable fragment renderers. Measured invariant checks: 12 / 12 passed.

Ontology-facing symbols in the analytical track—`location`, `observation`, `policy`, and `expected_free_energy`—map to **HiddenState**, **ObservationLikelihood**, **PolicyPosterior**, and **ExpectedFreeEnergy** in the GNN concordance figure ([@fig:gnn_ontology_concordance], [@sec:methods_analytical]).

<!-- sheaf-track:visualization -->

![Process diagram linking three scientific tracks to 7 pipeline gates and 10 sheaf fragment types across 16 manifest rows.](../figures/multi_track_architecture.png){#fig:multi_track_architecture width=95%}

*Figure I1 (intro). Multi-track architecture: analytical, pymdp, and sheaf composition lanes mapped to 7 pipeline gates and 10 composable fragment types.*

<!-- sheaf-track:ontology -->

### Ontology bindings

- `expected_free_energy` → **ExpectedFreeEnergy**
- `location` → **HiddenState**
- `observation` → **ObservationLikelihood**
- `policy` → **PolicyPosterior**



---



```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Methods}
\section*{Methods}
```

# Bernoulli–Ising analytical model {#sec:methods_analytical}

<!-- sheaf-track:prose -->

We study a minimal **K=2 Bernoulli / Ising** coupling as the analytical companion to multi-track verification. The entangled joint [@eq:entangled_joint] yields closed-form mutual information $I(\lambda)$, which serves as an oracle for Monte Carlo checks and GNN round-trips in [@sec:results_mi_sweep] ([@fig:gnn_ontology_concordance]).

Measured sweep grid points: 21. Invariants passed: 12 / 12.

<!-- sheaf-track:formalism -->

The entangled joint over binary policies satisfies

$$
q_\lambda(\pi) \propto E(\pi)\,\exp(\lambda J(\pi)),
$$ {#eq:entangled_joint}

with symmetric Ising coupling $J$ and deformation parameter $\lambda$. Mutual information is $I(\lambda)=\log 2 - H_b(\sigma(\lambda))$.

<!-- sheaf-track:simulation -->

The analytical track writes a parameter sweep comparing closed-form and empirical mutual information across $\lambda \in [0, 4]$ on 21 grid points ([@sec:results_mi_sweep], [@fig:ising_mi_curve]).

<!-- sheaf-track:visualization -->

![Two-panel plot of mutual information versus coupling strength lambda for the symmetric Bernoulli-Ising toy. Left panel shows closed-form curve (solid dark line) and Monte Carlo estimates (dashed blue line) with lambda on the x-axis and mutual information in nats on the y-axis. Right panel shows Monte Carlo minus closed-form residuals versus lambda with a zero reference line.](../figures/ising_mi_curve.png){#fig:ising_mi_curve width=90%}

*Figure 1 (methods). Closed-form and Monte Carlo mutual information I(λ) for the symmetric Bernoulli-Ising toy across 21 grid points up to λ_max = 4; grid maximum 0.6031 nats on the measured sweep.*

![Layered concordance diagram linking analytical symbols, GNN variables from bernoulli_toy.gnn.md (GNN v1.1), and Active Inference Ontology terms.](../figures/gnn_ontology_concordance.png){#fig:gnn_ontology_concordance width=90%}

*Figure 1b (methods). GNN ↔ ontology concordance for the Bernoulli–Ising toy (GNN v1.1).*

<!-- sheaf-track:gnn -->

The Bernoulli toy is declared in `gnn/bernoulli_toy.gnn.md` (GNN v1.1). [@fig:gnn_ontology_concordance] links GNN variables to Active Inference Ontology terms bound in the analytical ontology fragment; round-trip parity is checked before render.

Measured MI and sweep artifacts in [@sec:results_mi_sweep] ground the same symbol map used in the concordance diagram.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `J` → **CrossStreamCouplingPotential**
- `gamma` → **SophisticationWeight**
- `lam` → **EntanglementDeformationParameter**
- `pi1` → **Stream1PolicyVector**
- `pi2` → **Stream2PolicyVector**
- `q_joint` → **EntangledJointPosterior**



---



# pymdp simulation harness {#sec:methods_pymdp}

<!-- sheaf-track:prose -->

**Sophisticated inference (planning horizon).** This section documents a **pymdp state-inference harness** on a minimal T-maze ([@fig:tmaze_schematic]) with planning horizon `policy_len = 2`. Default mode is `state_inference` (T-maze rollout via `simulate_si_tmaze.py`). The Agent constructs a multi-step policy set (`num_policies` logged in SI artifacts); per-step **belief entropy** is aggregated as `mean_belief_entropy`.

Graph-world `infer_policies` is an opt-in extension stub — see `tracks.yaml` `extension_tracks.graph_world`. For the reference workflow, see [@sec:intro_motivation]; measured rollouts appear in [@sec:results_si_tmaze].

Mean belief entropy across steps: 0.3251.

<!-- sheaf-track:formalism -->

Given generative matrices $A,B,C,D$, pymdp computes state beliefs $q(s)$ via variational inference (`infer_states`). The Agent is configured with planning horizon $H =$ 2, which defines the **policy depth** used when constructing candidate policies (logged as `num_policies` in the SI summary artifact; see [@sec:results_si_tmaze]).

The default harness records belief entropy per step; extending to full expected-free-energy policy selection (`infer_policies`) is documented as a follow-on track in [@sec:discussion_outlook].

<!-- sheaf-track:pymdp -->

SI artifacts (summary, trace, optional JSONL log) record step count, actions, observations, and belief entropy for [@sec:results_si_tmaze]. Steps recorded: 2.

<!-- sheaf-track:visualization -->

![Schematic of the minimal T-maze POMDP with start and goal states, discrete actions and observations, and planning horizon policy_len = 2.](../figures/tmaze_schematic.png){#fig:tmaze_schematic width=85%}

*Figure M1 (methods). T-maze generative model schematic (2-step policy horizon, state_inference mode).*

<!-- sheaf-track:gnn -->

See `gnn/si_tmaze.gnn.md` for a GNN view of the T-maze hidden state, observation, and policy variables with ontology bindings.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `belief_entropy` → **BeliefEntropy**
- `loc` → **HiddenState**
- `obs` → **ObservationLikelihood**
- `pi` → **PolicyPosterior**



---



# Lean formalization boundary {#sec:methods_lean}

<!-- sheaf-track:prose -->

The Lean track provides minimal boundary witnesses checked by `lake build` under `lean/TemplateActiveInference/`. [@fig:lean_boundary_status] summarizes proved versus deferred statements; fragments cite theorem names without duplicating proof scripts in prose.

Horizon witnesses link back to the analytical toy ([@sec:methods_analytical]) and the pymdp planning depth ([@sec:methods_pymdp]).

<!-- sheaf-track:visualization -->

![Table figure listing Lean modules, declaration kinds, names, and proved versus sorry status under lean/TemplateActiveInference/.](../figures/lean_boundary_status.png){#fig:lean_boundary_status width=90%}

*Figure M2 (methods). Lean formalization boundary: module witnesses checked by lake build.*

<!-- sheaf-track:lean -->

Lean module `TemplateActiveInference.SophisticatedInference` declares the planning horizon parameter and a witness that horizon $> 1$ distinguishes sophisticated from myopic inference.

Build via `lake build` under `lean/`.



---



# Sheaf composition {#sec:methods_sheaf}

<!-- sheaf-track:prose -->

## Compose contract

Each manifest row in `manuscript/sheaf/manifest.yaml` binds fragment tracks from `manuscript/sheaf/tracks.yaml`. A track supplies a renderer, compose order, label, and optional flag; the composer flattens the binding set into one Markdown section for PDF and web output.

The operational claim is auditable binding: analytical, simulation, pymdp, visualization, Lean, GNN, ontology, and optional media fragments attach to each IMRAD row under [@eq:coverage_cell] (**P** present, **—** unbound, **M** missing).

## Coverage and figures

[@fig:sheaf_layers_overview] summarizes 10 fragment types and their IMRAD bindings. Generated tables below list every track definition and section×track binding at compose time.

## Compose commands

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Each run emits `output/data/sheaf_coverage_matrix.json` and regenerates coverage artifacts. Partial compose (`--section`) is draft-only; the matrix always reflects the full manifest. Coverage totals appear on [@sec:sheaf_coverage]; discussion scope is in [@sec:discussion_outlook].

<!-- sheaf-track:formalism -->

Let $\mathcal{T}$ be the registered fragment-track set and $\mathcal{S}$ the ordered IMRAD manifest rows. Each track $t \in \mathcal{T}$ maps to renderer $R(t)$, label $L(t)$, optional flag $O(t)$, and compose-order index $\pi(t)$ from `manuscript/sheaf/tracks.yaml`. Each row $s \in \mathcal{S}$ carries a partial binding map $F_s : \mathcal{T} \rightharpoonup \mathrm{Path}$ from track ids to fragment paths.

The coverage cell is

$$
B(s,t) \in \{\mathrm{P}, \mathrm{—}, \mathrm{M}\}
$$ {#eq:coverage_cell}

derived from $F_s(t)$ and filesystem existence at compose time: **P** when a bound fragment exists, **—** when the track is unbound for that row, and **M** when a bound path is missing. The current regenerated matrix reports 47 present / 47 bound / 0 missing cells.

Registry size: $|\mathcal{T}| = 10$ types across 16 IMRAD manifest rows. Formal track definitions and section×track bindings appear in the generated tables below.

<!-- sheaf-track:visualization -->

![Two-panel overview of sheaf fragment layers. Left panel shows 10 composable track types in registry compose order with labels and renderer ids. Right panel shows the IMRAD section binding heatmap with black present, white absent, and gray missing cells across 16 manifest rows and 10 tracks.](../figures/sheaf_layers_overview.png){#fig:sheaf_layers_overview width=98%}

*Figure 6 (methods). Sheaf layers overview: registry stack (compose order, renderer ids) and IMRAD binding heatmap for 10 fragment types across 16 manifest rows (47 present / 47 bound / 0 missing).*

<!-- sheaf-track:layers -->

<!-- sheaf-layers:registry -->
## Sheaf fragment track registry

Compose order and renderer bindings from `manuscript/sheaf/tracks.yaml`.

| Order | Track id | Label | Renderer | Optional |
| ---: | --- | --- | --- | --- |
| 10 | `prose` | Narrative prose | `markdown` | No |
| 20 | `formalism` | Mathematical formalism | `markdown` | No |
| 30 | `simulation` | Analytical simulation notes | `markdown` | No |
| 35 | `layers` | Sheaf layers tables | `layers_report` | Yes |
| 40 | `pymdp` | pymdp harness artifacts | `markdown` | No |
| 50 | `visualization` | Figure references | `section_figures` | No |
| 60 | `lean` | Lean boundary fragment | `markdown` | No |
| 70 | `gnn` | GNN notation fragment | `markdown` | No |
| 80 | `ontology` | Active Inference Ontology bindings | `ontology_yaml` | No |
| 90 | `animation` | Animation fragment | `markdown` | Yes |

**Track count:** 10 registered fragment types.

<!-- sheaf-layers:binding-matrix -->
## IMRAD binding matrix

Section rows versus fragment track columns. **P** = present (bound and file exists); **—** = absent (not bound); **M** = missing (bound, file absent).

| Section | prose | formalism | simulation | layers | pymdp | visualization | lean | gnn | ontology | animation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Introduction (group) | — | — | — | — | — | — | — | — | — | — |
|   Motivation and scope | P | — | — | — | — | — | — | — | — | — |
|   Contributions | P | — | — | — | — | P | — | — | P | — |
| Methods (group) | — | — | — | — | — | — | — | — | — | — |
|   Bernoulli–Ising analytical model | P | P | P | — | — | P | — | P | P | — |
|   pymdp simulation harness | P | P | — | — | P | P | — | P | P | — |
|   Lean formalization boundary | P | — | — | — | — | P | P | — | — | — |
|   Sheaf composition | P | P | — | P | — | P | — | — | — | — |
| Results (group) | — | — | — | — | — | — | — | — | — | — |
|   Mutual-information parameter sweep | P | P | P | — | — | P | — | — | — | — |
|   Free-energy decomposition | P | — | — | — | — | P | — | — | — | — |
|   T-maze sophisticated inference | P | — | — | — | P | P | — | — | — | — |
|   Validation invariants | P | — | P | — | — | P | — | — | — | — |
| Discussion (group) | — | — | — | — | — | — | — | — | — | — |
|   Limitations and outlook | P | — | P | — | — | — | — | — | P | — |
|   Appendix: full track coverage | P | P | P | — | P | P | P | P | P | P |

**Totals:** 47 present / 47 bound / 0 missing.

<!-- sheaf-layers:legend -->
| Symbol | Coverage color | Meaning |
| --- | --- | --- |
| P | Black | Track **present** (bound and fragment exists) |
| — | White | **Absent** (not bound for this section) |
| M | Gray | **Missing** (bound but fragment file absent) |



---



```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Results}
\section*{Results}
```

# Mutual-information parameter sweep {#sec:results_mi_sweep}

<!-- sheaf-track:prose -->

We sweep coupling strength $\lambda$ on a grid of 21 points up to $\lambda_{\max} = 4$. Closed-form mutual information from [@eq:entangled_joint] is compared to Monte Carlo estimates from the analytical module ([@sec:methods_analytical]).

Measured invariant checks: 12 / 12 passed on the clean tree.

<!-- sheaf-track:formalism -->

The sweep reuses the entangled joint defined in [@eq:entangled_joint] ([@sec:methods_analytical]). Mutual information $I(\lambda)=\log 2 - H_b(\sigma(\lambda))$ is evaluated on the same $\lambda$ grid as the analytical oracle and Monte Carlo estimates.

<!-- sheaf-track:simulation -->

Empirical MI estimates use fixed seed 0 and share the same $\lambda$ grid as the closed-form sweep ([@sec:methods_analytical], [@fig:ising_mi_curve]).

<!-- sheaf-track:visualization -->

![Two-panel plot of mutual information versus coupling strength lambda for the symmetric Bernoulli-Ising toy. Left panel shows closed-form curve (solid dark line) and Monte Carlo estimates (dashed blue line) with lambda on the x-axis and mutual information in nats on the y-axis. Right panel shows Monte Carlo minus closed-form residuals versus lambda with a zero reference line.](../figures/ising_mi_curve.png){width=90%}

*Figure 2 (results). Closed-form and Monte Carlo mutual information I(λ) for the symmetric Bernoulli-Ising toy across 21 grid points up to λ_max = 4; grid maximum 0.6031 nats on the measured sweep.*



---



# Free-energy decomposition {#sec:results_free_energy}

<!-- sheaf-track:prose -->

Free energy against the entangled prior is evaluated along the same $\lambda$ grid used for the MI sweep. The curve highlights how deformation strength trades off prior alignment and coupling energy in the analytical toy.

Saturation MI (grid maximum on the measured λ sweep): 0.6031 nats.

<!-- sheaf-track:visualization -->

![Line plot of free energy in nats versus coupling strength lambda for the entangled posterior relative to a mean-field prior. A single dark curve traces free energy across the sweep; the minimum is marked with a teal scatter point and labeled with the argmin lambda value.](../figures/free_energy_curve.png){#fig:free_energy_curve width=90%}

*Figure 3 (results). Free energy of the entangled posterior relative to the mean-field prior across the hyperparameter sweep (grid points 21).*



---



# T-maze sophisticated inference {#sec:results_si_tmaze}

<!-- sheaf-track:prose -->

The pymdp harness rolls out a T-maze sophisticated-inference agent with planning horizon 2. Summary metrics land in `output/data/si_tmaze_summary.json`.

Steps recorded: 2. Mean belief entropy: 0.3251.

<!-- sheaf-track:pymdp -->

Rollout trace: `output/data/si_tmaze_trace.json`. JSONL run log: `output/logs/pymdp_runs.jsonl`.

<!-- sheaf-track:visualization -->

![Line plot of belief entropy in nats versus timestep for the pymdp T-maze rollout. Entropy ranges from 0.3251 to 0.3251 nats across 2 steps in state_inference mode.](../figures/si_belief_entropy_curve.png){#fig:si_belief_entropy_curve width=90%}

*Figure 3a (results). Belief entropy over time for the T-maze rollout (mean 0.3251 nats).*

![Dual-panel plot of observation index and action index versus timestep for the pymdp T-maze rollout. The upper panel shows discrete observations; the lower panel shows actions. Goal reached flag is 1.](../figures/si_obs_action_trace.png){#fig:si_obs_action_trace width=90%}

*Figure 3b (results). Observation and action traces for the T-maze rollout (action diversity 2).*

![Step plot of discrete action index versus timestep for the pymdp sophisticated-inference T-maze rollout. Actions change at each timestep with light fill under the step trace; policy depth is 2 steps.](../figures/si_tmaze_actions.png){#fig:si_tmaze_actions width=90%}

*Figure 3c (results). Discrete action index over time for the pymdp T-maze rollout (policy length 2).*



---



# Validation invariants {#sec:results_invariants}

<!-- sheaf-track:prose -->

The analytical invariant registry runs before PDF rendering ([@sec:methods_analytical]). On a clean checkout **12 / 12** checks pass in the merged validation report, which records simulation invariants when the pymdp harness ran ([@sec:results_si_tmaze]).

[@fig:invariant_dashboard] lists each analytical and simulation gate; failures block publication artifacts. See [@sec:methods_sheaf] for how invariant counts hydrate manuscript tokens.

<!-- sheaf-track:simulation -->

Simulation invariants merge into the analytical report after the pymdp harness runs ([@sec:results_si_tmaze]). [@fig:invariant_dashboard] summarizes pass/fail status for both domains on the clean tree.

<!-- sheaf-track:visualization -->

![Horizontal bar checklist of analytical and simulation invariant names with pass or fail status. 12 of 12 checks pass on the merged report.](../figures/invariant_dashboard.png){#fig:invariant_dashboard width=90%}

*Figure 5 (results). Invariant dashboard: 12 / 12 merged analytical and simulation checks from the validation registry.*



---



```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Discussion}
\section*{Discussion}
```

# Limitations and outlook {#sec:discussion_outlook}

<!-- sheaf-track:prose -->

## Limitations

The Bernoulli–Ising toy, T-maze harness, and sheaf composition model are pedagogical. They validate analytical consistency, artifact wiring, renderer dispatch, and manuscript hydration—not empirical claims about biological agents. Default pymdp mode is `state_inference` with planning horizon 2; full policy inference remains an opt-in extension ([@sec:methods_pymdp]).

## Sheaf audit and outlook

[@sec:sheaf_coverage] and [@sec:appendix_full_sheaf] make binding state auditable under strict compose validation ([@sec:methods_sheaf]). Opt-in pipeline extensions in `tracks.yaml` `extension_tracks` (belief GIF via `render_animation.py`, graph-world SI stub) add artifacts outside the default analysis DAG; the appendix row already binds an `animation` sheaf fragment without new manifest rows.

Sweep RMSE 0 nats and SI goal reached 1 summarize measured agreement on the declared grids and rollout. Future work includes full expected-free-energy policy selection, richer graph-world rollouts, and expanded Lean proofs beyond the boundary witnesses in [@sec:methods_lean].

The discussion ontology binds `coverage_semantics` to the audit matrix in [@sec:sheaf_coverage], `pedagogical_scope` to the non-empirical scope of the toy models, and `state_inference_mode` to the pymdp harness contract in [@sec:methods_pymdp].

<!-- sheaf-track:simulation -->

Measured pymdp rollout (`state_inference`, config hash `ea4b126a9c22f22f`): mean belief entropy 0.3251 nats over 2 steps; goal reached flag 1; action diversity 2.

Analytical sweep residual RMSE 0 nats (max residual 0). Coverage audit: 47 present / 47 bound / 0 missing cells on the IMRAD matrix.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `coverage_semantics` → **Coverage matrix semantics**
- `pedagogical_scope` → **Pedagogical scope**
- `state_inference_mode` → **State inference harness**



---



```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Appendix}
\section*{Appendix}
```

# Appendix: full track coverage {#sec:appendix_full_sheaf}

<!-- sheaf-track:prose -->

This section is the **composability proof** for the manifest-indexed sheaf model: all 9 appendix-bound fragment tracks render into one flat manuscript section without section-specific compose branches. The registry defines 10 composable types; optional `layers` is methods-only and excluded from this row. The `animation` fragment is bound here as an optional registry type alongside prose, formalism, simulation, pymdp, visualization, lean, gnn, and ontology tracks.

The proof is a publication-systems check ([@eq:appendix_track_count]). It demonstrates that heterogeneous fragments share one registry, manifest, renderer dispatch path, coverage matrix, and hydration boundary; it does not assert that every track carries equal scientific weight.

<!-- sheaf-track:formalism -->

For each track $t \in \mathcal{T}_{\mathrm{Full}}$, the appendix row binds a fragment path $f(t)$ and the composer emits `<!-- sheaf-track:t -->` before the rendered body. Generated renderers such as `section_figures` and markdown renderers pass through the same `resolve_track_body()` dispatch, so the appendix exercises the common compose interface rather than a bespoke appendix path.

$$
|\mathcal{T}_{\mathrm{Full}}| = 9
$$ {#eq:appendix_track_count}

The fragment registry defines 10 composable track types; optional `layers` is bound on the methods sheaf section only. Optional `animation` is bound in this appendix proof; the opt-in GIF extension in `tracks.yaml` `extension_tracks` is separate from this fragment slot.

<!-- sheaf-track:simulation -->

Analytical sweep artifacts feed [@sec:results_mi_sweep] and [@sec:results_invariants]; simulation invariants merge after [@sec:results_si_tmaze]. No additional path listing is required beyond those Results sections.

<!-- sheaf-track:pymdp -->

pymdp harness summary: `output/data/si_tmaze_summary.json` (mean belief entropy, action trace). Full log: `output/logs/pymdp_runs.jsonl`.

<!-- sheaf-track:visualization -->

![Two-panel plot of mutual information versus coupling strength lambda for the symmetric Bernoulli-Ising toy. Left panel shows closed-form curve (solid dark line) and Monte Carlo estimates (dashed blue line) with lambda on the x-axis and mutual information in nats on the y-axis. Right panel shows Monte Carlo minus closed-form residuals versus lambda with a zero reference line.](../figures/ising_mi_curve.png){width=90%}

*Figure A1 (appendix). Closed-form and Monte Carlo mutual information I(λ) for the symmetric Bernoulli-Ising toy across 21 grid points up to λ_max = 4; grid maximum 0.6031 nats on the measured sweep.*

![Step plot of discrete action index versus timestep for the pymdp sophisticated-inference T-maze rollout. Actions change at each timestep with light fill under the step trace; policy depth is 2 steps.](../figures/si_tmaze_actions.png){width=90%}

*Figure A2 (appendix). Discrete action index over time for the pymdp T-maze rollout (policy length 2).*

![Heatmap matrix of IMRAD manuscript rows versus 10 sheaf fragment track columns. Black cells mean the track is bound and the fragment file exists; white cells mean the track is not bound; gray cells mean bound but missing. Rows are grouped by IMRAD block with indented subsection labels; column headers list track ids.](../figures/sheaf_coverage_heatmap.png){width=95%}

*Figure 4. Sheaf track coverage matrix: 16 IMRAD rows × 10 fragment columns. Black = present (P), white = absent (—), gray = missing (M). Counts: 47 present / 47 bound / 0 missing.*

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



---



# Conclusion {#sec:conclusion}

Analytical oracles ([@sec:methods_analytical]), pymdp rollouts ([@sec:results_si_tmaze]), and sheaf composition ([@sec:methods_sheaf]) share one auditable manuscript contract: measured artifacts hydrate 12 composed sections, [@sec:sheaf_coverage] reports binding state, and strict compose validation blocks gray matrix cells before PDF rendering.

The T-maze harness runs in `state_inference` mode with config hash `ea4b126a9c22f22f`; sweep RMSE 0 nats summarizes analytical–empirical agreement on the toy coupling grid. [@sec:results_invariants] merges analytical and simulation gates; [@sec:discussion_outlook] states scope and extensions. Scientific claims remain confined to declared models—not empirical statements about biological agents.



---



# References

See `manuscript/references.bib` for bibliography entries cited in the composed sections.



---



```{=latex}
% transmission-end-bookend
\clearpage
\thispagestyle{empty}
\setlength{\parskip}{0pt}
\setlength{\itemsep}{0pt}
\begin{samepage}
\scriptsize
```

```{=latex}
\section*{END OF TRANSMISSION}\label{end-of-transmission}
```

**Release:** v0.3.0 · DOI `10.5281/zenodo.20417021` · SHA-256 `pending…` · pairing pending

![Integrity QR strip](../figures/transmission_integrity_strip.png){width=88%}

**Prior:** _No prior releases._

```{=latex}
\end{samepage}
```


<!-- END OF TRANSMISSION -->

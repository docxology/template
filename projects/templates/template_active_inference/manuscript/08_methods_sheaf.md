# Sheaf composition {#sec:methods_sheaf}

<!-- sheaf-track:prose -->

## Compose contract

Each manifest row in `manuscript/sheaf/manifest.yaml` binds fragment tracks from `manuscript/sheaf/tracks.yaml`. A track supplies a renderer, compose order, label, and optional flag; the composer flattens the binding set into one Markdown section for PDF and web output.

The operational claim is auditable binding: analytical, simulation, pymdp, visualization, Lean, GNN, ontology, and optional media fragments attach to each IMRAD row under [@eq:coverage_cell] (**P** present, **—** unbound, **M** missing).

## Coverage and figures

[@fig:sheaf_layers_overview] summarizes {{sheaf_track_count}} fragment types and their IMRAD bindings. Generated tables below list every track definition and section×track binding at compose time.

## Compose commands

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Each run emits `output/data/sheaf_coverage_matrix.json` and regenerates coverage artifacts. Partial compose (`--section`) is draft-only; the matrix always reflects the full manifest. Coverage totals appear on [@sec:sheaf_coverage]; discussion scope is in [@sec:discussion_outlook].

## Law verification

`--validate-only --strict` runs the structural gate before any fragment is glued. Beyond per-cell coverage, it invokes the sheaf-law oracle (`verify_sheaf_laws`, `src/manuscript/sheaf/laws.py`), which checks {{sheaf_law_count}} axioms — poset, presheaf functoriality, separation, gluing, typing, and compositionality — and reports {{sheaf_laws_verified}}/{{sheaf_law_count}} satisfied for the current manifest. A violation is raised as an error-level issue and aborts the build, so a malformed manifest (a section colliding on an output file, an off-chain block, a mistyped fragment, a fragment shared between sections) can never compose. The formal statements are in the formalism block below; the negative-control suite (`tests/test_sheaf_laws.py`) proves each check is falsifiable.

The semantic layer is separate from those structural laws. `output/data/sheaf_gluing_certificate.json` records cross-track symbols, typed claim evidence, artifact sources, and manuscript-variable restrictions; validation fails when the analytical, pymdp, GNN, ontology, Lean, visualization, or manuscript tracks disagree about a shared symbol or measured claim.

<!-- sheaf-track:formalism -->

### Base poset and presheaf

The manuscript is modelled as a coverage sheaf over a finite base poset. Let the
**base** $P$ be the IMRAD blocks ordered as a chain,

$$
\mathsf{Introduction} \prec \mathsf{Methods} \prec \mathsf{Results} \prec \mathsf{Discussion} \prec \mathsf{Appendix},
$$ {#eq:imrad_chain}

with, in each block, a *group* node above its *section* nodes (written $G \sqsupseteq s$). $P$ is therefore a finite poset (equivalently a finite Alexandrov space). Let $\mathcal{T}$ be the registered fragment-track set from `manuscript/sheaf/tracks.yaml`; each track $t \in \mathcal{T}$ carries a renderer $R(t)$, label $L(t)$, optional flag $O(t)$, and a strict compose-order index $\pi(t)$.

The **presheaf** $\mathcal{F}$ is a contravariant functor on $P$ — $\mathcal{F}\colon P \to \mathbf{Set}$ with restriction maps along $\sqsupseteq$ — assigning to each composing section $s$ its bound fragment set $\mathcal{F}(s) = \{\,(t, F_s(t)) : t \text{ bound in } s\,\}$, where $F_s : \mathcal{T} \rightharpoonup \mathbf{Path}$ is the section's partial binding map. Restriction along $G \sqsupseteq s$ is projection onto a section's own bindings; group nodes carry the empty assignment and do not compose.

The coverage cell is

$$
B(s,t) \in \{\mathrm{P}, \mathrm{—}, \mathrm{M}\}
$$ {#eq:coverage_cell}

derived from $F_s(t)$ and filesystem existence at compose time: **P** when a bound fragment exists, **—** when the track is unbound for that row, and **M** when a bound path is missing. The current regenerated matrix reports {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing cells. Registry size: $|\mathcal{T}| = {{sheaf_track_count}}$ types across {{imrad_manifest_rows}} IMRAD manifest rows ({{imrad_group_count}} group rows, {{composed_section_count}} composing sections).

### Verified sheaf laws

What makes this presheaf a *sheaf* — rather than a bare incidence table — is that the composer's structural axioms are machine-checked. The oracle `verify_sheaf_laws` (`src/manuscript/sheaf/laws.py`) verifies {{sheaf_law_count}} laws, and the regenerated build reports {{sheaf_laws_verified}}/{{sheaf_law_count}} satisfied:

1. **Poset.** The IMRAD blocks form the chain of [@eq:imrad_chain]; compose order is monotone in block rank and every composing section's block carries a group row.
2. **Presheaf (functoriality).** Every bound track lies in $\mathcal{T}$; $\pi$ is a strict total order; and each section's resolved track order is the monotone restriction of $\pi$ (an explicit `track_order` override must be a permutation of the section's bound tracks).
3. **Separation (locality).** The map $s \mapsto \mathrm{output\_name}(s)$ is injective over composing sections: distinct locals glue to distinct global positions, so the global section is unique.
4. **Gluing.** Compose order is a linear extension of $P$ — each block's rows are contiguous and strictly increasing in order — so the local fragments glue to a unique global manuscript in which every composing section appears exactly once.
5. **Typing.** Each binding $(t, F_s(t))$ is well-typed: $R(t)$ is a registered renderer and the fragment suffix lies in $R(t)$'s accepted suffix set. Generated renderers (`section_figures`, `layers_report`) synthesize their body and are explicitly type-exempt.
6. **Compositionality.** Every fragment file is private to one section (no path is bound twice), so global composition is the coproduct of the per-section bodies and is independent of inclusion order.

Each law is paired with a negative control in `tests/test_sheaf_laws.py` — a single mutation that breaks the law and is proven to be caught — so the gate binds the laws' *content*, not merely their shape. Under `--strict`, any violation is surfaced as an error-level manifest issue and aborts composition.

### Scope (what is and is not claimed)

These laws verify the sheaf *axioms* on a finite base poset. They do **not** compute sheaf *cohomology* ($H^0$/$H^1$, Čech complexes, derived functors); "sheaf" here names the verified separation-and-gluing structure of a multi-track coverage assignment, not a cohomological invariant. Formal track definitions and section×track bindings appear in the generated tables below.

Semantic gluing then checks agreement of the glued content: coverage counts, manuscript variables, typed claim predicates, pymdp mode/hash, Bernoulli GNN ontology, and SI T-maze GNN ontology. This certificate is a content-level audit over the same base, not an additional topological law.

<!-- sheaf-track:visualization -->

![Two-panel overview of sheaf fragment layers. Left panel shows {{sheaf_track_count}} composable track types in registry compose order with labels and renderer ids. Right panel shows the IMRAD section binding heatmap with black present, white absent, and gray missing cells across {{imrad_manifest_rows}} manifest rows and {{sheaf_track_count}} tracks.](../output/figures/sheaf_layers_overview.png){#fig:sheaf_layers_overview width=98%}

*Figure 6 (methods). Sheaf layers overview: registry stack (compose order, renderer ids) and IMRAD binding heatmap for {{sheaf_track_count}} fragment types across {{imrad_manifest_rows}} manifest rows ({{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing).*

![Dependency diagram linking configured analysis scripts to generated evidence artifacts, manuscript consumers, and validation gates for the semantic sheaf gluing certificate.](../output/figures/semantic_gluing_graph.png){#fig:semantic_gluing_graph width=95%}

*Figure 6b (methods). Semantic gluing graph: configured producers, generated evidence artifacts, and validation consumers for the multi-track sheaf certificate.*

<!-- sheaf-track:provenance -->

The `provenance` fragment makes artifact lineage a live validation-spine track. The configured producer `generate_validation_spine.py` writes `output/data/artifact_provenance.json`, which hashes {{validation_spine_artifact_count}} core artifacts and records their producer scripts plus config digests. Publication claims that depend on generated files must be traceable to this lineage table or to a narrower artifact-specific certificate.

The first promoted provenance claim is intentionally limited: every listed core artifact exists, has a SHA-256 digest, and is produced by a configured analysis script. A changed file, missing producer, or stale saved digest is a validation failure, not a prose warning.

<!-- sheaf-track:counterexample -->

The `counterexample` fragment records expected-failure fixtures as first-class evidence. `output/reports/counterexample_matrix.json` lists {{counterexample_count}} negative controls that intentionally mutate ontology mappings, semantic certificates, graph-world trace agreement, typed claim evidence, and provenance hashes.

The matrix is not an empirical result. It is a falsifiability ledger: each row names the gate that must fail and the test that proves the failure path remains live.

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
| 42 | `provenance` | Artifact provenance spine | `markdown` | No |
| 44 | `reproducibility` | Deterministic replay spine | `markdown` | No |
| 46 | `counterexample` | Expected-failure counterexamples | `markdown` | No |
| 50 | `visualization` | Figure references | `section_figures` | No |
| 60 | `lean` | Lean boundary fragment | `markdown` | No |
| 70 | `gnn` | GNN notation fragment | `markdown` | No |
| 80 | `ontology` | Active Inference Ontology bindings | `ontology_yaml` | No |
| 90 | `animation` | Animation fragment | `markdown` | Yes |

**Track count:** {{sheaf_track_count}} registered fragment types.

<!-- sheaf-layers:binding-matrix -->
## IMRAD binding matrix

Section rows versus fragment track columns. **P** = present (bound and file exists); **—** = absent (not bound); **M** = missing (bound, file absent).

| Section | prose | formalism | simulation | layers | pymdp | provenance | reproducibility | counterexample | visualization | lean | gnn | ontology | animation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Introduction (group) | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Motivation and scope | P | — | — | — | — | — | — | — | — | — | — | — | — |
|   Contributions | P | — | — | — | — | — | — | — | P | — | — | P | — |
| Methods (group) | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Bernoulli–Ising analytical model | P | P | P | — | — | — | — | — | P | — | P | P | — |
|   pymdp simulation harness | P | P | — | — | P | — | — | — | P | — | P | P | — |
|   Lean formalization boundary | P | — | — | — | — | — | — | — | P | P | — | — | — |
|   Sheaf composition | P | P | — | P | — | P | — | P | P | — | — | — | — |
| Results (group) | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Mutual-information parameter sweep | P | P | P | — | — | — | — | — | P | — | — | — | — |
|   Free-energy decomposition | P | — | — | — | — | — | — | — | P | — | — | — | — |
|   T-maze active-inference rollout | P | — | — | — | P | — | — | — | P | — | — | — | — |
|   Validation invariants | P | — | P | — | — | — | P | — | P | — | — | — | — |
| Discussion (group) | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Limitations and outlook | P | — | P | — | — | — | — | — | — | — | — | P | — |
| Appendix (group) | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Appendix: full track coverage | P | P | P | — | P | P | P | P | P | P | P | P | P |

**Totals:** {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing.

<!-- sheaf-layers:legend -->
| Symbol | Coverage color | Meaning |
| --- | --- | --- |
| P | Black | Track **present** (bound and fragment exists) |
| — | White | **Absent** (not bound for this section) |
| M | Gray | **Missing** (bound but fragment file absent) |

<!-- sheaf-layers:evidence-crosswalk -->
## Evidence crosswalk

| Claim | Artifact | Producer | Gates |
| --- | --- | --- | --- |
| `sheaf_registry` | `manuscript/sheaf/tracks.yaml` | `manual` | validate_outputs |
| `sheaf_manifest` | `manuscript/sheaf/manifest.yaml` | `manual` | validate_outputs |
| `sheaf_coverage_config` | `manuscript/sheaf/coverage.yaml` | `manual` | validate_outputs |
| `sheaf_coverage_matrix` | `output/data/sheaf_coverage_matrix.json` | `generate_figures.py` | validate_outputs |
| `sheaf_gluing_certificate` | `output/data/sheaf_gluing_certificate.json` | `z_generate_manuscript_variables.py` | validate_manuscript, validate_outputs |
| `sheaf_evidence_crosswalk` | `output/data/sheaf_evidence_crosswalk.json` | `z_generate_manuscript_variables.py` | validate_manuscript, validate_outputs |
| `validation_dependency_graph` | `output/data/validation_dependency_graph.json` | `z_generate_manuscript_variables.py` | validate_manuscript, validate_outputs |
| `semantic_gluing_graph_figure` | `output/figures/semantic_gluing_graph.png` | `generate_figures.py` | validate_outputs, figure_registry |

**Claim rows:** 30 typed evidence claims.

<!-- sheaf-layers:artifact-producers -->
## Artifact producer graph

| Artifact | Producer | Configured | Consumers |
| --- | --- | --- | --- |
| `output/data/analysis_statistics.json` | `compute_statistics.py` | Yes | validate_outputs |
| `output/data/artifact_provenance.json` | `generate_validation_spine.py` | Yes | methods_sheaf |
| `output/data/manuscript_variables.json` | `z_generate_manuscript_variables.py` | Yes | validate_outputs |
| `output/data/parameter_sweep.csv` | `run_analytical_sweep.py` | Yes | validate_outputs |
| `output/data/sheaf_coverage_matrix.json` | `generate_figures.py` | Yes | validate_outputs |
| `output/data/sheaf_evidence_crosswalk.json` | `z_generate_manuscript_variables.py` | Yes | methods_sheaf |
| `output/data/sheaf_gluing_certificate.json` | `z_generate_manuscript_variables.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/si_graph_world_summary.json` | `simulate_si_graph_world.py` | Yes | methods_pymdp, results_si_tmaze |
| `output/data/si_graph_world_trace.json` | `simulate_si_graph_world.py` | Yes | methods_pymdp, results_si_tmaze, appendix_full_sheaf |
| `output/data/si_policy_comparison.json` | `simulate_si_tmaze.py` | Yes | methods_pymdp, results_si_tmaze |
| `output/data/si_tmaze_summary.json` | `simulate_si_tmaze.py` | Yes | validate_outputs |
| `output/data/si_tmaze_trace.json` | `simulate_si_tmaze.py` | Yes | validate_outputs |
| `output/data/validation_dependency_graph.json` | `z_generate_manuscript_variables.py` | Yes | methods_sheaf |
| `output/figures/si_belief_trajectory.gif` | `render_animation.py` | Yes | appendix_full_sheaf |
| `output/reports/counterexample_matrix.json` | `generate_validation_spine.py` | Yes | methods_sheaf |
| `output/reports/invariants.json` | `run_analytical_sweep.py` | Yes | validate_outputs |
| `output/reports/reproducibility_replay.json` | `generate_validation_spine.py` | Yes | results_invariants |
| `output/reports/si_invariants.json` | `simulate_si_tmaze.py` | Yes | validate_outputs |
| `output/reports/si_tmaze_run_report.json` | `simulate_si_tmaze.py` | Yes | validate_outputs |

**Producer issues:** 0.

<!-- sheaf-layers:semantic-restrictions -->
## Semantic gluing restrictions

| Restriction | Value |
| --- | --- |
| Coverage missing | `0` |
| Policy comparison rows | `4` |
| Graph-world trace agrees | `True` |
| Animation frames | `4` |
| Lean all proved | `True` |
| GNN ontology ok | `True` |
| Configured producers ok | `True` |


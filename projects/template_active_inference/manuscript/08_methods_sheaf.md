# Sheaf composition pipeline

<!-- sheaf-track:prose -->

Sheaf composition glues registered fragment tracks into flat manuscript sections using `manuscript/sheaf/manifest.yaml` and `manuscript/sheaf/tracks.yaml`.

The layers overview figure (registry caption in `figures.yaml` `section_figures.methods_sheaf`) summarizes the {{sheaf_track_count}} fragment layer types and their IMRAD bindings in one panel (registry stack plus binding heatmap). The tables below list every track definition and section×track binding from the live manifest at compose time.

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Each compose run emits `output/data/sheaf_coverage_matrix.json` and regenerates coverage artifacts. Partial compose (`--section`) is draft-only; the matrix always reflects the full manifest.

Coverage semantics: **black / P** = present (bound and file exists); **white / —** = absent (not bound); **gray / M** = missing (bound but file absent). Discussion limitations reference the same matrix counts (`{{coverage_present}}` / `{{coverage_bound}}` / `{{coverage_missing}}`).

<!-- sheaf-track:formalism -->

Each fragment track $t \in \mathcal{T}$ maps to renderer $R(t)$ and compose-order index $\pi(t)$ from `manuscript/sheaf/tracks.yaml`. For manifest row $s$, cell $B(s,t) \in \{\mathrm{P}, \mathrm{—}, \mathrm{M}\}$ follows the coverage matrix regenerated at compose time ({{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing).

Registry size: $|\mathcal{T}| = {{sheaf_track_count}}$ types across {{imrad_manifest_rows}} IMRAD manifest rows. Formal track definitions and section×track bindings appear in the generated tables below.

<!-- sheaf-track:visualization -->

![Two-panel overview of sheaf fragment layers. Left panel shows {{sheaf_track_count}} composable track types in registry compose order with labels and renderer ids. Right panel shows the IMRAD section binding heatmap with black present, white absent, and gray missing cells across {{imrad_manifest_rows}} manifest rows and {{sheaf_track_count}} tracks.](../output/figures/sheaf_layers_overview.png)

*Figure 6 (methods). Sheaf layers overview: registry stack (compose order, renderer ids) and IMRAD binding heatmap for {{sheaf_track_count}} fragment types across {{imrad_manifest_rows}} manifest rows ({{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing).*

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

**Track count:** {{sheaf_track_count}} registered fragment types.

<!-- sheaf-layers:binding-matrix -->
## IMRAD binding matrix

Section rows versus fragment track columns. **P** = present (bound and file exists); **—** = absent (not bound); **M** = missing (bound, file absent).

| Section | prose | formalism | simulation | layers | pymdp | visualization | lean | gnn | ontology | animation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Introduction (group) | — | — | — | — | — | — | — | — | — | — |
|   Motivation and Active Inference scope | P | — | — | — | — | — | — | — | — | — |
|   Exemplar contributions | P | — | — | — | — | — | — | — | P | — |
| Methods (group) | — | — | — | — | — | — | — | — | — | — |
|   Analytical Bernoulli–Ising toy | P | P | P | — | — | P | — | P | P | — |
|   pymdp sophisticated inference harness | P | P | — | — | P | — | — | P | P | — |
|   Lean boundary witnesses | P | — | — | — | — | — | P | — | — | — |
|   Sheaf composition pipeline | P | P | — | P | — | P | — | — | — | — |
| Results (group) | — | — | — | — | — | — | — | — | — | — |
|   Mutual information sweep | P | P | P | — | — | P | — | — | — | — |
|   Free energy decomposition | P | — | — | — | — | P | — | — | — | — |
|   T-maze sophisticated inference rollout | P | — | — | — | P | P | — | — | — | — |
|   Invariant gate summary | P | — | — | — | — | — | — | — | — | — |
| Discussion (group) | — | — | — | — | — | — | — | — | — | — |
|   Limitations and extensions | P | — | P | — | — | — | — | — | P | — |
|   Full sheaf track coverage (proof) | P | P | P | — | P | P | P | P | P | P |

**Totals:** {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing.

<!-- sheaf-layers:legend -->
| Symbol | Coverage color | Meaning |
| --- | --- | --- |
| P | Black | Track **present** (bound and fragment exists) |
| — | White | **Absent** (not bound for this section) |
| M | Gray | **Missing** (bound but fragment file absent) |


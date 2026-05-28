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

![Two-panel overview of sheaf fragment layers. Left panel shows 10 composable track types in registry compose order with labels and renderer ids. Right panel shows the IMRAD section binding heatmap with black present, white absent, and gray missing cells across 16 manifest rows and 10 tracks.](../output/figures/sheaf_layers_overview.png){#fig:sheaf_layers_overview width=98%}

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


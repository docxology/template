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

<!-- sheaf-track:visualization -->

![Two-panel overview of sheaf fragment layers. Left panel shows {{sheaf_track_count}} composable track types in registry compose order with labels and renderer ids. Right panel shows the IMRAD section binding heatmap with black present, white absent, and gray missing cells across {{imrad_manifest_rows}} manifest rows and {{sheaf_track_count}} tracks.](../output/figures/sheaf_layers_overview.png){#fig:sheaf_layers_overview width=98%}

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
| Appendix (group) | — | — | — | — | — | — | — | — | — | — |
|   Appendix: full track coverage | P | P | P | — | P | P | P | P | P | P |

**Totals:** {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing.

<!-- sheaf-layers:legend -->
| Symbol | Coverage color | Meaning |
| --- | --- | --- |
| P | Black | Track **present** (bound and fragment exists) |
| — | White | **Absent** (not bound for this section) |
| M | Gray | **Missing** (bound but fragment file absent) |


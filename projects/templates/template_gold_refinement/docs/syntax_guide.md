# Syntax Guide

## Citation syntax

- `[@smith2024]` — parenthetical citation
- `@smith2024` — narrative citation
- `[@smith2024; @doe2025]` — multiple citations

## Cross-references

| Type | Syntax | Example |
|------|--------|---------|
| Section | `[@sec:label]` | `[@sec:methodology]` |
| Figure | `[@fig:label]` | `[@fig:purity_progression]` |
| Equation | `[@eq:label]` | `[@eq:monotone_purity]` |
| Table | `[@tbl:label]` | `[@tbl:stages]` |

## Figure labels

All 13 entries below are owned by `src/figures/__init__.py::FIGURE_SPECS`
(the `src/figures/_common.py` module docstring lists the same registry).

| Label | File | Generator |
|-------|------|-----------|
| `{#fig:purity_progression}` | `purity_progression.png` | `figures.generate_purity_progression()` |
| `{#fig:karat_grading}` | `karat_grading.png` | `figures.generate_karat_grading_chart()` |
| `{#fig:token_density}` | `token_density.png` | `figures.generate_token_density_chart()` |
| `{#fig:provenance_sankey}` | `provenance_sankey.png` | `figures.generate_provenance_sankey()` |
| `{#fig:purity_claim_scatter}` | `purity_claim_scatter.png` | `figures.generate_purity_claim_scatter()` |
| `{#fig:token_heatmap}` | `token_heatmap.png` | `figures.generate_token_heatmap()` |
| `{#fig:seed_sensitivity}` | `seed_sensitivity.png` | `figures.generate_seed_sensitivity()` |
| `{#fig:integrity_gate_matrix}` | `integrity_gate_matrix.png` | `figures.generate_integrity_gate_matrix()` |
| `{#fig:formalism_traceability}` | `formalism_traceability.png` | `figures.generate_formalism_traceability()` |
| `{#fig:implementation_circuit}` | `implementation_circuit.png` | `figures.generate_implementation_circuit()` |
| `{#fig:claim_evidence_assay}` | `claim_evidence_assay.png` | `figures.generate_claim_evidence_assay()` |
| `{#fig:integrity_risk_matrix}` | `integrity_risk_matrix.png` | `figures.generate_integrity_risk_matrix()` |
| `{#fig:evidence_tier_ladder}` | `evidence_tier_ladder.png` | `figures.generate_evidence_tier_ladder()` |

Each figure also writes an `.svg` companion alongside its `.png` (see
`docs/output_conventions.md`).

## Token syntax

All numeric values and config-derived text use `{{UPPERCASE_TOKEN}}` syntax.

## Equations

```latex
\begin{equation}
\label{eq:monotone_purity}
p_{\text{out}}^{(i)} > p_{\text{in}}^{(i)} \quad \forall i
\end{equation}
```

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

| Label | File | Generator |
|-------|------|-----------|
| `{#fig:purity_progression}` | `purity_progression.png` | `figures.generate_purity_progression()` |
| `{#fig:karat_grading}` | `karat_grading.png` | `figures.generate_karat_grading_chart()` |
| `{#fig:token_density}` | `token_density.png` | `figures.generate_token_density_chart()` |

## Token syntax

All numeric values and config-derived text use `{{UPPERCASE_TOKEN}}` syntax.

## Equations

```latex
\begin{equation}
\label{eq:monotone_purity}
p_{\text{out}}^{(i)} > p_{\text{in}}^{(i)} \quad \forall i
\end{equation}
```

# Syntax Reference

## Citation syntax

Use Pandoc-crossref and natbib:

- `[@gold_refining_2024]` — parenthetical citation
- `@gold_refining_2024` — narrative citation
- `[@smith2024; @doe2025]` — multiple citations

## Cross-references

- `[@sec:abstract]` — section reference
- `[@eq:purity]` — equation reference
- `[@fig:convergence]` — figure reference
- `[@tbl:stages]` — table reference

## Token syntax

All numeric values and config-derived text use `{{UPPERCASE_TOKEN}}` syntax.

Example: `The refinery achieves {{REFINERY_FINAL_PURITY}} purity ({{REFINERY_FINAL_KARAT}}).`

## Equations

Use `\begin{equation}` and `\label{eq:label}` for numbered equations.

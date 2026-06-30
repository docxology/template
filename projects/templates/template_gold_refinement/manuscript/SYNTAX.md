# Syntax Reference

## Citation syntax

Use Pandoc-crossref and natbib:

- `[@marsden_house_2006]` — parenthetical citation
- `@marsden_house_2006` — narrative citation
- `[@gentner1983structure; @peng2011reproducible]` — multiple citations

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

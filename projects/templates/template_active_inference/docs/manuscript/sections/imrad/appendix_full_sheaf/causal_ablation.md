### Appendix track: causal ablation

`causal_ablation` binds `output/data/causal_ablation_matrix.json` into the full
sheaf appendix. Cells: {{causal_ablation_row_count}}. Complete grid:
`{{causal_ablation_complete_grid}}`.

The matrix is a finite teaching device: every row names a topology, a coupling
value, a perturbation, a scalar effect, and the generated source row that made
the effect admissible. It is not a claim about empirical interventions. It
shows how an intervention-shaped table can be made falsifiable inside the sheaf:
delete one perturbation cell or clear one deterministic flag and the grid gate
fails before the manuscript can reuse the result.

`output/reports/ablation_sensitivity_report.json` then joins those ablation
effects to the sensitivity and uncertainty artifacts. The report contributes
{{ablation_sensitivity_row_count}} source-backed rows, with source-backed status
`{{ablation_sensitivity_source_backed}}`, so the appendix heatmap is a rendered
view of validated JSON rather than a decorative restatement.

The appendix `manuscript_staleness` row points to
`output/reports/manuscript_staleness_report.json`. It checks
{{manuscript_staleness_row_count}} token bindings after hydration, including late
audit variables, and the pass flag is `{{manuscript_staleness_all_fresh}}`.

This is the rendered-output side of the sheaf contract. Source fragments may
contain hydration placeholders, but the public manuscript must not; the staleness report
compares each token's generated value against the resolved markdown so stale
counts are caught after composition, not only during source-file linting.

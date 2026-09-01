### Appendix track: state-space catalog

`state_space_catalog` binds `output/data/state_space_catalog.json` into the full
sheaf appendix. Rows: {{state_space_catalog_row_count}}. All finite:
`{{state_space_catalog_all_finite}}`.

The catalog is the finite-scope boundary for every toy claim in the exemplar.
Each row records a model id, state count, action count, policy count, source
artifact, and finite flag; the validator recomputes that counts are positive
and that every row remains finite. This prevents a manuscript sentence about
exhaustive checking from silently drifting into an unbounded or empirical
setting.

`output/data/state_transition_table.json` makes the boundary operational. It
contains {{state_transition_row_count}} deterministic transition rows and covers
all reachable finite models with status `{{state_transition_all_covered}}`.
Readers can therefore audit not just the number of states, but the actual
state/action/next-state relation used by the model-checking witnesses.

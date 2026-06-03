### Appendix track: artifact diffoscope

`artifact_diffoscope` binds `output/reports/artifact_diffoscope.json` into the
full sheaf appendix. Rows: {{artifact_diffoscope_row_count}}. All equal:
`{{artifact_diffoscope_all_equal}}`.

This diffoscope is deliberately narrow and reproducibility-facing. For each
non-cyclic generated artifact, it compares the saved provenance digest to the
live file digest at validation time. The validator re-derives equality from the
rows, so a stale `all_equal: true` summary cannot hide one changed artifact.

The row count is not a decoration; it is the number of artifact fingerprints
that survived cycle exclusion and therefore can be compared directly. This
keeps the release bundle honest about mutable files while avoiding
self-referential hashes for artifacts that necessarily include their own
provenance.

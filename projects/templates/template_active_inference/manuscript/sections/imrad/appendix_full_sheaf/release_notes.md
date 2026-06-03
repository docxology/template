### Appendix track: release notes evidence

`release_notes` binds `output/reports/release_notes_evidence.json` into the full
sheaf appendix. Rows: {{release_notes_row_count}}. Source-backed:
`{{release_notes_source_backed}}`.

Release notes are treated as claims, not as informal changelog prose. Each row
names a source artifact and a pass/deferred status, so the release note can say
only what validation, bundle, or semantic artifacts support. The validator
re-derives support from rows; flipping the summary bit without fixing a failed
row still fails.

`output/reports/release_attestation.json` is the compact final view over the
same boundary. It records {{release_attestation_row_count}} attestation rows for
validation, release bundle hash, license audit, semantic certificate, and
blocked-scope status, with all-attested flag `{{release_attestation_all_attested}}`.

### Appendix track: artifact license

`artifact_license` binds `output/reports/artifact_license_audit.json` into the
full sheaf appendix. Rows: {{artifact_license_row_count}}. All safe:
`{{artifact_license_all_safe}}`.

The license audit classifies each generated or source-backed artifact under the
public exemplar's configured license boundary. It is intentionally conservative:
generated local outputs and project-owned source files pass, while an artifact
outside those public source kinds would need an explicit provenance and license
row before it could support a manuscript claim.

This is also where the blocked empirical-adapter boundary matters. Private,
restricted, or network-derived data are not smuggled in as evidence; they remain
blocked until privacy, licensing, typed-claim, semantic, and negative-control
gates are implemented in the same artifact path.

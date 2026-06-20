# Syntax

Use uppercase placeholders such as:

- `{{TITLE_METHODS}}`
- `{{ABSTRACT_BODY}}`
- `{{AUTHORING_CONTRACT_BODY}}`
- `{{METHODS_FIGURES}}`
- `{{RESULTS_FIGURES}}`
- `{{CONFIGURATION_FIGURES}}`
- `{{EVALUATION_FIGURES}}`
- `{{CONFIGURED_FIELD_FIGURES}}`
- `{{CONFIGURED_FIELD_SUMMARY_TABLE}}`
- `{{CONFIGURED_FIELD_TABLE}}`
- `{{DESIGN_PRINCIPLE_TABLE}}`
- `{{METHOD_PROTOCOL_TABLE}}`
- `{{PIPELINE_PHASE_TABLE}}`
- `{{AUDIT_RULE_TABLE}}`
- `{{EVALUATION_CRITERIA_TABLE}}`
- `{{QUALITY_PROBE_TABLE}}`
- `{{FAILURE_MODE_TABLE}}`
- `{{AUTHORING_OBLIGATION_TABLE}}`
- `{{PROVENANCE_MATRIX_TABLE}}`

Do not hard-code manuscript figures in section shells. Use generated figure groups:

- `{{METHODS_FIGURES}}`: token-injection pipeline.
- `{{RESULTS_FIGURES}}`: token density, section allocation, and provenance map.
- `{{CONFIGURATION_FIGURES}}`: configured-field origin, section coverage, and field-origin summary.
- `{{EVALUATION_FIGURES}}`: quality-gate matrix.

`{{CONFIGURED_FIELD_FIGURES}}` is retained as a compatibility alias for `{{CONFIGURATION_FIGURES}}`.
The PDF cover image is declared with `paper.cover.image` and generated as
`output/figures/madlib_cover_overview.png`.

Keep Methods content large-grain. Do not replace `{{METHODS_BODY}}` with hand-authored prose in
`manuscript/02_methodology.md`; expand `madlib.method_protocol`, `madlib.pipeline_phases`,
`madlib.quality_probes`, `madlib.failure_modes`, `madlib.audit_rules`, `madlib.contribution_claims`,
and `src/composition.py` instead. Generated output under `output/manuscript/`, rendered PDF/HTML/slides,
and copied deliverables are disposable Stage 02-05 products.

Do not hard-code review-packet lists, token-selection invariants, claim-ledger boundaries, or fork-migration
instructions in section shells. Those belong in config-owned method rows and generated body variables so tests
can prove the visible Methods prose and tables stay aligned.

Avoid raw width literals in the figure reference; the evidence registry scans manuscript numbers and should not treat style-only widths as claims.

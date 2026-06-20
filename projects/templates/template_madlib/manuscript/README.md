# Manuscript

The manuscript directory is intentionally sparse. Numbered Markdown files carry section shells and large-grain placeholders such as `{{METHODS_BODY}}`, `{{METHOD_PROTOCOL_TABLE}}`, and `{{TITLE_RESULTS}}`. The actual content is generated from `manuscript/config.yaml` plus `src/` logic.

Important config blocks:

- `section_titles`: rendered H1 text for each manuscript section.
- `narrative_moves`: source-owned rhetorical plan for each section body.
- `method_protocol`: rows in the Methods protocol table and summary report. Keep these rows comprehensive: schema ingestion, review-scenario declaration, field-origin tracking, lexicon governance, digest construction, invariant review, slot expansion, section-condition handling, body composition, evidence tables, claim-ledger alignment, figure registry generation, manuscript hydration, render validation, review-packet assembly, copy validation, and fork-migration documentation should each remain visible when they are part of the forked method.
- `design_principles`: Methods rows that explain why the generator is structured this way.
- `pipeline_phases`: Methods rows that trace inputs, transformations, outputs, and guards. Each phase should name one concrete input artifact, transformation, output artifact, and gate.
- `evaluation_criteria`: readiness criteria shown in Evaluation and tied to local gates.
- `quality_probes`: Evaluation questions and passing signals for reviewer-facing QA. Add probes when a fork adds method responsibilities, not only when code changes.
- `failure_modes`: risks shown in Limitations with detection and mitigation. Forks that add domain claims should add domain failure modes and validators.
- `authoring_obligations`: Authoring Contract rows for human review and downstream forks.
- `paper.cover.image`: points the shared title-page renderer at the generated cover overview.
- `visualizations`: controls for configured-field, pipeline, allocation, provenance, and quality-gate figures.
- `audit_rules`: rules shown in Methods and enforced by tests/validation. At minimum, every method row should identify action, evidence, and output.
- `contribution_claims`: bounded claims shown in the Introduction. Do not add empirical or publication claims without claim-ledger evidence and matching validators.
- `lexicon` and `slots`: token categories and deterministic slot expansion.

Figure placeholders are grouped by section: `{{METHODS_FIGURES}}`, `{{RESULTS_FIGURES}}`,
`{{CONFIGURATION_FIGURES}}`, and `{{EVALUATION_FIGURES}}`. Configured-field placeholders distinguish
explicit YAML paths from loader-defaulted paths. The generated Configuration section reports both counts and
embeds the enabled origin/coverage figures.

The rendered section order is Abstract, Introduction, Methods, Results, Discussion, Configuration, Evaluation, Reproducibility, Limitations, Scope, Authoring Contract, and References.

When extending the Methods section, edit config-owned method rows and `src/composition.py` together. The source Markdown shells should keep large-grain placeholders such as `{{METHODS_BODY}}` and `{{METHODS_FIGURES}}`; generated Methods prose, tables, figures, and hydrated output remain disposable and must be regenerated through the pipeline.

Method review has three additional obligations:

- Token-selection invariants must remain explicit: only seed, slot, category, ordinal, and ordered category inventory should affect token choice.
- Claim-ledger alignment must travel with prose: a method or domain claim needs a local evidence row, external evidence, or an explicit non-claim boundary.
- Review-packet handoff must include hydrated Markdown, PDF, web output, slides, figures, data, reports, validation results, and copy statistics together.

Run hydration directly when editing manuscript placeholders:

```bash
uv run python projects/templates/template_madlib/scripts/z_generate_manuscript_variables.py
rg "\\{\\{" projects/templates/template_madlib/output/manuscript
```

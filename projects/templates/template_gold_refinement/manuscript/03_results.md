# {{TITLE_RESULTS}} {#sec:results}

The refinery pipeline produces a monotonically increasing purity sequence across {{REFINERY_NUM_STAGES}} stages, reaching final purity of {{REFINERY_FINAL_PURITY}} ({{REFINERY_FINAL_KARAT}}).

## Purity progression

{{FIGURE_PURITY_PROGRESSION}}

| Stage | Name | Output purity | Karat | Gain |
|-------|------|--------------|-------|------|
{{STAGE_TABLE_ROWS}}

## Karat grading scale

{{FIGURE_KARAT_GRADING}}

## Final certification

- **Final purity:** {{REFINERY_FINAL_PURITY}}
- **Final karat:** {{REFINERY_FINAL_KARAT}}
- **Total purity gain:** {{REFINERY_TOTAL_GAIN}}
- **Nine-nines certified:** {{REFINERY_IS_CERTIFIED}}
- **Nines count:** {{REFINERY_FINAL_NINES}}

## Token plan summary

The mega-madlib engine generated {{TOKEN_COUNT}} tokens from seed {{TOKEN_SEED}} across {{CONFIG_NUM_LEXICON_CATEGORIES}} lexicon categories.

{{FIGURE_TOKEN_DENSITY}}

### Category distribution

| Category | Count |
|----------|-------|
{{TOKEN_CATEGORY_TABLE}}

### Section distribution

| Section | Token count |
|---------|-----------|
{{TOKEN_SECTION_TABLE}}

### Provenance trace

| Variable | Category | Value | Section | Source |
|----------|----------|-------|---------|--------|
{{TOKEN_PROVENANCE_TABLE}}

Selected purity adjectives for this section: {{RESULTS_PURITY_ADJ_1}}, {{RESULTS_PURITY_ADJ_2}}. Selected evidence terms: {{RESULTS_EVIDENCE_TERM_1}}, {{RESULTS_EVIDENCE_TERM_2}}, {{RESULTS_EVIDENCE_TERM_3}}.

## Provenance flow

{{FIGURE_PROVENANCE_SANKEY}}

## Purity vs claim support

{{FIGURE_PURITY_CLAIM_SCATTER}}

## Token selection sensitivity

{{FIGURE_TOKEN_HEATMAP}}

## Integrity gate matrix

The integrity gate matrix in [@fig:integrity_gate_matrix] makes the validation story visible: audit rules are not prose promises unless they connect to tests, manuscript surfaces, and generated artifacts.

{{FIGURE_INTEGRITY_GATE_MATRIX}}

## Formalism traceability

The formalism traceability view in [@fig:formalism_traceability] links each equation-backed formalism to the source surface that owns it. This is the visual counterpart to [@tbl:formalism_registry].

{{FIGURE_FORMALISM_TRACEABILITY}}

## Implementation circuit

The implementation circuit in [@fig:implementation_circuit] shows how the concept is executed rather than merely described. Configuration feeds code; code emits variables, figures, and reports; manuscript hydration consumes those artifacts; validators feed errors back to source ownership. The figure is intentionally circular because the artifact is not complete after prose generation. It is complete only after the validation return path has no blocking evidence, citation, reference, or render failures.

{{FIGURE_IMPLEMENTATION_CIRCUIT}}

## Claim-evidence assay

The claim-evidence assay in [@fig:claim_evidence_assay] turns the assaying stage into a reader-facing diagnostic. Each bar is a contribution claim from `manuscript/config.yaml`, and each annotation names the source file or symbol used to support it. This makes the contribution ledger inspectable at the same level as the purity plots: unsupported claims would appear as failed assays rather than remaining hidden in prose.

{{FIGURE_CLAIM_EVIDENCE_ASSAY}}

## Scientific-integrity risk matrix

The integrity risk matrix in [@fig:integrity_risk_matrix] plots severity against detectability for the {{INTEGRITY_DIMENSION_COUNT}} integrity dimensions in [@tbl:integrity_dimensions]. Bubble size encodes residual risk, while color encodes the source tier that owns the evidence surface. This makes boundary failures more visible than cosmetic source checks without hiding whether the support comes from config, source code, claim ledger, generated metric, artifact, bibliography, or validation gate. The matrix is intentionally local: it prioritizes where this exemplar needs source ownership, not where every future manuscript should focus.

{{FIGURE_INTEGRITY_RISK_MATRIX}}

## Evidence-tier ladder

The evidence-tier ladder in [@fig:evidence_tier_ladder] summarizes the evidence surfaces available to the shared template evidence registry or, before that gate has run, the fallback source tiers from the integrity model. It gives a quick view of whether the manuscript is leaning on generated metrics, claim-ledger facts, bibliography records, source code, or disposable artifacts.

{{FIGURE_EVIDENCE_TIER_LADDER}}

| Source tier | Count | Role |
|-------------|-------|------|
{{EVIDENCE_TIER_TABLE}}
: Evidence tiers used by the integrity model and shared registry when available. {#tbl:evidence_tiers}

## Contribution claims

| Claim | Statement | Evidence | Boundary |
|-------|-----------|----------|----------|
{{CONTRIBUTION_CLAIMS_TABLE}}

The project-local claim-support assay reports {{CLAIM_SUPPORT_SUPPORTED}} supported claims out of {{CLAIM_SUPPORT_TOTAL}} total claims, for {{CLAIM_SUPPORT_RATE}} support. Unsupported claims: {{CLAIM_SUPPORT_UNSUPPORTED}}. The generated project report path is `{{CLAIM_SUPPORT_REGISTRY_PATH}}`; the shared template evidence report remains `output/reports/evidence_registry.json`.

## Shared evidence registry summary

When the template evidence gate has run, the shared registry supplies source-tiered facts used by the evidence validator. Current fact count available to this variable pass: {{SHARED_EVIDENCE_FACT_COUNT}}.

| Fact kind | Count |
|-----------|-------|
{{SHARED_EVIDENCE_KIND_TABLE}}
: Shared evidence-registry fact kinds when available. {#tbl:shared_evidence_kinds}

## Figure quality report

The visualization registry is paired with `{{FIGURE_QUALITY_REPORT_PATH}}`, a generated QA report that checks PNG and SVG existence, file dimensions, nonblank pixel mass, color variance, and registry parity. Current status: {{FIGURE_QUALITY_STATUS}} with {{FIGURE_QUALITY_PASSING_COUNT}}/{{FIGURE_QUALITY_TOTAL}} registered figures passing and registry parity reported as {{FIGURE_QUALITY_REGISTRY_PARITY}}. PNG remains the manuscript render path; SVG is the companion technical artifact for inspection, reuse, and source-level debugging. [@tbl:figure_quality] summarizes the generated surface.

| Figure | PNG | SVG | Dimensions | Nonwhite | Variance | Status |
|--------|-----|-----|------------|----------|----------|--------|
{{FIGURE_QUALITY_TABLE}}
: Figure-quality report generated from source-owned figure specs. {#tbl:figure_quality}

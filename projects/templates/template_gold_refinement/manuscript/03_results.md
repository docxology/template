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

The provenance flow in [@fig:provenance_sankey] makes the refinement analogy
auditable as a directed source path rather than a decorative metaphor. The graph
starts from the same stage sequence used in the purity table and carries that
sequence forward to certification, with edge width proportional to the purity
gain owned by `src/refinery.py::run_refinery`. A reader can therefore ask where
each improvement enters the pipeline and whether it is supported by the same
source that generated the reported purity numbers.

The main result is structural: certification is not allowed to appear as a
terminal label detached from the intermediate stages. It is only reached after
the upstream transformations have been generated, ordered, and connected. This
matters for the manuscript contract because provenance is doing more than
recording file paths. It is preserving causal custody from raw material through
assay and final certification, so a later change to the stage model must move
through the same graph, table, and validation surfaces.

{{FIGURE_PROVENANCE_SANKEY}}

## Purity vs claim support

The purity-versus-claim-support view in [@fig:purity_claim_scatter] places the
metallurgical purity sequence beside the contribution ledger. This prevents the
paper from treating purity as an isolated aesthetic score. A point can advance
only when two surfaces agree: the refinery computation supplies the stage purity,
and the claim-support registry supplies the cumulative evidence exposure for
the claims being made at that level of refinement.

In the current generated assay, {{CLAIM_SUPPORT_SUPPORTED}} of
{{CLAIM_SUPPORT_TOTAL}} contribution claims are supported
({{CLAIM_SUPPORT_RATE}}). The figure is useful because it would make a weaker
state visible immediately: a manuscript could still show late-stage material
purity while failing to carry its claims along the evidence axis. In that case,
the visual story would split, and the reader would see that certification prose
had outrun claim support. Here the two axes are deliberately co-present, so the
results section cannot celebrate purity while hiding unsupported contribution
language in a separate paragraph.

{{FIGURE_PURITY_CLAIM_SCATTER}}

## Token selection sensitivity

The token selection heatmap in [@fig:token_heatmap] turns the mega-madlib engine
into an inspectable sensitivity surface. The manuscript uses seed {{TOKEN_SEED}}
for the reported token plan, but the figure asks a neighboring question: how do
selected inventory indices move when seeds and lexicon categories vary? This is
not a stochastic robustness claim. It is a deterministic audit of the digest
rule in `src/composition.py::generate_token_plan` against the configured
lexicon inventories in `manuscript/config.yaml`.

This view separates three issues that prose alone tends to blur. First, token
injection is reproducible: the same seed and inventory generate the same
choices. Second, the available vocabulary is a real input surface: a thin or
unbalanced category would be visible as a constrained selection band. Third,
render-time hydration is not silently sampling new language. The heatmap
therefore protects the manuscript from a common generative-writing failure mode,
where a polished section appears stable but its wording is actually controlled
by hidden or late-bound choices. The result is a sensitivity check on authoring
machinery, not a claim that any particular synonym is scientifically superior.

{{FIGURE_TOKEN_HEATMAP}}

## Integrity gate matrix

The integrity gate matrix in [@fig:integrity_gate_matrix] makes the validation story visible: audit rules are not prose promises unless they connect to tests, manuscript surfaces, and generated artifacts.

Each row begins as a configured audit rule, but the matrix asks whether that rule
has enough contact with the project to matter. A rule that names a risk but does
not touch tests, manuscript text, or generated outputs remains advisory. A rule
that reaches all three surfaces becomes enforceable: tests can fail, manuscript
hydration can expose stale or missing variables, and generated reports can show
whether the artifact exists. The matrix is therefore a map of operational
coverage, not a checklist of intentions.

This is the validation story that supports the broader purity analogy. Smelting
can remove obvious dross, but scientific-integrity failures often survive as
well-written unsupported claims, stale tables, or figures that no longer match
their source data. By separating missing, partial, and full coverage across gate
surfaces, [@fig:integrity_gate_matrix] identifies where a future author would
need to add a test, generated artifact, or manuscript variable before
strengthening a claim. The result is intentionally local to this exemplar:
coverage is measured against the specific audit rules configured here, not
against a universal publication-readiness standard.

{{FIGURE_INTEGRITY_GATE_MATRIX}}

## Formalism traceability

The formalism traceability view in [@fig:formalism_traceability] links each equation-backed formalism to the source surface that owns it. This is the visual counterpart to [@tbl:formalism_registry].

The registry currently exposes {{FORMALISM_COUNT}} source-owned formalisms. The
figure makes their ownership legible by linking each formalism to its equation
identifier and to the source surface that emits it. That linkage is important
because equation labels can otherwise create a false sense of rigor: a numbered
equation looks formal even when its assumptions, variables, and implementation
owner are not recoverable. Here the formal object must remain connected to
`src/formalisms.py`, the generated registry table, and the manuscript reference
that consumes it.

The graph also helps distinguish formal support from decorative notation. A
formalism earns a place in the manuscript only when it names a claim boundary or
computation that the source can regenerate. If an equation is added without a
source owner, it should fail this traceability pattern before it becomes part of
the results narrative. Conversely, if the source registry changes, the visual
traceability layer should change with it. That is the desired behavior: the
formal layer is a generated contract, not hand-maintained mathematical
ornamentation.

{{FIGURE_FORMALISM_TRACEABILITY}}

## Implementation circuit

The implementation circuit in [@fig:implementation_circuit] shows how the concept is executed rather than merely described. Configuration feeds code; code emits variables, figures, and reports; manuscript hydration consumes those artifacts; validators feed errors back to source ownership. The figure is intentionally circular because the artifact is not complete after prose generation. It is complete only after the validation return path has no blocking evidence, citation, reference, or render failures.

The circuit is the results section's strongest guard against a prose-only
interpretation of the template. It shows four layers that must remain connected:
configuration, project code, generated artifacts, and validation feedback. A
change in `manuscript/config.yaml` is not complete when the file is saved. It
must pass through source functions, generate updated variables and figures,
hydrate the manuscript, and survive the validator return path. The circular
layout is therefore a process claim: the manuscript is complete only when the
loop closes without unresolved failures.

This view also explains why the exemplar treats generated output as disposable
but not optional. Output files are not edited by hand, yet they are the evidence
surface through which the reader and validators inspect the source contract.
When a validator reports a broken citation, missing figure, stale variable, or
unsupported claim, the circuit points backward to the owning source surface
rather than encouraging local patching of rendered Markdown. That direction of
repair is central to the manuscript's definition of refinement.

{{FIGURE_IMPLEMENTATION_CIRCUIT}}

## Claim-evidence assay

The claim-evidence assay in [@fig:claim_evidence_assay] turns the assaying stage into a reader-facing diagnostic. Each bar is a contribution claim from `manuscript/config.yaml`, and each annotation names the source file or symbol used to support it. This makes the contribution ledger inspectable at the same level as the purity plots: unsupported claims would appear as failed assays rather than remaining hidden in prose.

The generated assay currently reports {{CLAIM_SUPPORT_SUPPORTED}} supported
claims out of {{CLAIM_SUPPORT_TOTAL}}. The value of the figure is not the perfect
score by itself; it is the way the score is forced to name its evidence surface
and boundary. A contribution claim is not merely present in prose. It must be
registered, matched to supporting evidence, and assigned a boundary that tells
the reader what the support does not cover. This keeps contribution language
from drifting beyond the local evidence available in the project.

The bar-plus-topology design makes two failure modes visible. If a claim lacks
support, the bar view would show the failed assay directly. If a claim is
supported only within a narrow scope, the graph side still preserves the boundary
classification rather than flattening the result into a binary pass. That
matters for the security and integrity extensions in this manuscript: a claim
can be source-owned without becoming a compliance claim, and a generated assay
can confirm local evidence without pretending to certify the wider supply chain.

{{FIGURE_CLAIM_EVIDENCE_ASSAY}}

## Scientific-integrity risk matrix

The integrity risk matrix in [@fig:integrity_risk_matrix] plots severity against detectability for the {{INTEGRITY_DIMENSION_COUNT}} integrity dimensions in [@tbl:integrity_dimensions]. Bubble size encodes residual risk, while color encodes the source tier that owns the evidence surface. This makes boundary failures more visible than cosmetic source checks without hiding whether the support comes from config, source code, claim ledger, generated metric, artifact, bibliography, or validation gate. The matrix is intentionally local: it prioritizes where this exemplar needs source ownership, not where every future manuscript should focus.

The generated summary is: {{INTEGRITY_RISK_SUMMARY}} The matrix turns that
summary into a triage surface. Severity asks how damaging a failure would be if
it entered the manuscript. Detectability asks how readily the current project
would catch it. Residual risk then becomes visible as size rather than being
buried in a paragraph. A large point in a hard-to-detect region is a signal that
the authoring contract needs stronger source ownership or a clearer boundary,
even if the current text renders successfully.

Color is equally important because not all evidence tiers have the same
authority. A bibliography-backed statement, a source-code computation, a claim
ledger row, and a validation-gate result can all support prose, but they support
different kinds of claims. The risk matrix keeps that distinction visible. It
does not collapse integrity into a single score, and it does not imply that
every high-severity issue has already been eliminated. It shows which risks this
exemplar has made inspectable and where future work would need to add stronger
measurement before using stronger language.

{{FIGURE_INTEGRITY_RISK_MATRIX}}

## Evidence-tier ladder

The evidence-tier ladder in [@fig:evidence_tier_ladder] summarizes the evidence surfaces available to the shared template evidence registry or, before that gate has run, the fallback source tiers from the integrity model. It gives a quick view of whether the manuscript is leaning on generated metrics, claim-ledger facts, bibliography records, source code, or disposable artifacts.

The ladder complements the risk matrix by counting source tiers rather than
plotting risks. When the shared evidence registry is available, the manuscript
can report {{SHARED_EVIDENCE_FACT_COUNT}} source-tiered facts to the validation
surface. When that registry is not available, the same figure falls back to the
integrity model's configured tiers. Either way, the reader sees the evidentiary
mix instead of receiving an undifferentiated assurance that evidence exists.

This matters because evidence balance is itself an integrity signal. A manuscript
that leans only on generated artifacts may be reproducible but weakly grounded
in source rationale. A manuscript that leans only on bibliography may be
well-cited but not locally executable. A manuscript that leans only on tests may
catch regressions while still failing to explain claim boundaries to readers.
The ladder gives a compact audit of that mix, while [@tbl:evidence_tiers] keeps
the counts visible in tabular form. Together they close the figure sequence by
showing not only that the {{FIGURE_QUALITY_TOTAL}} public figures render, but
also which source tiers make their claims inspectable.

{{FIGURE_EVIDENCE_TIER_LADDER}}

| Source tier | Count | Role |
|-------------|-------|------|
{{EVIDENCE_TIER_TABLE}}
: Evidence tiers used by the integrity model and shared registry when available. {#tbl:evidence_tiers}

## Adversarial security assay

The adversarial assay reports {{SECURITY_ASSAY_SUMMARY}} {{SECURITY_ASSAY_BOUNDARY}} The rows are generated from `gold_refinement.security_assay` and are intentionally tabular rather than a new public figure, so the visual registry remains the stable {{FIGURE_QUALITY_TOTAL}}-figure contract.

| ID | Threat | Standard or guidance | Evidence surface | Validator or gate | Claim boundary |
|----|--------|----------------------|------------------|-------------------|----------------|
{{SECURITY_ASSAY_TABLE}}
: Source-owned adversarial security assay. {#tbl:security_assay}

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

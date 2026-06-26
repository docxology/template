# {{TITLE_METHODOLOGY}} {#sec:methodology}

The refinery pipeline consists of {{REFINERY_NUM_STAGES}} canonical stages, each mapping a metallurgical operation to a manuscript-composition operation. The pipeline is implemented in `src/refinery.py` and validated by `src/purity.py`. The methods surface now has three coupled layers: the refinery stages, the mega-madlib token plan, and the generated formalism registry.

## Stage definitions

| # | Stage | Output purity | Karat | Metallurgical operation |
|---|-------|-------------|-------|------------------------|
{{STAGE_TABLE_ROWS}}

## Purity progression

The purity sequence across all stages is: {{PURITY_SEQUENCE}}

Purity is strictly increasing — enforced by `assert_monotone_increase()` which raises `ValueError` if any stage's output purity does not exceed its input. Formally, for stages $s_1, \ldots, s_n$ with input purity $p_{\text{in}}^{(i)}$ and output purity $p_{\text{out}}^{(i)}$:

$$
p_{\text{out}}^{(i)} > p_{\text{in}}^{(i)} \quad \text{and} \quad p_{\text{in}}^{(i+1)} = p_{\text{out}}^{(i)} \quad \forall i \in \{1, \ldots, n-1\}
$$

The full purity progression is shown in [@fig:purity_progression] (see [@sec:results]).

## Formalism registry

The formal layer is generated from `src/formalisms.py`, not hand-numbered prose. [@tbl:formalism_registry] lists the source evidence for each equation, and the equation blocks below are auto-numbered by the renderer.

| ID | Formalism | Equation | Source |
|----|-----------|----------|--------|
{{FORMALISM_TABLE_ROWS}}
: Source-owned formalism registry. {#tbl:formalism_registry}

{{FORMALISM_EQUATION_BLOCKS}}

## Token selection

The mega-madlib engine selects tokens from config-owned lexicon categories using a deterministic digest:

$$
\text{index} = \text{int}\left(\text{SHA-256}\left(\text{seed} \mid \text{slot} \mid \text{category} \mid \text{ordinal} \mid \text{inventory}\right)[:12], 16\right) \mod n
$$

where $n$ is the size of the lexicon category inventory. Selected metallurgical terms: {{METHOD_METAL_TERM_1}}, {{METHOD_METAL_TERM_2}}, {{METHOD_METAL_TERM_3}}. Selected manuscript terms: {{METHOD_MANUSCRIPT_TERM_1}}, {{METHOD_MANUSCRIPT_TERM_2}}. The same digest rule is formalized in [@eq:token_digest], while the gate vocabulary for this section binds {{METHOD_GATE_TERM_1}}, {{METHOD_GATE_TERM_2}}, and {{METHOD_GATE_TERM_3}} to concrete validation surfaces.

## Config-owned lexicon

| Category | Count | Sample |
|----------|-------|--------|
{{LEXICON_TABLE}}

## Karat grading

Karat grades map purity fractions to standard gold fineness:

- 9K = 37.5% (ore stage)
- 18K = 75.0% (smelting stage)
- 22K = 91.67% (assaying stage)
- 24K = 99.9% (cupellation stage)
- Nine-nines = 99.9999999% (certification stage)

The mapping is implemented in `src/purity.py::karat_for_purity()`. The karat grading chart is shown in [@fig:karat_grading] (see [@sec:results]).

## Pipeline phases

| Phase | Input | Transformation | Output | Guard |
|-------|-------|----------------|--------|-------|
{{PIPELINE_PHASES_TABLE}}

The pipeline table is intentionally operational rather than decorative: a fork that changes the stages must update the source function, generated variables, figures, and validation gates together.

## Implementation trace

The implementation circuit shown in [@fig:implementation_circuit] is the method's wiring diagram. It distinguishes three ownership layers. First, authored sources own intent: config declares vocabulary and claims, `src/` owns computation, and the claim ledger registers evidence facts. Second, generated artifacts own observation: token plans, figures, resolved Markdown, reports, and dashboards are rebuilt rather than edited. Third, template gates own permission to promote the manuscript: unresolved tokens, unsupported facts, missing citations, broken references, and invalid PDFs block certification.

This split keeps the gold metaphor honest. A fork is allowed to change the ore, the furnace, or the assay, but it must do so in the source layer and then let the generated and validation layers expose the consequences.

## Scientific integrity model

The integrity model converts manuscript risks into source-owned dimensions. It does not replace peer review or domain validation. It names the failure class, severity, detectability, evidence surface, owner, and validator so the manuscript can distinguish "the analogy is vivid" from "the claim is backed by a regenerable check." The current pass reports {{INTEGRITY_RISK_SUMMARY}}

| ID | Dimension | Residual risk | Owner | Validator |
|----|-----------|---------------|-------|-----------|
{{INTEGRITY_DIMENSION_TABLE}}
: Source-owned scientific-integrity dimensions. {#tbl:integrity_dimensions}

The residual-risk score is deliberately simple: high severity and low detectability raise priority. The score is not a universal risk model; it is a local audit heuristic used to decide where a fork must add validators before expanding claims.

| Owner | Dimensions |
|-------|------------|
{{INTEGRITY_OWNER_TABLE}}
: Integrity dimensions by owning surface. {#tbl:integrity_owners}

This table also makes generated-number ownership explicit. Counts, support rates, and figure labels belong to regenerated reports and registries; the manuscript consumes them through variables. Authored prose may interpret those values, but it should not silently restate them as hand-maintained facts.

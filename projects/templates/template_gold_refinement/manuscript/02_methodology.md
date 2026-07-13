# {{TITLE_METHODOLOGY}} {#sec:methodology}

## Research design

We conducted a deterministic, artifact-based methods demonstration. The research object is one executable manuscript compendium comprising authored configuration and Markdown, project source code, generated data and reports, registered figures, and rendered publication files. The unit of transformation is a refinery stage; the unit of lexical composition is a configured token slot; the unit of evidentiary evaluation is a registered claim or gate. No human participants, stochastic sampling, trained model, or inferential statistical test is involved.

The method asks whether a metallurgical stage structure can be implemented as an inspectable manuscript workflow. It does **not** test whether the resulting purity values predict reader judgments, scientific validity, or editorial acceptance. Accordingly, all reported quantities are properties of this executable exemplar: stage outputs, token selections, registry contents, and validator outcomes.

The implementation has four coupled layers: (1) a {{REFINERY_NUM_STAGES}}-stage refinery model, (2) a deterministic mega-madlib token plan, (3) source-owned formalisms and evidence registries, and (4) validation gates that constrain certification language. This separation follows research-compendium practice, in which narrative, code, data, environment, and outputs remain distinct but linked [@marwick2018packaging]. It also follows executable-paper and notebook traditions in coupling narrative to runnable analysis rather than copying results into prose [@leisch2002sweave; @rule2019jupyter]. The narrower contribution here is provenance at the token and claim levels; the workflow does not purport to validate scientific truth.

## Source-domain construction and analogy boundary

Structured reporting guidelines provide the closest scholarly analogue for the gate layer, but they also set its limit. CONSORT, STROBE, PRISMA, ARRIVE, and the EQUATOR Network define field-specific reporting items so a manuscript can be inspected, appraised, and in some cases replicated more easily [@schulz2010consort; @vonelm2007strobe; @page2021prisma; @percie_du_sert2020arrive; @equator_network_reporting_guidelines]. In this exemplar, token coverage, evidence registration, and render validation play a similar internal role: they make omissions visible and bind declarations to artifacts. They do not test whether an external study was designed well, executed correctly, or substantively true.

The source domain was constructed from pre-1800 descriptions of extraction, smelting or refining, assay, parting/cupellation, fineness, and public marking. Pliny supplies extraction and touchstone context; Biringuccio and Agricola describe staged metallurgical operations; Badcock and the Goldsmiths' Company chronology document standards, weights, statutes, and marks; and Cramer presents assay as a disciplined relation between theory and practice [@pliny_natural_history_33; @biringuccio_pirotechnia_1540; @agricola_de_re_metallica_1556; @badcock_touchstone_1678; @goldsmiths_hallmarking_history; @cramer_assaying_metals_1741].

We normalized these historically plural practices into a five-stage relational model. The inclusion criterion was functional relevance to one of five target-domain operations: acquiring draft material, removing evident defects, testing claims, resolving document integrity, or recording a terminal validation state. The ordering preserves the refinement relation needed by the target workflow; it is not evidence that every historical workshop used this sequence or modern chemical theory. The analogy therefore transfers relations among separation, test, refinement, and marking—not regulatory authority, material equivalence, or empirical measures of prose quality [@gentner1983structure; @hesse1966models].

## Inputs and source ownership

The run begins from three authored inputs: `manuscript/config.yaml`, the Markdown section shells in `manuscript/`, and executable functions in `src/`. Configuration owns the seed, lexicon inventories, slot declarations, contribution claims, audit rules, and security-assay rows. Source modules own stage calculations, token selection, formalism records, evidence aggregation, and figure specifications. Markdown owns interpretation and cross-references but consumes computed values only through generated variables.

Generated files are observations, not editing surfaces. The analysis writes the refinery result, token plan, claim-support registry, integrity summaries, and figure-quality records; manuscript hydration then resolves variables into disposable Markdown. This ownership rule prevents a reported number or selected phrase from being corrected only in the rendered paper while its computational source remains unchanged.

## Stage definitions

| # | Stage | Output purity | Karat | Metallurgical operation |
|---|-------|-------------|-------|------------------------|
{{STAGE_TABLE_ROWS}}

## Refinery model and purity measure

The purity sequence across all stages is: {{PURITY_SEQUENCE}}

Each stage record contains an order, a metallurgical operation, its manuscript analogue, an input purity, and an output purity. The canonical values are design parameters declared in `src/refinery.py`; they are not estimated from a corpus or calibrated against external ratings. Their methodological role is to create a transparent ordinal progression on the bounded interval $[0,1]$.

The primary invariants are strict monotonicity, sequential stage order, and adjacent-state continuity. `assert_monotone_increase()` raises `ValueError` if a state fails to exceed its predecessor; `run_refinery()` also rejects empty pipelines, nonsequential order, and any stage whose input differs from the preceding output. For stages $s_1, \ldots, s_n$:

$$
p_{\text{out}}^{(i)} > p_{\text{in}}^{(i)} \quad \text{and} \quad p_{\text{in}}^{(i+1)} = p_{\text{out}}^{(i)} \quad \forall i \in \{1, \ldots, n-1\}
$$

The reverse-assay function `stages_to_target()` returns the shortest ordered prefix whose terminal output reaches a requested purity. Prefix restriction is essential: later stages depend on earlier states and cannot be selected as an unordered set. The full progression is reported in [@fig:purity_progression] (see [@sec:results]). Because the values are constructed, the analysis is descriptive and deterministic; no uncertainty interval or significance test is appropriate.

## Formalism registry

The formal layer is generated from `src/formalisms.py`, not hand-numbered prose. [@tbl:formalism_registry] lists the source evidence for each equation, and the equation blocks below are auto-numbered by the renderer.

| ID | Formalism | Equation | Source |
|----|-----------|----------|--------|
{{FORMALISM_TABLE_ROWS}}
: Source-owned formalism registry. {#tbl:formalism_registry}

{{FORMALISM_EQUATION_BLOCKS}}

## Deterministic token composition

The mega-madlib engine selects tokens from config-owned lexicon categories using a deterministic digest:

$$
\text{index} = \text{int}\left(\text{SHA-256}\left(\text{seed} \mid \text{slot} \mid \text{category} \mid \text{ordinal} \mid \text{inventory}\right)[:12], 16\right) \mod n
$$

where $n$ is the inventory size. For each declared slot, the procedure concatenates the seed, slot name, category, one-based ordinal, and the complete ordered inventory; hashes the UTF-8 string; converts the first 12 hexadecimal characters to an integer; and reduces it modulo $n$. Including the complete inventory makes selection sensitive to both membership and order. Replaying the same configuration reproduces the same plan; changing the seed, slot specification, or inventory may change it.

Each selected value is recorded with its variable name, slot, category, section, ordinal, and configuration path. This record permits exact replay and source tracing but does not imply that the selected synonym is semantically superior. Selected metallurgical terms are {{METHOD_METAL_TERM_1}}, {{METHOD_METAL_TERM_2}}, and {{METHOD_METAL_TERM_3}}; selected manuscript terms are {{METHOD_MANUSCRIPT_TERM_1}} and {{METHOD_MANUSCRIPT_TERM_2}}. [@eq:token_digest] formalizes the rule, while {{METHOD_GATE_TERM_1}}, {{METHOD_GATE_TERM_2}}, and {{METHOD_GATE_TERM_3}} name the corresponding validation surfaces.

## Config-owned lexicon

| Category | Count | Sample |
|----------|-------|--------|
{{LEXICON_TABLE}}

## Derived grading vocabulary

Karat grades map purity fractions to a gold-fineness vocabulary used here as an analogy surface. The pre-1800 evidence supports fineness as a regulated testing and marking problem, but not the modern nine-nines target used by this local software predicate [@badcock_touchstone_1678; @goldsmiths_hallmarking_history; @cramer_assaying_metals_1741; @marsden_house_2006; @lbma_good_delivery_rules]:

- 9K = 37.5% (ore stage)
- 18K = 75.0% (smelting stage)
- 22K = 91.67% (assaying stage)
- 24K = 99.9% (cupellation stage)
- Nine-nines = 99.9999999% (certification stage)

`src/purity.py::karat_for_purity()` assigns the highest configured grade whose threshold does not exceed the stage purity. The nine-nines label is a deliberately stringent local predicate. It is neither a continuous measure of manuscript quality nor an assertion about a universal gold-market threshold. The grading chart appears in [@fig:karat_grading] (see [@sec:results]).

## Execution procedure

| Phase | Input | Transformation | Output | Guard |
|-------|-------|----------------|--------|-------|
{{PIPELINE_PHASES_TABLE}}

For each run, the procedure is:

1. Parse and validate the configuration, including lexicon categories, slots, claims, audit rules, and policy declarations.
2. Execute the canonical stage sequence and reject discontinuous, nonmonotone, empty, or misordered refinery definitions.
3. Generate the token plan and record every selection with its configuration provenance.
4. Build claim-support, integrity, formalism, adversarial-assay, and figure registries from their source owners.
5. Write analysis artifacts and manuscript variables, then hydrate the Markdown section shells.
6. Render publication formats and run reference, evidence, figure, and document validators.
7. Permit certification language only when the required local predicates and gates pass.

The phase table identifies the input, transformation, output, and guard for each step. A fork that modifies a stage or claim must update its source definition, generated variables, visualizations, and validators together.

## Traceability and artifact lineage

The implementation circuit shown in [@fig:implementation_circuit] is the method's wiring diagram. It distinguishes three ownership layers. First, authored sources own intent: config declares vocabulary and claims, `src/` owns computation, and the claim ledger registers evidence facts. Second, generated artifacts own observation: token plans, figures, resolved Markdown, reports, and dashboards are rebuilt rather than edited. Third, template gates own permission to promote the manuscript: unresolved tokens, unsupported facts, missing citations, broken references, and invalid PDFs block certification. This is the manuscript analogue of provenance-aware workflow design: entities, activities, agents, and generated outputs are kept traceable so readers can assess reliability rather than infer it from polished prose [@moreau2013prov; @belhajjame2015ontologies].

This split keeps the gold metaphor honest. A fork is allowed to change the ore, the furnace, or the assay, but it must do so in the source layer and then let the generated and validation layers expose the consequences.

## Evaluation and acceptance criteria

Evaluation is criterion-based rather than comparative. The run is assessed against predeclared local invariants: complete token hydration, valid stage ordering and monotonicity, registered claim support, resolvable citations and cross-references, registry-aligned figures, successful rendering, and explicit security-claim boundaries. [@eq:integrity_vector] retains these outcomes as a vector so one strong surface cannot compensate for a failed required gate. [@eq:claim_support] reports the proportion of locally registered contribution claims with resolvable evidence pointers; it does not score the truth or importance of those claims.

The terminal predicate in [@eq:certification_predicate] requires the configured final purity threshold and successful required gates. Consequently, "certified" means internally consistent and reproducibly generated under this project's declared rules. It does not mean peer reviewed, externally replicated, historically authoritative, secure, or compliant with a reporting standard. Detailed probes and audit rules are reported in [@sec:evaluation].

### Adversarial assay

The implementation trace handles accidental drift: missing tokens, unsupported claims, malformed citations, stale figures, or broken renders. A security assay adds a different question: could the manuscript sound certified while omitting threat scope, supply-chain provenance, or scan evidence? The assay therefore treats zero trust, secure software development, supply-chain provenance, attack-path modeling, SBOM standards, and secure-by-design guidance as boundary-setting standards rather than proof of compliance [@nist_sp800_207_zero_trust; @nist_sp800_218_ssdf; @slsa_v1_2; @sigstore_docs; @mitre_attack; @cyclonedx_spec; @spdx_spec; @cisa_secure_by_design].

The assay is implemented as source-owned rows in `gold_refinement.security_assay` and generated records from `src/security_assay.py`. Each row must name a threat, standard or guidance source, local evidence surface, validator, and claim boundary, as specified by [@eq:adversarial_assay] and reported in [@tbl:security_assay]. This study did not run Codex Security or Deep Security Scan and reports no vulnerability findings. Completeness of the assay schema therefore supports scope disclosure, not security compliance.

### Scientific-integrity risk model

The integrity model converts manuscript risks into source-owned dimensions. It does not replace peer review or domain validation. It names the failure class, severity, detectability, evidence surface, owner, and validator so the manuscript can distinguish "the analogy is vivid" from "the claim is backed by a regenerable check." The current pass reports {{INTEGRITY_RISK_SUMMARY}}

| ID | Dimension | Residual risk | Owner | Validator |
|----|-----------|---------------|-------|-----------|
{{INTEGRITY_DIMENSION_TABLE}}
: Source-owned scientific-integrity dimensions. {#tbl:integrity_dimensions}

The residual-risk score is an ordinal prioritization heuristic: higher severity and lower detectability raise review priority. It was not fitted to incident data, validated against external judgments, or designed for comparison across projects. Its sole use is to identify where this exemplar—or a fork—needs stronger ownership, evidence, or validation before expanding a claim.

| Owner | Dimensions |
|-------|------------|
{{INTEGRITY_OWNER_TABLE}}
: Integrity dimensions by owning surface. {#tbl:integrity_owners}

This table also makes generated-number ownership explicit. Counts, support rates, and figure labels belong to regenerated reports and registries; the manuscript consumes them through variables. Authored prose may interpret those values, but it should not silently restate them as hand-maintained facts.

### Multi-objective purity

Scalar stage purity is retained only as the state variable of the refinery analogy. `src/purity.py::PurityVector` separately records stage completion, claim support, token provenance, and figure quality on $[0,1]$. The vector exposes its weakest dimension and a conjunctive all-complete predicate but intentionally defines no weighted average. This prevents a perfect render or terminal stage value from numerically compensating for unsupported claims or missing provenance. Weighting these dimensions would require an external validation study and is outside the present design.

## Reproducibility and validity safeguards

Determinism is assessed by exact replay from the same ordered configuration and source revision. Provenance is assessed by the existence of a path from each reported token, claim, equation, and figure to an owning source and generated record. Negative controls in the test suite exercise malformed configuration and invalid refinery states; figure checks assess file presence, registry parity, dimensions, nonblank content, and color variance. Environment and regeneration details are given in [@sec:reproducibility].

Four validity limits govern interpretation. First, **construct validity** is limited because purity is a designed workflow state, not a validated measure of writing quality. Second, **external validity** is limited to this exemplar until other domains implement their own mappings and validators. Third, **historical validity** is bounded by the normalized analogy and should not be read as a universal account of metallurgical practice. Fourth, **criterion validity** is local: passing gates demonstrates source ownership and internal consistency, not correctness of domain claims. These limits are part of the method's acceptance rule, not qualifications added after results are known.

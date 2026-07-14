# Methodology: The Refinery Pipeline {#sec:methodology}

## Research design

We conducted a deterministic, artifact-based methods demonstration. The research object is one executable manuscript compendium comprising authored configuration and Markdown, project source code, generated data and reports, registered figures, and rendered publication files. The unit of transformation is a refinery stage; the unit of lexical composition is a configured token slot; the unit of evidentiary evaluation is a registered claim or gate. No human participants, trained model, or empirical manuscript-quality outcome is involved. A separate seed-sensitivity pass uses deterministic technical replicates to describe token-plan variability and is not an inferential test of writing quality.

The method asks whether a metallurgical stage structure can be implemented as an inspectable manuscript workflow. It does **not** test whether the resulting purity values predict reader judgments, scientific validity, or editorial acceptance. Accordingly, all reported quantities are properties of this executable exemplar: stage outputs, token selections, registry contents, and validator outcomes.

The implementation has four coupled layers: (1) a 5-stage refinery model, (2) a deterministic mega-madlib token plan, (3) source-owned formalisms and evidence registries, and (4) validation gates that constrain certification language. This separation follows research-compendium practice, in which narrative, code, data, environment, and outputs remain distinct but linked [@marwick2018packaging]. It also follows executable-paper and notebook traditions in coupling narrative to runnable analysis rather than copying results into prose [@leisch2002sweave; @rule2019jupyter]. The narrower contribution here is provenance at the token and claim levels; the workflow does not purport to validate scientific truth.

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
| 1 | ore | 37.50% | 9K | Extract raw gold-bearing ore from the earth |
| 2 | smelting | 75.00% | 18K | Heat ore to separate gold from slag and dross |
| 3 | assaying | 91.67% | 22K | Test a sample to determine gold content and impurities |
| 4 | cupellation | 99.900% | 24K | Refine by blowing air through molten lead-gold alloy |
| 5 | certification | 99.9999999% (nine-nines) | 24K (nine-nines certified) | Certify purity grade and stamp hallmark |

## Refinery model and purity measure

The purity sequence across all stages is: 0.100000, 0.375000, 0.750000, 0.916700, 0.999000, 1.000000

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
| F1 | Purity functional | [@eq:purity_functional] | `src/purity.py::format_purity` |
| F2 | Monotone refinement | [@eq:monotone_refinery] | `src/purity.py::assert_monotone_increase` |
| F3 | Token-selection digest | [@eq:token_digest] | `src/composition.py::_choose_value` |
| F4 | Claim-support fraction | [@eq:claim_support] | `src/evidence.py::EvidenceRegistry.support_rate` |
| F5 | Integrity vector | [@eq:integrity_vector] | `manuscript/config.yaml#gold_refinement.audit_rules` |
| F6 | Certification predicate | [@eq:certification_predicate] | `src/refinery.py::RefineryResult.is_nine_nines_certified` |
| F7 | Adversarial assay | [@eq:adversarial_assay] | `src/security_assay.py::build_security_assay` |
: Source-owned formalism registry. {#tbl:formalism_registry}

**F1: Purity functional.** Manuscript purity is treated as a bounded fraction mapped to a reader-facing grade.

$$
\pi(s) \in [0, 1], \qquad g(s) = \operatorname{karat}(\pi(s))
$$ {#eq:purity_functional}

The value is descriptive: it summarizes local validation state rather than external quality. Source: `src/purity.py::format_purity`.

**F2: Monotone refinement.** A valid refinery run requires every stage to improve the previous purity state.

$$
\pi_0 < \pi_1 < \cdots < \pi_n
$$ {#eq:monotone_refinery}

The test suite rejects equal or decreasing stage outputs. Source: `src/purity.py::assert_monotone_increase`.

**F3: Token-selection digest.** Every mega-madlib token is selected from config-owned inventory by a deterministic digest.

$$
i = \operatorname{int}(\operatorname{SHA256}(seed \Vert slot \Vert category \Vert ordinal \Vert inventory)_{0:12}, 16) \bmod \lvert inventory \rvert
$$ {#eq:token_digest}

Changing the seed or inventory changes the plan; replaying both reproduces it. Source: `src/composition.py::_choose_value`.

**F4: Claim-support fraction.** Contribution claims are assayed by counting supported local evidence pointers.

$$
\sigma = \frac{\lvert\{c \in C : supported(c)\}\rvert}{\lvert C \rvert}
$$ {#eq:claim_support}

The numerator and denominator come from the project-local claim-support registry. Source: `src/evidence.py::EvidenceRegistry.support_rate`.

**F5: Integrity vector.** Scientific integrity is represented as a vector of gate outcomes rather than one scalar badge.

$$
\mathbf{v} = (v_{tokens}, v_{figures}, v_{claims}, v_{render}, v_{references}, v_{security})
$$ {#eq:integrity_vector}

A publication claim is only as strong as the weakest required gate. Source: `manuscript/config.yaml#gold_refinement.audit_rules`.

**F6: Certification predicate.** Certification is a predicate over final purity and validation readiness.

$$
\operatorname{certified}(r) \iff \pi_{final}(r) \geq 0.999999999 \land gates(r)
$$ {#eq:certification_predicate}

The predicate binds the nine-nines metaphor to the actual validation chain. Source: `src/refinery.py::RefineryResult.is_nine_nines_certified`.

**F7: Adversarial assay.** Certification requires an explicit adversarial and supply-chain scope, not only ordinary gate success.

$$
\operatorname{certified}_{adv}(r) \iff \operatorname{certified}(r) \land \forall a \in A_r:\ threat(a) \land standard(a) \land evidence(a) \land validator(a) \land boundary(a)
$$ {#eq:adversarial_assay}

The adversarial assay defines scope and evidence requirements; it is not proof of compliance or live scan findings. Source: `src/security_assay.py::build_security_assay`.

## Deterministic token composition

The mega-madlib engine selects tokens from config-owned lexicon categories using a deterministic digest:

$$
\text{index} = \text{int}\left(\text{SHA-256}\left(\text{seed} \mid \text{slot} \mid \text{category} \mid \text{ordinal} \mid \text{inventory}\right)[:12], 16\right) \mod n
$$

where $n$ is the inventory size. For each declared slot, the procedure concatenates the seed, slot name, category, one-based ordinal, and the complete ordered inventory; hashes the UTF-8 string; converts the first 12 hexadecimal characters to an integer; and reduces it modulo $n$. Including the complete inventory makes selection sensitive to both membership and order. Replaying the same configuration reproduces the same plan; changing the seed, slot specification, or inventory may change it.

Each selected value is recorded with its variable name, slot, category, section, ordinal, and configuration path. This record permits exact replay and source tracing but does not imply that the selected synonym is semantically superior. Selected metallurgical terms are assaying, parting, and smelting; selected manuscript terms are evidence and evidence. [@eq:token_digest] formalizes the rule, while evidence validation, figure registry check, and citation validation name the corresponding validation surfaces.

## Seed-sensitivity design

The canonical publication plan uses seed 431. To measure sensitivity to that declared input, the analysis additionally evaluates 1024 technical seed replicates over the range 0–1023. Agreement is the fraction of token slots whose selected value matches the canonical plan; unique-plan count and lexicon inventory coverage are reported separately. The thresholded rate counts replicates with at least 25% slot agreement and uses a score interval rather than a naive Wald interval [@newcombe1998proportion]. This follows computational benchmarking work that recommends representing pipeline performance as a distribution over sources of variation rather than as a single run [@bouthillier2021accounting].

The sample size is a precision choice for a bounded computational summary, not a power calculation for people or a claim that 1024 runs constitute 1024 manuscripts. Accuracy-based sample-size justification is appropriate only after the estimand and inferential goal are declared [@lakens2022samplesize]. For the declared bounded-metric target, the algebraic minimum is 738 replicates; the project uses 1024 as a documented power-of-two ceiling. At the nominal 95% level, the distribution-free radius is 4.24% against a target of 5.00%.

The interval language is conditional. Seeds are enumerated as contiguous_integer_seeds, not sampled from manuscripts, readers, or a natural population. The normal interval is a Normal approximation; descriptive conditional summary; the threshold interval is a Wilson score interval; conditional binomial summary; and the bounded radius is a Hoeffding bound; conditional bounded-metric guarantee. These summaries are interpretable under the declared exchangeability assumption—Conditional on exchangeable random-seed draws; the declared contiguous seed range is a sensitivity surface, not an empirical population.—but they are not unconditional confidence statements about future software versions or external writing outcomes. A deterministic bootstrap percentile interval over 2000 resamples, using bootstrap seed 431, provides a sensitivity check for the empirical seed-range mean: 20.10%–21.11% [@efron1979bootstrap]. The full report records the cumulative sample-size ladder in [@tbl:seed_sensitivity_ladder] and the generated distribution in [@fig:seed_sensitivity].

| Seed sample size | Mean agreement | SD | 95% bound radius | Inventory coverage |
|------------------|----------------|----|------------------|--------------------|
| 16 | 19.53% | 7.72% | 33.95% | 100.00% |
| 32 | 20.70% | 8.69% | 24.01% | 100.00% |
| 64 | 19.40% | 7.36% | 16.98% | 100.00% |
| 128 | 20.31% | 7.86% | 12.00% | 100.00% |
| 256 | 20.00% | 7.88% | 8.49% | 100.00% |
| 512 | 20.41% | 8.94% | 6.00% | 100.00% |
| 1024 | 20.62% | 8.56% | 4.24% | 100.00% |
: Seed-sensitivity precision ladder. {#tbl:seed_sensitivity_ladder}

## Config-owned lexicon

| Category | Count | Sample |
|----------|-------|--------|
| boundary_terms | 5 | local claim, analogy boundary, fork obligation... |
| evidence_terms | 5 | fact registry, artifact manifest, citation check... |
| gate_terms | 5 | prerender, evidence validation, figure registry check... |
| integrity_terms | 5 | evidence spine, source tier, validation gate... |
| manuscript_terms | 5 | draft, claim, citation... |
| metallurgical_terms | 5 | cupellation, assaying, smelting... |
| purity_adjectives | 5 | unrefined, purified, certified... |
| refinement_verbs | 5 | assaying, certifying, refining... |

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
| Schema intake | manuscript/config.yaml | Load and validate gold_refinement block | GoldRefinementConfig | config schema tests |
| Refinery execution | GoldRefinementConfig | Run five refinery stages with monotone purity | RefineryResult | monotone purity test |
| Token planning | GoldRefinementConfig | Expand slots into deterministic token choices | TokenPlan | seed-stability tests |
| Figure generation | RefineryResult and TokenPlan | Generate purity progression, karat grading, and token density figures | output/figures/*.png | nonblank figure tests |
| Integrity risk modeling | audit rules, failure modes, claims, and shared evidence registry | Score integrity dimensions and summarize evidence tiers | integrity tables and risk visualizations | tests/test_integrity.py |
| Security assay | gold_refinement.security_assay | Map adversarial threats and standards to source-owned evidence and claim boundaries | security assay table and variables | tests/test_security_assay.py |
| Seed sensitivity | GoldRefinementConfig and token plan | Evaluate token-plan agreement across the declared seed sample and compute bounded precision summaries | output/data/seed_sensitivity.json and seed-sensitivity figure | tests/test_seed_sensitivity.py |
| Manuscript hydration | manuscript shells and manuscript_variables.json | Resolve {{TOKEN}} placeholders into output/manuscript/ | hydrated Markdown manuscript | unresolved-token scan |
| Render and validate | output/manuscript | Render PDF, HTML through shared template pipeline | output/pdf and output/web | render command |

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

The integrity model converts manuscript risks into source-owned dimensions. It does not replace peer review or domain validation. It names the failure class, severity, detectability, evidence surface, owner, and validator so the manuscript can distinguish "the analogy is vivid" from "the claim is backed by a regenerable check." The current pass reports 9 integrity dimensions; highest residual risk is I4 (Analogy boundary) at 15.

| ID | Dimension | Residual risk | Owner | Validator |
|----|-----------|---------------|-------|-----------|
| I1 | Monotone refinery | 4 | source code | tests/test_refinery.py |
| I2 | Lexicon completeness | 3 | config | tests/test_config.py |
| I3 | Token hydration | 5 | generated variables | tests/test_manuscript_variables.py |
| I4 | Analogy boundary | 15 | claim ledger | infrastructure.validation.cli evidence --fail-on-issues |
| I5 | Claim support | 10 | evidence assay | output/reports/claim_support_registry.json |
| I6 | Figure registry | 8 | figure producer | tests/test_registry_integrity.py |
| I7 | Citation hygiene | 4 | bibliography | infrastructure.reference.citation validate |
| I8 | Render readiness | 8 | template pipeline | template pipeline render and validate stages |
| I9 | Adversarial security assay | 15 | security assay | tests/test_security_assay.py and manuscript source review |
: Source-owned scientific-integrity dimensions. {#tbl:integrity_dimensions}

The residual-risk score is an ordinal prioritization heuristic: higher severity and lower detectability raise review priority. It was not fitted to incident data, validated against external judgments, or designed for comparison across projects. Its sole use is to identify where this exemplar—or a fork—needs stronger ownership, evidence, or validation before expanding a claim.

| Owner | Dimensions |
|-------|------------|
| bibliography | 1 |
| claim ledger | 1 |
| config | 1 |
| evidence assay | 1 |
| figure producer | 1 |
| generated variables | 1 |
| security assay | 1 |
| source code | 1 |
| template pipeline | 1 |
: Integrity dimensions by owning surface. {#tbl:integrity_owners}

This table also makes generated-number ownership explicit. Counts, support rates, and figure labels belong to regenerated reports and registries; the manuscript consumes them through variables. Authored prose may interpret those values, but it should not silently restate them as hand-maintained facts.

### Multi-objective purity

Scalar stage purity is retained only as the state variable of the refinery analogy. `src/purity.py::PurityVector` separately records stage completion, claim support, token provenance, and figure quality on $[0,1]$. The vector exposes its weakest dimension and a conjunctive all-complete predicate but intentionally defines no weighted average. This prevents a perfect render or terminal stage value from numerically compensating for unsupported claims or missing provenance. Weighting these dimensions would require an external validation study and is outside the present design.

## Reproducibility and validity safeguards

Determinism is assessed by exact replay from the same ordered configuration and source revision. Provenance is assessed by the existence of a path from each reported token, claim, equation, and figure to an owning source and generated record. Negative controls in the test suite exercise malformed configuration and invalid refinery states; figure checks assess file presence, registry parity, dimensions, nonblank content, and color variance. Environment and regeneration details are given in [@sec:reproducibility].

Four validity limits govern interpretation. First, **construct validity** is limited because purity is a designed workflow state, not a validated measure of writing quality. Second, **external validity** is limited to this exemplar until other domains implement their own mappings and validators. Third, **historical validity** is bounded by the normalized analogy and should not be read as a universal account of metallurgical practice. Fourth, **criterion validity** is local: passing gates demonstrates source ownership and internal consistency, not correctness of domain claims. These limits are part of the method's acceptance rule, not qualifications added after results are known.

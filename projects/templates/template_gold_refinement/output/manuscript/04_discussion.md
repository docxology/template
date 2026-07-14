# Discussion: Load-Bearing vs Rhetorical Analogy {#sec:discussion}

## Load-bearing vs rhetorical

The gold-refining analogy operates on two levels. **Rhetorically**, it provides a memorable framing for a methods paper: purity progression, karat grading, and certification are vivid metaphors for manuscript quality. **Operationally**, each stage maps to a real template-infrastructure operation - smelting to claim removal, assaying to evidence validation, cupellation to cross-reference resolution, and certification to full pipeline validation. The scholarship makes the test sharper: the analogy is useful only where the relation among stages is preserved, not where surface language makes writing sound like metallurgy [@gentner1983structure; @hesse1966models].

The pre-1800 metallurgy sources strengthen the analogy by making that relation historically concrete, but they also narrow it. They show several traditions of staged work - ancient extraction and testing, Renaissance printed metallurgy, seventeenth-century goldsmith standards, and eighteenth-century assay manuals - rather than one timeless method [@pliny_natural_history_33; @biringuccio_pirotechnia_1540; @agricola_de_re_metallica_1556; @badcock_touchstone_1678; @cramer_assaying_metals_1741]. The manuscript therefore imports structure, not authority: cupellation does not make citation review chemical, a hallmark does not make a rendered PDF legally certified, and a karat scale does not make local validation equivalent to external truth.

The analogy is smelting the manuscript: it performs the refinement it describes. Its fork obligation is equally important. Gold refining can model staged purification, but it cannot certify domain truth unless the fork supplies a real domain validator and evidence source.

The added implementation and claim-assay figures sharpen that boundary. They show that "purity" is not a free-standing aesthetic judgment. It is a local statement about whether source-owned stages, generated artifacts, claim ledgers, figure registries, and validation commands agree. The figures therefore make a negative claim as important as the positive one: when a fork lacks a validator, a ledger, or a source artifact, the metaphor must stop at analogy and cannot be promoted to certification. That boundary follows reproducibility scholarship as much as metaphor theory: formal traceability can support rerunning and auditing, but it cannot by itself establish external validity [@peng2011reproducible; @wilkinson2016fair; @ioannidis2005false].

The same caution applies to checklist-shaped infrastructure. Reporting guidelines improve the inspectability of research reports by naming information that should be present, but checklist completion is not the same as methodological quality, absence of bias, or truth of results [@equator_network_reporting_guidelines; @schulz2010consort; @page2021prisma]. The gold-refinement gates should therefore be read as completeness and traceability checks. They can expose a missing citation, an unresolved token, or an unsupported local claim; they cannot convert weak domain evidence into strong domain evidence.

## Useful adaptation cases

- **Domain-specific refinement pipelines**: fork the exemplar and remap stages to domain operations (e.g., clinical evidence, legal citation, engineering specification).
- **Staged-state visualization**: reuse the purity and karat vocabulary only when the fork declares what each state means, enforces ordering and continuity, and avoids presenting designed values as validated quality measurements.
- **Mega-madlib composition**: reuse the deterministic token engine for any config-owned lexical composition task.
- **Domain adapters**: use `src/domain_adapter.py` and `domain_profile.yaml` to translate a domain's own metrics into the same purity scale before reusing certification language.
- **Research compendia**: package manuscript shells, token rules, analysis outputs, figures, and validation reports as a single reproducible object rather than a loose bundle of supplementary files [@marwick2018packaging].

## Misuse modes

| Mode | Risk | Detection | Mitigation |
|------|------|-----------|------------|
| Non-monotone purity | A stage has lower output purity than input. | assert_monotone_increase raises ValueError. | Fix stage purity targets in src/refinery.py. |
| Empty lexicon category | A required lexicon category is empty or missing. | Config validation raises GoldRefinementConfigError. | Add vocabulary to manuscript/config.yaml. |
| Unresolved token | A manuscript placeholder has no generated variable. | test_all_manuscript_tokens_are_generated fails. | Add variable in src/manuscript_variables.py. |
| Rhetorical-only analogy | The analogy is decorative with no operational mapping. | Review that each stage maps to a real infrastructure operation. | Connect stages to template pipeline operations. |
| Undetected integrity gap | A high-severity failure mode is present but no owner, validator, or generated artifact makes it visible. | build_integrity_dimensions lists severity, detectability, owner, validator, and evidence surface. | Add or revise the source-owned integrity dimension before promoting the manuscript. |
| Citation laundering | A real citation is used to make a stronger claim than the source supports. | Scope and evaluation prose separate analogy support, reproducibility support, and domain-evidence support. | Lower the claim boundary or add a source-owned validator before using certification language. |
| Checklist theater | A fork treats filled reporting rows or passed template gates as proof of scientific validity. | Methods, scope, discussion, and evaluation prose separate completeness, traceability, and reproducibility from domain truth. | Add the field's reporting guideline, domain validators, and independent evidence before making compliance or validity claims. |
| Executable-package ambiguity | A fork publishes a rendered manuscript without enough software, metadata, or version identity to rebuild the object. | Reproducibility, scope, evaluation, and authoring-contract prose require source-owned metadata, exact release citation, and regenerated output reports. | Record software/template release identity, preserve source-owned metadata, and rerun the full pipeline before publishing. |
| Security theater | Security language is presented as compliance, secure-by-design proof, or scan evidence without generated artifacts. | Security assay rows require a threat, standard, evidence surface, validator, and claim boundary. | Keep security claims bounded to the configured assay unless validated scan receipts exist. |
| Scan result laundering | A future scan summary is imported as prose without the artifact, receipt, and validator that produced it. | Authoring-contract and evaluation prose require scan artifacts before real Codex Security or Deep Security Scan findings are claimed. | Integrate only generated scan reports with evidence-registry alignment and explicit claim boundaries. |
| Seed-count overclaim | A large number of deterministic seed runs is presented as evidence of external manuscript quality or domain validity. | The seed-sensitivity report and manuscript label seeds as technical replicates and retain local non-claims. | Report seed variability as computational sensitivity and add independent domain evidence before expanding the claim. |
| Seed-report drift | A stale or edited JSON report hydrates manuscript statistics that no longer match the current configuration. | Manuscript hydration validates the report against deterministic recomputation. | Regenerate analysis outputs and fail hydration when any report field differs from the recomputed payload. |

## Design principles

| Principle | Rationale |
|-----------|-----------|
| Analogy is load-bearing | Each metallurgical stage maps to a real template-infrastructure operation, not mere decoration. |
| Purity increases monotonically | The refinery pipeline guarantees strictly increasing purity from ore to certification. |
| Token selection is deterministic | A fixed seed and lexicon produce the same injection plan across reruns. |
| Configuration owns prose choices | Reviewers can inspect the declared language surface before generation. |
| Generated output is disposable | The durable artifact is the regeneration contract, not hand-edited output. |
| Scholarship sets boundaries | External sources can anchor analogy, reproducibility, and provenance claims, but they cannot expand local certification beyond what the source-owned evidence supports. |
| Completeness is not validity | Checklist-shaped gates can show that required reporting surfaces are present and traceable, but they do not certify domain truth, study design quality, or absence of bias. |
| Executable package is the object | Narrative, config, code, metadata, figures, reports, and rendered outputs must travel as a rebuildable package rather than as detached static prose. |
| Adversarial purity is bounded | Security standards frame threats and evidence requirements, but local certification cannot claim compliance or scan results without source-owned artifacts. |

## Analogy-break boundary

The analogy breaks when purity becomes a rhetorical grade detached from evidence. In this exemplar, [@eq:claim_support] and [@eq:integrity_vector] keep the grade tied to claim support and gate coverage. A fork that cannot provide comparable source-owned gates should keep the gold-refining language as metaphor only and avoid publication-strength claims.

The reverse assay clarifies a second boundary. It can identify the shortest prefix that reaches a **declared** target, but it cannot identify the cheapest, fairest, or scientifically best workflow unless stages have empirically justified costs and outcomes. Likewise, the multi-objective purity vector prevents compensatory averaging, but its dimensions are still local engineering observables rather than a validated psychometric scale.

The practical rule is simple: do not add an impressive figure unless its path through [@fig:implementation_circuit] is visible. A visual can summarize an idea, but it only supports a manuscript claim when the claim-evidence assay can point to the owning file, symbol, generated artifact, and validation surface.

The integrity risk matrix adds one more brake. A fork may have all figures registered and still be scientifically weak if its highest-severity risks are only weakly detectable. In this exemplar, [@tbl:integrity_dimensions] makes that weakness inspectable by pairing each dimension with an owner and validator. The useful question for a fork is therefore not "can the manuscript render?" but "which severe failures would the current pipeline miss, and what source-owned gate would expose them?"

The evidence-tier ladder also prevents a common drift in generated manuscripts: treating generated artifacts as if they were independent evidence. A generated metric can support an internal consistency claim, but a domain claim needs a domain source tier. The ladder makes that distinction visible without pretending that a large fact count is the same as stronger external validity. In FAIR and PROV terms, richer metadata improves findability, reuse, and traceability, but it does not convert weak evidence into strong evidence [@wilkinson2016fair; @moreau2013prov].

Open-science standards push in the same direction. The TOP Guidelines and UNESCO Recommendation on Open Science emphasize transparency, scrutiny, reproducibility, accountability, and shared research objects [@nosek2015top; @unesco2021_open_science]. This exemplar implements a small local version of those values; it does not claim that openness alone resolves study design, fairness, or domain-validity problems.

Security guidance adds an adversarial version of the same brake. Zero trust, secure development, supply-chain provenance, signing, SBOM, attack-path, and secure-by-design frameworks are useful because they ask who or what should not be trusted by default [@nist_sp800_207_zero_trust; @nist_sp800_218_ssdf; @slsa_v1_2; @sigstore_docs; @mitre_attack; @cyclonedx_spec; @spdx_spec; @cisa_secure_by_design]. In this manuscript they do not certify security. They make overclaiming harder: a security claim must point to [@tbl:security_assay], and a real scan claim must point to scan artifacts that this pass does not produce.

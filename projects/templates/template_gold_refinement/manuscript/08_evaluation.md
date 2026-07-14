# Quality Probes {#sec:evaluation}

## QA probes

| Probe | Question | Passing signal | Artifact |
|-------|----------|---------------|----------|
{{QUALITY_PROBES_TABLE}}

The selected evaluation gate terms are {{EVALUATION_GATE_TERM_1}} and {{EVALUATION_GATE_TERM_2}}. They are intentionally narrower than peer review: they check source ownership, token coverage, figure registration, claim support, and rendering integrity before a human reviewer assesses the substantive analogy.

Evaluation uses three noninterchangeable levels. **Invariant tests** reject invalid executable states such as nonmonotone, discontinuous, or misordered stages. **Artifact checks** establish presence, readability, provenance, and registry parity. **Claim-boundary review** asks whether the prose says no more than those tests and artifacts support. Certification requires all applicable levels; a pass at one level cannot compensate for failure at another.

## Audit rules

| Rule | Check | Test |
|------|-------|------|
{{AUDIT_RULES_TABLE}}

The audit rules are summarized visually in [@fig:integrity_gate_matrix] and algebraically in [@eq:integrity_vector]. A failed audit rule should block certification language even if the PDF renders.

Scholarship adds one more gate: citation validity and claim-boundary discipline. A source can support a relation, a practice, or a caution without supporting every attractive extrapolation from that source. The evaluation surface therefore treats analogy theory, reproducibility literature, provenance standards, and pre-1800 metallurgy references as boundary-setting evidence, not as decorations added after the pipeline already decided the claim [@gentner1983structure; @peng2011reproducible; @wilkinson2016fair; @biringuccio_pirotechnia_1540; @agricola_de_re_metallica_1556; @badcock_touchstone_1678; @cramer_assaying_metals_1741]. A passing source review must preserve the distinction between historically documented assay/marking practices and this exemplar's local software certification predicate.

The reporting-guideline literature keeps that gate modest. A passed checklist row certifies that a required reporting surface is present and traceable; it does not certify that the study behind the report is unbiased, sufficiently powered, or externally valid [@equator_network_reporting_guidelines; @vonelm2007strobe; @percie_du_sert2020arrive]. The same rule governs the quality probes here. Passing them supports local claims about source ownership, artifact completeness, and reproducible rendering, not universal claims about manuscript quality.

Executable-compendium scholarship adds a more operational evaluation target: can a reader identify the paper object, its source code, its generated artifacts, its metadata, and the software version needed to rebuild it [@nuest2017erc; @chen2021metadata; @smith2016softwarecitation]? The current gates answer that question locally through variable hydration, artifact counts, evidence facts, figure registration, and PDF/HTML validation. They do not measure long-term preservation, cross-platform portability, reviewer workload, or reader comprehension; those would require separate empirical studies.

The adversarial assay adds a security-specific evaluation target: can a reader distinguish declared threat scope from actual scan evidence? [@tbl:security_assay] maps zero-trust, secure-development, supply-chain, SBOM, attack-path, and secure-by-design guidance to local evidence surfaces and validators [@nist_sp800_207_zero_trust; @nist_sp800_218_ssdf; @slsa_v1_2; @sigstore_docs; @mitre_attack; @cyclonedx_spec; @spdx_spec; @cisa_secure_by_design]. The passing condition is bounded: the table must be complete and the prose must not claim compliance or Codex Security findings unless future scan artifacts are generated and integrated.

The risk model adds prioritization to the gate list. [@fig:integrity_risk_matrix] separates easy-to-detect implementation failures from severe boundary failures that need clearer ownership. This keeps the evaluation surface from becoming a checklist of equally weighted boxes: token coverage, citation validity, claim support, and render readiness all matter, but a high-severity low-detectability failure should shape the next source edit before cosmetic manuscript polish.

The seed-sensitivity gate adds a quantitative robustness surface without
changing the claim boundary. It requires a declared replicate count, an
agreement estimand, a score interval for the thresholded rate, a bounded
precision radius, and a sample-size ladder. The current run reports
{{SEED_STUDY_N}} technical replicates, {{SEED_STUDY_UNIQUE_PLANS}} unique plans,
and {{SEED_STUDY_INVENTORY_COVERAGE}} inventory coverage. These quantities
describe the behavior of the deterministic composition engine; they do not
measure reader agreement, factual correctness, or scientific validity. The
intervals and Hoeffding radius are conditional on the declared exchangeability
assumption for the seed draws; the contiguous integer range is not a random
sample of manuscripts or deployments. A validator must therefore check both
the report schema and its deterministic recomputation from configuration.

Figure review follows the same rule. File existence and nonblank pixels are necessary but not sufficient. The figure caption, encoding declaration, source data, and prose interpretation must describe the same measurement. This criterion specifically prohibits inferring a stagewise trend from a project-level aggregate, which is why [@fig:purity_claim_scatter] repeats one observed claim-support rate rather than inventing cumulative values.

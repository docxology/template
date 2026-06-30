# Quality Probes {#sec:evaluation}

## QA probes

| Probe | Question | Passing signal | Artifact |
|-------|----------|---------------|----------|
| Monotone purity | Does purity increase strictly across all refinery stages? | assert_monotone_increase passes on the purity sequence. | src/refinery.py and output/data/refinery_results.json |
| Token provenance | Can every selected token be traced to a category, section, value, and config key? | The token plan contains one row for each generated token. | output/reports/token_plan.json |
| Karat grade correctness | Does each stage map to the correct karat grade? | karat_for_purity returns the expected grade for each stage. | src/purity.py |
| Integrity risk visibility | Can the manuscript identify high-severity integrity failures and the validator or artifact that detects them? | The integrity risk model emits dimensions, owners, residual risk scores, and evidence-tier rows. | src/integrity.py and output/figures/integrity_risk_matrix.png |
| Scholarship boundary | Do external references support the analogy, reproducibility, provenance, and metallurgy framing without being used as evidence for universal manuscript-quality claims? | The scope, discussion, and evaluation sections cite the scholarship while keeping certification local to source-owned gates. | manuscript/references.bib and manuscript/07_scope.md |
| Reporting-guideline completeness | Does the manuscript distinguish checklist-style completeness from methodological validity? | The methods, scope, discussion, and evaluation sections cite reporting-guideline scholarship while explicitly limiting what the local gates prove. | manuscript/02_methodology.md, manuscript/04_discussion.md, manuscript/07_scope.md, and manuscript/08_evaluation.md |
| Executable-compendium identity | Can a reader identify the executable package, metadata stack, software release, and generated artifacts needed to rebuild the manuscript? | The reproducibility, scope, evaluation, and authoring-contract sections cite executable-publication and software-citation scholarship while keeping preservation and portability claims bounded. | manuscript/06_reproducibility.md, manuscript/07_scope.md, manuscript/08_evaluation.md, manuscript/09_authoring_contract.md, output/reports/evidence_registry.json, and output/reports/output_statistics.json |

The selected evaluation gate terms are prerender and citation validation. They are intentionally narrower than peer review: they check source ownership, token coverage, figure registration, claim support, and rendering integrity before a human reviewer assesses the substantive analogy.

## Audit rules

| Rule | Check | Test |
|------|-------|------|
| Purity monotonicity | Purity must strictly increase from stage to stage | tests/test_refinery.py |
| Token determinism | Same seed and lexicon must produce same token plan | tests/test_composition.py |
| Token coverage | Every manuscript {{TOKEN}} must have a generated variable | tests/test_manuscript_variables.py |
| Config validation | Invalid config must raise GoldRefinementConfigError | tests/test_config.py |
| Figure generation | All figure generators must produce non-blank PNGs | tests/test_figures.py |
| Integrity model coverage | Integrity dimensions must have unique IDs, owners, validators, and evidence surfaces | tests/test_integrity.py |
| Scholarship boundary | Citations must anchor framing and limitations without substituting for domain validation | prerender citation/evidence validation plus human source review |
| Reporting-guideline boundary | Checklist-style completeness must not be represented as methodological validity or external reporting compliance | prerender citation/evidence validation plus human source review |
| AI/template accountability | Tool assistance must not be represented as authorship or independent responsibility | authoring-contract source review plus publication-ethics citation check |
| Executable-package identity | The manuscript must distinguish a regenerated local package from long-term archival preservation or universal executable-paper compliance | reproducibility source review plus output statistics and evidence-registry validation |

The audit rules are summarized visually in [@fig:integrity_gate_matrix] and algebraically in [@eq:integrity_vector]. A failed audit rule should block certification language even if the PDF renders.

Scholarship adds one more gate: citation validity and claim-boundary discipline. A source can support a relation, a practice, or a caution without supporting every attractive extrapolation from that source. The evaluation surface therefore treats analogy theory, reproducibility literature, provenance standards, and metallurgy references as boundary-setting evidence, not as decorations added after the pipeline already decided the claim [@gentner1983structure; @peng2011reproducible; @wilkinson2016fair; @marsden_house_2006].

The reporting-guideline literature keeps that gate modest. A passed checklist row certifies that a required reporting surface is present and traceable; it does not certify that the study behind the report is unbiased, sufficiently powered, or externally valid [@equator_network_reporting_guidelines; @vonelm2007strobe; @percie_du_sert2020arrive]. The same rule governs the quality probes here. Passing them supports local claims about source ownership, artifact completeness, and reproducible rendering, not universal claims about manuscript quality.

Executable-compendium scholarship adds a more operational evaluation target: can a reader identify the paper object, its source code, its generated artifacts, its metadata, and the software version needed to rebuild it [@nuest2017erc; @chen2021metadata; @smith2016softwarecitation]? The current gates answer that question locally through variable hydration, artifact counts, evidence facts, figure registration, and PDF/HTML validation. They do not measure long-term preservation, cross-platform portability, reviewer workload, or reader comprehension; those would require separate empirical studies.

The risk model adds prioritization to the gate list. [@fig:integrity_risk_matrix] separates easy-to-detect implementation failures from severe boundary failures that need clearer ownership. This keeps the evaluation surface from becoming a checklist of equally weighted boxes: token coverage, citation validity, claim support, and render readiness all matter, but a high-severity low-detectability failure should shape the next source edit before cosmetic manuscript polish.

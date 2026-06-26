# Quality Probes {#sec:evaluation}

## QA probes

| Probe | Question | Passing signal | Artifact |
|-------|----------|---------------|----------|
| Monotone purity | Does purity increase strictly across all refinery stages? | assert_monotone_increase passes on the purity sequence. | src/refinery.py and output/data/refinery_results.json |
| Token provenance | Can every selected token be traced to a category, section, value, and config key? | The token plan contains one row for each generated token. | output/reports/token_plan.json |
| Karat grade correctness | Does each stage map to the correct karat grade? | karat_for_purity returns the expected grade for each stage. | src/purity.py |
| Integrity risk visibility | Can the manuscript identify high-severity integrity failures and the validator or artifact that detects them? | The integrity risk model emits dimensions, owners, residual risk scores, and evidence-tier rows. | src/integrity.py and output/figures/integrity_risk_matrix.png |

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

The audit rules are summarized visually in [@fig:integrity_gate_matrix] and algebraically in [@eq:integrity_vector]. A failed audit rule should block certification language even if the PDF renders.

The risk model adds prioritization to the gate list. [@fig:integrity_risk_matrix] separates easy-to-detect implementation failures from severe boundary failures that need clearer ownership. This keeps the evaluation surface from becoming a checklist of equally weighted boxes: token coverage, citation validity, claim support, and render readiness all matter, but a high-severity low-detectability failure should shape the next source edit before cosmetic manuscript polish.

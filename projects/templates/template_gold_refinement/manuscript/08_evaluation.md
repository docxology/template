# Quality Probes {#sec:evaluation}

## QA probes

| Probe | Question | Passing signal | Artifact |
|-------|----------|---------------|----------|
{{QUALITY_PROBES_TABLE}}

The selected evaluation gate terms are {{EVALUATION_GATE_TERM_1}} and {{EVALUATION_GATE_TERM_2}}. They are intentionally narrower than peer review: they check source ownership, token coverage, figure registration, claim support, and rendering integrity before a human reviewer assesses the substantive analogy.

## Audit rules

| Rule | Check | Test |
|------|-------|------|
{{AUDIT_RULES_TABLE}}

The audit rules are summarized visually in [@fig:integrity_gate_matrix] and algebraically in [@eq:integrity_vector]. A failed audit rule should block certification language even if the PDF renders.

The risk model adds prioritization to the gate list. [@fig:integrity_risk_matrix] separates easy-to-detect implementation failures from severe boundary failures that need clearer ownership. This keeps the evaluation surface from becoming a checklist of equally weighted boxes: token coverage, citation validity, claim support, and render readiness all matter, but a high-severity low-detectability failure should shape the next source edit before cosmetic manuscript polish.

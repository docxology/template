# act_inf_metaanalysis v2: Comprehensive Accuracy & Quality Corrections

**Priority:** CRITICAL - manuscript contains factual inaccuracies about validation.

## Goal
Correct all factual inaccuracies (especially false claim that 10%% manual validation was completed),
fix failing tests and coverage gaps, add missing ASSERTION_SUPPORT_PCT/ASSERTION_CONTRADICT_PCT,
bring entire project to v2 release state.

## Phases
1. Manuscript Truthfulness Corrections
2. Test Infrastructure Repairs
3. Missing Variable Implementation
4. Polish & Validation

---

### Task 1.1: Fix 02b_methods_extraction.md validation section

Replace the three-tier list (lines ~117-124) with:

Validation of LLM-extracted assertions follows a planned three-tier protocol:

1. **Validation Dataset (10%%, planned).** ...targeting a κ > 0.70 threshold...
   **This manual annotation dataset has not yet been created; it remains a prioritized next step.**

2. **Boundary-case audit (conceptual design).** ...would be specifically checked...
   **This audit mechanism has been designed but not yet executed.**

3. **Aggregate consistency (conceptual design).** ...would be compared...
   **This consistency check is part of the validation design but has not been systematically applied.**

Remove the "Preliminary experiments on a sampled subset..." paragraph entirely.
Add concluding sentence: "Importantly, the current pipeline operates without human-validated ground truth; confidence scores are uncalibrated..."

Commit: manuscript/02b_methods_extraction.md

### Task 1.2: Fix 03_results_hypothesis.md

Replace entire "Methodological Validation and LLM Calibration" subsection with:

The evidence presented here derives from automated LLM-based assertion extraction operating
on paper abstracts only, without human-validated ground truth calibration. Confidence scores
reflect the model's self-assessed certainty and have not been correlated with human
adjudication... A formal validation protocol—including 10%% manual annotation, Cohen's κ
assessment, and boundary-case auditing—remains a critical next step...

Commit: manuscript/03_results_hypothesis.md

### Task 1.3: Fix 04_conclusion.md

- Line 27: "instituted" → "specified, but this dataset has not yet been created"
- Line 51: "current 10%% manual-annotation baseline" → "planned 10%% manual-annotation baseline would... not yet performed"
- Rubric table (current col for Extraction direction accuracy): change "κ > 0.70" → "not measured"
- Line 87: "existing baseline" → "targeted baseline to be established"

Commit: manuscript/04_conclusion.md

### Task 1.4: Clarify abstract
00_abstract.md: insert "(operating without human-validated ground truth)" after
"automated LLM-driven assertion extraction" in final paragraph.
Commit.

---

## PHASE 2: TEST INFRASTRUCTURE

### Task 2.1: Dependency verification & environment docs
- tests/conftest.py: add module-level check for rdflib, wordcloud, sklearn with clear ImportError
- README.md: add note "Run tests from project directory: cd projects/act_inf_metaanalysis && uv run pytest"
Commit.

### Task 2.2: Ensure ≥90%% coverage
After deps fixed, 8 previously failing tests should pass.
If coverage <90%%, add tests in test_nanopublication.py for RDF/Trig coverage.
Commit test additions.

---

## PHASE 3: MISSING VARIABLES

### Task 3.1: Implement ASSERTION_SUPPORT_PCT / ASSERTION_CONTRADICT_PCT
In src/manuscript/variables.py assertion summary block, add:

        type_counts = assertion.get("type_counts", {})
        total_sup = type_counts.get("supports", 0)
        total_con = type_counts.get("contradicts", 0)
        total_sc = total_sup + total_con
        if total_sc > 0:
            variables["ASSERTION_SUPPORT_PCT"] = f"{(total_sup/total_sc*100):.1f}"
            variables["ASSERTION_CONTRADICT_PCT"] = f"{(total_con/total_sc*100):.1f}"
        else:
            variables["ASSERTION_SUPPORT_PCT"] = "0.0"
            variables["ASSERTION_CONTRADICT_PCT"] = "0.0"

Add 3 tests to tests/test_variables.py for pct computation, zero-case, missing-file case.
Commit.

---

## PHASE 4: POLISH

### Task 4.1: Remove unused bib entry
manuscript/references.bib: delete @article{engel2016pragmatic, ...}. Commit.

### Task 4.2: Final verification
- scripts/05_inject_variables.py: no unresolved vars (except intentional VAR_NAME)
- pytest: 520 passed, coverage ≥90%%
- PDF renders via infrastructure
- Cross-refs all valid
Commit.

### Task 4.3: Version bump and changelog
- manuscript/config.yaml: version "2.0"
- README.md: add "## Changelog" section with v2.0 bullet list
Commit.

---

**Total:** ~15–20 atomic commits.

# template_registered_report TODO

## Current validation evidence

- Tests cover registration freezing, required sections, duplicate hypotheses, outcome drift, deviation classification, stage/ethics metadata, sensitivity-analysis validation, review packets, exploratory-claim boundaries, and the deterministic demonstration study (seeded data synthesis, permutation test, plan-driven analysis binding, figure-data helpers, and manuscript-prose binding against live analysis values). `scripts/generate_review_artifacts.py` exports deterministic frozen-registration, adherence, deviation-ledger, and review-packet artifacts under `output/reports/`; `scripts/generate_figures.py` renders four committed manuscript figures and writes the executed analysis to `output/data/demo_analysis.json`, to which the manuscript numbers are bound.
- Fresh full-suite run: all tests pass with coverage above the 90% floor; prerender validation reports no render-blocking pitfalls; the combined PDF renders with zero LaTeX errors and zero unresolved `??` references.

## Pass log (2026-08-02)

- Corrected stale documentation listings: `tests/README.md` and `tests/AGENTS.md` now name all four test files on disk (`test_protocol.py`, `test_demo_study.py`, `test_figures.py`, `test_generate_figures_script.py`); `scripts/AGENTS.md` now lists `generate_review_artifacts.py` alongside `generate_figures.py`.
- Corrected `src/registered_report/README.md` (was "two modules" and claimed figure rendering lives in `scripts/`): it now documents the three modules including `figures.py` and the thin-script split; aligned `manuscript/figures/README.md` and `src/registered_report/AGENTS.md` to the same module map.
- Added the missing `.agents/README.md` and `.agents/skills/README.md` orientation files per the shared exemplar contract.
- Verified version consistency across `pyproject.toml`, `manuscript/config.yaml`, `CITATION.cff`, `codemeta.json`, and `.zenodo.json` (all `0.1.0`, DOI `10.5281/zenodo.21298892`, repository `docxology/template_registered_report`); verified the manuscript's registration-hash prefix (`96a34a11d132`) and every quoted statistic against a fresh `run_registered_analysis` / review-packet regeneration.
- Regenerated figures, analysis data, review artifacts, and the combined PDF through the canonical pipeline; no source defects found.
- Second pass (same day): shipped the manuscript sensitivity-analysis surface — `04_results.md` now renders the registered sensitivity row (bound to the frozen registration's `sensitivity_analyses`, the source `build_review_packet` consumes) and the abstract names the preregistered sensitivity check. Added binding tests: the sensitivity row and deviation-ledger prose are re-derived against live code, and `test_review_artifacts_match_fresh_regeneration` asserts the committed `output/reports/*.json` artifacts equal a fresh `scripts/generate_review_artifacts.py`-equivalent regeneration. This closes the "Add rendered sensitivity-analysis tables" test/validator gap and the "keep review artifacts regenerated" integrity gap.

## Integrity and template-status gaps

- Keep rendered manuscript outputs and registered-report review artifacts regenerated after fixture, deviation, or sensitivity-analysis changes (now enforced by `test_review_artifacts_match_fresh_regeneration` for the committed artifacts).

## Configurable-surface gaps

- Keep ethics-review and registered-report-stage metadata aligned with any future journal-specific fixtures.

## Documentation and signposting gaps

- Keep standalone fork guidance synchronized with the validator API.

## Test and validator gaps

- (Closed 2026-08-02) Rendered sensitivity-analysis tables — shipped in manuscript/test surface.

## Ordered improvement ladder

1. Keep preregistration tests green.
2. Deviation-ledger export — shipped in source/tests.
3. Registered-report review packet — shipped in source/tests/script.
4. Rendered registration packet outputs — shipped in script/output generation.
5. Deterministic demonstration study + four manuscript figures — shipped in source/tests/script/manuscript.
6. Add publication receipts for a real exemplar.

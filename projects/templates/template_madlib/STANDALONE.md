# Standalone Notes

This project can be copied as a starting point for conditional manuscript generation. In the template monorepo it is built and rendered through the shared pipeline; after copying it elsewhere, keep these surfaces aligned:

- `manuscript/config.yaml` owns lexicon categories, slots, section switches, section titles, narrative moves, method protocol, design principles, pipeline phases, evaluation criteria, QA probes, failure modes, authoring obligations, visualization controls, audit rules, and contribution claims.
- `src/config.py` owns schema validation plus explicit/default path tracking.
- `src/tokens.py` owns deterministic token selection.
- `src/composition.py` owns generated manuscript bodies, Markdown evidence tables, and grouped figure references.
- `src/analysis.py` owns artifact generation, configured-field inventories, the cover overview, and generated manuscript figures.
- `src/manuscript_variables.py` owns the hydrated manuscript variable map.
- `scripts/z_generate_manuscript_variables.py` owns writing `output/manuscript/`.

Before a fork claims a new method, update the config-owned method surface first:

- Add or revise `method_protocol` rows for each action, evidence artifact, and output.
- Add or revise `pipeline_phases` for each input, transformation, output, and guard.
- Document token-selection invariants and keep token choice isolated from renderer state or copied-output state.
- Add `quality_probes`, `failure_modes`, and `audit_rules` that can catch the new method failing.
- Add `contribution_claims` and `data/claim_ledger.yaml` rows only for claims backed by local artifacts or real external evidence.
- Assemble a review packet that includes generated Markdown, PDF, HTML, slides, figures, data, reports, validation results, and copy statistics.
- Write fork migration notes that name config, source, tests, validators, pipeline stages, and claim-ledger changes.
- Add domain validators before making empirical, theoretical, benchmark, or reader-quality claims.

Run the project-local gate after edits:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/01_generate_madlib_artifacts.py
uv run python scripts/z_generate_manuscript_variables.py
```

Do not add DOI metadata until the fork has a real deposited record. Do not hand-edit generated Markdown, PDF, HTML, slides, figures, reports, or copied deliverables as if they were source; regenerate them through the equivalent Stage 02-05 pipeline.

# Standalone Notes

This project can be copied as a starting point for analogical manuscript
composition with mega-madlib token injection. In the template monorepo it is
built and rendered through the shared pipeline; after copying it elsewhere,
keep these surfaces aligned:

- `manuscript/config.yaml` owns the `gold_refinement:` schema: seed, lexicon,
  slots, section conditions, section titles, narrative moves, design
  principles, quality probes, failure modes, and authoring obligations.
- `src/refinery.py` owns the five refinery stages and monotone purity enforcement.
- `src/purity.py` owns karat grading and nine-nines certification.
- `src/config.py` owns schema validation and the mega-madlib config dataclass.
- `src/composition.py` owns deterministic token selection and section composition.
- `src/assay.py` owns claim-evidence validation.
- `src/manuscript_variables.py` owns the hydrated manuscript variable map.
- `scripts/z_generate_manuscript_variables.py` owns writing `output/manuscript/`.

Before a fork claims a new method, update the config-owned method surface first:

- Add or revise refinery stages in `src/refinery.py` with matching purity targets.
- Update lexicon categories in `manuscript/config.yaml` to reflect domain vocabulary.
- Connect refinery stages to real domain operations (not just decorative labels).
- Add `design_principles`, `quality_probes`, and `failure_modes` that can catch
  the new method failing.
- Add `data/claim_ledger.yaml` rows only for claims backed by local artifacts.
- Add domain validators before making empirical, theoretical, or benchmark claims.

Run the project-local gate after edits:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/refinement_analysis.py
uv run python scripts/z_generate_manuscript_variables.py
```

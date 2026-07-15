# template_advanced_literature_review TODO

Forward-only backlog for the advanced multi-phase literature review exemplar. Keep this file focused on evidence, generated artifacts, and claim boundaries for the multi-phase architecture.

## Current validation evidence

Run from the template repository root:

```bash
uv run pytest projects/templates/template_advanced_literature_review/tests/ --cov=projects/templates/template_advanced_literature_review/src --cov-fail-under=90
uv run python scripts/audit/check_template_drift.py --strict --project templates/template_advanced_literature_review
uv run python scripts/docgen/exemplar_roster.py --check
```

Live test counts and coverage snapshots belong in `../../../docs/_generated/COUNTS.md`.

## Integrity and template-status gaps

- Keep the multi-phase corpus clearly marked with real DOI sources and proper attribution in README, manuscript, and generated-output prose.
- Ensure phase provenance is maintained throughout the pipeline: every generated artifact should trace back to contributing phases.
- Keep `data/subfield_defaults_exoplanet.yaml` tied to project-local configuration, not borrowed from sibling exemplars.

## Configurable-surface gaps

- Retargeting should remain config-owned through `manuscript/config.yaml` phase definitions; avoid hard-coded domain terms in multi-phase `src/` modules.
- Keep phase temporal boundaries, filtering criteria, and LLM prompts explicit and configurable.
- Ensure new domains can define their own methodological phases without code changes.

## Documentation and signposting gaps

- Keep README, AGENTS, and `docs/_generated/exemplar_roster.md` synchronized through the generator.
- Document multi-phase architecture distinctly from single-term template capabilities.
- Keep troubleshooting examples specific to multi-phase scenarios (phase filtering failures, cross-phase validation conflicts).

## Test and validator gaps

The open work below should add tests or validators before promoting new claim surfaces.

| ID | Track | Future improvement | Proving artifact | Gate |
| --- | --- | --- | --- | --- |
| `ARL-PHASE-VALIDATION-1` | Multi-phase | Add negative controls for phase temporal boundary violations | `output/data/phase_validation_report.json` | Phase boundary test with overlapping/invalid ranges |
| `ARL-CROSS-PHASE-1` | Cross-validation | Persist cross-phase hypothesis validation metadata alongside scoring | `output/data/cross_phase_analysis.json` | Cross-phase validation test with conflicting evidence |
| `ARL-LLM-FILTER-1` | Filtering | Add calibration fixtures for LLM-based abstract content filtering | calibration fixture bundle | LLM filter tests with known positive/negative examples |
| `ARL-PHASE-PROVENANCE-1` | Provenance | Ensure all generated artifacts maintain phase-level provenance | all `output/` artifacts with phase metadata | Provenance audit across full pipeline |

## Ordered improvement ladder

1. Preserve multi-phase corpus integrity with proper attribution and real DOI sources.
2. Add focused validators for phase boundary enforcement and cross-phase consistency checks.
3. Expand LLM filtering calibration with domain-specific positive/negative controls.
4. Implement comprehensive phase provenance tracking across all pipeline stages.
5. Document advanced multi-phase patterns for replication in other domains.
6. Refresh generated docs after any multi-phase surface changes.

## Multi-Phase Specific Considerations

- **Phase Definition Discipline**: New phases should have clear temporal boundaries, distinct methodological focus, and appropriate filtering criteria.
- **Cross-Phase Validation**: Later phases should validate, not merely supplement, earlier phase findings.
- **LLM Filter Calibration**: Abstract content filtering requires domain-specific calibration datasets for reliable precision/recall.
- **Temporal Coherence**: Phase-aware statistics must handle temporal overlaps and methodological transitions gracefully.

## Promotion Rule

Move an item out of this file only after its source producer, generated artifact, documentation, and focused tests are updated together AND multi-phase provenance is verified throughout the pipeline.
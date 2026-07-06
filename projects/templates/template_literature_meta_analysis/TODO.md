# template_literature_meta_analysis TODO

Forward-only backlog for the public literature meta-analysis exemplar. Keep this file focused on evidence, generated artifacts, and claim boundaries.

## Current validation evidence

Run from the template repository root:

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90
uv run python scripts/audit/check_template_drift.py --strict --project templates/template_literature_meta_analysis
uv run python scripts/docgen/exemplar_roster.py --check
```

Live test counts and coverage snapshots belong in `../../../docs/_generated/COUNTS.md`.

## Integrity and template-status gaps

- Keep the fixture corpus clearly marked as synthetic in README, manuscript, and generated-output prose.
- Keep `data/claim_ledger.yaml` tied to project-local sources, not sibling exemplar paths.

## Configurable-surface gaps

- Retargeting should remain config-owned through `manuscript/config.yaml`; avoid hard-coded domain terms in `src/`.
- Keep live retrieval knobs explicit for engines, relevance keywords, subfields, and hypotheses.

## Documentation and signposting gaps

- Keep README, AGENTS, and `docs/_generated/exemplar_roster.md` synchronized through the generator.
- Keep troubleshooting examples on `template_literature_meta_analysis`, not sibling exemplars.

## Test and validator gaps

The open work below should add tests or validators before promoting new claim surfaces.

| ID | Track | Future improvement | Proving artifact | Gate |
| --- | --- | --- | --- | --- |
| `LIT-ENGINE-POLITENESS-1` | Retrieval | Add per-engine persisted rate-limit/backoff metadata for live retrieval runs | `output/data/retrieval_run_manifest.json` | Live-run smoke with skipped/limited engine rows |
| `LIT-FIXTURE-HONESTY-1` | Manuscript | Add a validator that fails if synthetic fixture results are phrased as empirical modafinil findings | fixture-claim audit report | Negative-control manuscript sentence fails |
| `LIT-FULLTEXT-1` | Full text | Expand full-text availability report with provider, license, and checksum fields | `output/fulltext/fulltext_inventory.json` | Full-text report test with OA and non-OA fixtures |
| `LIT-KG-CALIBRATION-1` | Knowledge graph | Add extraction-calibration fixtures for each configured hypothesis family | calibration fixture bundle | KG parser/scorer tests preserve score direction |

## Ordered improvement ladder

1. Preserve offline fixture reproducibility and synthetic-data honesty.
2. Add focused validators for live retrieval manifests and full-text inventories.
3. Expand KG calibration only with fixture-backed negative controls.
4. Refresh generated docs after any public-surface change.

## Promotion Rule

Move an item out of this file only after its source producer, generated artifact, documentation, and focused tests are updated together.

## Recent improvements (2026-06)

- Added 87 new targeted tests covering previously untested code paths in `variables.py`,
  `field_overview.py`, `citation_plots.py`, `figure_runner.py`, and `embeddings.py`.
- Coverage improved from 93.64% → 96.86% (project-level src/) with 859 tests passing.
- Key coverage gains: `variables.py` 74.11% → 96.30%, `field_overview.py` 92.41% → 100%,
  `citation_plots.py` 93.81% → 98.97%, `figure_runner.py` 85.28% → 95.43%.
- New test classes: `TestHumanizeList`, `TestFulltextAssessmentVariables`,
  `TestDescriptiveStatsVariables`, `TestEntityVariables`, `TestEmbeddingAnalysisVariables`,
  `TestAdvancedCitationVariables`.
- `ruff` and `mypy` both clean (no new issues).

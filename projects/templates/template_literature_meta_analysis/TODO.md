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
| `LIT-ENGINE-POLITENESS-1` | Retrieval | Persist per-engine retry and rate-limit-hit metadata alongside the existing elapsed time | `output/data/retrieval_run_manifest.json` | Live-run smoke with skipped/limited engine rows |
| `LIT-FULLTEXT-1` | Full text | Add license and checksum fields to the provider-aware full-text availability report | `output/fulltext/fulltext_inventory.json` | Full-text report test with OA and non-OA fixtures |
| `LIT-KG-CALIBRATION-1` | Knowledge graph | Add extraction-calibration fixtures for each configured hypothesis family | calibration fixture bundle | KG parser/scorer tests preserve score direction |

## Ordered improvement ladder

1. Preserve offline fixture reproducibility and synthetic-data honesty.
2. Add focused validators for live retrieval manifests and full-text inventories.
3. Expand KG calibration only with fixture-backed negative controls.
4. Refresh generated docs after any public-surface change.

## Promotion Rule

Move an item out of this file only after its source producer, generated artifact, documentation, and focused tests are updated together.

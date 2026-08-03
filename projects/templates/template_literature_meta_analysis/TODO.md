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

### 2026-08-02 publication-pass evidence

- Pre-render validation passed: no render-blocking pitfalls or undefined citations.
- Project tests passed: 1,162 passed, 0 failed, 0 skipped; coverage 94.10% (required 90%).
- Stage 02 analysis completed successfully and regenerated the offline fixture outputs.
- Stage 03 rendered the combined PDF, web manuscript, slides, and figure outputs. The
  compiled TeX contained all 18 figure labels, with 0 literal `{{#fig:...}}` leaks and
  0 LaTeX `!` errors; the committed PDF contained 0 unresolved `??` references and
  was 40 pages. The three captions not exposed by `pdftotext` were present in the
  compiled `.aux` figure-label records (figures 3, 6, and 8).
- Stage 04 validation passed after refreshing the integrity manifest; all checks passed,
  including PDF, Markdown, figure registry (21 registered / 18 referenced), evidence,
  design overlays, artifact manifest, and rendered provenance inputs.
- Stage 05 copied 265 outputs, including the 7.01 MB combined PDF, to the root output
  tree. Template drift check passed with no drift detected.

### Fixed in this publication pass

- Replaced invalid double-braced pandoc-crossref figure labels with single-braced labels.
- Reconciled the ten configured retrieval engines in the claim ledger and documentation.
- Corrected stale citation, figure-count, hypothesis-token, and subfield-token claims.
- Updated script/figure inventories and added the missing `.agents` README signposts.
- Removed the unsupported SHA-256 figure-registry claim and documented the actual registry
  fields; removed the unused validation block from `config.yaml.example`.

## Integrity and template-status gaps

- Keep the fixture corpus clearly marked as synthetic in README, manuscript, and generated-output prose.
- Keep `data/claim_ledger.yaml` tied to project-local sources, not sibling exemplar paths.

### Shipped in the current lane

- `LIT-FULLTEXT-1`: stage 06 now writes `output/fulltext/fulltext_inventory.json`
  with provider, declared-license, local-path, byte-size, and SHA-256 fields.
  Open-access status never substitutes for a declared license, and a remote URL
  never substitutes for a local artifact checksum. Focused OA/non-OA fixtures
  cover both refusal-to-infer and local-file paths.

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
| `LIT-KG-CALIBRATION-1` | Knowledge graph | Add extraction-calibration fixtures for each configured hypothesis family | calibration fixture bundle | KG parser/scorer tests preserve score direction |

## Ordered improvement ladder

1. Preserve offline fixture reproducibility and synthetic-data honesty.
2. Add focused validators for live retrieval manifests and full-text inventories.
3. Expand KG calibration only with fixture-backed negative controls.
4. Refresh generated docs after any public-surface change.

## Promotion Rule

Move an item out of this file only after its source producer, generated artifact, documentation, and focused tests are updated together.

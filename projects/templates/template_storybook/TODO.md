# template_storybook TODO

Forward-only backlog for the full-page illustrated storybook exemplar.

## Current validation evidence

- Project tests and coverage (2026-08-02):
  `uv run pytest projects/templates/template_storybook/tests/ --cov=projects/templates/template_storybook/src --cov-fail-under=90`
  → 21 passed, 0 failed, 0 skipped; coverage 95.68% (pytest) / 94.4% (stage-01
  project-tests run, `scripts/pipeline/stage_01_test.py --project-only --project templates/template_storybook`).
- Pre-render validation:
  `uv run python -m infrastructure.validation.cli prerender projects/templates/template_storybook/manuscript --repo-root .`
  → no render-blocking pitfalls or undefined citations.
- Stage-02 storybook render: 15/15 analysis scripts passed; primary PDF
  `output/pdf/the-shape-between.pdf` (14 pages) + contact sheet + manifest
  regenerated.
- Stage-03 manuscript render: `template_storybook_combined.pdf` (8 pages) plus
  HTML and 6 Beamer slide decks; 0 `^! ` lines in `output/pdf/*.log`, 0 `??`
  in both PDFs.
- Stage-04 validation: all checks passed; rendered provenance receipt written.
- Stage-05 copy: outputs copied to repo `output/templates/template_storybook/`.
- Template drift (2026-08-02):
  `uv run python scripts/audit/check_template_drift.py --project templates/template_storybook --strict`
  → no drift detected.

## Integrity and template-status gaps

- Keep story text in `content/story.yaml` and rendering behavior in `src/storybook/`.
- Keep every story page as a full-page illustration; no manuscript-style partial
  figures for the primary artifact.
- Page-level accessibility alt text is now generated in
  `output/data/storybook_manifest.json`; keep it descriptive when page content
  changes.
- 2026-08-02 pass: enumerated the actual script and test files in
  `scripts/AGENTS.md` and `tests/AGENTS.md` so the listings can be compared
  against disk; completed the `docs/README.md` index (added `style_guide.md`
  and `agent_instructions.md`); added `.agents/README.md` and
  `.agents/skills/README.md` orientation files to complete the shared
  `.agents/` skill-catalog surface.

## Configurable-surface gaps

- Add optional page trim sizes beyond the current letter-ratio PNG and PDF.
- Add per-page text placement controls if future forks need top, middle, and
  bottom caption zones.

## Documentation and signposting gaps

- Keep README examples clear that Stage 02 renders the storybook PDF, while
  Stage 03 renders the descriptive manuscript PDF.
- The deterministic contact sheet is generated at
  `output/figures/storybook_contact_sheet.png` for every Stage-02 render.

## Test and validator gaps

- Add a small raster contrast audit for direct text overlays. **Shipped:**
  `tests/test_contrast_audit.py` implements WCAG 2.1 contrast-ratio checks
  using real pixel math on rendered storybook pages; the Stage-02 PDF builder
  runs the same audit for every rendered page and records the results in the
  manifest. Extend the palette contract if future forks add new overlay modes.

## Ordered improvement ladder

1. Keep deterministic page rendering and PDF assembly green.
2. Add trim-size variants.
3. Keep contact-sheet generation and page-level accessibility metadata aligned
   with content changes.
4. Keep the raster contrast audit aligned with any new overlay modes.

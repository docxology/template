# template_storybook TODO

Forward-only backlog for the full-page illustrated storybook exemplar.

## Current validation evidence

- Project tests and coverage:
  `uv run pytest projects/templates/template_storybook/tests/ --cov=projects/templates/template_storybook/src --cov-fail-under=90`
- Stage-02 storybook render:
  `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_storybook`
- Stage-03 manuscript render:
  `uv run python scripts/pipeline/stage_03_render.py --project templates/template_storybook`

## Integrity and template-status gaps

- Keep story text in `content/story.yaml` and rendering behavior in `src/storybook/`.
- Keep every story page as a full-page illustration; no manuscript-style partial
  figures for the primary artifact.
- Page-level accessibility alt text is now generated in
  `output/data/storybook_manifest.json`; keep it descriptive when page content
  changes.

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

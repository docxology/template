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
- Add richer accessibility alt-text metadata if the project grows beyond this
  initial exemplar.

## Configurable-surface gaps

- Add optional page trim sizes beyond the current letter-ratio PNG and PDF.
- Add per-page text placement controls if future forks need top, middle, and
  bottom caption zones.

## Documentation and signposting gaps

- Keep README examples clear that Stage 02 renders the storybook PDF, while
  Stage 03 renders the descriptive manuscript PDF.
- Add a visual contact sheet for the current fourteen-page book.

## Test and validator gaps

- Add a small raster contrast audit for direct text overlays.

## Ordered improvement ladder

1. Keep deterministic page rendering and PDF assembly green.
2. Add trim-size variants.
3. Add contact-sheet generation.
4. Add accessibility metadata and contrast validation.

# Forking Guide — make it *your* paper

Because content is data, turning *The Triplicate* into a different title is an
edit to `content/`, not to `src/`.

## 1. Rename the masthead

Edit `content/edition.yaml` → `masthead`:

```yaml
masthead:
  nameplate: "The Campus Daily"
  city: "Your Town"
  state: "Your State"
  date: "Monday, September 1, 2025"
  motto: "Independent since 2025"
  established: "2025"
  weather_strip: "TODAY: Sunny, 75°"
```

## 2. Rewrite the pages

Each file in `content/pages/` is a self-describing page. Replace the stories,
boxes and figures with your own (see `docs/syntax_guide.md`). To change the
number of pages, edit the `pages:` list in `edition.yaml` — the engine adapts to
any count.

## 3. Bring your own art

Drop images in `output/figures/` and point a story/figure `path` at them, or
extend `src/newspaper/figures.py` with new procedural scenes/charts and add them
to `generate_all`. Missing images degrade to placeholders, so you can lay out
first and add art later.

The shipped art is **procedural** (Pillow halftone scenes — harbor, lighthouse,
redwoods, lily fields, baseball, crab boat — plus Matplotlib charts), which is
deterministic and needs no API. To use **AI-generated** photos or engravings
instead, generate them with the `/art` skill (requires an image-model API key —
`GOOGLE_API_KEY` / `OPENAI_API_KEY` / Flux), save them under `output/figures/`
(the configured `figures_dir`, where the generators also write), and point the
figure `path` at them. `_resolve_image_path` resolves any path relative to the
project root, so the engine treats a custom image identically to a generated one.

## 4. Tune the look (optional)

- Trim size, columns, rail width, gutter: `edition.yaml` → `render`.
- Type scale, colors, fonts: `src/newspaper/typography.py` (the *only* place a
  font is named).
- Page templates: `front | standard | opinion | feature | classified`. Only
  `front` (nameplate) and `classified` (dense grid) change the layout path;
  `standard`/`opinion`/`feature` share the standard inside-page furniture and are
  semantic/section tags — distinct looks (A5 masthead, A4 jump) come from the
  page's *content* blocks, not the template.

## 5. Render and verify

```bash
python scripts/10_generate_figures.py
python scripts/20_render_newspaper.py
pdftoppm -png -r 100 output/pdf/<your-basename>.pdf /tmp/p   # then look
```

## Common adaptations

| You want… | Do this |
|-----------|---------|
| A 4-page program | trim `pages:` to 4 files |
| A broadsheet | `render: { page: broadsheet }` |
| No left rail on the front | remove the `rail:` block, set `rail_enabled: false` |
| A wider, magazine-y feel | `columns: 3` on feature pages |
| A pure classifieds flyer | one `classified` page with many `generic` boxes |

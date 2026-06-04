# Assets

Static, hand-managed assets for the book — distinct from the **generated**
figures and diagrams that scripts produce into `output/`.

## Contents

- `cover/` — the book cover image.
  - `cover/template_textbook_cover.png` — **placeholder** cover, to be generated.
    The path and alt text are declared in [`../config.yaml`](../config.yaml) under
    `book.cover` (`image:` and `alt:`). Replace the placeholder with a real cover
    and keep the config entry in sync.

## Conventions

- Reference assets from manuscript markdown with **relative** links
  (e.g. `assets/cover/template_textbook_cover.png`), never absolute paths.
- Give every image meaningful alt text.
- Static assets that authors curate by hand live here; anything a script can
  regenerate belongs in `output/` and must not be committed.

<!-- STUB: list additional static assets (logos, photographs, externally
licensed images) and their licenses as you add them. -->

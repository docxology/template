# Troubleshooting

### Headlines look italic / wrong weight
A `.ttc` font collection orders its faces by an index that is **face-specific**.
Didot is `0=Regular, 1=Italic, 2=Bold`. If you add a display face, verify with
`TTFont(name, path, subfontIndex=i).face` before trusting an index.

### The nameplate runs off the edge
The nameplate auto-fits to ~90% of the content width (`furniture.draw_nameplate`
scales the font size with `stringWidth`). If you hard-set a size, it can
overflow — let the auto-fit work, or lower the cap.

### A page is mostly white at the bottom
The page is **under-set**: compact boxes and tables do not fill a 15″ column —
prose does. Add a longer article, more letters, or more directory/legal copy.
Balancing is intentionally sequential (fill column 1, then 2, …), like many real
papers.

### `RenderResult.all_pages_fit` is False
A page is **over-set** — content was dropped off the bottom of the last column.
`oversets` names the page and how many flowables didn't fit. Shorten the copy or
move an item to another page. Run `20_render_newspaper.py --strict` to fail the
stage on over-set.

### A figure shows a gray "photo" box
The image path didn't resolve (relative to the project root). Run
`10_generate_figures.py`, or fix the `path:` in the page YAML. Missing images are
intentional placeholders, never crashes.

### Fonts differ on another machine
Expected. Didot/Georgia are macOS supplemental fonts; on machines without them
the engine falls back to Times/Helvetica. The layout is identical; only the
typeface changes.

### `discover_projects` doesn't list the project
It requires `src/` (with `.py` files) and `tests/`. Confirm both exist and that
you're pointing at the repo root.

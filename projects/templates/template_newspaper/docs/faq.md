# FAQ

**Is *The Triplicate* a real paper?**
Yes — Crescent City, California's newspaper, founded 1879 and named for the three
copies of its first press run. This project is a *template edition*: the masthead
is homage, but every story, byline, name and event in `content/` is fictional.

**Why a newspaper?**
It is the hardest, most legible test of a layout engine: mastheads, spanning
headlines, flowing columns, rails, boxes, tables and figures, all on one page,
across twelve pages. If the engine can do a newspaper, it can do a report.

**Why ReportLab and not HTML/CSS (WeasyPrint)?**
Pure Python, no system (pango/cairo) dependencies, and exact frame/rule control.
The newspaper PDF builds anywhere Python runs.

**Can I make a 4-page or 24-page paper?**
Yes. The `pages:` list in `content/edition.yaml` sets the count; the engine
adapts. The "12-page" figure is just this edition's roster.

**Can I use color?**
The template is monochrome (newsprint). You can set `spot_color` and extend the
palette in `typography.py`, but the figures are designed grayscale.

**Where does the newspaper PDF come from in the pipeline?**
Stage 02 (analysis), via `scripts/`. Stage 03 separately renders the descriptive
`manuscript/`. See `rendering_pipeline.md`.

**How do I add a new figure type?**
Add a builder to `src/newspaper/figures.py` and register it in `generate_all`;
reference it from a page's `figure: { path: ... }`.

**Why is one page emptier than the others?**
See troubleshooting → under-set. Compact boxes don't fill tall columns; add
prose.

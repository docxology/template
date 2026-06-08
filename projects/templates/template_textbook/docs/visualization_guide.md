# Visualization Guide

All figures and diagrams are generated **deterministically** from `src/` — never
edited by hand and never committed. Re-running the generators reproduces
byte-stable artifacts, which keeps renders reproducible and tests honest.

## Figures: `src/visualization`

[`src/visualization/plots.py`](../src/visualization/plots.py) produces two kinds
of matplotlib figure:

1. **Worked figures** — four figures driven by the tested formalisms in
   [`src/textbook/models.py`](../src/textbook/models.py):
   - `plot_logistic_growth`
   - `plot_saturating_response`
   - `plot_exponential_decay`
   - `plot_linear_fit`
2. **Chapter placeholders** — `generate_chapter_placeholders()` emits one neutral
   titled placeholder per chapter in `config.yaml`, via `placeholder_overview()`.

`generate_all_figures(output_dir, config=None)` produces all of them. The shared
helpers [`src/visualization/_scaffold.py`](../src/visualization/_scaffold.py)
(`new_figure`, `save_figure`) keep styling and the save path consistent and
deterministic.

The committed cover image
[`manuscript/assets/cover/template_textbook_cover.png`](../manuscript/assets/cover/template_textbook_cover.png)
is itself a deterministic, tested artifact: regenerate it by calling
`cover_art(output_dir)` from [`src/visualization/plots.py`](../src/visualization/plots.py)
(byte-stable nested modular blocks), then copy the result over the tracked asset.

### The filename contract

Each chapter placeholder is named **`<part_id>_<stem>.png`** — for example
`part_0_orientation.png`, `part_I_first_principles.png`. This exactly matches the
image path the scaffolded chapter already references:

```markdown
![Overview schematic …](../../output/figures/part_0_orientation.png){#fig:part_0_orientation width=90%}
```

Because the filename is derived from the same `ChapterRef` the manuscript uses,
a newly scaffolded chapter's figure path resolves the moment you run the
generator — no manual wiring.

### Generating figures

```bash
uv run python scripts/generate_figures.py                 # → output/figures/
uv run python scripts/generate_figures.py --output-dir <dir>
```

[`scripts/generate_figures.py`](../scripts/generate_figures.py) is a thin
orchestrator: it calls `generate_all_figures` and prints each output path for the
pipeline manifest. It is one of the `analysis.scripts` in
[`config.yaml`](../manuscript/config.yaml), so it runs during a normal build.

## Diagrams: `src/mermaid`

[`src/mermaid/`](../src/mermaid) renders Mermaid diagrams from
[`diagram_specs.yaml`](../src/mermaid/diagram_specs.yaml):

- `load_specs()` reads the spec list.
- `build_flowchart()` / `build_source()` turn a spec into Mermaid source.
- `generate_all_diagrams(output_dir, specs_path=None)` writes every diagram. If
  the Mermaid CLI `mmdc` is available (`mmdc_available()`), each diagram renders
  to **PNG**; otherwise it falls back to a `.mmd` source file so a build never
  hard-fails on a missing optional tool.

```bash
uv run python scripts/generate_diagrams.py
```

Note: these are the *standalone* diagram assets. The **inline** `` ```mermaid ``
block required inside every chapter is rendered by the document renderer at PDF
build time, not by this generator.

## Adding a real figure for a chapter

To replace a chapter's generated placeholder with a real, data-driven figure:

1. **Put the math in `src/`.** Add the computation to
   [`src/textbook/models.py`](../src/textbook/models.py) (or a new tested module)
   — never in the script. Add a test for it (no mocks; real numbers).
2. **Add a plot function** in `plots.py` that imports the model function, builds
   the figure with `_scaffold.new_figure`, and saves it with `save_figure` under
   the **same filename** the chapter references: `<part_id>_<stem>.png`. Override
   the placeholder by registering it in `generate_all_figures` (or replacing the
   corresponding `generate_chapter_placeholders` entry).
3. **Regenerate** with `uv run python scripts/generate_figures.py` and confirm
   `output/figures/<part_id>_<stem>.png` exists.
4. **Update the chapter** so the figure caption and the `<!-- alt: ... -->`
   comment describe the real figure (the image path is already correct).
5. **Run the visualization tests** (see the [testing guide](testing_guide.md)):
   `uv run --extra dev python -m pytest tests/test_visualization.py`.

Keep figures deterministic: fixed seeds, fixed sizes via `new_figure`, no
timestamps or randomised colours. The same input must always produce the same
PNG.

## Rendering Mermaid diagrams to images (PDF/HTML)

Inline ```` ```mermaid ```` blocks in chapters are rendered to images at build
time by the repository's render pipeline using the Mermaid CLI (`mmdc`), which
needs a Chrome/Chromium binary. Two ways to point it at one:

1. Set `PUPPETEER_EXECUTABLE_PATH` (or `CHROME_EXECUTABLE_PATH`) to your browser
   binary before rendering, or
2. Drop a local `.puppeteer.json` at the project root (git-ignored — it holds a
   machine-specific path), for example:

   ```json
   {
     "executablePath": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
     "args": ["--no-sandbox", "--disable-setuid-sandbox"]
   }
   ```

Without a reachable browser, diagrams degrade gracefully to fenced code blocks in
the output and `src/mermaid` writes `.mmd` source instead of PNG — the build
never hard-fails. With it, the combined PDF embeds the rendered diagrams (verified:
17 inline diagrams render into the book).

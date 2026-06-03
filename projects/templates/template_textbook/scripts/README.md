# `scripts/` — thin orchestrators

Every script here is a **thin orchestrator**: it imports tested code from
[`../src/`](../src/), handles I/O / orchestration, and prints output paths for
the pipeline's manifest collection. **Scripts never implement logic** — all
computation, validation, and rendering lives in `src/`.

## Scripts

| Script | Purpose | Command | Default output |
| --- | --- | --- | --- |
| `generate_figures.py` | Generate every matplotlib figure the manuscript references. Delegates to `visualization.plots.generate_all_figures`. | `uv run python scripts/generate_figures.py` | `output/figures/` |
| `generate_diagrams.py` | Render every Mermaid diagram (PNG, or `.mmd` fallback). Delegates to `mermaid.diagrams.generate_all_diagrams`. | `uv run python scripts/generate_diagrams.py` | `output/figures/mermaid/` |
| `analysis.py` | Run the worked models and emit a small JSON data artifact. All maths comes from `textbook.models`; the script only does I/O. | `uv run python scripts/analysis.py` | `output/data/` |
| `scaffold_chapter.py` | Author tool — materialise missing chapter / lab / question stub files declared in `config.yaml`. Delegates to `textbook.content`. Existing files untouched unless `--force`. | `uv run python scripts/scaffold_chapter.py` | `manuscript/{<part>,labs,questions}/` |
| `audit_textbook_quality.py` | Quality gate — load `config.yaml`, validate each chapter against the `textbook.content` contract, confirm matching lab/question files exist, print a stub/word-count progress table. Exits non-zero on any missing or invalid chapter. | `uv run python scripts/audit_textbook_quality.py` | stdout (gate; no files) |

## Growing the book

1. Add a chapter entry to `manuscript/config.yaml`.
2. `uv run python scripts/scaffold_chapter.py` to write contract-satisfying stubs.
3. Fill the stubs (replace `<!-- STUB -->`, `TODO:`, `TKTK`).
4. `uv run python scripts/audit_textbook_quality.py` to check structure and progress.

If you need new behavior, add it to `src/` (with a test) and call it from a
script — do not implement it inline.

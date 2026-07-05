# `scripts/` — agent notes

These are **thin orchestrators only**. The hard rule: import tested functions
from [`../src/`](../src/), do I/O and orchestration, print output paths. **Never
implement algorithms, validation, or rendering in a script.** If logic is needed,
add it to a `src/` module with a test, then import it.

Each script begins by importing `from _bootstrap import PROJECT, ensure_project_paths`
and calling `ensure_project_paths()` so the `src/` packages resolve. Follow that
pattern for any new script.

## What each script delegates to

| Script | Delegates to | Output |
| --- | --- | --- |
| `generate_figures.py` | `visualization.plots.generate_all_figures`, optional `visualization.gallery.generate_gallery_figures`, `visualization.registry.write_figure_registry` | `output/figures/` |
| `generate_diagrams.py` | `mermaid.diagrams.generate_all_diagrams` | `output/figures/mermaid/` |
| `analysis.py` | `textbook.models` | `output/data/` (JSON) |
| `scaffold_chapter.py` | `textbook.content`, `textbook.config.iter_chapters` / `iter_unit_intros`, `textbook_io.write_text_atomic` | stub `.md` files under `manuscript/` |
| `audit_textbook_quality.py` | `textbook.audit.run_manuscript_audit` | stdout gate (strict by default; `--lenient` optional) |

## Conventions

- Print every produced path to stdout so the pipeline can collect a manifest.
- Keep figures/data deterministic — fixed seeds, headless matplotlib (`MPLBACKEND=Agg`).
- `audit_textbook_quality.py` is a real gate: strict by default (missing declared
  files and orphan part markdown fail). Pass `--lenient` only when intentionally
  auditing partial trees.
- `scaffold_chapter.py` must not overwrite authored files unless `--force`.

## Do not touch

`manuscript/config.yaml`, `references.bib`, `glossary.md`, and any chapter / lab /
question markdown are authored content. Scripts read them; agents editing scripts
must not modify them.

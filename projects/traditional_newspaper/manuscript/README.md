# Manuscript

- **Core:** `01_front_page.md` … `16_classifieds.md` — each opens `multicols{3}`; the front page includes the masthead image first.
- **Supplemental (tracked, after core):** `S01_layout_and_pipeline.md`, `S02_typography_and_measure.md`, `S03_validation_and_outputs.md` — same order as `newspaper.sections.all_tracked_manuscript_basenames()`.
- **Glossary:** `98_newspaper_and_pipeline_terms.md` — term table (after the supplemental trio).

## Assets

- `preamble.md` — tabloid `geometry`, `graphicx`, `multicol`, column separation.
- `config.yaml` — title and metadata for `\maketitle`.
- `references.bib` — includes `template2026gazette` (cited on front page and in `S01`).

## Figures

- `../output/figures/masthead.png` (front page; run analysis stage first).
- `../output/figures/section_banner_{stem}.png` — one per interior core folio (`02`–`16`) and each optional slice (`S01`–`S03`, `98`); from `generate_section_banners.py`.
- `../output/figures/layout_schematic.png` (S01).
- `../output/figures/wordcount_bars_bw.png` (S03; after `manuscript_stats.json`).

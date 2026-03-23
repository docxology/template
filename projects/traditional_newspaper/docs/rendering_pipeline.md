# Rendering pipeline — `traditional_newspaper`

## Manuscript assembly

- Markdown files under `manuscript/` are discovered by infrastructure (`discover_manuscript_files`) in an order consistent with the template (numbered sections, then supplemental `S*`, then glossary-style `98_*` where present).
- The PDF renderer inserts **`\newpage`** between combined files so each folio starts a fresh page (plus template title front matter).

## Preamble

- [`../manuscript/preamble.md`](../manuscript/preamble.md) sets paper size (tabloid), loads `graphicx`, `multicol`, and column separation. Folio bodies typically open `\begin{multicols}{3}` in raw LaTeX blocks.

## Figures

| Asset | Produced by | Referenced from |
|-------|-------------|-----------------|
| `masthead.png` | `scripts/generate_masthead.py` | Front page markdown (path relative to manuscript/output layout used in project) |
| `section_banner_*.png` | `scripts/generate_section_banners.py` | Interior core folios `02`–`16` and supplements `S01`–`S03`, glossary `98` |
| `layout_schematic.png` | `scripts/generate_layout_schematic.py` | Supplemental S01 (below the S01 banner figure) |
| `wordcount_bars_bw.png` | `scripts/visualization_wordcount_bw.py` | Supplemental S03 (`fig:wordcount_bw`); depends on `manuscript_stats.json` from the prior stats script in sorted analysis order |

Run `scripts/02_run_analysis.py --project traditional_newspaper` before render if figures are missing.

## Bibliography

- [`../manuscript/references.bib`](../manuscript/references.bib) includes entries such as `template2026gazette` cited from the front page and supplemental material.

## Validation

- Use root validation CLI as documented in the template, for example markdown validation on `manuscript/` and PDF checks on `output/traditional_newspaper/pdf/` after copy stage.

## See also

- [syntax_guide.md](syntax_guide.md) — `{=latex}` usage
- [../manuscript/README.md](../manuscript/README.md) — slice list

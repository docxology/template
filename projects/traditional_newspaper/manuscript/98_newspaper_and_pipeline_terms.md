# Glossary: Newspaper and pipeline terms

Short definitions for readers of this exemplar (not a general journalism style guide). Terms apply to the `traditional_newspaper` project and the surrounding template infrastructure unless noted.

| Term | Meaning here |
|------|----------------|
| **Folio** | One manuscript slice (`01_*.md` … `16_*.md`) that becomes a new page boundary in the combined PDF after the previous slice (plus template title front matter). |
| **Masthead** | The nameplate graphic at the top of the front page; raster asset `output/figures/masthead.png`, floated as Figure~\ref{fig:masthead} in the combined PDF. |
| **Slice** | Same as folio file: one ordered markdown unit in `manuscript/`. |
| **Preamble** | `manuscript/preamble.md`: LaTeX injected into the Pandoc document (geometry, `graphicx`, `multicol`). |
| **Raw LaTeX block** | Pandoc fenced region ` ```{=latex}` … ` ``` ` passing TeX through to the PDF engine. |
| **Thin orchestrator** | Script under `scripts/` that only configures paths, logging, and calls `src/newspaper/` functions. |
| **Fixture copy** | Deterministic placeholder paragraphs from `newspaper.content.fixture_copy` / `fixture_paragraph` for layout stress tests. |
| **Figure** | LaTeX `figure` environment with `\includegraphics`, `\caption`, and `\label`; autonumbered in PDF, mapped to `<figure>` in HTML when filters match. |
| **Caption** | Text under a figure explaining content; must avoid nested `}` braces inside `\caption{...}` for HTML conversion regexes. |
| **Label** | `\label{fig:...}` token paired with `\ref{...}` for cross-references resolved across multiple LaTeX passes. |
| **Combined PDF** | Single manuscript PDF built from all discovered slices in order; output path under `output/traditional_newspaper/pdf/`. |
| **XeLaTeX** | Unicode-capable LaTeX engine used by Pandoc `--pdf-engine=xelatex` in this project. |
| **layout_schematic.png** | Diagram from `render_layout_schematic_png`, written by `scripts/generate_layout_schematic.py`; illustrates `NewspaperLayout` constants. |
| **PAGE_SLICES** | Tuple in `sections.py` mapping stems to human section titles; defines the sixteen core edition order. |
| **MANUSCRIPT_OPTIONAL_FILENAMES** | Tuple listing `S01`, `S02`, `S03`, and `98_*` files included in stats and documentation beyond core inventory. |
| **discover_manuscript_files** | Infrastructure function sorting numeric stems, then `S*`, then `98_*`, then `99_*` references. |

The sixteen core folios are the “edition pages”; `S01_*`–`S03_*` and `98_*` files document the system without changing the numbering of those pages. When adding optional slices, extend `MANUSCRIPT_OPTIONAL_FILENAMES` and update tests that assert file counts.

# AGENTS: `manuscript/`

## Slice list (order)

Core edition folios match `src/newspaper/sections.PAGE_SLICES`:

1. `01_front_page` — `\includegraphics` masthead + `\cite{template2026gazette}` hook + `multicols{3}`
2. `02_national` … `16_classifieds` — `figure` with `section_banner_{stem}.png` (B\&W desk strip), then `multicols{3}` body

**After** core sections (per `discover_manuscript_files`):

- `S01_layout_and_pipeline.md` — pipeline, floats, figures (`masthead`, `layout_schematic`)
- `S02_typography_and_measure.md` — type, grids, print and screen notes
- `S03_validation_and_outputs.md` — CLI validation, outputs, ops checklist; `wordcount_bars_bw.png` float (`fig:wordcount_bw`)
- `98_newspaper_and_pipeline_terms.md` — glossary table and narrative

## Raw LaTeX

Sections use Pandoc fenced blocks:

````markdown
```{=latex}
\begin{multicols}{3}
```
````

Closing `\end{multicols}` in a matching block.

## Pipeline

Discovered by `infrastructure.rendering.manuscript_discovery.discover_manuscript_files`; `\newpage` is inserted **between** files by `PDFRenderer._combine_markdown_files`.

## Bibliography

`references.bib` includes `template2026gazette`; cited from `01_front_page.md` and `S01_layout_and_pipeline.md`.

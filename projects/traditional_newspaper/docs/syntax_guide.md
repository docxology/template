# Manuscript syntax — `traditional_newspaper`

## Raw LaTeX in Markdown

Folios use Pandoc **fenced code blocks** attributed to LaTeX:

````markdown
```{=latex}
\begin{multicols}{3}
```
````

Close environments in a matching block (for example `\end{multicols}`).

## Headlines and metadata lines

- The Python package [`../src/newspaper/snippets.py`](../src/newspaper/snippets.py) defines helpers such as `headline`, `byline`, `rule_line`, `dateline`, `section_label`, `pull_quote`, and `classified_line`. They escape LaTeX specials for safe inclusion in generated or templated strings.
- In static markdown, authors can write LaTeX directly inside `{=latex}` blocks; keep commands compatible with the preamble (see [`../manuscript/preamble.md`](../manuscript/preamble.md)).

## Graphics and citations

- `\includegraphics` paths must match files present under the project output or figure directories after analysis (see [rendering_pipeline.md](rendering_pipeline.md)).
- `\cite{key}` keys must exist in [`../manuscript/references.bib`](../manuscript/references.bib).

## Slice filenames

- Core: `01_front_page.md` through `16_classifieds.md` (stems must match `sections.PAGE_SLICES`).
- Optional tracked: `S01_layout_and_pipeline.md`, `S02_typography_and_measure.md`, `S03_validation_and_outputs.md`, `98_newspaper_and_pipeline_terms.md`.

## See also

- [../manuscript/AGENTS.md](../manuscript/AGENTS.md) — ordered slice description
- [architecture.md](architecture.md) — where slice lists are defined in code

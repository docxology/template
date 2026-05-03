# template_search_project/manuscript — Agent guide

## Purpose

Markdown source, LaTeX preamble, and bibliography for the literature-search manuscript. Source sections may use `{{UPPER_SNAKE}}` placeholders. Run `scripts/z_generate_manuscript_variables.py` after `run_search_pipeline.py`: it writes `output/data/manuscript_variables.json` and substitutes tokens into `output/manuscript/*.md` (plus copies `config.yaml` and `*.bib`). The PDF-rendering stage prefers `output/manuscript/` when it contains markdown (`infrastructure.rendering.pipeline._resolve_manuscript_dir`), so the PDF reflects resolved values. `src.analysis.validate_variables_resolved` scans `output/manuscript/` when present, otherwise `manuscript/`.

## Key files

| File | Role |
|------|------|
| [`config.yaml`](config.yaml) | Search query, LLM knobs, paper metadata |
| [`preamble.md`](preamble.md) | Shared LaTeX for PDF |
| [`00_abstract.md`](00_abstract.md) … section files | Body |
| [`99_references.md`](99_references.md) | Pointer to BibTeX |
| [`S01_literature_review.md`](S01_literature_review.md) | Auto-composed deep-search supplement (`s_compose_literature_review.py`) |
| [`references.bib`](references.bib) | Single-query pipeline / review |
| [`references_deep.bib`](references_deep.bib) | Deep-search unified bibliography |

## Contracts

- Do not hand-edit metrics that belong in `manuscript_variables.json`.
- Citations use Pandoc citekeys present in the union of `manuscript/*.bib`.

## See also

- [`SYNTAX.md`](SYNTAX.md) — Pandoc citation/cross-reference syntax for this manuscript.
- [`../../../docs/guides/manuscript-semantics.md`](../../../docs/guides/manuscript-semantics.md) — Repository-wide canonical manuscript semantics.
- [`../src/manuscript_variables.py`](../src/manuscript_variables.py)
- [`../scripts/z_generate_manuscript_variables.py`](../scripts/z_generate_manuscript_variables.py)
- [`README.md`](README.md)

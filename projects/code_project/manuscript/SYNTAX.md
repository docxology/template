# Manuscript Syntax Reference

Formatting and syntax conventions for manuscript Markdown files in the `code_project` exemplar.

## Citation Syntax (Pandoc)

```markdown
<!-- Single citation -->
[@knuth1997]

<!-- Multiple citations -->
[@knuth1997; @cormen2009]

<!-- Citation with locator -->
[@knuth1997, pp. 42-45]

<!-- Narrative citation -->
@knuth1997 showed that...
```

All citation keys must exist in `references.bib`. The pipeline will flag undefined keys as errors.

## Equation Environments

```markdown
<!-- Numbered equation with label -->
\begin{equation}
\label{eq:gradient}
\nabla f(x) = Ax - b
\end{equation}

<!-- Reference in text -->
As shown in Equation \ref{eq:gradient}, the gradient...
```

Pandoc-crossref resolves `{#eq:label}` and `@eq:label` during rendering. Do **not** use raw `\label{}` / `\ref{}` — the Markdown filter handles this.

## Figure References

```markdown
<!-- Figure with label -->
![Convergence plot showing objective value vs iteration](figures/convergence_plot.png){#fig:convergence width=80%}

<!-- Reference in text -->
@fig:convergence demonstrates...
```

- Images must exist in `output/figures/` at render time
- Use `width=` or `height=` to control sizing (prevents float-too-large warnings)
- Captions should be descriptive (they appear in the PDF)

## Table References

```markdown
<!-- Table with label -->
| Step Size | Iterations | Converged |
|-----------|-----------|-----------|
| 0.01      | 412       | Yes       |

: Performance comparison across step sizes {#tbl:performance}

<!-- Reference in text -->
@tbl:performance shows...
```

## Preamble Injection

`preamble.md` contains raw LaTeX injected before the document body:

```markdown
---
header-includes:
  - \usepackage{amsmath}
  - \tolerance=800
  - \hfuzz=2pt
---
```

- Preamble is parsed by `infrastructure.rendering.latex_utils.py`
- Changes to tolerance/hfuzz affect line-breaking globally
- Do **not** duplicate package imports already in the infrastructure renderer

## BibTeX Entry Format

```bibtex
@article{knuth1997,
  author  = {Donald E. Knuth},
  title   = {The Art of Computer Programming},
  journal = {Addison-Wesley},
  year    = {1997},
  volume  = {1}
}
```

- Keys must be lowercase alphanumeric with optional underscores
- Author names use `{Last, First}` or `{First Last}` format
- All entries must have at minimum: `author`, `title`, `year`

## Section Numbering

```text
00_abstract.md    → Section 0 (unnumbered in PDF)
01_introduction.md → Section 1
02_methodology.md  → Section 2
03_results.md      → Section 3
04_conclusion.md   → Section 4
```

Files are assembled in lexicographic order by `infrastructure.rendering.pdf_renderer.py`. The `00_` prefix ensures the abstract renders first.

## Prose Conventions

- No "In summary" or "In conclusion" at section ends (RASP standard)
- Use active voice for methodology descriptions
- Use explicit file paths when referencing code: `src/optimizer.py`, not "the optimizer module"
- Keep paragraphs focused — one idea per paragraph

## See Also

- [AGENTS.md](AGENTS.md) — RASP protocol and AI agent constraints
- [rendering_pipeline.md](../docs/rendering_pipeline.md) — Full rendering flow
- [preamble.md](preamble.md) — Active LaTeX preamble

# Usage Documentation

## Overview

Technical guide for `docs/usage/` — content authoring, formatting, visualization, and manuscript patterns for the Research Project Template.

## Files

| File | Purpose |
|------|---------|
| `examples.md` | Project renaming and customization examples |
| `examples-showcase.md` | Real-world usage showcase |
| `template-description.md` | Template feature overview |
| `markdown-template-guide.md` | Markdown authoring and cross-referencing |
| `output-formats.md` | Five-format output reference: PDF/HTML/Slides/DOCX/EPUB + `render.formats` config |
| `manuscript-numbering-system.md` | Section numbering conventions |
| `style-guide.md` | Equations, figures, captions, and tables |
| `image-management.md` | Image insertion, captioning, and cross-referencing |
| `visualization-guide.md` | Publication-quality figure generation |

## Key Conventions

- **Manuscript examples**: default to [`projects/templates/template_code_project/manuscript/`](../../projects/templates/template_code_project/manuscript/); active `projects/` names → [_generated/active_projects.md](../_generated/active_projects.md).
- Figures use Pandoc image syntax `![caption](path){#fig:name}` with cross-references `[@fig:name]` — never a raw LaTeX `\begin{figure}`/`\ref{fig:name}` pair (see [Manuscript Semantics](../guides/manuscript-semantics.md)).
- Equations use `$$ … $$ {#eq:name}` (or `\begin{equation}\label{eq:name}…\end{equation}`) with cross-references `[@eq:name]` — never raw `\eqref{eq:name}`.
- All images must exist in `output/figures/` before manuscript build
- Use descriptive link text (no bare URLs)
- Follow the style guide for consistent formatting

## See Also

- [README.md](README.md) — Quick navigation
- [Visualization Guide](visualization-guide.md) — Figure generation details
- [Modules Guide](../modules/modules-guide.md) — Analysis module usage

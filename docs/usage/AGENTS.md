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
| `manuscript-numbering-system.md` | Section numbering conventions |
| `style-guide.md` | Equations, figures, captions, and tables |
| `image-management.md` | Image insertion, captioning, and cross-referencing |
| `visualization-guide.md` | Publication-quality figure generation |

## Key Conventions

- Figures use LaTeX `\begin{figure}` environments with `\label{fig:name}` and `\ref{fig:name}`
- Equations use `\begin{equation}\label{eq:name}` and `\eqref{eq:name}`
- All images must exist in `output/figures/` before manuscript build
- Use descriptive link text (no bare URLs)
- Follow the style guide for consistent formatting

## See Also

- [README.md](README.md) — Quick navigation
- [Visualization Guide](visualization-guide.md) — Figure generation details
- [Modules Guide](../modules/modules-guide.md) — Analysis module usage

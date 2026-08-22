# LaTeX Preamble

The fenced `latex` block below is extracted by the renderer
(`infrastructure/rendering/_pdf_latex_helpers.py::extract_preamble`) and injected
before `\begin{document}`. Keep it to package loads and macro definitions only.

**Typography is config-driven.** Page margins live in
`manuscript/config.yaml` → `metadata.geometry` (forwarded to pandoc as `-V geometry:`),
so do **not** declare `\geometry{...}` here — a second declaration would clash with the
pandoc-emitted `geometry` package. Global font size is set here via the class-agnostic
`fontsize` package because the default `article` class only accepts 10/11/12 pt natively.

```latex
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
% Dense 9pt body via class-agnostic global rescaling (works on the default
% `article` class). Signature: \changefontsize[<baselineskip>]{<size>} — the
% baselineskip is the OPTIONAL bracketed arg; a second brace would print as text.
\usepackage{fontsize}
\changefontsize[11pt]{9pt}
```

# LaTeX Preamble

This file contains LaTeX packages and commands that are automatically
injected into the document compilation by
`infrastructure/rendering/_pdf_latex_helpers.py`. Forkers extending the
manuscript with mathematical notation, algorithm pseudocode, or
multi-page tables will likely need everything below.

```latex
% Core mathematics (FKGL / FRE references and any math the manuscript carries)
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}

% Document layout
\usepackage{geometry}
\usepackage{float}
\usepackage{graphicx}
\geometry{margin=1in}

% Tables (longtable is required for any review-report table that crosses pages)
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}

% Typography
\usepackage{microtype}
\usepackage{xcolor}

% Cross-references and citations
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    citecolor=teal,
    urlcolor=teal
}
\usepackage[capitalise,noabbrev]{cleveref}

% Optional: algorithm pseudocode (uncomment if any section embeds \begin{algorithm})
% \usepackage[ruled,vlined,linesnumbered]{algorithm2e}

% Optional: code listings (uncomment if any section embeds non-fenced code blocks)
% \usepackage{listings}
```

> **Differences from `template_code_project/manuscript/preamble.md`.**
> The sibling exemplar additionally pins JuliaMono for full Unicode math
> glyph coverage (used by gradient-descent equations) and sets
> `latinmodern-math.otf` via `unicode-math`. The prose exemplar's
> default math content is light enough that the Pandoc/Latin Modern
> defaults suffice. If you fork from prose and add heavy math, port the
> font block from the code sibling.

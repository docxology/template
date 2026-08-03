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
\geometry{margin=0.25in}

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
% \IfFileExists{algorithm2e.sty}{\usepackage[ruled,vlined,linesnumbered]{algorithm2e}}{}

% Optional: code listings (uncomment if any section embeds non-fenced code blocks)
% \usepackage{listings}
```

> **Heavy math fork.** If you add gradient-descent equations or other Unicode-heavy
> notation, port a JuliaMono / `unicode-math` font block into this preamble.
> See [`manuscript/AGENTS.md`](AGENTS.md) for operator guidance.

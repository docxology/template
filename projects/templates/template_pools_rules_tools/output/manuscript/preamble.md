<!--
manuscript/preamble.md — LaTeX preamble for the Pools, Rules, and Tools manuscript.

`infrastructure/rendering/_pdf_latex_helpers.py::extract_preamble` only
recovers content between a closed ```latex ... ``` fence. An unfenced file
falls back to a conservative single-line whitelist that silently drops any
multi-line directive (geometry blocks, hypersetup, tcolorbox definitions,
etc.) — keep this fence intact.

Page margins are sourced from `manuscript/config.yaml`'s
`metadata.geometry` key (single source of truth) — do not add a
`\geometry{}` call here, or the two declarations conflict.
-->

```latex
% ============================================================
% Core packages
% ============================================================
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{microtype}
\usepackage{cleveref}
\usepackage{float}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{setspace}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{tcolorbox}
\usepackage{mdframed}
\usepackage{fontsize}

% ============================================================
% Base font size (denser layout) — fontsize package is class-agnostic,
% unlike pandoc's own `fontsize` metadata variable which only spans
% 10/11/12pt for the article class. Bracketed arg is baselineskip
% (OPTIONAL, first); the required body-size arg is second. Do not swap
% the order — `\changefontsize{9pt}{11pt}` sets the wrong size and leaks
% "11pt" as a literal token on the page.
% ============================================================
\changefontsize[10pt]{8pt}

% ============================================================
% Typography
% ============================================================
\setstretch{1.08}
\captionsetup{font=small, labelfont=bf, skip=6pt}

% ============================================================
% Header and footer
% ============================================================
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textit{Pools, Rules, and Tools}}
\fancyhead[R]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% ============================================================
% Code listing style
% ============================================================
\lstset{
  basicstyle=\ttfamily\small,
  keywordstyle=\color{blue}\bfseries,
  commentstyle=\color{gray}\itshape,
  stringstyle=\color{teal},
  numberstyle=\tiny\color{gray},
  breaklines=true,
  frame=single,
  captionpos=b,
  language=Python,
  numbers=left,
  stepnumber=1,
  xleftmargin=2em,
  xrightmargin=0.5em,
  aboveskip=0.8em,
  belowskip=0.8em,
}

% ============================================================
% Semantic macros for this manuscript
% ============================================================
\newcommand{\module}[1]{\texttt{#1}}
\newcommand{\fondname}[1]{\texttt{#1}}
\newcommand{\ruleset}[1]{\texttt{#1}}
\newcommand{\toolname}[1]{\texttt{#1}}
\newcommand{\repopath}[1]{\texttt{#1}}
\newcommand{\token}[1]{\texttt{\{\{#1\}\}}}
\newcommand{\jsonkey}[1]{\texttt{"#1"}}
\newcommand{\exitcode}[1]{\texttt{#1}}

% ============================================================
% Coloured note boxes
% ============================================================
\tcbuselibrary{skins}
\newtcolorbox{noteBox}[1][]{
  colback=blue!5!white,
  colframe=blue!60!black,
  fonttitle=\bfseries,
  title=Note,
  #1
}
\newtcolorbox{warningBox}[1][]{
  colback=orange!10!white,
  colframe=orange!80!black,
  fonttitle=\bfseries,
  title=Warning,
  #1
}

% ============================================================
% Cross-reference setup
% ============================================================
\hypersetup{
  colorlinks=true,
  linkcolor=red!70!black,
  citecolor=red!70!black,
  urlcolor=red!70!black,
  pdftitle={Pools, Rules, and Tools: A Template-Integrated Resource Architecture},
  pdfauthor={Daniel Ari Friedman},
  pdfkeywords={research software, fonds, rules, tools, monorepo},
}

% cleveref configuration — use \cref{} for all cross-references
\crefname{figure}{Figure}{Figures}
\crefname{table}{Table}{Tables}
\crefname{section}{Section}{Sections}
\crefname{listing}{Listing}{Listings}
```

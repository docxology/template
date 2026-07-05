% manuscript/preamble.md
% LaTeX preamble configuration for the Pools, Rules, and Tools manuscript.
%
% This file is passed to the rendering pipeline before the main manuscript
% sections. It configures packages, typography, cross-reference macros, and
% custom environments.

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
\usepackage{geometry}
\usepackage{setspace}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{tcolorbox}
\usepackage{mdframed}

% ============================================================
% Page geometry
% ============================================================
\geometry{
  a4paper,
  margin=2.5cm,
  top=3cm,
  bottom=3cm,
}

% ============================================================
% Typography
% ============================================================
\setstretch{1.15}
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
  linkcolor=blue!70!black,
  citecolor=teal!80!black,
  urlcolor=blue!80!black,
  pdftitle={Pools, Rules, and Tools: A Template-Integrated Resource Architecture},
  pdfauthor={Research Template Author},
  pdfkeywords={research software, fonds, rules, tools, monorepo},
}

% cleveref configuration — use \cref{} for all cross-references
\crefname{figure}{Figure}{Figures}
\crefname{table}{Table}{Tables}
\crefname{section}{Section}{Sections}
\crefname{listing}{Listing}{Listings}

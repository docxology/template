# LaTeX Preamble

This file contains LaTeX packages and commands that are automatically included in the document compilation.

```latex
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{amsthm}
\usepackage{geometry}
\usepackage{float}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{hyperref}
\usepackage{natbib}
\usepackage{algorithm}
\usepackage{algorithmic}
\usepackage{tikz}
\usepackage{fancyhdr}

% Custom theorem environments
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{corollary}{Corollary}
\newtheorem{proposition}{Proposition}

% Custom notation shortcuts for Active Inference
\newcommand{\EFE}{\mathcal{F}}
\newcommand{\FEP}{\text{FEP}}
\newcommand{\AI}{\text{AI}}

% Matrix notation
\newcommand{\matA}{A}
\newcommand{\matB}{B}
\newcommand{\matC}{C}
\newcommand{\matD}{D}

% Quadrant notation
\newcommand{\Qone}{Q_{1}}
\newcommand{\Qtwo}{Q_{2}}
\newcommand{\Qthree}{Q_{3}}
\newcommand{\Qfour}{Q_{4}}

% Conditional probability notation
\newcommand{\given}{\mid}

% Ensure proper text justification (left-aligned, not center-aligned)
% Default LaTeX behavior is justified text, but we explicitly ensure no center alignment
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}
```

# LaTeX Preamble: Packages, Commands, and Notation

This file contains LaTeX packages and commands that are automatically included in the document compilation.

```latex
% Core mathematics
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{amsthm}

% Document layout
\usepackage[margin=1.8cm]{geometry}
\usepackage{float}
\usepackage{graphicx}
\usepackage[section]{placeins}  % Constrain floats to their section
\renewcommand{\floatpagefraction}{0.7}  % Require 70% fill for float-only pages
\renewcommand{\topfraction}{0.9}        % Allow large top floats

% Tables
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{multirow}

% Code listings
\usepackage{listings}

% Typography and formatting
\usepackage{microtype}
\usepackage{xcolor}

% Cross-references and citations (hyperref loaded by other packages with [unicode]; set options only)
\hypersetup{colorlinks=true,linkcolor=red,citecolor=red,urlcolor=red}
\usepackage[capitalise,noabbrev]{cleveref}
% NOTE: natbib is auto-injected by Pandoc via --natbib (which also writes
% \bibliographystyle{plainnat}). Do not re-declare \usepackage{natbib} here
% or LaTeX will error with "Option clash for package natbib".

% Figure caption formatting
\usepackage{caption}
\usepackage{subcaption}

% Algorithm typesetting
\usepackage[ruled,vlined]{algorithm2e}

% Custom commands for domain notation
\newcommand{\FEP}{\textsc{fep}}
\newcommand{\AIF}{\textsc{aif}}
\newcommand{\KL}{\mathrm{KL}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\F}{\mathcal{F}}

% NMF and topic modeling notation
\newcommand{\matW}{\mathbf{W}}  % NMF document-topic matrix
\newcommand{\matH}{\mathbf{H}}  % NMF topic-term matrix
\newcommand{\matV}{\mathbf{V}}  % NMF document-term matrix
\newcommand{\tfidf}{\text{TF-IDF}}
\newcommand{\cagr}{\text{CAGR}}
\newcommand{\score}{\operatorname{score}}
\newcommand{\corpusvar}[1]{\texttt{\{\{#1\}\}}}
\newcommand{\scoreH}[1]{\text{score}(H_{#1})}
\newcommand{\EBM}{\textsc{ebm}}
\newcommand{\VFE}{\mathcal{F}_{\text{VFE}}}
\newcommand{\RBM}{\textsc{rbm}}

% Assertion and evidence notation
\newcommand{\supports}{\mathrel{\text{supports}}}
\newcommand{\contradicts}{\mathrel{\text{contradicts}}}
\newcommand{\neutral}{\mathrel{\text{neutral}}}

% Domain taxonomy shorthands
\newcommand{\domA}{\text{A}}
\newcommand{\domB}{\text{B}}
\newcommand{\domC}{\text{C}}

% Evidence-score and growth metrics
\newcommand{\EFE}{\mathbf{G}}       % Evidence-score matrix
\newcommand{\doubling}{t_d}         % Doubling time
\newcommand{\meangrowth}{\bar{g}}   % Mean year-over-year growth rate

% Corpus and scoring notation
\newcommand{\Nstart}{N_{\text{start}}}  % Publication count in first year
\newcommand{\Nend}{N_{\text{end}}}      % Publication count in last year
\newcommand{\SH}{S(H)}                  % Supporting assertions for H
\newcommand{\CH}{C(H)}                  % Contradicting assertions for H
\newcommand{\AH}{A(H)}                  % All assertions for H

% Tool and project shorthands
\newcommand{\nanopub}{\textsc{np}}      % Nanopublication shorthand
\newcommand{\ollama}{\textsc{Ollama}}   % Ollama LLM server
\newcommand{\pymdp}{\textsc{pymdp}}     % pymdp library

% Network and graph operators
\DeclareMathOperator{\PageRank}{PageRank}  % PageRank operator
```

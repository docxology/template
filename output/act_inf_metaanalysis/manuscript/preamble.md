# LaTeX Preamble: Packages, Commands, and Notation

This file contains LaTeX packages and commands that are automatically included in the document compilation.

```latex
% Core mathematics
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{amsthm}

% Document layout
\usepackage[margin=2.2cm]{geometry}
\usepackage{float}
\usepackage{graphicx}

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

% Cross-references and citations
\usepackage[colorlinks=true,linkcolor=red,citecolor=red,urlcolor=red]{hyperref}
\usepackage[capitalise,noabbrev]{cleveref}
\usepackage{natbib}

% Figure caption formatting
\usepackage{caption}
\usepackage{subcaption}

% Algorithm typesetting
\usepackage[ruled,vlined]{algorithm2e}

% Custom commands for Active Inference notation
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

% Assertion and evidence notation
\newcommand{\supports}{\mathrel{\text{supports}}}
\newcommand{\contradicts}{\mathrel{\text{contradicts}}}
\newcommand{\neutral}{\mathrel{\text{neutral}}}

% Domain taxonomy shorthands
\newcommand{\domA}{\text{A}}
\newcommand{\domB}{\text{B}}
\newcommand{\domC}{\text{C}}

% Expected free energy and growth metrics
\newcommand{\EFE}{\mathbf{G}}       % Expected free energy matrix
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

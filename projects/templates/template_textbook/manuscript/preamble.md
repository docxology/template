# LaTeX Preamble

<!-- This block is injected into the LaTeX/PDF render before the body. It is
intentionally conservative and xelatex-safe: it does NOT use
`\DeclareUnicodeCharacter` (which breaks under xelatex). Page geometry,
fonts, and link colours are normally driven from `config.yaml` (layout /
typography); the packages below provide the features the chapter contract
relies on — booktabs/longtable tables, pandoc-crossref numbering, math,
code listings, and graphics. Adjust margins or line spacing here only if you
are not already setting them in config.yaml. -->

```latex
% --- Page geometry: conservative, print-friendly margins ---
\usepackage[letterpaper,margin=1in]{geometry}

% --- Tables (pandoc + pandoc-crossref emit booktabs/longtable) ---
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{multirow}

% --- Mathematics ---
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{mathtools}
\usepackage{amsthm}            % theorem/lemma/definition/proof environments
\usepackage{siunitx}          % \SI{}{} and \num{} dimensioned quantities
% Theorem-like environments (optional; chapters may also use portable block quotes).
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\theoremstyle{definition}
\newtheorem{definition}{Definition}

% --- Graphics / figures ---
\usepackage{graphicx}
\usepackage{float}

% --- Captions (figures, tables) ---
\usepackage{caption}
\captionsetup{font=small,labelfont=bf,labelsep=period}

% --- Code blocks (verbatim / listings fallback) ---
\usepackage{fancyvrb}
\usepackage{upquote}

% --- Hyperlinks + cross-references (pandoc-crossref resolves the labels) ---
\usepackage{hyperref}
\hypersetup{
  colorlinks=true,
  linkcolor={[HTML]{1A5276}},
  citecolor={[HTML]{1A5276}},
  urlcolor={[HTML]{1A5276}},
  breaklinks=true
}
\usepackage[capitalise,nameinlink]{cleveref}

% --- Running heads / footers ---
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\leftmark}
\fancyhead[R]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% --- Line spacing (modest; keep in sync with config.yaml layout.line_height) ---
\usepackage{setspace}
\setstretch{1.15}

% --- Avoid overfull lines from long URLs / inline code ---
\sloppy
```

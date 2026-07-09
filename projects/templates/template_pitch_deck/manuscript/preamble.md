# LaTeX Preamble

This file contains LaTeX packages and commands automatically injected into the
"about this template" manuscript's compilation (the deck artifacts themselves
are rendered by `infrastructure/rendering/{slide_deck,pptx_deck}.py`, not this
LaTeX path — see `manuscript/README.md`).

> **Infrastructure Note**: This file is parsed by `infrastructure/rendering/latex_utils.py` and combined with the configuration output by `infrastructure/rendering/pdf_renderer.py` before final Pandoc execution.

```latex
% Core mathematics
\usepackage{amsmath}
\usepackage{amssymb}

% Document layout
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{float}
\usepackage{graphicx}

% Tables
\usepackage{booktabs}
\usepackage{longtable}

% Typography and formatting
\usepackage{microtype}
\usepackage{xcolor}

% Cross-references and citations
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    allcolors=red
}
\usepackage[capitalise,noabbrev]{cleveref}
\usepackage{natbib}
```

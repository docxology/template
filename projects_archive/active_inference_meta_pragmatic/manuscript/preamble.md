# LaTeX Preamble Customizations

This file contains custom LaTeX preamble commands for the Active Inference manuscript.

## Custom Commands

```latex
% Custom theorem environments
\\newtheorem{theorem}{Theorem}
\\newtheorem{lemma}{Lemma}
\\newtheorem{corollary}{Corollary}
\\newtheorem{proposition}{Proposition}

% Custom notation shortcuts
\\newcommand{\\EFE}{\\mathcal{F}}
\\newcommand{\\FEP}{\\text{FEP}}
\\newcommand{\\AI}{\\text{AI}}

% Matrix notation
\\newcommand{\\matA}{A}
\\newcommand{\\matB}{B}
\\newcommand{\\matC}{C}
\\newcommand{\\matD}{D}

% Quadrant notation
\\newcommand{\\Qone}{Q_1}
\\newcommand{\\Qtwo}{Q_2}
\\newcommand{\\Qthree}{Q_3}
\\newcommand{\\Qfour}{Q_4}
```

## Package Requirements

The manuscript requires the following LaTeX packages:
- amsmath, amssymb (mathematical notation)
- graphicx (figures and images)
- hyperref (cross-references and links)
- geometry (page layout)
- fancyhdr (headers and footers)
- natbib (bibliography formatting)
- algorithm, algorithmic (algorithms)
- tikz (diagrams and illustrations)
# LaTeX Preamble

This file contains LaTeX preamble commands that will be inserted at the beginning of each generated document.

**BasicTeX Compatibility**: All packages listed below are available in BasicTeX 2025 after running:
```bash
sudo tlmgr install multirow cleveref doi newunicodechar
```
(Note: `bm` and `subcaption` are already included in BasicTeX as part of the `tools` and `caption` packages)

```latex
% ============================================================================
% REQUIRED PACKAGES - Essential for document rendering
% ============================================================================

% Mathematical typesetting (required for equations and symbols)
\usepackage{amsmath,amssymb}          % Mathematical symbols and environments
\usepackage{amsfonts}                 % Additional math fonts
\usepackage{amsthm}                   % Theorem environments

% Graphics and page layout (required for figures and formatting)
\usepackage{graphicx}                 % Include graphics (REQUIRED for figures)
\usepackage[margin=1in]{geometry}     % Page margins
\usepackage{float}                    % Better float placement

% Tables (required for table formatting)
\usepackage{booktabs}                 % Professional tables
\usepackage{longtable}                % Long tables spanning pages
\usepackage{array}                    % Advanced table formatting

% PDF features (required for cross-references and metadata)
\usepackage{url}                      % URL formatting
\usepackage{hyperref}                 % Hyperlinks and cross-references
\usepackage{natbib}                   % Bibliography support (REQUIRED)

% ============================================================================
% ENHANCED PACKAGES - Improve formatting and functionality
% ============================================================================

% Table enhancements (optional but recommended)
\usepackage{multirow}                 % Multi-row table cells
\usepackage{caption}                  % Enhanced caption formatting
\usepackage{subcaption}               % Sub-figures and sub-tables

% Math enhancements (optional but recommended)
\usepackage{bm}                       % Bold math symbols

% Reference enhancements (optional but recommended)
\usepackage{cleveref}                 % Intelligent cross-referencing
\usepackage{doi}                      % DOI links

% Configure figure numbering and captions
\renewcommand{\figurename}{Figure}
\captionsetup{
    justification=centering,
    font=small,
    labelfont=bf,
    labelsep=period
}

% Configure table numbering and captions
\renewcommand{\tablename}{Table}
\captionsetup[table]{
    justification=centering,
    font=small,
    labelfont=bf,
    labelsep=period
}

% Configure section numbering
\setcounter{secnumdepth}{3}
\renewcommand{\thesection}{\arabic{section}}
\renewcommand{\thesubsection}{\arabic{section}.\arabic{subsection}}
\renewcommand{\thesubsubsection}{\arabic{section}.\arabic{subsection}.\arabic{subsubsection}}

% Configure equation numbering
\numberwithin{equation}{section}

% Configure hyperref for proper linking
\hypersetup{
    colorlinks=true,
    linkcolor=red,
    citecolor=red,
    urlcolor=red,
    filecolor=red,
    pdfborder={0 0 0},
    bookmarks=true,
    bookmarksnumbered=true,
    bookmarkstype=toc,
    pdftitle={Tree Grafting Science and Practice},
    pdfauthor={InferAnt #016},
    pdfsubject={Horticultural Science and Computational Agriculture},
    pdfkeywords={tree grafting, compatibility prediction, rootstock selection, computational agriculture},
    pdfcreator={Research Project Template},
    pdfproducer={XeLaTeX}
}

% ============================================================================
% PACKAGE CONFIGURATION
% ============================================================================

% Configure cleveref for intelligent cross-references
\crefname{section}{Section}{Sections}
\crefname{subsection}{Subsection}{Subsections}
\crefname{subsubsection}{Subsubsection}{Subsubsections}
\crefname{equation}{Equation}{Equations}
\crefname{figure}{Figure}{Figures}
\crefname{table}{Table}{Tables}
\crefname{appendix}{Appendix}{Appendices}

% Configure fonts for Unicode support with fallbacks
\usepackage{newunicodechar}
\newunicodechar{⁴}{\textsuperscript{4}}
\newunicodechar{₄}{\textsubscript{4}}
\newunicodechar{²}{\textsuperscript{2}}
\newunicodechar{₀}{\textsubscript{0}}
\newunicodechar{₁}{\textsubscript{1}}
\newunicodechar{₂}{\textsubscript{2}}
\newunicodechar{₃}{\textsubscript{3}}

% ============================================================================
% FONTS AND TYPOGRAPHY
% ============================================================================

% Use standard fonts for better compatibility
\usepackage{lmodern}
\usepackage[T1]{fontenc}

% ============================================================================
% CODE BLOCK STYLING
% ============================================================================

% Enhanced code block styling for better contrast and readability
\usepackage{fancyvrb}
\usepackage{xcolor}
\usepackage{listings}

% Define custom colors for code blocks
\definecolor{codebg}{RGB}{248, 248, 248}      % Very light gray background
\definecolor{codeborder}{RGB}{200, 200, 200}  % Medium gray border
\definecolor{codefg}{RGB}{34, 34, 34}         % Dark gray text
\definecolor{commentcolor}{RGB}{102, 102, 102} % Comment color
\definecolor{keywordcolor}{RGB}{0, 0, 0}       % Keyword color
\definecolor{stringcolor}{RGB}{0, 102, 0}      % String color

% Configure Verbatim environment for inline code
\DefineVerbatimEnvironment{Verbatim}{Verbatim}{%
    fontsize=\small,
    frame=single,
    framerule=0.5pt,
    framesep=3pt,
    rulecolor=\color{codeborder},
    bgcolor=\color{codebg},
    fgcolor=\color{codefg}
}

% Configure code block styling
\DefineVerbatimEnvironment{Highlighting}{Verbatim}{%
    fontsize=\footnotesize,
    frame=single,
    framerule=0.5pt,
    framesep=5pt,
    rulecolor=\color{codeborder},
    bgcolor=\color{codebg},
    fgcolor=\color{codefg}
}

% Style inline code with \texttt
\renewcommand{\texttt}[1]{%
    \colorbox{codebg}{\color{codefg}\ttfamily #1}%
}

% Configure listings package for code blocks
\lstset{
    backgroundcolor=\color{codebg},
    basicstyle=\footnotesize\ttfamily\color{codefg},
    breakatwhitespace=false,
    breaklines=true,
    captionpos=b,
    commentstyle=\color{commentcolor},
    deletekeywords={...},
    escapeinside={\%*}{*)},
    extendedchars=true,
    frame=single,
    framerule=0.5pt,
    framesep=5pt,
    keepspaces=true,
    keywordstyle=\color{keywordcolor}\bfseries,
    language=Python,
    morekeywords={*,...},
    numbers=left,
    numbersep=5pt,
    numberstyle=\tiny\color{codefg},
    rulecolor=\color{codeborder},
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    stepnumber=1,
    stringstyle=\color{stringcolor},
    tabsize=4,
    title=\lstname
}

% Override any Pandoc default lstset configurations
\AtBeginDocument{
    \lstset{
        backgroundcolor=\color{codebg},
        basicstyle=\footnotesize\ttfamily\color{codefg},
        frame=single,
        framerule=0.5pt,
        framesep=5pt,
        rulecolor=\color{codeborder},
        numbers=left,
        numbersep=5pt,
        numberstyle=\tiny\color{codefg}
    }
}

% Configure bibliography
% Note: Using plainnat with natbib package for proper citation processing
% The bibliography style and commands (\bibliographystyle and \bibliography) are in 99_references.md

% Simple page break support for document structure
% Note: Page breaks are handled in the markdown generation, not here

% ============================================================================
% DOCUMENT FORMATTING
% ============================================================================

% Ensure proper spacing and formatting
\frenchspacing  % Single space after periods
\linespread{1.2}  % Slightly increased line spacing for readability

% ============================================================================
% NOTES FOR BASICTEX USERS
% ============================================================================
% If you encounter "File *.sty not found" errors, install missing packages:
%   sudo tlmgr update --self
%   sudo tlmgr install multirow cleveref doi newunicodechar
% 
% Packages already in BasicTeX (no installation needed):
%   - bm (part of tools package)
%   - subcaption (part of caption package)
%   - amsmath, graphicx, hyperref, natbib (core packages)
```

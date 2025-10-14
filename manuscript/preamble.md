# LaTeX Preamble

This file contains LaTeX preamble commands that will be inserted at the beginning of each generated document.

```latex
% Essential packages for academic documents
\usepackage{amsmath,amssymb}          % Mathematical symbols and environments
\usepackage{amsfonts}                 % Additional math fonts
\usepackage{amsthm}                   % Theorem environments
\usepackage{graphicx}                 % Include graphics
\usepackage{float}                    % Better float placement
\usepackage{booktabs}                 % Professional tables
\usepackage{longtable}                % Long tables spanning pages
\usepackage{array}                    % Advanced table formatting
\usepackage{multirow}                 % Multi-row table cells
\usepackage{caption}                  % Enhanced caption formatting
\usepackage{subcaption}               % Sub-figures and sub-tables
\usepackage{bm}                       % Bold math symbols
\usepackage{url}                      % URL formatting
\usepackage{hyperref}                 % Hyperlinks and cross-references
\usepackage{cleveref}                 % Intelligent cross-referencing
\usepackage[capitalise]{cleveref}     % Capitalize cross-reference labels
\usepackage{natbib}                   % Bibliography support
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
    linkcolor=blue,
    citecolor=blue,
    urlcolor=blue,
    filecolor=blue,
    pdfborder={0 0 0},
    bookmarks=true,
    bookmarksnumbered=true,
    bookmarkstype=toc,
    pdftitle={Research Project Template},
    pdfauthor={Template Author},
    pdfsubject={Academic Research},
    pdfkeywords={research, template, academic, LaTeX},
    pdfcreator={render_pdf.sh},
    pdfproducer={XeLaTeX}
}

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

% Use standard fonts for better compatibility
\usepackage{lmodern}
\usepackage[T1]{fontenc}

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
\bibliographystyle{unsrt}  % Unsorted bibliography style
\bibliography{references}  % Bibliography file (if it exists)

% Simple page break support for document structure
% Note: Page breaks are handled in the markdown generation, not here

% Ensure proper spacing and formatting
\frenchspacing  % Single space after periods
\linespread{1.2}  % Slightly increased line spacing for readability

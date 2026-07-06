% Page margins are config-driven: manuscript/config.yaml -> metadata.geometry
% (forwarded to pandoc as `-V geometry:`). Do not declare \geometry{...} here —
% a second declaration would clash with the pandoc-emitted geometry package.
\usepackage{fancyhdr}
% hyperref options forwarded via PassOptionsToPackage to avoid an option clash
% with the \PassOptionsToPackage{unicode}{hyperref} that pandoc injects at the
% top of the generated .tex file.
\PassOptionsToPackage{colorlinks=true, linkcolor=teal, urlcolor=teal, citecolor=teal}{hyperref}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{xcolor}
% Dense 9pt body via class-agnostic global rescaling (works on the default
% `article` class). Signature: \changefontsize[<baselineskip>]{<size>} — the
% baselineskip is the OPTIONAL bracketed arg; a second brace would print as text.
\usepackage{fontsize}
\changefontsize[11pt]{9pt}

\pagestyle{fancy}
\fancyhf{}
\rhead{template\_autopoiesis}
\lhead{Autopoietic Project Generation}
\cfoot{\thepage}

\definecolor{brand-teal}{HTML}{0d9488}
\definecolor{brand-slate}{HTML}{1e293b}

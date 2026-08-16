```latex
\usepackage{amsthm}
\usepackage{graphicx}
\usepackage{listings}
\newtheorem{theorem}{Theorem}
\newtheorem{remark}{Remark}
\newtheorem{example}{Example}
\makeatletter
\@ifpackageloaded{geometry}
  {\geometry{margin=1.0in}}
  {\usepackage[margin=1.0in]{geometry}}
\@ifpackageloaded{hyperref}
  {\hypersetup{colorlinks=true, linkcolor=red, filecolor=magenta, urlcolor=red, citecolor=red}}
  {\usepackage{hyperref}\hypersetup{colorlinks=true, linkcolor=red, filecolor=magenta, urlcolor=red, citecolor=red}}
\makeatother

% Force newpage before References/Bibliography
\let\oldbibliography\bibliography
\renewcommand{\bibliography}[1]{\newpage\oldbibliography{#1}}
```

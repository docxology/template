```latex
\makeatletter
\@ifpackageloaded{geometry}
  {\geometry{margin=1.0in}}
  {\usepackage[margin=1.0in]{geometry}}
\@ifpackageloaded{hyperref}
  {\hypersetup{colorlinks=true, linkcolor=blue, filecolor=magenta, urlcolor=blue, citecolor=blue}}
  {\usepackage{hyperref}\hypersetup{colorlinks=true, linkcolor=blue, filecolor=magenta, urlcolor=blue, citecolor=blue}}
\makeatother

\let\oldbibliography\bibliography
\renewcommand{\bibliography}[1]{\newpage\oldbibliography{#1}}
```

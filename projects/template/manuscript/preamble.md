```latex
\makeatletter
\@ifpackageloaded{geometry}
  {\geometry{margin=1in}}
  {\usepackage[margin=1in]{geometry}}
\@ifpackageloaded{hyperref}
  {\hypersetup{colorlinks=true, linkcolor=red, filecolor=magenta, urlcolor=red, citecolor=red}}
  {\usepackage{hyperref}\hypersetup{colorlinks=true, linkcolor=red, filecolor=magenta, urlcolor=red, citecolor=red}}
\makeatother
```

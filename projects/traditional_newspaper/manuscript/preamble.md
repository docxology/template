```latex
\makeatletter
\@ifpackageloaded{geometry}
  {\geometry{paperwidth=11in,paperheight=17in,margin=0.45in}}
  {\usepackage[paperwidth=11in,paperheight=17in,margin=0.45in]{geometry}}
\@ifpackageloaded{hyperref}
  {\hypersetup{colorlinks=true, linkcolor=black, filecolor=black, urlcolor=black, citecolor=black}}
  {\usepackage{hyperref}\hypersetup{colorlinks=true, linkcolor=black, filecolor=black, urlcolor=black, citecolor=black}}
\usepackage{graphicx}
\usepackage{multicol}
\setlength{\columnsep}{0.22in}
\makeatother
```

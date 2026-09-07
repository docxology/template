"""Beamer-safe handling for Pandoc cross-referenced code listings."""

from __future__ import annotations

_OVERRIDE_MARKER = "% template: Beamer-safe codelisting override"


def _override(font_command: str) -> str:
    return rf"""
{_OVERRIDE_MARKER}
% pandoc-crossref declares codelisting as a float in the generated preamble.
% Floats cannot appear inside Beamer frames, so retain its counter while
% replacing only the begin/end environment after all Pandoc preamble code.
\makeatletter
\@ifundefined{{c@codelisting}}{{\newcounter{{codelisting}}}}{{}}
\newcommand{{\templatecodelistingbegin}}{{%
  \refstepcounter{{codelisting}}%
  \par\medskip
  \begin{{beamercolorbox}}[wd=\linewidth,sep=0.5em]{{block body}}%
  {font_command}
  \renewcommand{{\caption}}[2][]{{%
    \par\textbf{{Listing~\thecodelisting: }}##2\par\smallskip%
  }}%
}}
\newcommand{{\templatecodelistingend}}{{%
  \end{{beamercolorbox}}%
  \par\medskip
}}
\@ifundefined{{codelisting}}{{%
  \newenvironment{{codelisting}}{{\templatecodelistingbegin}}{{\templatecodelistingend}}%
}}{{%
  \renewenvironment{{codelisting}}{{\templatecodelistingbegin}}{{\templatecodelistingend}}%
}}
\makeatother
"""


def make_codelisting_slide_safe(
    tex_content: str,
    *,
    accessible_body_font_pt: int | None = None,
) -> tuple[str, int]:
    """Replace pandoc-crossref's generated listing float for Beamer.

    ``pandoc-crossref`` emits a regular LaTeX float named ``codelisting``.
    Beamer frames reject floats with ``Not in outer par mode``. The filter's
    declaration is generated after Pandoc ``-H`` snippets, so a header cannot
    safely override it. Inject the non-floating environment immediately
    before ``\\begin{document}``, after every generated preamble declaration.

    The override preserves the crossref-owned counter and labels, accepts both
    long and optional short captions, and is idempotent.
    """
    if r"\begin{codelisting}" not in tex_content:
        return tex_content, 0
    if _OVERRIDE_MARKER in tex_content:
        return tex_content, 0
    document_marker = r"\begin{document}"
    if document_marker not in tex_content:
        return tex_content, 0
    font_command = (
        r"\footnotesize"
        if accessible_body_font_pt is None
        else rf"\fontsize{{{accessible_body_font_pt}pt}}{{{accessible_body_font_pt + 4}pt}}\selectfont"
    )
    return tex_content.replace(document_marker, f"{_override(font_command)}\n{document_marker}", 1), 1


__all__ = ["make_codelisting_slide_safe"]

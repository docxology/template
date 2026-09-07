"""Web-only markdown preprocess: raw LaTeX spans, citations, theorem blocks."""

from __future__ import annotations

import re

import infrastructure.rendering._web_postprocess as web_postprocess

_RAW_LATEX_INLINE_RE = re.compile(r"`([^`]+)`\{=latex\}")
_CITE_RE = re.compile(
    r"\\cite(?:p|t|alp|alt|author|year|yearpar)?"
    r"(?:\[[^\]]*\]\s*){0,2}\{([^{}]+)\}"
)
_HYPERREF_RE = re.compile(r"\\hyperref\[[^\]]+\]\{([^{}]+)\}")
_HREF_RE = re.compile(r"\\href\{[^{}]+\}\{([^{}]+)\}")
_LABEL_RE = re.compile(r"\\(?:phantomsection\s*)?\\?label\{[^{}]+\}")
_REF_RE = re.compile(r"\\(?:eqref|ref|autoref)\{([^{}]+)\}")
# Pandoc-style citations ``[@key]`` / ``[@key1; @key2]`` / ``[-@key]``.
# The PDF path resolves these via ``--citeproc``; the HTML writer leaves them
# raw, so this web-only pass renders them as readable ``[key1; key2]`` text
# (mirroring the ``\citep{...}`` handling) instead of emitting literal
# ``[@key]`` markdown into the rendered page.
_PANDOC_CITATION_RE = re.compile(r"\[(?P<body>[^\]]*?@[A-Za-z0-9_][^\]]*?)\]")
_PANDOC_CITEKEY_RE = re.compile(r"-?@([A-Za-z0-9_][A-Za-z0-9_:.#$%&+?<>~/-]*)")
#: Reference prefixes a filter resolves later, so the citation pre-pass must
#: not strip their ``@``. The first four belong to pandoc-crossref; the rest
#: are the formalism kinds ``formalism.lua`` numbers. Stripping a formalism
#: ``@`` left the per-section pages showing raw ``[def:registry]`` with the
#: block above it unlabelled.
_PANDOC_CROSSREF_PREFIXES = (
    "fig:",
    "tbl:",
    "sec:",
    "eq:",
    "def:",
    "prop:",
    "thm:",
    "lem:",
    "cor:",
    "rem:",
    "ax:",
)
# Raw-LaTeX theorem-like environments. Pandoc's HTML writer silently DROPS
# these blocks (the ``\newtheorem`` definitions live in the LaTeX-only
# preamble), so a manuscript's Theorems/Definitions vanish from the web page.
# WebRenderer rewrites them (web-only) into numbered ``.theorem-box`` Divs.
# The display names share one running counter, mirroring the conventional
# ``\newtheorem{lemma}[theorem]{Lemma}`` shared-counter linkage so the web
# numbers match the PDF's.
_THEOREM_ENVS = {
    "theorem": "Theorem",
    "lemma": "Lemma",
    "proposition": "Proposition",
    "corollary": "Corollary",
    "definition": "Definition",
}
_THEOREM_BLOCK_RE = re.compile(
    r"\\begin\{(theorem|lemma|proposition|corollary|definition)\}"
    r"(?:\[([^\]]*)\])?"
    r"(?:[ \t]*\\label\{([^}]*)\})?[ \t]*\n(.*?)\n\\end\{\1\}",
    re.DOTALL,
)
# Theorem-body-only cleanups (see _clean_theorem_body). Pandoc's markdown
# reader treats ``\texttt{...}`` as raw inline LaTeX (dropped by the HTML
# writer) and does not enable ``tex_math_single_backslash``, so ``\(...\)``
# math degrades to bare parens. Applied ONLY inside theorem bodies.
_THEOREM_TEXTTT_RE = re.compile(r"\\texttt\{([^{}]*)\}")
_THEOREM_INLINE_MATH_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
_THEOREM_DISPLAY_MATH_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)


def html_safe_markdown(
    content: str,
    *,
    render_citations: bool = True,
    preserve_crossrefs: bool = True,
) -> str:
    """Convert PDF-only raw-LaTeX inline spans into readable HTML text.

    The canonical manuscript uses Pandoc raw-LaTeX spans such as
    ``\\citep{...}`` and ``\\hyperref[label]{visible text}`` because those
    are the right primitives for the PDF build.  Pandoc's HTML writer drops
    raw LaTeX, which can turn prose like "NumPy \\citep{...}, SciPy
    \\citep{...}" into "NumPy , SciPy".  This web-only pass preserves the
    visible text while leaving the source manuscript and PDF path unchanged.
    """

    def _citation_text(keys_csv: str) -> str:
        keys = [key.strip() for key in keys_csv.split(",") if key.strip()]
        return "[" + "; ".join(keys) + "]" if keys else ""

    def _visible_ref(label: str) -> str:
        return label.replace("_", " ")

    def _clean_latex_text(text: str) -> str:
        text = text.replace(r"\S", "§")
        text = text.replace(r"\%", "%")
        text = text.replace(r"\&", "&")
        text = text.replace(r"\_", "_")
        text = text.replace(r"~", " ")
        text = text.replace(r"\ ", " ")
        return re.sub(r"\s+", " ", text).strip()

    def _replace_raw_span(match: re.Match[str]) -> str:
        latex = match.group(1).strip()
        latex = _HYPERREF_RE.sub(
            lambda m: _clean_latex_text(m.group(1)),
            latex,
        )
        latex = _HREF_RE.sub(
            lambda m: _clean_latex_text(m.group(1)),
            latex,
        )
        latex = _CITE_RE.sub(
            lambda m: _citation_text(m.group(1)),
            latex,
        )
        latex = _LABEL_RE.sub("", latex)
        latex = latex.replace(r"\phantomsection", "")
        latex = _REF_RE.sub(lambda m: _visible_ref(m.group(1)), latex)
        return _clean_latex_text(latex)

    # Rewrite raw-LaTeX theorem blocks into numbered Divs BEFORE the inline
    # raw-span pass strips them; the Div body then flows through citation /
    # ref handling like any other prose.
    content = html_theorem_blocks(content)
    if render_citations:
        content = render_pandoc_citations(content, preserve_crossrefs=preserve_crossrefs)
    return web_postprocess.normalize_figure_paths(_RAW_LATEX_INLINE_RE.sub(_replace_raw_span, content))


def html_theorem_blocks(content: str) -> str:
    """Rewrite raw-LaTeX theorem-like environments into numbered ``.theorem-box`` Divs.

    Web-only. Each ``\\begin{theorem}[optional name]...\\end{theorem}`` block (for
    theorem / lemma / proposition / corollary / definition) becomes a Pandoc
    fenced Div ``::: {.theorem-box .<env>}`` led by a bold ``**Theorem N**``
    label (the optional name follows, with its math left outside the bold so it
    renders). A same-line ``\\label{...}`` after the name (the standard amsthm
    idiom) is consumed and becomes the Div's anchor id. The environments share
    one running counter so the web numbers match the PDF's shared-counter
    convention. The PDF path never sees this — it consumes the original
    ``\\begin{theorem}`` against the LaTeX preamble.

    Theorem names and bodies are additionally cleaned via
    ``clean_theorem_body`` so
    content that pandoc's HTML path would otherwise drop or degrade survives:
    ``\\texttt{X}`` becomes a markdown code span (``\\_`` unescaped) and
    ``\\(...\\)`` / ``\\[...\\]`` math delimiters become ``$...$`` /
    ``$$...$$`` so the HTML+MathJax path renders them. ``\\label{eq:...}``
    lines and ``\\ref{...}`` are left to the existing downstream passes.

    Known limitation (web-only, cosmetic): other raw-LaTeX macros inside
    theorem bodies (e.g. ``\\emph{...}``, custom preamble macros) still pass
    through pandoc's raw-inline-LaTeX drop; the PDF surface is unaffected.
    """
    counter = {"n": 0}

    def _replace(match: re.Match[str]) -> str:
        env, name, anchor, body = (
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4),
        )
        counter["n"] += 1
        label = f"**{_THEOREM_ENVS[env]} {counter['n']}**"
        if name and name.strip():
            clean_name = clean_theorem_body(name.strip())
            label += f" ({clean_name})"
        attrs = f".theorem-box .{env}"
        if anchor and anchor.strip():
            attrs += f" #{anchor.strip()}"
        body = clean_theorem_body(body.strip())
        return f"\n\n::: {{{attrs}}}\n{label}. {body}\n:::\n\n"

    return _THEOREM_BLOCK_RE.sub(_replace, content)


def clean_theorem_body(body: str) -> str:
    """Make a theorem-Div body survive pandoc's HTML path (web-only).

    Conservative, theorem-body-scoped rewrites only:

    - ``\\texttt{X}`` → markdown code span `` `X` `` with ``\\_`` unescaped,
      so filenames like ``expected_free_energy.py`` surface instead of
      vanishing with the raw-LaTeX drop.
    - ``\\(...\\)`` → ``$...$`` and ``\\[...\\]`` → ``$$...$$`` so pandoc's
      HTML+MathJax pipeline renders the math instead of degrading it.

    ``\\label{...}`` / ``\\ref{...}`` are deliberately untouched — the
    existing raw-span and crossref passes own those.
    """
    body = _THEOREM_TEXTTT_RE.sub(
        lambda m: "`" + m.group(1).replace(r"\_", "_") + "`",
        body,
    )
    body = _THEOREM_DISPLAY_MATH_RE.sub(
        lambda m: f"$${m.group(1).strip()}$$",
        body,
    )
    body = _THEOREM_INLINE_MATH_RE.sub(
        lambda m: f"${m.group(1).strip()}$",
        body,
    )
    return body


def render_pandoc_citations(content: str, *, preserve_crossrefs: bool = True) -> str:
    """Render Pandoc ``[@key]`` citation groups as readable ``[key]`` text.

    The HTML writer (unlike the citeproc-driven PDF path) leaves Pandoc
    citation syntax untouched, which would surface literal ``[@key]`` markup
    on the page and trip publication validators. Bracket groups that contain
    only bibliographic citekeys are rewritten to ``[key1; key2]``; pandoc-
    crossref keys such as ``[@fig:plot]`` are preserved so the crossref
    filter can resolve them during combined HTML rendering.
    """

    def _replace(match: re.Match[str]) -> str:
        keys = _PANDOC_CITEKEY_RE.findall(match.group("body"))
        if not keys:
            return match.group(0)
        if preserve_crossrefs and any(key.startswith(_PANDOC_CROSSREF_PREFIXES) for key in keys):
            return match.group(0)
        return "[" + "; ".join(keys) + "]"

    return _PANDOC_CITATION_RE.sub(_replace, content)

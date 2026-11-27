"""Exercise the combined HTML raw-label adapter with real Pandoc and crossref."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from infrastructure.rendering._pandoc_filters import combined_html_lua_filters

RENDERING = Path(__file__).resolve().parents[3] / "infrastructure" / "rendering"


def _render(markdown: str, *, has_crossref: bool = True) -> str:
    pandoc = shutil.which("pandoc")
    crossref = shutil.which("pandoc-crossref")
    if pandoc is None or (has_crossref and crossref is None):
        pytest.skip("matching Pandoc and crossref tools are required")
    args = [
        pandoc,
        "-f", "markdown+raw_tex+header_attributes",
        "-t", "html5",
        "--number-sections",
        "--metadata=linkReferences:true",
        "--math-method=mathjax",
    ]
    for path in combined_html_lua_filters(RENDERING, has_crossref=has_crossref):
        args.extend(["--lua-filter", str(path)])
    if has_crossref:
        args.extend(["--filter", crossref])
    return subprocess.run(args, input=markdown, text=True, check=True, capture_output=True).stdout


def test_resolves_native_heading_and_figure_with_legacy_heading_alias() -> None:
    markdown = r"""
# Results page

\label{sec:results}

Section \ref{sec:results}; Figure \ref{fig:plot}.
Literal example: `\ref{fig:plot}`. Math: $x+y$.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.7\textwidth]{figures/plot.png}
\caption{Scientific caption with $x+y$.}
\label{fig:plot}
\end{figure}
"""
    html = _render(markdown)
    assert html.count('id="results-page"') == 1
    assert html.count('id="sec:results"') == 1
    assert 'href="#sec:results">1</a>' in html
    assert '<figure id="fig:plot">' in html
    assert 'href="#fig:plot">1</a>' in html
    assert r"<code>\ref{fig:plot}</code>" in html
    assert "Scientific caption" in html
    assert 'class="math inline"' in html
    no_crossref = _render(markdown, has_crossref=False)
    assert 'id="sec:results"' not in no_crossref
    assert '<figure class="figure">' in no_crossref


def test_duplicate_or_wrong_type_targets_and_occupied_alias_use_fallback() -> None:
    markdown = r"""
# Native owner {#sec:duplicate}

# Raw owner

\label{sec:duplicate}

Reference \ref{sec:duplicate}.

::: {#sec:wrong-type}
This is a div.
:::

# Wrong type

\label{sec:wrong-type}

Reference \ref{sec:wrong-type}.

::: {#occupied-alias}
This anchor already exists.
:::

# Occupied alias

\label{sec:safe}

Reference \ref{sec:safe}.

![Native figure](native.png){#fig:duplicate}

Reference \ref{fig:duplicate}.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.7\textwidth]{figures/plot.png}
\caption{A duplicate raw figure.}
\label{fig:duplicate}
\end{figure}
"""
    html = _render(markdown)
    for label in ("sec:duplicate", "sec:wrong-type", "fig:duplicate"):
        assert html.count(f'id="{label}"') == 1
        assert f'href="#{label}"' not in html
    assert html.count('id="occupied-alias"') == 1
    assert html.count('id="sec:safe"') == 1
    assert 'href="#sec:safe">' in html


@pytest.mark.parametrize(
    ("anchor", "raw_format"),
    [
        ('<span ID=sec:human>Existing marker</span>', "html"),
        ('<a NAME="sec&#58;human">Existing marker</a>', "HTML"),
        ('<!--> <span id=sec:human>Existing marker</span> -->', "html"),
        ('<span id="sec:human">Existing marker</span>', "html5"),
    ],
)
def test_opaque_raw_html_preserves_existing_anchor_and_disables_normalization(anchor: str, raw_format: str) -> None:
    markdown = f"""`{anchor}`{{={raw_format}}}

# Human-readable heading

\\label{{sec:human}}

Reference \\ref{{sec:human}}.
"""
    html = _render(markdown)
    assert anchor in html
    assert '<h1 data-number="1" id="human-readable-heading">' in html
    assert '<h1 data-number="1" id="sec:human">' not in html
    assert 'href="#sec:human"' not in html

"""Config-driven LaTeX title page, book cover, and publishing front matter.

Facade module. The implementation is split across cohesive private
siblings to keep each module within the advisory line-count budget:

- ``_pdf_title_page_latex``     — LaTeX text-escaping helpers.
- ``_pdf_title_page_config``    — config loading and metadata normalization.
- ``_pdf_title_page_images``    — cover-image resolution and includegraphics.
- ``_pdf_title_page_publishing``— publishing-page and book-cover blocks.

Public and cross-module names are re-exported here so importers can keep
using ``infrastructure.rendering._pdf_title_page`` as the single path.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_title_page_config import (
    _metadata_from_config,
    _rendering_options,
    build_pandoc_metadata,
)

# Re-exported for existing importers (e.g. _combined_exports); the explicit
# ``as`` alias marks it an intentional re-export so `mypy --strict` accepts the
# private-name import at the call sites.
from infrastructure.rendering._pdf_title_page_config import (
    _load_render_config as _load_render_config,
)
from infrastructure.rendering._pdf_title_page_images import (
    _cover_image_alt as _cover_image_alt,
    _cover_image_block,
    _cover_image_path as _cover_image_path,
    _has_available_paper_cover,
)
from infrastructure.rendering._pdf_title_page_latex import (
    _latex_href_url,
    _latex_text,
)
from infrastructure.rendering._pdf_title_page_publishing import (
    _book_cover_body,
    _paper_cover_author_lines,
    _publication_doi_line,
)

__all__ = [
    "build_pandoc_metadata",
    "generate_title_page_body",
    "generate_title_page_preamble",
]

logger = get_logger(__name__)

# ── Author-block leading ─────────────────────────────────────────────────────
#
# A name, an affiliation, an email and an ORCID describe ONE person. Set at the
# default leading they read as four unrelated centered lines, and the title page
# loses the grouping a reader needs to tell one author from the next. Both
# constants below tighten that block without touching a single type size, so
# nothing shrinks below its designed print size.

#: Extra leading between the metadata lines of one author inside ``\author{}``.
#: ``\maketitle`` typesets ``\@author`` inside a one-column tabular, so the rows
#: are ``\\``-separated and take an optional dimension directly.
_AUTHOR_LINE_TRIM = "-2pt"

#: Baseline multiplier for the custom-paper-cover author stack.
#: :func:`_paper_cover_author_lines` emits each line as its own ``\par`` group,
#: so there is no ``\\`` for ``_AUTHOR_LINE_TRIM`` to attach to; the equivalent
#: tightening is a reduced ``\baselinestretch`` with no inter-paragraph glue,
#: scoped to the block so the rest of the title page keeps normal leading.
_AUTHOR_BLOCK_LINESPREAD = "0.92"


def _tightened_author_block(author_lines: list[str]) -> list[str]:
    """Wrap paper-cover author lines so each author reads as one compact unit.

    Args:
        author_lines: LaTeX lines from ``_paper_cover_author_lines``, each of
            which ends its own paragraph.

    Returns:
        The same lines inside a group that removes paragraph glue and reduces
        the baseline stretch, or an empty list when there is nothing to wrap.
    """
    if not author_lines:
        return []
    return [
        r"\begingroup",
        r"\setlength{\parskip}{0pt}",
        r"\linespread{" + _AUTHOR_BLOCK_LINESPREAD + r"}\selectfont",
        *author_lines,
        r"\endgroup",
    ]


def generate_title_page_preamble(manuscript_dir: Path) -> str:
    """Generate LaTeX title page preamble commands from config.yaml metadata."""
    config, config_file = _load_render_config(manuscript_dir)
    if not config:
        return ""

    try:
        metadata = _metadata_from_config(config)
        authors = config.get("authors", [])
        custom_paper_cover = _has_available_paper_cover(config, config_file)

        title = _latex_text(metadata["title"])
        date = metadata["date"]
        rendering = _rendering_options(config)
        doi_line = _publication_doi_line(config)

        preamble_lines = [
            f"\\title{{{title}}}",
        ]

        if authors:
            author_blocks = []
            for author in authors:
                if "name" not in author:
                    continue

                name = _latex_text(author["name"])
                parts = [name]

                if not custom_paper_cover:
                    # Every metadata row of one author is pulled up by
                    # _AUTHOR_LINE_TRIM so the four lines read as one block.
                    row = f"\\\\[{_AUTHOR_LINE_TRIM}]"
                    affils: list[str] = []
                    if "affiliations" in author:
                        raw = author["affiliations"]
                        affils = [raw] if isinstance(raw, str) else list(raw)
                    elif "affiliation" in author:
                        affils = [author["affiliation"]]
                    for affil in affils:
                        parts.append(f"{row}\\footnotesize{{{_latex_text(affil)}}}")

                    if "email" in author:
                        parts.append(f"{row}\\footnotesize{{\\texttt{{{_latex_text(author['email'])}}}}}")

                    if "orcid" in author:
                        orcid = str(author["orcid"])
                        parts.append(
                            f"{row}\\footnotesize{{\\href{{https://orcid.org/{_latex_href_url(orcid)}}}{{ORCID: {_latex_text(orcid)}}}}}"  # noqa: E501
                        )

                author_block = "".join(parts)
                author_blocks.append(author_block)

            if author_blocks:
                author_str = " \\\\and ".join(author_blocks)

                extras = []
                if doi_line and not custom_paper_cover:
                    extras.append(doi_line)

                if extras:
                    author_str += " \\\\ " + " \\\\ ".join([f"\\footnotesize{{{e}}}" for e in extras])

                preamble_lines.append(f"\\author{{{author_str}}}")

        if rendering["include_date"] and date:
            preamble_lines.append(f"\\date{{{date}}}")
        elif rendering["include_date"]:
            preamble_lines.append(r"\date{\today}")
        else:
            preamble_lines.append(r"\date{}")

        logger.debug(f"Generated title page preamble with {len(preamble_lines)} commands")
        return "\n".join(preamble_lines)

    except (OSError, yaml.YAMLError, KeyError, ValueError) as e:
        logger.warning(f"Error reading config.yaml: {e}")
        return ""


def generate_title_page_body(manuscript_dir: Path) -> str:
    """Generate LaTeX title page body command from config.yaml metadata."""
    config, config_file = _load_render_config(manuscript_dir)
    if not config or config_file is None:
        return ""

    try:
        if isinstance(config.get("book"), dict) and config["book"].get("title"):
            body = _book_cover_body(config, config_file)
            logger.debug("Generated book-style title, publishing, and contents opening")
            return body

        metadata = _metadata_from_config(config)
        rendering = _rendering_options(config)
        title = _latex_text(metadata["title"])
        subtitle = _latex_text(metadata["subtitle"])
        image_block = _cover_image_block(
            config,
            config_file,
            height=rf"{rendering['cover_height_fraction']}\textheight",
            section_name="paper",
        )

        if image_block:
            author_lines = _paper_cover_author_lines(config)
            body_lines = [
                r"\begin{titlepage}",
                r"\centering",
                r"\vspace*{0.55cm}",
                r"{\Huge\sffamily\bfseries " + title + r"\par}",
                r"\vspace{0.4em}",
                r"{\Large\sffamily " + subtitle + r"\par}" if subtitle else "",
                r"\vspace{0.75em}",
                *_tightened_author_block(author_lines),
                r"\vspace{0.35em}",
                r"\makeatletter",
                r"{\@date\par}",
                r"\makeatother",
                r"\vfill",
                image_block,
                r"\vfill",
                r"\end{titlepage}",
                r"\thispagestyle{empty}",
            ]
        elif subtitle:
            body_lines = [
                r"\begin{titlepage}",
                r"\centering",
                r"\vspace*{2cm}",
                r"{\LARGE\bfseries " + title + r"\par}",
                r"\vspace{0.75em}",
                r"{\large " + subtitle + r"\par}",
                r"\vfill",
                r"\makeatletter",
                r"{\@author\par}",
                r"\vspace{1em}",
                r"{\@date\par}",
                r"\makeatother",
                r"\vfill",
                r"\end{titlepage}",
                r"\thispagestyle{empty}",
            ]
        else:
            body_lines = [
                "\\maketitle",
                "\\thispagestyle{empty}",
            ]

        logger.debug(f"Generated title page body with {len(body_lines)} commands")
        return "\n".join(body_lines)

    except (OSError, yaml.YAMLError, KeyError, ValueError) as e:
        logger.warning(f"Error reading config.yaml: {e}")
        return ""

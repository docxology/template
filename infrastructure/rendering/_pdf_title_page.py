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
    _cover_image_block,
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
                    affils: list[str] = []
                    if "affiliations" in author:
                        raw = author["affiliations"]
                        affils = [raw] if isinstance(raw, str) else list(raw)
                    elif "affiliation" in author:
                        affils = [author["affiliation"]]
                    for affil in affils:
                        parts.append(f"\\\\\\footnotesize{{{_latex_text(affil)}}}")

                    if "email" in author:
                        parts.append(f"\\\\\\footnotesize{{\\texttt{{{_latex_text(author['email'])}}}}}")

                    if "orcid" in author:
                        orcid = str(author["orcid"])
                        parts.append(
                            f"\\\\\\footnotesize{{\\href{{https://orcid.org/{_latex_href_url(orcid)}}}{{ORCID: {_latex_text(orcid)}}}}}"  # noqa: E501
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

        if date:
            preamble_lines.append(f"\\date{{{date}}}")
        else:
            preamble_lines.append(r"\date{\today}")

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
                *author_lines,
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

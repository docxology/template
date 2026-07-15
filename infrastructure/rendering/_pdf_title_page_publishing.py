"""Publishing-page and book-cover LaTeX blocks for the title page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.rendering._pdf_title_page_config import (
    _author_blocks,
    _front_matter_options,
    _metadata_from_config,
)
from infrastructure.rendering._pdf_title_page_images import (
    _configured_image_path,
    _cover_image_block,
    _image_block,
)
from infrastructure.rendering._pdf_title_page_latex import (
    _latex_href_url,
    _latex_paragraphs,
    _latex_text,
)
from infrastructure.publishing.repository_metadata import normalized_repository_url

__all__ = [
    "_book_cover_body",
    "_paper_cover_author_lines",
    "_publication_doi_line",
    "_publishing_acknowledgement_block",
    "_publishing_page_visual_block",
    "_publishing_quote_box",
    "_suggested_citation_line",
]


def _publishing_quote_box(config: dict[str, Any]) -> list[str]:
    """Return optional page-two quotation box lines."""
    quote = _front_matter_options(config).get("page_two_quote", {}) or {}
    if not isinstance(quote, dict):
        return []
    text = quote.get("text", "")
    if not text:
        return []
    attribution = _latex_text(quote.get("attribution", ""))
    citation = _latex_text(quote.get("citation", ""))
    attribution_line = ""
    if attribution:
        attribution_line = r"\par\vspace{0.35em}\raggedleft\upshape --- " + attribution
        if citation:
            attribution_line += r"\par{\scriptsize " + citation + r"}"
    return [
        r"\vspace{0.8em}",
        r"\begin{center}",
        r"\begingroup",
        r"\setlength{\fboxsep}{8pt}",
        r"\fcolorbox{red!55!black}{red!3}{%",
        r"\begin{minipage}{0.88\textwidth}",
        r"\footnotesize\itshape " + _latex_paragraphs(text),
        attribution_line,
        r"\end{minipage}%",
        r"}",
        r"\endgroup",
        r"\end{center}",
    ]


def _publishing_acknowledgement_block(config: dict[str, Any]) -> list[str]:
    """Return optional page-two acknowledgement block lines."""
    acknowledgement = _front_matter_options(config).get("page_two_acknowledgements", {}) or {}
    if not isinstance(acknowledgement, dict):
        return []
    text = acknowledgement.get("text", "")
    if not text:
        return []
    title = _latex_text(acknowledgement.get("title", "Acknowledgements"))
    return [
        r"\vspace{0.6em}",
        r"\noindent\fcolorbox{black!35}{black!2}{%",
        r"\begin{minipage}{0.94\textwidth}",
        r"{\sffamily\bfseries " + title + r"}\par\vspace{0.25em}",
        r"{\footnotesize " + _latex_paragraphs(text) + r"}",
        r"\end{minipage}%",
        r"}",
        r"\par",
    ]


def _suggested_citation_line(
    config: dict[str, Any],
    *,
    title: str,
    subtitle: str,
    edition: str,
    year: str,
    tail: str,
) -> str:
    """Build suggested-citation LaTeX from config or author metadata."""
    publication = config.get("publication", {}) or {}
    if isinstance(publication, dict):
        override = str(publication.get("suggested_citation", "")).strip()
        if override:
            return r"\noindent Suggested citation: " + _latex_text(override) + tail

    authors = config.get("authors", [])
    author_names: list[str] = []
    if isinstance(authors, list):
        for author in authors:
            if isinstance(author, dict) and author.get("name"):
                author_names.append(str(author["name"]))
    if not author_names:
        author_names = ["Project Author"]
    if len(author_names) == 1:
        author_text = _latex_text(author_names[0])
    elif len(author_names) == 2:
        author_text = _latex_text(f"{author_names[0]} & {author_names[1]}")
    else:
        author_text = _latex_text(", ".join(author_names[:-1]) + f", & {author_names[-1]}")

    publisher = "Active Inference Institute"
    if isinstance(publication, dict) and publication.get("publisher"):
        publisher = str(publication["publisher"])

    return (
        r"\noindent Suggested citation: "
        + author_text
        + r" ("
        + (year or r"\the\year")
        + r"). \textit{"
        + title
        + (": " + subtitle if subtitle else "")
        + r"} (Edition "
        + (edition or "1.0")
        + r"). "
        + _latex_text(publisher)
        + "."
        + tail
    )


def _publishing_page_visual_block(config: dict[str, Any], config_file: Path) -> list[str]:
    """Return optional page-two visual image block lines."""
    visual = _front_matter_options(config).get("page_two_visual", {}) or {}
    if not isinstance(visual, dict):
        return []
    image = visual.get("image", "")
    if not image:
        return []
    image_block = _image_block(
        _configured_image_path(image, config_file),
        config_file,
        width=r"0.94\textwidth",
        height=r"0.50\textheight",
    )
    if not image_block:
        return []
    title = _latex_text(visual.get("title", ""))
    caption = _latex_paragraphs(visual.get("caption", ""))
    lines = [
        r"\vspace{0.8em}",
        r"\begin{center}",
    ]
    if title:
        lines.extend(
            [
                r"{\sffamily\bfseries " + title + r"\par}",
                r"\vspace{0.35em}",
            ]
        )
    lines.append(image_block)
    if caption:
        lines.extend(
            [
                r"\par\vspace{0.35em}",
                r"\begin{minipage}{0.92\textwidth}",
                r"{\scriptsize " + caption + r"}",
                r"\end{minipage}",
            ]
        )
    lines.append(r"\end{center}")
    return lines


def _publication_doi_line(config: dict[str, Any]) -> str:
    """Return DOI cover text, including an explicit forthcoming status."""
    publication = config.get("publication", {}) or {}
    if not isinstance(publication, dict):
        return ""
    doi = str(publication.get("doi", "")).strip()
    if doi:
        doi_target = _latex_href_url(f"https://doi.org/{doi}")
        return r"DOI: \href{" + doi_target + r"}{" + _latex_text(doi) + r"}"
    doi_status = str(publication.get("doi_status", "")).strip()
    if doi_status:
        return r"DOI: " + _latex_text(doi_status)
    return ""


def _paper_cover_author_lines(config: dict[str, Any]) -> list[str]:
    """Return visible author/ORCID/DOI lines for the custom paper cover."""
    authors = _author_blocks(config)
    lines: list[str] = []
    for author in authors:
        lines.append(r"{\large\sffamily\bfseries " + _latex_text(author["name"]) + r"\par}")
        if author["affiliation"]:
            lines.append(r"{\small\sffamily " + _latex_text(author["affiliation"]) + r"\par}")
        if author["email"]:
            lines.append(r"{\small\sffamily\texttt{" + _latex_text(author["email"]) + r"}\par}")
        if author["orcid"]:
            orcid = _latex_text(author["orcid"])
            lines.append(
                r"{\small\sffamily\href{https://orcid.org/"
                + _latex_href_url(author["orcid"])
                + r"}{ORCID: "
                + orcid
                + r"}\par}"
            )
        lines.append(r"\vspace{0.08em}")
    if not lines:
        lines.append(r"{\large\sffamily\bfseries Project Author\par}")

    doi_line = _publication_doi_line(config)
    if doi_line:
        lines.append(r"{\small\sffamily " + doi_line + r"\par}")
    return lines


def _book_cover_body(config: dict[str, Any], config_file: Path) -> str:
    """Generate a book-style cover, publishing page, and contents page."""
    metadata = _metadata_from_config(config)
    authors = _author_blocks(config)
    publication = config.get("publication", {}) or {}
    if not isinstance(publication, dict):
        publication = {}
    doi = str(publication.get("doi", ""))
    title = _latex_text(metadata["title"])
    subtitle = _latex_text(metadata["subtitle"])
    edition = _latex_text(metadata["edition"])
    year = _latex_text(metadata["year"])
    license_name = _latex_text(metadata["license"])
    code_license = _latex_text(metadata["code_license"])

    author_lines: list[str] = []
    for author in authors:
        author_lines.append(r"{\Large\bfseries " + _latex_text(author["name"]) + r"}\\[0.35em]")
        if author["affiliation"]:
            author_lines.append(r"{\normalsize " + _latex_text(author["affiliation"]) + r"}\\[0.25em]")
        if author["email"]:
            email = _latex_text(author["email"])
            author_lines.append(r"{\normalsize\texttt{" + email + r"}}\\[0.25em]")
        if author["orcid"]:
            orcid = _latex_text(author["orcid"])
            author_lines.append(
                r"{\normalsize\href{https://orcid.org/"
                + _latex_text(author["orcid"])
                + r"}{ORCID: "
                + orcid
                + r"}}\\[0.5em]"
            )
    if not author_lines:
        author_lines.append(r"{\Large\bfseries Project Author}\\[0.5em]")

    image_block = _cover_image_block(config, config_file, height=r"0.62\textheight", section_name="book")

    edition_line = ""
    if edition or year:
        edition_line = r"{\small Edition " + (edition or "1.0") + (" -- " + year if year else "") + r"}"

    cover_doi_line = ""
    publishing_doi_line = ""
    if doi:
        escaped_doi = _latex_text(doi)
        doi_target = _latex_href_url(f"https://doi.org/{doi}")
        cover_doi_line = r"{\small DOI: \href{" + doi_target + r"}{" + escaped_doi + r"}\par}"
        publishing_doi_line = r"\noindent DOI: \href{" + doi_target + r"}{" + escaped_doi + r"}\\"

    publishing_lines = [
        r"\clearpage",
        r"\thispagestyle{empty}",
        r"\section*{Publishing Information}",
        "",
        r"\noindent{\Large\bfseries " + title + r"}\\",
    ]
    if subtitle:
        publishing_lines.append(r"{\large " + subtitle + r"}\\[1.2em]")
    publishing_lines.extend(author_lines)
    publishing_lines.extend(
        [
            r"\vspace{1.0em}",
            r"\noindent Edition " + (edition or "1.0") + (" -- " + year if year else "") + r"\\",
            r"\noindent Text license: " + (license_name or "CC BY 4.0") + r"\\",
            r"\noindent Source-code license: " + (code_license or "Apache-2.0") + r"\\",
        ]
    )
    if publishing_doi_line:
        publishing_lines.append(publishing_doi_line)
    repo_url = normalized_repository_url(publication) or ""
    if repo_url:
        repo_label = str(publication.get("repository_label", "")).strip() or "Source repository"
        repo_target = _latex_href_url(repo_url)
        repo_display = _latex_text(repo_url)
        publishing_lines.append(
            r"\noindent " + _latex_text(repo_label) + r": \href{" + repo_target + r"}{" + repo_display + r"}\\"
        )
    publishing_lines.extend(_publishing_quote_box(config))
    publishing_lines.extend(_publishing_acknowledgement_block(config))
    publishing_lines.extend(_publishing_page_visual_block(config, config_file))
    suggested_citation_parts: list[str] = []
    if repo_url:
        suggested_citation_parts.append(r"\href{" + _latex_href_url(repo_url) + r"}{" + _latex_text(repo_url) + r"}")
    if doi:
        doi_url = f"https://doi.org/{doi}"
        suggested_citation_parts.append(r"\href{" + _latex_href_url(doi_url) + r"}{" + _latex_text(doi_url) + r"}")
    suggested_citation_tail = ""
    if suggested_citation_parts:
        suggested_citation_tail = " " + ". ".join(suggested_citation_parts) + "."
    suggested_citation_line = _suggested_citation_line(
        config, title=title, subtitle=subtitle, edition=edition, year=year, tail=suggested_citation_tail
    )
    publishing_lines.extend(
        [
            r"\vspace{1.0em}",
            suggested_citation_line,
            "",
            r"\vspace{1.0em}",
            r"\noindent This open textbook is generated from version-controlled Markdown, tested Python modules, "
            r"programmatic figures, and rendered Mermaid diagrams. Corrections and improvements may be submitted "
            + (r"via the source repository linked above." if repo_url else r"through the project repository."),
            "",
            r"\vfill",
            r"\noindent Accessibility note: the compact PDF is optimized for dense print. Reader-profile builds, "
            r"HTML output, and source Markdown can be generated from the same manuscript materials.",
            r"\clearpage",
            r"\tableofcontents",
            r"\clearpage",
        ]
    )

    return "\n".join(
        [
            r"\begin{titlepage}",
            r"\thispagestyle{empty}",
            r"\setcounter{page}{1}",
            r"\centering",
            r"\vspace*{0.6cm}",
            r"{\Huge\sffamily\bfseries " + title + r"\par}",
            r"\vspace{0.35cm}",
            r"{\Large\sffamily " + subtitle + r"\par}" if subtitle else "",
            r"\vspace{0.8cm}",
            *author_lines,
            r"\vfill",
            image_block,
            r"\vfill",
            edition_line,
            cover_doi_line,
            r"\end{titlepage}",
            *publishing_lines,
        ]
    )

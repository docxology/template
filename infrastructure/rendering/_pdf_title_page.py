"""Config-driven LaTeX title page, book cover, and publishing front matter."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_LATEX_ESCAPE_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _resolve_config_yaml(manuscript_dir: Path) -> Path | None:
    """Locate ``config.yaml`` near a manuscript directory."""
    primary = manuscript_dir / "config.yaml"
    if primary.is_file():
        return primary
    for parent in (manuscript_dir.parent, manuscript_dir.parent.parent):
        try:
            candidate = parent / "manuscript" / "config.yaml"
        except (TypeError, ValueError):
            continue
        if candidate.is_file() and candidate != primary:
            return candidate
    return None


def _load_render_config(manuscript_dir: Path) -> tuple[dict[str, Any] | None, Path | None]:
    """Load the nearest manuscript config file."""
    config_file = _resolve_config_yaml(manuscript_dir)
    if config_file is None:
        logger.debug(f"Config file not found near: {manuscript_dir}")
        return None, None
    try:
        with config_file.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as e:
        logger.warning(f"Error reading config.yaml: {e}")
        return None, None
    if not isinstance(config, dict):
        return None, config_file
    return config, config_file


def build_pandoc_metadata(config: dict[str, Any]) -> dict[str, Any]:
    """Build pandoc YAML metadata from a manuscript config dict."""
    paper = config.get("paper") or {}
    meta: dict[str, Any] = {}
    if paper.get("title"):
        meta["title"] = str(paper["title"])
    if paper.get("subtitle"):
        meta["subtitle"] = str(paper["subtitle"])
    authors: list[str] = []
    for entry in config.get("authors") or []:
        if isinstance(entry, dict) and entry.get("name"):
            name = str(entry["name"])
            affiliations = entry.get("affiliations") or []
            if affiliations:
                name += " (" + "; ".join(str(affiliation) for affiliation in affiliations) + ")"
            authors.append(name)
        elif isinstance(entry, str):
            authors.append(entry)
    if authors:
        meta["author"] = authors
    date = paper.get("date") or (config.get("publication") or {}).get("year")
    if date:
        meta["date"] = str(date)
    return meta


def _latex_text(value: object) -> str:
    """Escape a short text value for LaTeX text mode."""
    text = str(value)
    return "".join(_LATEX_ESCAPE_REPLACEMENTS.get(ch, ch) for ch in text)


def _latex_href_url(url: str) -> str:
    """Escape a URL for hyperref ``\\href`` first argument (not text mode)."""
    minimal = {"\\": r"\\", "%": r"\%", "#": r"\#", "&": r"\&"}
    return "".join(minimal.get(ch, ch) for ch in url)


def _latex_paragraphs(value: object) -> str:
    """Escape a prose block for LaTeX and preserve paragraph breaks."""
    raw = str(value).strip()
    if not raw:
        return ""
    paragraphs = [line.strip() for line in re.split(r"\n\s*\n", raw) if line.strip()]
    return r"\par ".join(_latex_text(paragraph) for paragraph in paragraphs)


def _front_matter_options(config: dict[str, Any]) -> dict[str, Any]:
    """Return optional front-matter rendering settings."""
    front_matter = config.get("front_matter", {}) or {}
    return front_matter if isinstance(front_matter, dict) else {}


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


def _metadata_from_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return book/paper metadata with book fields taking precedence."""
    book = config.get("book", {}) or {}
    paper = config.get("paper", {}) or {}
    if not isinstance(book, dict):
        book = {}
    if not isinstance(paper, dict):
        paper = {}
    title = book.get("title") or paper.get("title") or "Research Paper"
    subtitle = book.get("subtitle") or paper.get("subtitle") or ""
    year = book.get("year") or paper.get("year") or ""
    edition = book.get("edition") or ""
    date = paper.get("date") or (str(year) if year else "")
    return {
        "book": book,
        "paper": paper,
        "title": str(title),
        "subtitle": str(subtitle),
        "date": str(date),
        "year": str(year),
        "edition": str(edition),
        "license": str(book.get("license", "")),
        "code_license": str(book.get("code_license", "")),
    }


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


def _author_blocks(config: dict[str, Any]) -> list[dict[str, str]]:
    """Normalize author metadata from config."""
    raw_authors = config.get("authors", [])
    authors: list[dict[str, str]] = []
    if isinstance(raw_authors, list):
        for author in raw_authors:
            if not isinstance(author, dict) or not author.get("name"):
                continue
            affil = author.get("affiliation", "")
            if not affil and isinstance(author.get("affiliations"), list):
                affil = ", ".join(str(item) for item in author["affiliations"])
            authors.append(
                {
                    "name": str(author.get("name", "")),
                    "affiliation": str(affil),
                    "email": str(author.get("email", "")),
                    "orcid": str(author.get("orcid", "")),
                }
            )
    if authors:
        return authors

    book = config.get("book", {}) or {}
    if isinstance(book, dict) and book.get("author"):
        authors.append(
            {
                "name": str(book.get("author", "")),
                "affiliation": "",
                "email": "",
                "orcid": str(book.get("orcid", "")),
            }
        )
    return authors


def _cover_image_path(config: dict[str, Any], config_file: Path) -> Path | None:
    """Resolve the configured book or paper cover image path, if any."""
    for section_name in ("book", "paper"):
        image_path = _section_cover_image_path(config, config_file, section_name)
        if image_path is not None:
            return image_path
    return None


def _section_cover_image_path(config: dict[str, Any], config_file: Path, section_name: str) -> Path | None:
    """Resolve a cover image from one metadata section only."""
    cover: dict[str, Any] | None = None
    section = config.get(section_name, {}) or {}
    if not isinstance(section, dict):
        return None
    candidate = section.get("cover", {}) or {}
    if isinstance(candidate, dict) and candidate.get("image"):
        cover = candidate
    if cover is None:
        return None
    raw_image = cover.get("image")
    if not raw_image:
        return None
    return _configured_image_path(raw_image, config_file)


def _configured_image_path(raw_image: object, config_file: Path) -> Path | None:
    """Resolve a config-declared image path near the manuscript/output tree."""
    image_path = Path(str(raw_image))
    if not str(image_path):
        return None
    if image_path.is_absolute():
        return image_path
    candidates = [config_file.parent / image_path]
    project_roots = [config_file.parent.parent]
    if config_file.parent.name == "manuscript" and config_file.parent.parent.name == "output":
        project_roots.append(config_file.parent.parent.parent)
    for root in project_roots:
        candidates.extend(
            [
                root / image_path,
                root / "manuscript" / image_path,
                root / "output" / image_path,
            ]
        )
    for parent in config_file.parents:
        candidates.append(parent / "manuscript" / image_path)
    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)
    for candidate in unique_candidates:
        if candidate.is_file():
            return candidate
    return unique_candidates[0]


def _image_latex_path(image_path: Path, config_file: Path) -> str:
    """Return a LaTeX-safe image path without embedding local absolute paths."""
    manuscript_dir = config_file.parent
    parent = manuscript_dir.parent
    if manuscript_dir.name == "manuscript":
        output_root = parent if parent.name == "output" else parent / "output"
        latex_dir = output_root / "pdf"
    else:
        latex_dir = manuscript_dir
    try:
        return Path(os.path.relpath(image_path.resolve(), latex_dir.resolve())).as_posix()
    except OSError:
        return image_path.as_posix() if not image_path.is_absolute() else image_path.name


def _image_block(
    image_path: Path | None,
    config_file: Path,
    *,
    height: str,
    width: str = r"0.98\textwidth",
) -> str:
    """Return a LaTeX includegraphics block for a configured image."""
    if image_path is None:
        return ""
    if not image_path.is_file():
        logger.warning("Configured image does not exist: %s", image_path)
        return ""
    latex_image = _image_latex_path(image_path, config_file)
    return (
        r"\includegraphics[width="
        + width
        + r",height="
        + height
        + r",keepaspectratio]{"
        + r"\detokenize{"
        + latex_image
        + r"}}"
    )


def _cover_image_block(
    config: dict[str, Any],
    config_file: Path,
    *,
    height: str,
    section_name: str | None = None,
) -> str:
    """Return a LaTeX includegraphics block for the configured cover image."""
    image_path = (
        _section_cover_image_path(config, config_file, section_name)
        if section_name is not None
        else _cover_image_path(config, config_file)
    )
    return _image_block(image_path, config_file, height=height)


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


def _has_available_paper_cover(config: dict[str, Any], config_file: Path | None) -> bool:
    """Return true when a paper cover image is configured and present."""
    if config_file is None:
        return False
    paper = config.get("paper", {}) or {}
    if not isinstance(paper, dict):
        return False
    cover = paper.get("cover", {}) or {}
    if not isinstance(cover, dict) or not cover.get("image"):
        return False
    cover_image = _section_cover_image_path(config, config_file, "paper")
    return cover_image is not None and cover_image.is_file()


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
    repo_url = str(publication.get("repository_url", "")).strip()
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
        title = _latex_text(metadata["title"])
        subtitle = _latex_text(metadata["subtitle"])
        image_block = _cover_image_block(config, config_file, height=r"0.60\textheight", section_name="paper")

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

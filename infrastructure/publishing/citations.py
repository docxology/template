"""Citation generation functions for academic publishing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from infrastructure.publishing.models import PublicationMetadata


def format_authors_apa(authors: List[str]) -> str:
    """Format authors for APA style.

    Args:
        authors: List of author names

    Returns:
        APA-formatted author string
    """
    if not authors:
        return "Unknown Author"

    if len(authors) == 1:
        return authors[0]

    if len(authors) == 2:
        return f"{authors[0]} & {authors[1]}"

    # Three or more authors
    return f"{authors[0]}, et al."


def format_authors_mla(authors: List[str]) -> str:
    """Format authors for MLA style.

    Args:
        authors: List of author names

    Returns:
        MLA-formatted author string
    """
    if not authors:
        return "Unknown Author"

    if len(authors) == 1:
        return authors[0]

    if len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"

    # Three or more authors
    return f"{authors[0]}, et al."


def generate_citation_bibtex(metadata: PublicationMetadata) -> str:
    """Generate BibTeX citation format.

    Args:
        metadata: Publication metadata

    Returns:
        BibTeX formatted citation
    """
    # Create a simple citation key
    first_author = (
        metadata.authors[0].replace(" ", "").lower() if metadata.authors else "unknown"
    )
    year = (
        metadata.publication_date.split("-")[0] if metadata.publication_date else "2024"
    )
    citation_key = f"{first_author}{year}"

    bibtex = f"""@software{{{citation_key},
  author = {{{' and '.join(metadata.authors)}}},
  title = {{{metadata.title}}},
  year = {{{year}}},
  publisher = {{{metadata.publisher or 'Self-published'}}},
  url = {{{metadata.repository_url or ''}}},
  license = {{{metadata.license}}},
  abstract = {{{metadata.abstract}}},
  keywords = {{{', '.join(metadata.keywords)}}}
"""

    if metadata.doi:
        bibtex = bibtex.rstrip() + f",\n  doi = {{{metadata.doi}}}\n"

    bibtex += "}\n"

    return bibtex


def generate_citation_apa(metadata: PublicationMetadata) -> str:
    """Generate APA citation format.

    Args:
        metadata: Publication metadata

    Returns:
        APA formatted citation
    """
    authors_text = format_authors_apa(metadata.authors)
    year = (
        metadata.publication_date.split("-")[0] if metadata.publication_date else "2024"
    )

    citation = f"{authors_text} ({year}). {metadata.title}."

    if metadata.doi:
        citation += f" https://doi.org/{metadata.doi}"

    return citation


def generate_citation_mla(metadata: PublicationMetadata) -> str:
    """Generate MLA citation format.

    Args:
        metadata: Publication metadata

    Returns:
        MLA formatted citation
    """
    authors_text = format_authors_mla(metadata.authors)
    year = (
        metadata.publication_date.split("-")[0] if metadata.publication_date else "2024"
    )

    citation = f'{authors_text}. "{metadata.title}." {year}.'

    if metadata.repository_url:
        citation += f" {metadata.repository_url}."

    return citation


def generate_citations_markdown(metadata: PublicationMetadata) -> str:
    """Generate markdown section with all citation formats.

    Args:
        metadata: Publication metadata

    Returns:
        Markdown formatted citation section
    """
    section = """# Citation

If you use this template in your research, please cite:

## BibTeX

```bibtex
"""

    section += generate_citation_bibtex(metadata)

    section += """

## APA Style

"""

    section += generate_citation_apa(metadata)

    section += """

## MLA Style

"""

    section += generate_citation_mla(metadata)

    section += f"""

## Plain Text

{format_authors_apa(metadata.authors)}. ({metadata.publication_date.split('-')[0] if metadata.publication_date else '2024'}). {metadata.title}. {metadata.publisher or 'Self-published'}.
"""

    if metadata.doi:
        section += f" https://doi.org/{metadata.doi}"

    section += "\n"

    return section


def extract_citations_from_markdown(markdown_files: List[Path]) -> List[str]:
    """Extract all citations from markdown files.

    Args:
        markdown_files: List of markdown files to analyze

    Returns:
        List of citation keys found
    """
    citations = set()

    for md_file in markdown_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find various citation patterns
            citation_patterns = [
                r"\\cite\{([^}]+)\}",
                r"\\[a-z]*cite[a-z]*\{([^}]+)\}",
                r"\[(\d+)\]",
                r"\((\d+)\)",
            ]

            for pattern in citation_patterns:
                matches = re.findall(pattern, content)
                citations.update(matches)

        except Exception:
            continue

    return sorted(list(citations))

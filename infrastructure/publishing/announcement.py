"""Publication announcement and DOI badge generation."""

from __future__ import annotations

from infrastructure.publishing.citations import generate_citation_apa
from infrastructure.publishing.models import PublicationMetadata


def generate_doi_badge(doi: str, style: str = "zenodo") -> str:
    """Generate DOI badge markdown.

    Args:
        doi: DOI string
        style: Badge style ('zenodo', 'github', 'shields')

    Returns:
        Markdown formatted badge
    """
    if style == "zenodo":
        return f"[![DOI](https://zenodo.org/badge/DOI/{doi}.svg)](https://doi.org/{doi})"
    elif style == "github":
        return f"[![DOI](https://img.shields.io/badge/DOI-{doi}-blue.svg)](https://doi.org/{doi})"
    elif style == "shields":
        return f"[![DOI](https://img.shields.io/badge/DOI-{doi.replace('/', '%2F')}-informational)](https://doi.org/{doi})"
    else:
        return f"**DOI**: [{doi}](https://doi.org/{doi})"


def create_publication_announcement(metadata: PublicationMetadata) -> str:
    """Create a publication announcement for social media and blogs.

    Args:
        metadata: Publication metadata

    Returns:
        Markdown formatted announcement
    """

    announcement = f"""# New Publication: {metadata.title}

**Authors**: {", ".join(metadata.authors)}

## Abstract

{metadata.abstract}

## Keywords

{", ".join(f"`{keyword}`" for keyword in metadata.keywords)}

## Key Features

- **Comprehensive template** for research project development
- **Test-driven development** with 100% coverage requirements
- **Automated PDF generation** from markdown sources
- **Professional documentation** and cross-referencing
- **Thin orchestrator pattern** for maintainable code

## Links

"""

    if metadata.doi:
        announcement += f"- **DOI**: https://doi.org/{metadata.doi}\n"

    if metadata.repository_url:
        announcement += f"- **Repository**: {metadata.repository_url}\n"

    announcement += f"- **License**: {metadata.license}\n\n"

    announcement += "## Citation\n\n"
    announcement += generate_citation_apa(metadata)

    if metadata.doi:
        announcement += f"\n\nhttps://doi.org/{metadata.doi}"

    return announcement

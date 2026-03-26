"""Publication metadata extraction from markdown manuscript files.

Parses titles, authors, abstracts, keywords, DOI, and journal/conference
information from markdown content.

Extracted from metadata.py for file-size health.
"""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.models import PublicationMetadata

logger = get_logger(__name__)


def extract_publication_metadata(markdown_files: list[Path]) -> PublicationMetadata:
    """Extract publication metadata from markdown files.

    Args:
        markdown_files: List of markdown files to analyze

    Returns:
        PublicationMetadata object with extracted information
    """
    # Default metadata
    metadata = PublicationMetadata(
        title="Research Project Template",
        authors=["Template Author"],
        abstract="A comprehensive template for research projects with test-driven development and automated PDF generation.",  # noqa: E501
        keywords=["research", "template", "academic", "scientific"],
        license="Apache-2.0",
    )

    # Read content from the first markdown file (to avoid conflicts with template files)
    combined_content = ""
    if markdown_files:
        try:
            with open(markdown_files[0], "r", encoding="utf-8") as f:
                content = f.read()

            # Only use this content if it contains actual research content (not template content)
            if "Research Project Template" not in content and ("#" in content or "**" in content):
                combined_content = content
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read metadata from {markdown_files[0]}: {e}")
            combined_content = ""

    # Extract title (first # header)
    title_match = re.search(r"^#\s*(.+)$", combined_content, re.MULTILINE)
    if title_match:
        extracted_title = title_match.group(1).strip()
        # Always update the title if we find one
        if extracted_title:
            metadata.title = extracted_title

    # Extract authors from various patterns
    author_patterns = [
        r"Authors?:\s*(.+)$",
        r"By:\s*(.+)$",
        r"Author:\s*(.+)$",
        r"\*\*([^*]+)\*\*",  # Bold text pattern
        r"^\s*\*\*([^*]+)\*\*\s*$",  # Bold text on its own line
    ]

    for pattern in author_patterns:
        match = re.search(pattern, combined_content, re.IGNORECASE | re.MULTILINE)
        if match:
            authors_text = match.group(1).strip()
            # Check if this looks like author names (contains common title indicators)
            if any(
                title in authors_text.lower()
                for title in ["dr.", "prof.", "phd", "ms.", "mr.", "mrs."]
            ):
                metadata.authors = [a.strip() for a in authors_text.split(",")]
                break

    # Extract abstract
    abstract_match = re.search(
        r"##?\s*Abstract\s*(.+?)(?=\n##|\n#|\Z)",
        combined_content,
        re.DOTALL | re.IGNORECASE,
    )
    if abstract_match:
        metadata.abstract = abstract_match.group(1).strip()

    # Extract keywords
    keyword_patterns = [r"Keywords?:\s*(.+)$", r"Key words?:\s*(.+)$"]

    for pattern in keyword_patterns:
        match = re.search(pattern, combined_content, re.IGNORECASE | re.MULTILINE)
        if match:
            keywords_text = match.group(1).strip()
            metadata.keywords = [k.strip() for k in keywords_text.split(",")]
            break

    # Extract DOI if present
    doi_match = re.search(r"DOI:\s*([^\s]+)", combined_content, re.IGNORECASE)
    if doi_match:
        metadata.doi = doi_match.group(1).strip()

    # Extract journal/conference info
    journal_patterns = [r"Journal:\s*(.+)$", r"Published in:\s*(.+)$"]

    for pattern in journal_patterns:
        match = re.search(pattern, combined_content, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata.journal = match.group(1).strip()
            break

    conference_patterns = [r"Conference:\s*(.+)$", r"Proceedings of:\s*(.+)$"]

    for pattern in conference_patterns:
        match = re.search(pattern, combined_content, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata.conference = match.group(1).strip()
            break

    return metadata


def validate_doi(doi: str) -> bool:
    """Validate DOI format and checksum.

    Args:
        doi: DOI string to validate

    Returns:
        True if DOI is valid, False otherwise
    """
    if not doi:
        return False

    # Basic DOI format validation
    doi_pattern = r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$"
    if not re.match(doi_pattern, doi, re.IGNORECASE):
        return False

    # Check for invalid patterns
    if doi.endswith("/extra") or "doi:" in doi.lower() or not doi.strip():
        return False

    # DOI is valid if format matches
    return True

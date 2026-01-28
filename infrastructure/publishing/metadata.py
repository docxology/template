"""Metadata extraction and management functions for academic publishing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from infrastructure.publishing.models import PublicationMetadata


def extract_publication_metadata(markdown_files: List[Path]) -> PublicationMetadata:
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
        abstract="A comprehensive template for research projects with test-driven development and automated PDF generation.",
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
            if "Research Project Template" not in content and (
                "#" in content or "**" in content
            ):
                combined_content = content
        except Exception:
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


def generate_publication_summary(metadata: PublicationMetadata) -> str:
    """Generate a publication summary for repository README.

    Args:
        metadata: Publication metadata

    Returns:
        Markdown formatted publication summary
    """
    from infrastructure.publishing.citations import generate_citation_apa

    summary = f"""## 📚 Publication Information

**Title**: {metadata.title}

**Authors**: {', '.join(metadata.authors)}

**Abstract**: {metadata.abstract[:200]}...

**Keywords**: {', '.join(metadata.keywords)}

"""

    if metadata.doi:
        summary += f"**DOI**: [{metadata.doi}](https://doi.org/{metadata.doi})\n\n"

    if metadata.journal:
        summary += f"**Journal**: {metadata.journal}\n\n"

    if metadata.conference:
        summary += f"**Conference**: {metadata.conference}\n\n"

    summary += "**Citation**:"
    summary += f"\n\n{generate_citation_apa(metadata)}"

    return summary


def create_academic_profile_data(metadata: PublicationMetadata) -> Dict[str, Any]:
    """Create academic profile data for ORCID, ResearchGate, etc.

    Args:
        metadata: Publication metadata

    Returns:
        Dictionary with academic profile data
    """
    profile_data = {
        "title": metadata.title,
        "authors": metadata.authors,
        "abstract": metadata.abstract,
        "keywords": metadata.keywords,
        "publication_type": (
            "software" if "template" in metadata.title.lower() else "article"
        ),
        "license": metadata.license,
        "repository_url": metadata.repository_url,
        "publication_date": metadata.publication_date,
    }

    if metadata.doi:
        profile_data["identifiers"] = [
            {
                "type": "doi",
                "value": metadata.doi,
                "url": f"https://doi.org/{metadata.doi}",
            }
        ]

    return profile_data


def generate_publication_metrics(metadata: PublicationMetadata) -> Dict[str, Any]:
    """Generate publication metrics for reporting.

    Args:
        metadata: Publication metadata

    Returns:
        Dictionary with publication metrics
    """
    from infrastructure.publishing.metadata import calculate_complexity_score

    # Calculate various metrics
    title_length = len(metadata.title)
    abstract_length = len(metadata.abstract)
    author_count = len(metadata.authors)
    keyword_count = len(metadata.keywords)

    # Estimate reading time (words per minute)
    abstract_words = len(metadata.abstract.split())
    reading_time_minutes = max(1, abstract_words // 200)  # 200 words per minute

    metrics = {
        "title_length": title_length,
        "abstract_length": abstract_length,
        "abstract_word_count": abstract_words,
        "author_count": author_count,
        "keyword_count": keyword_count,
        "reading_time_minutes": reading_time_minutes,
        "license_type": metadata.license,
        "has_doi": bool(metadata.doi),
        "publication_type": (
            "software" if "template" in metadata.title.lower() else "article"
        ),
        "complexity_score": calculate_complexity_score(metadata),
    }

    return metrics


def calculate_complexity_score(metadata: PublicationMetadata) -> int:
    """Calculate a complexity score for the publication.

    Args:
        metadata: Publication metadata

    Returns:
        Complexity score (0-100)
    """
    score = 0

    # Title complexity (0-20 points)
    title_words = len(metadata.title.split())
    if title_words >= 10:
        score += 20
    elif title_words >= 7:
        score += 15
    elif title_words >= 5:
        score += 10
    else:
        score += 5

    # Abstract complexity (0-30 points)
    abstract_words = len(metadata.abstract.split())
    if abstract_words >= 300:
        score += 30
    elif abstract_words >= 200:
        score += 25
    elif abstract_words >= 100:
        score += 20
    elif abstract_words >= 50:
        score += 15
    else:
        score += 5

    # Author count (0-15 points)
    author_count = len(metadata.authors)
    if author_count >= 5:
        score += 15
    elif author_count >= 4:
        score += 12
    elif author_count >= 3:
        score += 10
    elif author_count >= 2:
        score += 5

    # Keyword count (0-15 points)
    keyword_count = len(metadata.keywords)
    if keyword_count >= 8:
        score += 15
    elif keyword_count >= 5:
        score += 10
    elif keyword_count >= 3:
        score += 5

    # Metadata completeness (0-20 points)
    if metadata.doi:
        score += 5
    if metadata.journal or metadata.conference:
        score += 5
    if metadata.publisher:
        score += 5
    if metadata.publication_date:
        score += 5

    return min(score, 100)


def create_repository_metadata(metadata: PublicationMetadata) -> str:
    """Create repository metadata JSON for GitHub/GitLab.

    Args:
        metadata: Publication metadata

    Returns:
        JSON formatted repository metadata
    """
    import json

    # Convert authors array to expected format with 'author' key
    author_list = [{"name": author} for author in metadata.authors]

    repo_metadata = {
        "@type": "SoftwareSourceCode",
        "name": metadata.title,
        "description": metadata.abstract[:200],
        "keywords": metadata.keywords,
        "license": metadata.license,
        "author": author_list,
    }

    if metadata.repository_url:
        repo_metadata["url"] = metadata.repository_url

    if metadata.doi:
        repo_metadata["identifier"] = f"https://doi.org/{metadata.doi}"

    return json.dumps(repo_metadata, indent=2)

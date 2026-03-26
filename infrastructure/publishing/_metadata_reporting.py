"""Publication metadata reporting, profiling, and serialization.

Generates summaries, academic profiles, metrics, complexity scores,
and repository metadata JSON from PublicationMetadata objects.

Extracted from metadata.py for file-size health.
"""

from __future__ import annotations

import json
from typing import Any

from infrastructure.publishing.citations import generate_citation_apa
from infrastructure.publishing.models import PublicationMetadata


def generate_publication_summary(metadata: PublicationMetadata) -> str:
    """Generate a publication summary for repository README.

    Args:
        metadata: Publication metadata

    Returns:
        Markdown formatted publication summary
    """
    summary = f"""## 📚 Publication Information

**Title**: {metadata.title}

**Authors**: {", ".join(metadata.authors)}

**Abstract**: {metadata.abstract[:200]}...

**Keywords**: {", ".join(metadata.keywords)}

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


def create_academic_profile_data(metadata: PublicationMetadata) -> dict[str, Any]:
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
        "publication_type": ("software" if "template" in metadata.title.lower() else "article"),
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


def generate_publication_metrics(metadata: PublicationMetadata) -> dict[str, Any]:
    """Generate publication metrics for reporting.

    Args:
        metadata: Publication metadata

    Returns:
        Dictionary with publication metrics
    """
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
        "publication_type": ("software" if "template" in metadata.title.lower() else "article"),
        "complexity_score": calculate_metadata_complexity_score(metadata),
    }

    return metrics

def calculate_metadata_complexity_score(metadata: PublicationMetadata) -> int:
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


def calculate_complexity_score(metadata: PublicationMetadata) -> int:
    """Backwards-compatible alias for complexity scoring."""

    return calculate_metadata_complexity_score(metadata)


def create_repository_metadata(metadata: PublicationMetadata) -> str:
    """Create repository metadata JSON for GitHub/GitLab.

    Args:
        metadata: Publication metadata

    Returns:
        JSON formatted repository metadata
    """
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

"""Build metadata-driven filenames for Zenodo and GitHub deposit uploads."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.config.loader import load_config
from infrastructure.core.text_slug import (
    extract_surname,
    pascal_case_token,
    title_key_word,
)
from infrastructure.publishing.models import PublicationMetadata

_MAX_BASENAME = 200
_MAX_TOPIC_CHARS = 24
_HASH_PREFIX_LEN = 8


@dataclass(frozen=True)
class DepositPublishContext:
    """Manuscript config slices used when naming deposit uploads."""

    deposit_filename_config: dict[str, Any]
    authors_config: list[dict[str, Any]]


def load_deposit_publish_context(config_path: Path) -> DepositPublishContext:
    """Load deposit-filename settings and raw author rows from ``config.yaml``."""
    config = load_config(config_path) or {}
    return deposit_context_from_config(dict(config))


def deposit_context_from_config(config: dict[str, Any]) -> DepositPublishContext:
    """Build deposit context from an already-loaded manuscript config dict."""
    publication_block = config.get("publication") or {}
    if not isinstance(publication_block, dict):
        publication_block = {}
    deposit_filename_config = publication_block.get("deposit_filename") or {}
    if not isinstance(deposit_filename_config, dict):
        deposit_filename_config = {}
    authors_config = config.get("authors") or []
    if not isinstance(authors_config, list):
        authors_config = []
    return DepositPublishContext(
        deposit_filename_config=deposit_filename_config,
        authors_config=authors_config,
    )


def _pick_author_name(
    metadata: PublicationMetadata,
    authors_config: list[dict[str, Any]] | None,
) -> str:
    if authors_config:
        for author in authors_config:
            if isinstance(author, dict) and author.get("corresponding") and author.get("name"):
                return str(author["name"])
    if metadata.author_records:
        return metadata.author_records[0].name
    if metadata.authors:
        return metadata.authors[0]
    return "Author"


def author_segment(
    metadata: PublicationMetadata,
    *,
    authors_config: list[dict[str, Any]] | None = None,
) -> str:
    """Build the author segment (PascalCase surname)."""
    surname = extract_surname(_pick_author_name(metadata, authors_config))
    segment = pascal_case_token(surname)
    return segment or "Author"


def year_segment(metadata: PublicationMetadata, release_tag: str) -> str:
    """Build a four-digit year segment from metadata or the release tag."""
    if metadata.publication_date:
        match = re.match(r"(\d{4})", str(metadata.publication_date).strip())
        if match:
            return match.group(1)
    tag_match = re.search(r"(20\d{2})", release_tag)
    if tag_match:
        return tag_match.group(1)
    return str(datetime.now(timezone.utc).year)


def topic_segment(metadata: PublicationMetadata, *, topic_override: str | None = None) -> str:
    """Build the topic segment from override text or the paper title."""
    if topic_override and topic_override.strip():
        raw = pascal_case_token(topic_override.strip())
    else:
        raw = pascal_case_token(title_key_word(metadata.title))
    if not raw:
        return ""
    return raw[:_MAX_TOPIC_CHARS]


def hash_segment(pdf_sha256: str, *, length: int = _HASH_PREFIX_LEN) -> str:
    """Return a lowercase hex prefix of the PDF SHA-256."""
    clean = re.sub(r"[^a-f0-9]", "", pdf_sha256.lower())
    if len(clean) >= length:
        return clean[:length]
    return (clean + "0" * length)[:length]


def fallback_deposit_filename(project_name: str) -> str:
    """Return the conventional ``{project}_combined.pdf`` fallback name."""
    return f"{project_name}_combined.pdf"


def build_deposit_filename(
    *,
    metadata: PublicationMetadata,
    pdf_sha256: str,
    project_name: str,
    release_tag: str,
    publish_context: DepositPublishContext | None = None,
    deposit_filename_config: dict[str, Any] | None = None,
    authors_config: list[dict[str, Any]] | None = None,
) -> str:
    """Build ``{Author}_{Year}_{Topic}_{Hash8}.pdf`` for deposit uploads.

    When ``deposit_filename.enabled`` is false, returns the fallback combined name.
    Falls back to the fallback name when author or topic segments sanitize to empty.
    """
    if publish_context is not None:
        config = publish_context.deposit_filename_config
        authors_config = publish_context.authors_config
    else:
        config = deposit_filename_config or {}

    if config.get("enabled") is False:
        return fallback_deposit_filename(project_name)

    topic_override = config.get("topic")
    override_text = str(topic_override).strip() if topic_override else None

    author = author_segment(metadata, authors_config=authors_config)
    year = year_segment(metadata, release_tag)
    topic = topic_segment(metadata, topic_override=override_text)
    digest = hash_segment(pdf_sha256)

    if not author or not topic:
        return fallback_deposit_filename(project_name)

    basename = f"{author}_{year}_{topic}_{digest}"
    if len(basename) > _MAX_BASENAME:
        allowed_topic = _MAX_BASENAME - len(f"{author}_{year}_{digest}_")
        if allowed_topic < 1:
            return fallback_deposit_filename(project_name)
        topic = topic[:allowed_topic]
        basename = f"{author}_{year}_{topic}_{digest}"

    return f"{basename}.pdf"

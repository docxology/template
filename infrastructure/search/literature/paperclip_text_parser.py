"""Parse Paperclip CLI-style text blocks into paper records."""

from __future__ import annotations

import re
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.search.literature.models import Paper

logger = get_logger(__name__)

_TITLE_RE = re.compile(r"^\s*\d+\.[ \t]+(.+?)\s*$", re.MULTILINE)
_ID_TOKEN_RE = re.compile(
    r"\b((?:pmc|arxiv|doi|biorxiv|medrxiv|pmid):[A-Za-z0-9._/+-]+)\b",
    re.IGNORECASE,
)
_META_ROW_RE = re.compile(
    r"^\s+([A-Za-z0-9_.]+)\s*·\s*([^·\n]+?)\s*·\s*(\d{4})(?:-\d{2}-\d{2})?\s*$",
    re.MULTILINE,
)
_DOI_URL_RE = re.compile(r"https?://(?:dx\.)?doi\.org/(\S+)", re.IGNORECASE)
_BLOCK_RE = re.compile(r"(?=^[ \t]*\d+\.[ \t]+)", re.MULTILINE)


def parse_cli_blocks(text: str, *, source: str = "paperclip") -> list[Paper]:
    """Extract papers from Paperclip MCP textual CLI output."""
    if not text.strip():
        return []

    blocks = [b for b in _BLOCK_RE.split(text) if re.match(r"^\s*\d+\.", b)]
    out: list[Paper] = []
    for idx, block in enumerate(blocks, start=1):
        title_match = _TITLE_RE.search(block)
        if not title_match:
            continue
        title = re.sub(r"\s+", " ", title_match.group(1)).strip()
        tail = block[title_match.end() :]

        authors: list[str] = []
        for line in tail.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("http") or stripped.startswith('"'):
                break
            if " · " in stripped:
                break
            authors = [re.sub(r"\s*\*+\s*$", "", a).strip() for a in stripped.split(",") if a.strip()]
            break

        meta = _META_ROW_RE.search(tail)
        internal_id = meta.group(1) if meta else None
        venue = meta.group(2).strip() if meta else None
        year: int | None = None
        if meta:
            try:
                year = int(meta.group(3))
            except ValueError:
                year = None

        doi_match = _DOI_URL_RE.search(tail)
        doi = doi_match.group(1).rstrip(").,;") if doi_match else None

        id_token_match = _ID_TOKEN_RE.search(tail)
        if id_token_match:
            paper_id = id_token_match.group(1).lower()
        elif internal_id and internal_id.startswith(("arx_", "arxiv_")):
            arxiv_id = internal_id.split("_", 1)[1]
            paper_id = f"arxiv:{arxiv_id}"
        elif internal_id and internal_id.startswith("pmc_"):
            paper_id = f"pmc:{internal_id.split('_', 1)[1]}"
        elif internal_id and internal_id.startswith("pmid_"):
            paper_id = f"pmid:{internal_id.split('_', 1)[1]}"
        elif doi:
            paper_id = f"doi:{doi}"
        elif internal_id:
            paper_id = f"paperclip:{internal_id}"
        else:
            paper_id = f"paperclip:result_{idx}"

        abstract_match = re.search(r'"([^"]+)"', tail, re.DOTALL)
        abstract = re.sub(r"\s+", " ", abstract_match.group(1)).strip() if abstract_match else None

        url = f"https://doi.org/{doi}" if doi else None
        venue_type = None
        if venue:
            v_lower = venue.lower()
            if "arxiv" in v_lower:
                venue_type = "preprint"
            elif "biorxiv" in v_lower or "medrxiv" in v_lower:
                venue_type = "preprint"
            elif "pubmed" in v_lower or "pmc" in v_lower:
                venue_type = "journal"

        try:
            out.append(
                Paper(
                    id=paper_id,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    year=year,
                    doi=doi,
                    url=url,
                    venue=venue,
                    venue_type=venue_type,
                    source=source,
                )
            )
        except (TypeError, ValueError) as exc:  # pragma: no cover
            logger.debug("Skipping unparsable Paperclip text record: %s", exc)
    return out


def papers_from_text_content(content: list[dict[str, Any]], *, source: str = "paperclip") -> list[Paper]:
    """Join MCP content blocks and parse CLI-style records."""
    text = "\n".join(block.get("text", "") for block in content if isinstance(block, dict))
    return parse_cli_blocks(text, source=source)


__all__ = ["parse_cli_blocks", "papers_from_text_content"]

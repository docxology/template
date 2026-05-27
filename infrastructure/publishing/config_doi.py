"""Comment-preserving updates to publication.doi in manuscript config.yaml."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.exceptions import MetadataError
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing._metadata_extraction import validate_doi

logger = get_logger(__name__)

_PUBLICATION_BLOCK_RE = re.compile(
    r"(^publication:\s*\n(?:[ \t]+[^\n]+\n)*)",
    re.MULTILINE,
)
_DOI_LINE_RE = re.compile(r"^([ \t]*)doi:\s*.*$", re.MULTILINE)


def update_publication_doi(config_path: Path, doi: str, *, dry_run: bool = False) -> bool:
    """Set ``publication.doi`` in config.yaml without re-serializing the whole file.

    Args:
        config_path: Path to ``manuscript/config.yaml``.
        doi: DOI string (without ``doi:`` prefix).
        dry_run: When True, report whether a change would occur without writing.

    Returns:
        True if the file content would change (or did change), False if already set.
    """
    normalized = doi.strip()
    if not validate_doi(normalized):
        raise MetadataError(f"Invalid DOI format: {doi!r}")

    if not config_path.exists():
        raise MetadataError(f"Config file not found: {config_path}")

    original = config_path.read_text(encoding="utf-8")
    updated = _apply_doi_edit(original, normalized)

    if updated == original:
        logger.info("publication.doi already set to %s", normalized)
        return False

    if dry_run:
        logger.info("Dry run: would update publication.doi to %s", normalized)
        return True

    config_path.write_text(updated, encoding="utf-8")
    logger.info("Updated publication.doi in %s", config_path)
    return True


def _parse_doi_field_value(raw: str) -> str:
    """Extract a DOI string from a YAML ``doi:`` value fragment."""
    text = raw.strip()
    if not text or text.startswith("#"):
        return ""
    if "#" in text:
        text = text.split("#", 1)[0].strip()
    return text.strip('"').strip("'").strip()


def read_publication_doi(config_path: Path) -> str | None:
    """Return the current ``publication.doi`` value from config, if present."""
    if not config_path.exists():
        return None
    text = config_path.read_text(encoding="utf-8")
    block = _PUBLICATION_BLOCK_RE.search(text)
    if not block:
        return None
    match = _DOI_LINE_RE.search(block.group(1))
    if not match:
        return None
    value = _parse_doi_field_value(match.group(0).split(":", 1)[1])
    return value or None


def _apply_doi_edit(content: str, doi: str) -> str:
    block_match = _PUBLICATION_BLOCK_RE.search(content)
    if block_match:
        block = block_match.group(1)
        if _DOI_LINE_RE.search(block):

            def _replace_doi_line(match: re.Match[str]) -> str:
                indent = match.group(1)
                original = match.group(0)
                hash_idx = original.find("#")
                comment = (" " + original[hash_idx:].rstrip()) if hash_idx >= 0 else ""
                return f'{indent}doi: "{doi}"{comment}'

            new_block = _DOI_LINE_RE.sub(_replace_doi_line, block, count=1)
            return content[: block_match.start(1)] + new_block + content[block_match.end(1) :]
        indent = "  "
        for line in block.splitlines()[1:]:
            if line.strip() and not line.lstrip().startswith("#"):
                indent = re.match(r"^(\s*)", line).group(1)  # type: ignore[union-attr]
                break
        insertion = f'{indent}doi: "{doi}"\n'
        new_block = block.rstrip("\n") + "\n" + insertion
        return content[: block_match.start(1)] + new_block + content[block_match.end(1) :]

    suffix = f'\npublication:\n  doi: "{doi}"\n'
    if content and not content.endswith("\n"):
        return content + suffix
    return content + suffix.lstrip("\n")

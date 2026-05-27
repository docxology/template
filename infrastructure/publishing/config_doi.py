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
_VERSION_DOI_LINE_RE = re.compile(r"^([ \t]*)version_doi:\s*.*$", re.MULTILINE)
_VERSION_RECORD_LINE_RE = re.compile(r"^([ \t]*)version_record:\s*.*$", re.MULTILINE)


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


def read_publication_version_doi(config_path: Path) -> str | None:
    """Return ``publication.version_doi`` when the split Zenodo DOI layout is used."""
    if not config_path.exists():
        return None
    text = config_path.read_text(encoding="utf-8")
    block = _PUBLICATION_BLOCK_RE.search(text)
    if not block:
        return None
    match = _VERSION_DOI_LINE_RE.search(block.group(1))
    if not match:
        return None
    value = _parse_doi_field_value(match.group(0).split(":", 1)[1])
    return value or None


def uses_split_zenodo_doi_fields(config_path: Path) -> bool:
    """True when ``publication.version_doi`` is declared (concept DOI stays in ``doi``)."""
    if not config_path.exists():
        return False
    block = _PUBLICATION_BLOCK_RE.search(config_path.read_text(encoding="utf-8"))
    return bool(block and _VERSION_DOI_LINE_RE.search(block.group(1)))


def zenodo_record_url_for_doi(doi: str) -> str:
    """Map ``10.5281/zenodo.<id>`` to the public Zenodo record URL."""
    normalized = doi.strip()
    if not validate_doi(normalized):
        raise MetadataError(f"Invalid DOI format: {doi!r}")
    record_id = normalized.rsplit(".", maxsplit=1)[-1]
    return f"https://zenodo.org/records/{record_id}"


def update_publication_version_doi(
    config_path: Path,
    version_doi: str,
    *,
    version_record: str | None = None,
    dry_run: bool = False,
) -> bool:
    """Set ``publication.version_doi`` (and ``version_record``) without touching ``publication.doi``."""
    normalized = version_doi.strip()
    if not validate_doi(normalized):
        raise MetadataError(f"Invalid DOI format: {version_doi!r}")

    if not config_path.exists():
        raise MetadataError(f"Config file not found: {config_path}")

    record_url = version_record or zenodo_record_url_for_doi(normalized)
    original = config_path.read_text(encoding="utf-8")
    updated = _apply_version_doi_edit(original, normalized, record_url)

    if updated == original:
        logger.info("publication.version_doi already set to %s", normalized)
        return False

    if dry_run:
        logger.info("Dry run: would update publication.version_doi to %s", normalized)
        return True

    config_path.write_text(updated, encoding="utf-8")
    logger.info("Updated publication.version_doi in %s", config_path)
    return True


def update_publication_after_zenodo_deposit(
    config_path: Path,
    deposited_doi: str,
    *,
    dry_run: bool = False,
) -> bool:
    """Write a new Zenodo version DOI without overwriting a stable concept DOI."""
    if uses_split_zenodo_doi_fields(config_path):
        return update_publication_version_doi(config_path, deposited_doi, dry_run=dry_run)
    return update_publication_doi(config_path, deposited_doi, dry_run=dry_run)


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


def _replace_yaml_line(match: re.Match[str], *, key: str, value: str) -> str:
    indent = match.group(1)
    original = match.group(0)
    hash_idx = original.find("#")
    comment = (" " + original[hash_idx:].rstrip()) if hash_idx >= 0 else ""
    return f'{indent}{key}: "{value}"{comment}'


def _apply_version_doi_edit(content: str, version_doi: str, version_record: str) -> str:
    block_match = _PUBLICATION_BLOCK_RE.search(content)
    if not block_match:
        raise MetadataError("publication block not found for version_doi update")

    block = block_match.group(1)
    indent = "  "
    for line in block.splitlines()[1:]:
        if line.strip() and not line.lstrip().startswith("#"):
            indent = re.match(r"^(\s*)", line).group(1)  # type: ignore[union-attr]
            break

    if _VERSION_DOI_LINE_RE.search(block):
        block = _VERSION_DOI_LINE_RE.sub(
            lambda match: _replace_yaml_line(match, key="version_doi", value=version_doi),
            block,
            count=1,
        )
    else:
        block = block.rstrip("\n") + f'\n{indent}version_doi: "{version_doi}"\n'

    if _VERSION_RECORD_LINE_RE.search(block):
        block = _VERSION_RECORD_LINE_RE.sub(
            lambda match: _replace_yaml_line(match, key="version_record", value=version_record),
            block,
            count=1,
        )
    else:
        block = block.rstrip("\n") + f'\n{indent}version_record: "{version_record}"\n'

    return content[: block_match.start(1)] + block + content[block_match.end(1) :]

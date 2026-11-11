"""Shared symbol collection and cross-reference resolution for manuscripts."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.content.markdown_strip import strip_fences

logger = get_logger(__name__)

EQ_LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")
ANCHOR_PATTERN = re.compile(r"\{#([^}]+)\}")
REF_PATTERN = re.compile(r"\\ref\{([^}]+)\}")
EQREF_PATTERN = re.compile(r"\\eqref\{([^}]+)\}")

_PREFIX_TO_KEY = {
    "eq:": "equations",
    "fig:": "figures",
    "tab:": "tables",
    "sec:": "sections",
    "cite:": "citations",
    "ref:": "citations",
}


def collect_symbols(md_paths: list[str]) -> tuple[set[str], set[str]]:
    """Collect equation labels and section anchors from markdown files."""
    labels: set[str] = set()
    anchors: set[str] = set()
    for path in md_paths:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        labels.update(EQ_LABEL_PATTERN.findall(text))
        anchors.update(ANCHOR_PATTERN.findall(text))
        body = strip_fences(text)
        for raw_heading in re.findall(r"(?m)^#{1,6}[ \t]+(.+?)[ \t]*$", body):
            heading = re.sub(r"\s*\{#[^}]+\}\s*$", "", raw_heading).strip()
            slug = re.sub(r"[^\w\s-]", "", heading.lower())
            slug = re.sub(r"\s+", "-", slug).strip("-")
            if slug:
                anchors.add(slug)
    return labels, anchors


def collect_latex_labels(content: str) -> set[str]:
    """Collect LaTeX and markdown-style labels from one document."""
    labels = set(EQ_LABEL_PATTERN.findall(content))
    labels.update(ANCHOR_PATTERN.findall(content))
    return labels


def collect_latex_references(content: str) -> set[str]:
    """Collect LaTeX-style references from one document."""
    refs = set(REF_PATTERN.findall(content))
    refs.update(EQREF_PATTERN.findall(content))
    return refs


def resolve_cross_reference_integrity(
    markdown_files: list[Path],
) -> dict[str, bool]:
    """Verify cross-reference integrity across markdown files."""
    integrity: dict[str, bool] = {
        "equations": True,
        "figures": True,
        "tables": True,
        "sections": True,
        "citations": True,
        "scan_healthy": True,
    }

    labels: set[str] = set()
    references: set[str] = set()
    scan_error_count = 0

    for md_file in markdown_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            labels.update(collect_latex_labels(content))
            references.update(collect_latex_references(content))
        except OSError as exc:
            logger.error("Error reading %s: %s", md_file, exc)
            scan_error_count += 1

    if scan_error_count > 0:
        integrity["scan_healthy"] = False

    missing_labels = references - labels
    if missing_labels:
        logger.warning("Missing labels for references: %s", missing_labels)
        for ref in missing_labels:
            matched = False
            for prefix, key in _PREFIX_TO_KEY.items():
                if ref.startswith(prefix):
                    integrity[key] = False
                    matched = True
                    break
            if not matched:
                logger.debug("Unresolved reference with unknown prefix: %s", ref)
    else:
        logger.debug("Found %d labels and %d references", len(labels), len(references))

    return integrity


__all__ = [
    "ANCHOR_PATTERN",
    "EQ_LABEL_PATTERN",
    "collect_latex_labels",
    "collect_latex_references",
    "collect_symbols",
    "resolve_cross_reference_integrity",
]

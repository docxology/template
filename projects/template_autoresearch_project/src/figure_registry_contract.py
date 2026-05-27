"""Registry-level figure caption and method contracts."""

from __future__ import annotations

from typing import Any

from .figure_specs import FIGURE_METHODS

FIGURE_VALIDATION_NOTE = (
    "Registry metadata records the generation method, source artifact, and claim boundary for validation."
)


def finalize_figure_registry(records: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    """Add method and validation metadata to figure registry records."""
    for label, record in records.items():
        method = figure_method(label)
        record["caption"] = caption_with_contract(str(record.get("caption", "")), method)
        metadata = _metadata(record)
        metadata["method"] = method
        metadata["validated_by"] = (
            "Stage 04 output validation, figure registry validation, and AutoResearch readiness validation."
        )
        record["metadata"] = metadata
    return records


def caption_with_contract(caption: str, method: str) -> str:
    """Attach the method sentence and common figure-validation phrase to a caption."""
    if FIGURE_VALIDATION_NOTE in caption:
        return caption
    return f"{caption} Generation method: {method} {FIGURE_VALIDATION_NOTE}"


def figure_method(label: str) -> str:
    """Return the concise generation method for a figure label."""
    return FIGURE_METHODS.get(label, "Registered deterministic figure generated from local artifacts.")


def _metadata(record: dict[str, object]) -> dict[str, Any]:
    metadata = record.get("metadata")
    return metadata if isinstance(metadata, dict) else {}

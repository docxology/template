"""Figure registry metadata for generated AutoResearch figures."""

from __future__ import annotations

from .figure_registry_captions import build_figure_registry_captions
from .figure_registry_contract import finalize_figure_registry
from .figure_registry_records import build_figure_registry_records
from src.ml.task import MLTaskResult
from src.models import AutoResearchLoopResult


def figure_registry_payload(
    result: AutoResearchLoopResult | None = None,
    ml_result: MLTaskResult | None = None,
) -> dict[str, dict[str, object]]:
    """Return figure registry metadata for generated AutoResearch figures."""
    captions = build_figure_registry_captions(result, ml_result)
    records = build_figure_registry_records(captions)
    return finalize_figure_registry(records)

"""Project-owned provenance metadata for methods-paper figures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MethodsFigureSpec:
    """Registry contract for one generated methods-paper figure."""

    label: str
    filename: str
    caption: str
    generated_by: str


FIGURE_REGISTRY_SCHEMA = "template-methods-paper-figure-registry-v1"
METHODS_FIGURE_SPECS: tuple[MethodsFigureSpec, ...] = (
    MethodsFigureSpec(
        label="fig:step_counts",
        filename="step_counts.png",
        caption="Step counts for each deterministically compiled example method.",
        generated_by="scripts.methods_analysis.run_methods_analysis",
    ),
)


__all__ = ["FIGURE_REGISTRY_SCHEMA", "METHODS_FIGURE_SPECS", "MethodsFigureSpec"]

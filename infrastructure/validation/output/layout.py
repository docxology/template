"""Shared output directory layout constants for validation."""

from __future__ import annotations

OUTPUT_SUBDIR_NAMES: tuple[str, ...] = (
    "pdf",
    "web",
    "slides",
    "figures",
    "data",
    "reports",
    "simulations",
    "llm",
    "logs",
)

OPTIONAL_OUTPUT_SUBDIRS: frozenset[str] = frozenset({"llm", "logs", "simulations"})

__all__ = ["OPTIONAL_OUTPUT_SUBDIRS", "OUTPUT_SUBDIR_NAMES"]

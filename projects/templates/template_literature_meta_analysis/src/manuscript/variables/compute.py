"""Merge registered extractors into the final variable map."""

from __future__ import annotations

from pathlib import Path

from manuscript.variables._logging import logger
from manuscript.variables.context import ExtractContext
from manuscript.variables.io import load_config
from manuscript.variables.registry import EXTRACTORS


def compute_variables(output_dir: Path) -> dict[str, str]:
    """Process compute variables."""
    cfg = load_config(output_dir.parent)
    ctx = ExtractContext.from_output_dir(output_dir, cfg)
    variables: dict[str, str] = {}
    for extractor in EXTRACTORS:
        variables.update(extractor(ctx))
    logger.info("Computed %d template variables from pipeline output", len(variables))
    return variables

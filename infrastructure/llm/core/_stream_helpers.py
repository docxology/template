"""Streaming helper utilities for LLM client.

Provides the partial-response save helper and the TIMEOUT_WARNING_FRACTION constant
used by streaming queries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import requests

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# Issue a one-time warning when elapsed time crosses this fraction of the configured timeout.
# Gives callers early notice that a slow model may hit the timeout.
TIMEOUT_WARNING_FRACTION = 0.3


def try_save_partial(
    full_response: list[str],
    save_response: bool,
    partial_saved: bool,
    save_streaming_state_fn: Callable[..., bool],
    save_path: Path | None,
    model_name: str,
    prompt: str,
    chunk_count: int,
    start_time: float,
    context: str,
    skip_if_already_saved: bool = True,
) -> bool:
    """Try to save a partial streaming response; returns new partial_saved state.

    Parameters split into three groups:
    - Guards: full_response, save_response, partial_saved, skip_if_already_saved
    - Callback: save_streaming_state_fn (and save_path, model_name, prompt, chunk_count,
      start_time which are forwarded verbatim to it)
    - Logging: context (used in the info message on success)
    """
    if not (full_response and save_response):
        return partial_saved
    if skip_if_already_saved and partial_saved:
        return partial_saved
    if save_streaming_state_fn(full_response, save_path, model_name, prompt, chunk_count, start_time, is_error=True):
        logger.info(f"Saved partial response ({chunk_count} chunks) {context}")
        return True
    return partial_saved

"""Streaming helper utilities for LLM client.

Provides the partial-response save helper, the TIMEOUT_WARNING_FRACTION constant,
and the requests re-export (guarded so missing requests surfaces a clear error).
"""

from __future__ import annotations

from typing import Callable

from infrastructure.core.logging.utils import get_logger

try:
    import requests  # noqa: F401 — re-exported for _stream_impl.py
except ImportError as _err:
    raise ImportError(
        "The 'requests' package is required to use LLM streaming features. "
        "Install it with: pip install requests  (or: pip install template[llm])"
    ) from _err

logger = get_logger(__name__)

# Issue a one-time warning when elapsed time crosses this fraction of the configured timeout.
# Gives callers early notice that a slow model may hit the timeout.
TIMEOUT_WARNING_FRACTION = 0.3


def try_save_partial(
    full_response: list[str],
    save_response: bool,
    partial_saved: bool,
    save_fn: Callable[..., bool],
    chunk_count: int,
    context: str,
    skip_if_already_saved: bool = True,
) -> bool:
    """Try to save a partial streaming response; returns new partial_saved state.

    Parameters split into three groups:
    - Guards: full_response, save_response, partial_saved, skip_if_already_saved
    - Callback: save_fn — a pre-bound callable accepting (full_response, chunk_count).
      Stable per-request params (save_path, model_name, prompt, start_time) must be
      pre-bound at the call site before passing save_fn here.
    - Logging: context (used in the info message on success)
    """
    if not (full_response and save_response):
        return partial_saved
    if skip_if_already_saved and partial_saved:
        return partial_saved
    if save_fn(full_response, chunk_count, is_error=True):
        logger.info(f"Saved partial response ({chunk_count} chunks) {context}")
        return True
    return partial_saved

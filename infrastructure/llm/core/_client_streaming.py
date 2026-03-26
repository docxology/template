"""Streaming query implementation extracted from LLMClient.

Module-level functions that handle streaming LLM responses with retry logic,
progress tracking, and error recovery. Called by LLMClient's thin wrapper methods.

Implementation is split across focused submodules:
- ``_stream_helpers``: Partial-save helper, requests stub, timeout constant
- ``_stream_impl``: Main stream_query_impl generator
"""

from __future__ import annotations

# Re-export public API so all existing imports continue to work
from infrastructure.llm.core._stream_helpers import (  # noqa: F401
    TIMEOUT_WARNING_FRACTION as _TIMEOUT_WARNING_FRACTION,
    try_save_partial as _try_save_partial,
)
from infrastructure.llm.core._stream_impl import stream_query_impl  # noqa: F401

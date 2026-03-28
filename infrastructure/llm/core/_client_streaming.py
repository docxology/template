"""Streaming query implementation extracted from LLMClient.

Module-level functions that handle streaming LLM responses with retry logic,
progress tracking, and error recovery. Called by LLMClient's thin wrapper methods.

Implementation is split across focused submodules:
- ``_stream_helpers``: Partial-save helper, requests stub, timeout constant
- ``_stream_impl``: Main stream_query_impl generator

Callers should import directly from the submodule:
    from infrastructure.llm.core._stream_impl import stream_query_impl
"""

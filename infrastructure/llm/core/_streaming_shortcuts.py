"""Short and long streaming convenience wrappers.

Thin wrappers around stream_query_impl that apply standard instructions
and token limits for short/long response modes.
Extracted from _client_streaming.py for file-size health.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator

from infrastructure.llm.core._client_streaming import stream_query_impl
from infrastructure.llm.core.config import GenerationOptions, OllamaClientConfig
from infrastructure.llm.core.context import ConversationContext
from infrastructure.llm.core.sanitization import sanitize_llm_input


def stream_short_impl(
    config: OllamaClientConfig,
    context: ConversationContext,
    save_streaming_state_fn: Callable[..., bool],
    prompt: str,
    model: str | None = None,
    options: GenerationOptions | None = None,
    save_response: bool = False,
    save_path: Path | None = None,
    log_progress: bool = True,
    retries: int = 1,
) -> Iterator[str]:
    """Stream a concise response (≤150 words) with standard logging.

    Same parameters as stream_long_impl but uses short_max_tokens and a brevity instruction.
    Yields response chunks.
    """
    prompt = sanitize_llm_input(prompt)
    short_options = GenerationOptions(
        max_tokens=config.short_max_tokens,
        temperature=options.temperature if options else None,
        seed=options.seed if options else None,
    )
    instruction = (
        "Provide a concise, brief response (less than 150 words). "
        "Be direct and to the point.\n\n"
    )
    yield from stream_query_impl(
        config,
        context,
        save_streaming_state_fn,
        instruction + prompt,
        model,
        options=short_options,
        save_response=save_response,
        save_path=save_path,
        log_progress=log_progress,
        retries=retries,
    )


def stream_long_impl(
    config: OllamaClientConfig,
    context: ConversationContext,
    save_streaming_state_fn: Callable[..., bool],
    prompt: str,
    model: str | None = None,
    options: GenerationOptions | None = None,
    save_response: bool = False,
    save_path: Path | None = None,
    log_progress: bool = True,
    retries: int = 1,
) -> Iterator[str]:
    """Stream a comprehensive, detailed response with standard logging.

    Same parameters as stream_short_impl but uses long_max_tokens and a thoroughness instruction.
    Yields response chunks.
    """
    prompt = sanitize_llm_input(prompt)
    long_options = GenerationOptions(
        max_tokens=config.long_max_tokens,
        temperature=options.temperature if options else None,
        seed=options.seed if options else None,
    )
    instruction = (
        "Provide a comprehensive, detailed response with examples and "
        "thorough explanation. Use multiple paragraphs if needed.\n\n"
    )
    yield from stream_query_impl(
        config,
        context,
        save_streaming_state_fn,
        instruction + prompt,
        model,
        options=long_options,
        save_response=save_response,
        save_path=save_path,
        log_progress=log_progress,
        retries=retries,
    )

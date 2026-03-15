"""Streaming query implementation extracted from LLMClient.

Module-level functions that handle streaming LLM responses with retry logic,
progress tracking, and error recovery. Called by LLMClient's thin wrapper methods.
"""

from __future__ import annotations

import json
import time as time_module
from pathlib import Path
from typing import Any, Callable, Iterator

from infrastructure.core.exceptions import LLMConnectionError
from infrastructure.core.logging_utils import get_logger
from infrastructure.llm.core._text_utils import strip_thinking_tags
from infrastructure.llm.core.config import GenerationOptions, OllamaClientConfig
from infrastructure.llm.core.context import ConversationContext


logger = get_logger(__name__)


def _try_save_partial(
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
    """Try to save a partial streaming response; returns new partial_saved state."""
    if not (full_response and save_response):
        return partial_saved
    if skip_if_already_saved and partial_saved:
        return partial_saved
    if save_streaming_state_fn(full_response, save_path, model_name, prompt, chunk_count, start_time, is_error=True):
        logger.info(f"Saved partial response ({chunk_count} chunks) {context}")
        return True
    return partial_saved

# Lazy import to match client.py pattern
try:
    import requests
except ImportError as _import_err:
    _requests_import_error = _import_err

    class _RequestsStub:
        """Raises ImportError with clear message on any attribute access."""

        def __getattr__(self, name: str) -> Any:
            raise ImportError(
                "LLM streaming requires the 'requests' package: pip install requests"
            ) from _requests_import_error

    requests = _RequestsStub()  # type: ignore[assignment]


def stream_query_impl(
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
    """Stream response from LLM with comprehensive logging and error recovery.

    Yields response chunks as they arrive for real-time display.

    Args:
        config: LLM configuration
        context: Conversation context for message history
        save_streaming_state_fn: Callback to save partial/final streaming state
        prompt: User prompt
        model: Model to use
        options: Generation options
        save_response: Whether to save response to file
        save_path: Path to save response (auto-generated if None and save_response=True)
        log_progress: Whether to log streaming progress (DEBUG level)
        retries: Number of retry attempts on transient failures

    Yields:
        Response text chunks
    """
    start_time = time_module.time()
    model_name = model or config.default_model
    logger.debug("Starting streaming query model=%s", model_name)

    context.add_message("user", prompt)
    url = f"{config.base_url}/api/chat"

    opts = options or GenerationOptions()
    ollama_options = opts.to_ollama_options(config)

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": context.get_messages(),
        "stream": True,
        "options": ollama_options,
    }

    if opts.format_json:
        payload["format"] = "json"

    full_response: list[str] = []
    chunk_count = 0
    first_chunk_time = None
    last_chunk_time = None
    error_count = 0
    partial_saved = False
    _timeout_warned = False
    last_error = ""

    # Initialize metrics (imported locally to avoid circular import with review.metrics)
    from infrastructure.llm.review.metrics import StreamingMetrics  # noqa: PLC0415

    metrics = StreamingMetrics()

    for attempt in range(retries + 1):
        try:
            if attempt > 0:
                wait_time = min((attempt + 1) * 1.0, 5.0)
                logger.debug(
                    f"Retrying streaming request (attempt {attempt + 1}/{retries + 1}) after {wait_time}s..."  # noqa: E501
                )
                time_module.sleep(wait_time)

            with requests.post(
                url, json=payload, stream=True, timeout=config.timeout
            ) as r:
                r.raise_for_status()

                for line in r.iter_lines():
                    current_time = time_module.time()

                    # Note: Early warning is handled by StreamHeartbeatMonitor in review/translation scripts  # noqa: E501
                    # This avoids duplicate warnings. Stall detection after first token is handled below.  # noqa: E501

                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("message", {}).get("content", "")

                            if chunk:
                                chunk_count += 1
                                full_response.append(chunk)

                                # Track timing
                                if first_chunk_time is None:
                                    first_chunk_time = current_time
                                    metrics.first_chunk_time = current_time - start_time
                                    logger.debug(
                                        f"First chunk received after {metrics.first_chunk_time:.2f}s",  # noqa: E501
                                        extra={"chunk_count": chunk_count},
                                    )

                                prev_chunk_time = last_chunk_time
                                last_chunk_time = current_time

                                # Check for stalled stream (configurable threshold)
                                if (
                                    prev_chunk_time is not None
                                    and (current_time - prev_chunk_time)
                                    > config.stall_threshold
                                ):
                                    time_since_last_chunk = current_time - prev_chunk_time
                                    logger.warning(
                                        f"Streaming stalled: no tokens received for {time_since_last_chunk:.1f}s",  # noqa: E501
                                        extra={
                                            "model": model_name,
                                            "time_since_last_chunk": time_since_last_chunk,
                                            "stall_threshold": config.stall_threshold,
                                            "total_elapsed": current_time - start_time,
                                            "timeout_remaining": max(
                                                0,
                                                config.timeout
                                                - (current_time - start_time),
                                            ),
                                            "token_count": chunk_count,
                                        },
                                    )

                                yield chunk

                                # Log timeout remaining when approaching limit (warn once only)
                                elapsed = current_time - start_time
                                if (
                                    not _timeout_warned
                                    and elapsed > config.timeout * 0.3
                                ):
                                    remaining = config.timeout - elapsed
                                    if remaining > 0:
                                        _timeout_warned = True
                                        logger.info(
                                            f"Streaming timeout warning: {remaining:.1f}s remaining",  # noqa: E501
                                            extra={
                                                "model": model_name,
                                                "elapsed": elapsed,
                                                "timeout": config.timeout,
                                                "remaining": remaining,
                                                "progress": f"{chunk_count} chunks, {sum(len(c) for c in full_response)} chars",  # noqa: E501
                                            },
                                        )

                        except json.JSONDecodeError as e:
                            logger.warning(
                                f"Failed to parse streaming chunk: {e}",
                                extra={"line": line[:100]},
                            )
                            error_count += 1
                            metrics.error_count = error_count
                            continue

            # Success - break retry loop
            break

        except requests.exceptions.Timeout as e:
            error_count += 1
            metrics.error_count = error_count
            last_error = f"Timeout after {config.timeout}s"

            if attempt < retries:
                logger.debug(
                    f"Streaming timeout (attempt {attempt + 1}/{retries + 1}), will retry..."
                )
                # Save partial response before retry
                partial_saved = _try_save_partial(
                    full_response, save_response, partial_saved, save_streaming_state_fn,
                    save_path, model_name, prompt, chunk_count, start_time, "before retry",
                )
                continue
            else:
                logger.error(f"Streaming timeout after {retries + 1} attempts: {last_error}")
                # Save partial response on final failure
                partial_saved = _try_save_partial(
                    full_response, save_response, partial_saved, save_streaming_state_fn,
                    save_path, model_name, prompt, chunk_count, start_time, "after timeout",
                    skip_if_already_saved=False,
                )
                raise LLMConnectionError(
                    f"Streaming timeout ({model_name}): {last_error}",
                    context={
                        "url": url,
                        "model": model_name,
                        "chunks_received": chunk_count,
                    },
                ) from e

        except requests.exceptions.ConnectionError as e:
            error_count += 1
            metrics.error_count = error_count
            last_error = f"Connection error: {e}"

            if attempt < retries:
                logger.debug(
                    f"Streaming connection error (attempt {attempt + 1}/{retries + 1}), will retry..."  # noqa: E501
                )
                # Save partial response before retry
                partial_saved = _try_save_partial(
                    full_response, save_response, partial_saved, save_streaming_state_fn,
                    save_path, model_name, prompt, chunk_count, start_time, "before retry",
                )
                continue
            else:
                logger.error(
                    f"Streaming connection error after {retries + 1} attempts: {last_error}"
                )
                # Save partial response on final failure
                partial_saved = _try_save_partial(
                    full_response, save_response, partial_saved, save_streaming_state_fn,
                    save_path, model_name, prompt, chunk_count, start_time, "after connection error",
                    skip_if_already_saved=False,
                )
                raise LLMConnectionError(
                    f"Streaming connection failed ({model_name}): {last_error}",
                    context={
                        "url": url,
                        "model": model_name,
                        "chunks_received": chunk_count,
                    },
                ) from e

        except requests.exceptions.RequestException as e:
            error_count += 1
            metrics.error_count = error_count
            logger.error(f"Streaming request error ({model_name}): {e}")
            raise LLMConnectionError(
                f"Stream failed ({model_name}): {e}",
                context={
                    "url": url,
                    "model": model_name,
                    "chunks_received": chunk_count,
                },
            ) from e

    # Calculate final metrics
    end_time = time_module.time()
    streaming_time = end_time - start_time
    full_response_text = strip_thinking_tags("".join(full_response))
    total_chars = len(full_response_text)
    total_tokens_est = total_chars // 4

    metrics.chunk_count = chunk_count
    metrics.total_chars = total_chars
    metrics.total_tokens_est = total_tokens_est
    metrics.streaming_time_seconds = streaming_time
    metrics.chunks_per_second = chunk_count / streaming_time if streaming_time > 0 else 0.0
    metrics.bytes_per_second = total_chars / streaming_time if streaming_time > 0 else 0.0
    metrics.error_count = error_count
    metrics.partial_response_saved = partial_saved
    if last_chunk_time:
        metrics.last_chunk_time = last_chunk_time - start_time

    # Add full response to context
    context.add_message("assistant", full_response_text)

    # Save response if requested
    if save_response and not partial_saved:
        if save_streaming_state_fn(full_response, save_path, model_name, prompt, chunk_count, start_time, is_error=error_count > 0, options=options):
            logger.info("Saved final streaming response")



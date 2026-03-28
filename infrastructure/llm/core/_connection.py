"""Connection checking and low-level HTTP generation for LLMClient.

Extracted from client.py to keep each module under 300 LOC.
These are mixed into LLMClient via _ConnectionMixin.
"""

from __future__ import annotations

import time as time_module
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    import requests
except ImportError as _err:
    raise ImportError(
        "The 'requests' package is required to use LLM features. "
        "Install it with: pip install requests  (or: uv sync --group llm)"
    ) from _err

from infrastructure.core.exceptions import LLMConnectionError
from infrastructure.core.logging.utils import get_logger
from infrastructure.llm.core._text_utils import strip_thinking_tags
from infrastructure.llm.core.config import GenerationOptions

if TYPE_CHECKING:
    from infrastructure.llm.core.config import OllamaClientConfig

logger = get_logger(__name__)


class _ConnectionMixin:
    """Mixin providing connection checks, model listing, and low-level HTTP generation.

    Expects the host class to provide:
    - self.config: OllamaClientConfig
    """

    config: OllamaClientConfig

    def _generate_response_direct(
        self,
        model: str,
        messages: list[dict[str, Any]],
        options: GenerationOptions | None = None,
        retries: int = 1,
    ) -> str:
        """Generate response from Ollama API with direct messages and retry logic.

        Args:
            model: Model name
            messages: List of message dicts
            options: Generation options
            retries: Number of retry attempts on transient failures

        Returns:
            Generated text

        Raises:
            LLMConnectionError: If connection fails after retries
        """
        url = f"{self.config.base_url}/api/chat"

        # Build options dict
        opts = options or GenerationOptions()
        ollama_options = opts.to_ollama_options(self.config)

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": ollama_options,
        }

        # Add format for native JSON mode
        if opts.format_json:
            payload["format"] = "json"

        last_error: str = ""  # accumulates last failure reason across retry attempts

        logger.debug(
            "Sending request to Ollama",
            extra={
                "model": model,
                "message_count": len(messages),
                "url": url,
            },
        )

        for attempt in range(retries + 1):
            try:
                if attempt > 0:
                    wait_time = min((attempt + 1) * 1.0, 5.0)  # Max 5s wait
                    logger.debug(
                        f"Retrying request (attempt {attempt + 1}/{retries + 1}) after {wait_time}s..."  # noqa: E501
                    )
                    time_module.sleep(wait_time)

                response = requests.post(url, json=payload, timeout=self.config.timeout)
                response.raise_for_status()

                data = response.json()
                content = data.get("message", {}).get("content", "")

                if not content:
                    # Check if there's an error in the response before stripping
                    if "error" in data:
                        error_msg = data.get("error", "Unknown error")
                        raise LLMConnectionError(
                            f"Ollama returned error ({model}): {error_msg}",
                            context={"url": url, "model": model, "response": data},
                        )
                    logger.warning(f"Empty response from Ollama ({model}); will proceed to strip phase")

                # Strip thinking tags if present (e.g., from Qwen models)
                content = strip_thinking_tags(content)

                if not content:
                    # Content was either empty before stripping or was entirely <think> tags
                    logger.warning(
                        "Response is empty after stripping thinking tags; "
                        "model may have returned only <think> content or an empty body"
                    )
                    raise LLMConnectionError(
                        "Model response was empty after stripping thinking tags",
                        context={"model": model, "url": url},
                    )

                if attempt > 0:
                    logger.info(f"Request succeeded on retry {attempt + 1}")

                return content

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout after {self.config.timeout}s"
                if attempt < retries:
                    logger.debug(
                        f"Request timeout (attempt {attempt + 1}/{retries + 1}), will retry..."
                    )
                    continue
                else:
                    logger.error(f"Request timeout after {retries + 1} attempts: {last_error}")
                    raise LLMConnectionError(
                        f"Ollama request timeout ({model}): {last_error}",
                        context={
                            "url": url,
                            "model": model,
                            "timeout": self.config.timeout,
                        },
                    ) from e

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                if attempt < retries:
                    logger.debug(
                        f"Connection error (attempt {attempt + 1}/{retries + 1}), will retry..."
                    )
                    continue
                else:
                    logger.error(f"Connection error after {retries + 1} attempts: {last_error}")
                    raise LLMConnectionError(
                        f"Failed to connect to Ollama ({model}): {last_error}",
                        context={"url": url, "model": model},
                    ) from e

            except requests.exceptions.HTTPError as e:
                # Don't retry HTTP errors (4xx, 5xx) - they're not transient.
                # response is always defined here: raise_for_status() requires a response object.
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error(f"HTTP error from Ollama ({model}): {error_msg}")
                raise LLMConnectionError(
                    f"Ollama HTTP error ({model}): {error_msg}",
                    context={
                        "url": url,
                        "model": model,
                        "status_code": response.status_code,
                    },
                ) from e

            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {e}"
                logger.error(f"Request error from Ollama ({model}): {last_error}")
                raise LLMConnectionError(
                    f"Failed to connect to Ollama ({model}): {last_error}",
                    context={"url": url, "model": model},
                ) from e

        # Unreachable: all loop paths either return or raise. Here for type-checker completeness.
        raise RuntimeError(f"Retry loop exited unexpectedly for model {model!r}")

    def _save_streaming_state(
        self,
        full_response: list[str],
        save_path: Path | None,
        model_name: str,
        prompt: str,
        chunk_count: int,
        start_time: float,
        is_error: bool = False,
        options: GenerationOptions | None = None,
    ) -> bool:
        """Save partial or final streaming response and metadata."""
        from infrastructure.llm.core.response_saver import ResponseMetadata, save_streaming_response

        try:
            text = "".join(full_response)
            if save_path is None:
                suffix = "partial_" if is_error else ""
                save_path = Path(f"streaming_response_{suffix}{int(time_module.time())}.md")

            metadata = ResponseMetadata(
                timestamp=datetime.now().isoformat(),
                model=model_name,
                prompt=prompt,
                prompt_length=len(prompt),
                response_length=len(text),
                response_tokens_est=len(text) // 4,
                streaming=True,
                chunk_count=chunk_count,
                streaming_time_seconds=time_module.time() - start_time,
                error_occurred=is_error,
                partial_response=is_error,
            )
            if options and not is_error:
                metadata.options = {
                    "temperature": options.temperature,
                    "max_tokens": options.max_tokens,
                    "seed": options.seed,
                }
            save_streaming_response(text, save_path, metadata)
            return True
        except (OSError, ValueError) as e:
            logger.warning(f"Failed to save streaming response: {e}")
            return False

    def get_available_models(self) -> list[str]:
        """Get list of available models from Ollama.

        Returns:
            List of model names (deduplicated, version tags stripped).
            Falls back to ``config.fallback_models`` if the Ollama server is
            unreachable or returns a non-200 response. The fallback list is
            never empty — callers can always rely on at least one model name
            being present in the return value.
        """
        url = f"{self.config.base_url}/api/tags"
        try:
            response = requests.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            data = response.json()
            models = [m["name"].split(":")[0] for m in data.get("models", [])]
            return list(set(models))  # Remove duplicates
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch available models: {e}")
            return self.config.fallback_models

    def check_connection(self, timeout: float = 2.0) -> bool:
        """Return True if the Ollama server is reachable.

        Use check_connection_with_reason() when you also need the failure reason string.
        """
        is_available, _ = self.check_connection_with_reason(timeout=timeout)
        return is_available

    def check_connection_with_reason(self, timeout: float = 2.0) -> tuple[bool, str | None]:
        """Return (is_available, error_message) for the Ollama server.

        Alias: check_connection_detailed() delegates here for backwards compatibility.
        """
        try:
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=timeout)
            if response.status_code == 200:
                logger.debug(f"Ollama connection check successful at {self.config.base_url}")
                return (True, None)
            error_msg = f"HTTP {response.status_code}"
            logger.warning(f"Ollama connection check failed: {error_msg}")
            return (False, error_msg)
        except requests.exceptions.Timeout:
            error_msg = f"Timeout after {timeout}s"
            logger.debug(f"Ollama connection check timeout: {error_msg}")
            return (False, error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {e}"
            logger.debug(f"Ollama connection check failed: {error_msg}")
            return (False, error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            logger.warning(f"Ollama connection check failed: {error_msg}")
            return (False, error_msg)

    def check_connection_detailed(self, timeout: float = 2.0) -> tuple[bool, str | None]:
        """Return (is_available, error_message) for the Ollama server.

        Use check_connection() when only the boolean result is needed.
        Backwards-compat alias for check_connection_with_reason().
        """
        return self.check_connection_with_reason(timeout=timeout)

"""Core logic for LLM module.

Provides LLMClient for interacting with Ollama local LLMs with:
- Multiple response modes (short, long, structured)
- Streaming and non-streaming queries
- Per-query generation options
- Context management with system prompt injection
- Template support for research tasks
"""

from __future__ import annotations

import dataclasses
import json
import time as time_module
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar, cast

_T = TypeVar("_T")

try:
    import requests
except ImportError as _requests_import_error:
    raise ImportError(
        "The 'requests' package is required for LLM connectivity. "
        "Install it with: pip install requests"
    ) from _requests_import_error

from infrastructure.core.exceptions import LLMConnectionError, LLMError
from infrastructure.core.logging_utils import get_logger
from infrastructure.llm.core._text_utils import strip_thinking_tags
from infrastructure.llm.core.config import GenerationOptions, OllamaClientConfig, ResponseMode
from infrastructure.llm.core.context import ConversationContext
from infrastructure.llm.core.sanitization import sanitize_llm_input
from infrastructure.llm.templates import get_template

logger = get_logger(__name__)

# Try to import prompt system for system prompt loading
try:
    from infrastructure.llm.prompts.loader import get_default_loader

    PROMPT_LOADER_AVAILABLE = True
except ImportError:
    PROMPT_LOADER_AVAILABLE = False

# ResponseMode is defined in config.py (alongside GenerationOptions) to avoid
# a validation→client import cycle. Re-exported here for backwards compatibility.
__all__ = ["LLMClient", "ResponseMode"]


class LLMClient:
    """Client for interacting with LLM providers (Ollama).

    Manages conversation context, system prompt injection, and provides
    both blocking and streaming query variants. All inputs are sanitized
    before sending; structured queries parse JSON responses automatically.

    Parameter asymmetry by design: blocking variants (query, query_structured)
    and streaming variants (stream_query) expose different optional parameters
    because streaming requires chunk-level callbacks and retry semantics that
    are not applicable to blocking calls.

    Example:
        >>> client = LLMClient()
        >>>
        >>> # Simple query
        >>> response = client.query("What is machine learning?")
        >>>
        >>> # With custom options
        >>> opts = GenerationOptions(temperature=0.0, seed=42)
        >>> response = client.query("Explain...", options=opts)
        >>>
        >>> # Structured response
        >>> data = client.query_structured(
        ...     "Extract entities",
        ...     schema={"type": "object", "properties": {...}}
        ... )
    """

    def __init__(self, config: OllamaClientConfig | None = None):
        """Initialize LLM client.

        Args:
            config: OllamaClientConfig instance. If None, loads from environment.
        """
        self.config = config or OllamaClientConfig.from_env()
        self.context = ConversationContext(max_tokens=self.config.context_window)
        self._system_prompt_injected = False

        # Store the default system prompt to detect if user explicitly set it
        default_system_prompt = (
            "You are an expert research assistant. "
            "Provide clear, accurate, and scientifically rigorous responses. "
            "Cite sources when possible."
        )

        # Try to load system prompt from prompt system if available
        # Only load default if system_prompt is the default value (not explicitly set to empty/None)
        # AND auto_inject is enabled (don't load if user disabled injection)
        if (
            PROMPT_LOADER_AVAILABLE
            and self.config.auto_inject_system_prompt
            and self.config.system_prompt == default_system_prompt
        ):
            try:
                loader = get_default_loader()
                # Try to get manuscript review system prompt
                self.config.system_prompt = loader.get_system_prompt("manuscript_review")
            except Exception as e:  # noqa: BLE001  # loader failure is expected; fall through to no system prompt
                logger.debug(f"Could not load system prompt from prompt system: {e}")

        # Inject system prompt if configured
        # Only inject if system_prompt is truthy (not empty string or None)
        if self.config.auto_inject_system_prompt and self.config.system_prompt:
            self._inject_system_prompt()

    def _inject_system_prompt(self) -> None:
        """Inject system prompt into context if not already present."""
        if not self._system_prompt_injected and self.config.system_prompt:
            self.context.add_message("system", self.config.system_prompt)
            self._system_prompt_injected = True

    @staticmethod
    def _time_call(fn: Callable[[], _T]) -> tuple[_T, float]:
        """Execute fn() and return (result, elapsed_seconds)."""
        start = time_module.time()
        result = fn()
        return result, time_module.time() - start

    def query(
        self,
        prompt: str,
        model: str | None = None,
        reset_context: bool = False,
        options: GenerationOptions | None = None,
    ) -> str:
        """Send a query to the LLM with context management.

        Args:
            prompt: User prompt
            model: Model to use (overrides config)
            reset_context: Whether to clear conversation history
            options: Per-query generation options

        Returns:
            Generated text response

        Example:
            >>> response = client.query("What is quantum computing?")
            >>>
            >>> # With options
            >>> opts = GenerationOptions(temperature=0.0, seed=42)
            >>> response = client.query("Explain...", options=opts)
        """
        model_name = model or self.config.default_model

        if reset_context:
            self.context.clear()
            self._system_prompt_injected = False
            if self.config.auto_inject_system_prompt:
                self._inject_system_prompt()

        prompt = sanitize_llm_input(prompt)
        self.context.add_message("user", prompt)

        try:
            response_text, _ = self._time_call(
                lambda: self._generate_response_direct(model_name, self.context.get_messages(), options=options)
            )

            self.context.add_message("assistant", response_text)

            return response_text

        except LLMConnectionError:
            # Try fallback models
            for fallback in self.config.fallback_models:
                try:
                    fallback_start = time_module.time()
                    logger.info(
                        "Retrying with fallback model",
                        extra={
                            "fallback_model": fallback,
                            "original_model": model_name,
                            "attempt": self.config.fallback_models.index(fallback) + 1,
                        },
                    )
                    response_text = self._generate_response_direct(fallback, self.context.get_messages(), options=options)
                    generation_time = time_module.time() - fallback_start

                    logger.info(
                        "Query completed with fallback model",
                        extra={
                            "model": fallback,
                            "response_length": len(response_text),
                            "generation_time_seconds": generation_time,
                        },
                    )

                    self.context.add_message("assistant", response_text)
                    return response_text
                except LLMConnectionError:
                    logger.debug(
                        "Fallback model failed, trying next",
                        extra={"fallback_model": fallback},
                    )
                    continue
            raise

    def query_raw(
        self,
        prompt: str,
        model: str | None = None,
        options: GenerationOptions | None = None,
        add_to_context: bool = False,
    ) -> str:
        """Send a raw prompt without system prompt or instructions.

        Bypasses context, system prompt injection, AND input sanitization
        (``sanitize_llm_input`` is intentionally not called here). Use only
        when the caller has already validated the prompt or when sanitization
        would interfere with the intended low-level interaction (e.g. testing
        raw model behaviour). Prefer ``query()`` for user-facing prompts.

        Args:
            prompt: Raw prompt to send
            model: Model to use (overrides config)
            options: Per-query generation options
            add_to_context: Whether to add to conversation context

        Returns:
            Raw LLM response

        Example:
            >>> response = client.query_raw("Complete: The quick brown fox")
        """
        model_name = model or self.config.default_model

        # Create temporary context for raw query
        messages = [{"role": "user", "content": prompt}]

        response_text, _ = self._time_call(
            lambda: self._generate_response_direct(model_name, messages, options=options)
        )

        if add_to_context:
            self.context.add_message("user", prompt)
            self.context.add_message("assistant", response_text)
            logger.debug(
                "Added raw query to context",
                extra={
                    "context_messages_after": len(self.context.messages),
                    "context_tokens_est_after": self.context.estimated_tokens,
                },
            )

        return response_text

    def apply_template(self, template_name: str, **kwargs: Any) -> str:
        """Render a template and query the LLM.

        Args:
            template_name: Name of template to use
            **kwargs: Template variables

        Returns:
            LLM response to rendered template
        """
        template = get_template(template_name)
        prompt = template.render(**kwargs)
        return self.query(prompt)

    def query_short(
        self,
        prompt: str,
        model: str | None = None,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate a short response (< 150 tokens).

        Blocking variant. The streaming counterpart stream_short() accepts
        additional params (save_response, save_path, retries) that are not
        available here — use stream_short() when response persistence is needed.

        Args:
            prompt: User prompt
            model: Model to use (overrides config)
            options: Additional generation options

        Returns:
            Brief response text
        """
        return self._query_with_mode(
            prompt,
            model=model,
            max_tokens=self.config.short_max_tokens,
            instruction=(
                "Provide a concise, brief response (less than 150 words). "
                "Be direct and to the point.\n\n"
            ),
            options=options,
        )

    def query_long(
        self,
        prompt: str,
        model: str | None = None,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate a comprehensive, detailed response (> 500 tokens).

        Configures generation for in-depth analysis and documentation.

        Args:
            prompt: User prompt
            model: Model to use (overrides config)
            options: Additional generation options

        Returns:
            Detailed response text
        """
        return self._query_with_mode(
            prompt,
            model=model,
            max_tokens=self.config.long_max_tokens,
            instruction=(
                "Provide a comprehensive, detailed response with examples and "
                "thorough explanation. Use multiple paragraphs if needed.\n\n"
            ),
            options=options,
        )

    def _query_with_mode(
        self,
        prompt: str,
        model: str | None,
        max_tokens: int,
        instruction: str,
        options: GenerationOptions | None = None,
    ) -> str:
        """Run query with a fixed token budget and instruction prefix.

        Keeps token-budget configuration and instruction injection in one place
        rather than duplicating it across query_short and query_long.
        """
        model_name = model or self.config.default_model
        mode_options = (
            dataclasses.replace(options, max_tokens=max_tokens)
            if options
            else GenerationOptions(max_tokens=max_tokens)
        )
        response, _ = self._time_call(
            lambda: self.query(instruction + prompt, model=model_name, options=mode_options)
        )
        return response

    def query_structured(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        model: str | None = None,
        options: GenerationOptions | None = None,
        use_native_json: bool = True,
    ) -> dict[str, Any]:
        """Generate a structured JSON response.

        Uses Ollama's native JSON format mode when available for guaranteed
        valid JSON output.

        Args:
            prompt: User prompt
            schema: JSON schema for response structure (optional)
            model: Model to use (overrides config)
            options: Additional generation options
            use_native_json: Use Ollama format="json" (default: True)

        Returns:
            Parsed JSON response as dictionary

        Raises:
            LLMError: If response cannot be parsed as JSON or is flagged as off-topic.

        Example:
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "summary": {"type": "string"},
            ...         "key_points": {"type": "array"}
            ...     },
            ...     "required": ["summary"]
            ... }
            >>> result = client.query_structured("Analyze...", schema=schema)
        """
        prompt = sanitize_llm_input(prompt)
        model_name = model or self.config.default_model

        logger.debug("Starting structured query (JSON) model=%s", model_name)

        # Configure for JSON output
        struct_options = options or GenerationOptions()
        if use_native_json:
            struct_options = GenerationOptions(
                temperature=struct_options.temperature,
                max_tokens=struct_options.max_tokens,
                seed=struct_options.seed,
                stop=struct_options.stop,
                format_json=True,  # Ollama native JSON mode
            )

        schema_instruction = ""
        if schema:
            schema_instruction = (
                f"\n\nReturn valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
            )

        instruction = (
            "Return your response as valid JSON only, no markdown or extra text. "
            f"{schema_instruction}\n\n"
        )

        # Use raw generation for structured to bypass context issues with JSON
        messages = self.context.get_messages() + [{"role": "user", "content": instruction + prompt}]

        response_text, generation_time = self._time_call(
            lambda: self._generate_response_direct(model_name, messages, options=struct_options)
        )

        # Add to context
        self.context.add_message("user", instruction + prompt)
        self.context.add_message("assistant", response_text)

        # Parse and validate JSON response
        try:
            parsed = cast(dict[str, Any], json.loads(response_text))
            return parsed
        except json.JSONDecodeError as e:
            # Try to extract JSON if wrapped
            if "{" in response_text and "}" in response_text:
                start = response_text.index("{")
                end = response_text.rindex("}") + 1
                try:
                    parsed = cast(dict[str, Any], json.loads(response_text[start:end]))
                    logger.warning(
                        "Structured response required JSON extraction (wrapped in text)",
                        extra={
                            "model": model_name,
                            "extracted_length": end - start,
                            "original_length": len(response_text),
                        },
                    )
                    return parsed
                except json.JSONDecodeError as e:
                    logger.error(
                        "Failed to parse structured response as JSON",
                        extra={
                            "model": model_name,
                            "error": str(e),
                            "response_preview": response_text[:200],
                        },
                    )
                    raise LLMError(
                        "Failed to parse structured response as JSON",
                        context={"error": str(e), "response": response_text[:200]},
                    ) from e
            logger.error(
                "Structured response is not valid JSON",
                extra={
                    "model": model_name,
                    "response_preview": response_text[:200],
                },
            )
            raise LLMError(
                "Structured response must be valid JSON",
                context={"response": response_text[:200]},
            ) from e

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

        last_error = None

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
                    logger.warning(f"Empty response from Ollama ({model})")
                    # Check if there's an error in the response
                    if "error" in data:
                        error_msg = data.get("error", "Unknown error")
                        raise LLMConnectionError(
                            f"Ollama returned error ({model}): {error_msg}",
                            context={"url": url, "model": model, "response": data},
                        )

                # Strip thinking tags if present (e.g., from Qwen models)
                content = strip_thinking_tags(content)

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

    def stream_query(
        self,
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
        Delegates to :func:`infrastructure.llm.core._client_streaming.stream_query_impl`.

        Args:
            prompt: User prompt
            model: Model to use
            options: Generation options
            save_response: Whether to save response to file
            save_path: Path to save response (auto-generated if None and save_response=True)
            log_progress: Whether to log streaming progress (DEBUG level)
            retries: Number of retry attempts on transient failures

        Yields:
            Response text chunks

        Example:
            >>> for chunk in client.stream_query("Explain AI", log_progress=True):
            ...     print(chunk, end="")
        """
        from infrastructure.llm.core._client_streaming import stream_query_impl

        prompt = sanitize_llm_input(prompt)
        yield from stream_query_impl(
            config=self.config,
            context=self.context,
            save_streaming_state_fn=self._save_streaming_state,
            prompt=prompt,
            model=model,
            options=options,
            save_response=save_response,
            save_path=save_path,
            log_progress=log_progress,
            retries=retries,
        )

    def stream_short(
        self,
        prompt: str,
        model: str | None = None,
        options: GenerationOptions | None = None,
        save_response: bool = False,
        save_path: Path | None = None,
        log_progress: bool = True,
        retries: int = 1,
    ) -> Iterator[str]:
        """Stream a short response with comprehensive logging.

        Delegates to :func:`infrastructure.llm.core._client_streaming.stream_short_impl`.

        Args:
            prompt: User prompt
            model: Model to use
            options: Additional options
            save_response: Whether to save response to file
            save_path: Path to save response
            log_progress: Whether to log streaming progress
            retries: Number of retry attempts on failure

        Yields:
            Response chunks
        """
        from infrastructure.llm.core._streaming_shortcuts import stream_short_impl

        yield from stream_short_impl(
            config=self.config,
            context=self.context,
            save_streaming_state_fn=self._save_streaming_state,
            prompt=prompt,
            model=model,
            options=options,
            save_response=save_response,
            save_path=save_path,
            log_progress=log_progress,
            retries=retries,
        )

    def stream_long(
        self,
        prompt: str,
        model: str | None = None,
        options: GenerationOptions | None = None,
        save_response: bool = False,
        save_path: Path | None = None,
        log_progress: bool = True,
        retries: int = 1,
    ) -> Iterator[str]:
        """Stream a comprehensive response with detailed logging.

        Delegates to :func:`infrastructure.llm.core._client_streaming.stream_long_impl`.

        Args:
            prompt: User prompt
            model: Model to use
            options: Additional options
            save_response: Whether to save response to file
            save_path: Path to save response
            log_progress: Whether to log streaming progress
            retries: Number of retry attempts on failure

        Yields:
            Response chunks
        """
        from infrastructure.llm.core._streaming_shortcuts import stream_long_impl

        yield from stream_long_impl(
            config=self.config,
            context=self.context,
            save_streaming_state_fn=self._save_streaming_state,
            prompt=prompt,
            model=model,
            options=options,
            save_response=save_response,
            save_path=save_path,
            log_progress=log_progress,
            retries=retries,
        )

    def get_available_models(self) -> list[str]:
        """Get list of available models from Ollama.

        Returns:
            List of model names (deduplicated)
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
        """Return True if the Ollama server is reachable."""
        is_available, _ = self.check_connection_detailed(timeout=timeout)
        return is_available

    def check_connection_detailed(self, timeout: float = 2.0) -> tuple[bool, str | None]:
        """Return (is_available, error_message) for the Ollama server."""
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

    def reset(self) -> None:
        """Reset client state, clearing context and system prompt."""
        self.context.clear()
        self._system_prompt_injected = False
        # Only re-inject if auto_inject is enabled
        if self.config.auto_inject_system_prompt and self.config.system_prompt:
            self._inject_system_prompt()

    def set_system_prompt(self, prompt: str) -> None:
        """Set a new system prompt and reset context.

        Args:
            prompt: New system prompt
        """
        self.config.system_prompt = prompt
        self.reset()

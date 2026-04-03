"""Core logic for LLM module.

Provides LLMClient for interacting with Ollama local LLMs with:
- Multiple response modes (short, long, structured)
- Streaming and non-streaming queries
- Per-query generation options
- Context management with system prompt injection
- Template support for research tasks
"""

from __future__ import annotations

import time as time_module
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar

from infrastructure.core.exceptions import LLMConnectionError
from infrastructure.core.logging.utils import get_logger
from infrastructure.llm.core._connection import _ConnectionMixin
from infrastructure.llm.core._structured_queries import _StructuredQueryMixin
from infrastructure.llm.core.config import GenerationOptions, OllamaClientConfig, ResponseMode
from infrastructure.llm.core.context import ConversationContext
from infrastructure.llm.core.sanitization import sanitize_llm_input
from infrastructure.llm.templates import get_template

_T = TypeVar("_T")

logger = get_logger(__name__)

# Try to import prompt system for system prompt loading
try:
    from infrastructure.llm.prompts.loader import get_default_loader

    PROMPT_LOADER_AVAILABLE = True
except ImportError:
    PROMPT_LOADER_AVAILABLE = False

# ResponseMode is defined in config.py (alongside GenerationOptions) to avoid
# a validation->client import cycle. Re-exported here for backwards compatibility.
__all__ = ["LLMClient", "ResponseMode"]


class LLMClient(_ConnectionMixin, _StructuredQueryMixin):
    """Client for interacting with LLM providers (Ollama).

    Manages conversation context, system prompt injection, and provides
    both blocking and streaming query variants. All inputs are sanitized
    before sending; structured queries parse JSON responses automatically.

    **Blocking vs streaming parameter asymmetry:**
    Streaming variants (stream_query, stream_short, stream_long) accept extra
    params not available on their blocking counterparts:
      - ``save_response`` (bool): persist streamed output to disk
      - ``save_path`` (Path | None): override the default save location
      - ``retries`` (int): retry count on transient errors
    Use the streaming variant when response persistence or retry control is needed.

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
            except Exception as e:  # noqa: BLE001  # loader failure is non-fatal; fall through to default prompt
                logger.warning(f"Could not load system prompt from prompt system: {e}")

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
        sanitize: bool = True,
    ) -> str:
        """Send a query to the LLM with context management.

        Args:
            prompt: User prompt
            model: Model to use (overrides config)
            reset_context: Whether to clear conversation history
            options: Per-query generation options
            sanitize: Whether to apply input sanitization (default True).
                Set to False for trusted internal content (e.g. manuscript
                review prompts built from local PDF text) where the
                dangerous-pattern check would false-positive on legitimate
                technical references like ``open()`` or ``pathlib``.

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
            logger.info("Resetting context", extra={"model": model_name})
            self.context.clear()
            self._system_prompt_injected = False
            if self.config.auto_inject_system_prompt:
                self._inject_system_prompt()

        if sanitize:
            prompt = sanitize_llm_input(prompt)
        self.context.add_message("user", prompt)

        try:
            response_text, _ = self._time_call(
                lambda: self._generate_response_direct(model_name, self.context.get_messages(), options=options)
            )

            self.context.add_message("assistant", response_text)

            return response_text

        except LLMConnectionError as primary_err:
            # Try fallback models. Log the primary failure so it is not silently discarded.
            logger.warning(
                "Primary model failed; attempting fallback",
                extra={"original_model": model_name, "error": str(primary_err)},
            )
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

        Security note: callers are responsible for validating the prompt before
        passing it here. A ``raw_llm_query`` audit event is emitted to
        SecurityMonitor at ``info`` severity so the sanitization bypass is
        traceable in the audit log.

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

        # Emit audit event so the sanitization bypass is traceable in SecurityMonitor.
        # Deferred import breaks the circular dependency: llm/core/client → core/security
        # → (transitively) llm/core/sanitization → llm/core/client.  Moving this import
        # to module level would create an import-time cycle.  The cycle itself is a known
        # design debt; the correct long-term fix is to extract the SecurityMonitor audit
        # interface into a separate lightweight module that neither side depends on.
        from infrastructure.core.security import get_security_monitor  # noqa: PLC0415
        get_security_monitor().log_security_event(
            "raw_llm_query",
            {"model": model_name, "prompt_length": len(prompt)},
            "info",
        )

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

    def stream_query(
        self,
        prompt: str,
        model: str | None = None,
        options: GenerationOptions | None = None,
        save_response: bool = False,
        save_path: Path | None = None,
        log_progress: bool = True,
        retries: int = 1,
        sanitize: bool = True,
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
            sanitize: Whether to apply input sanitization (default True).
                Set to False for trusted internal content.

        Yields:
            Response text chunks

        Example:
            >>> for chunk in client.stream_query("Explain AI", log_progress=True):
            ...     print(chunk, end="")
        """
        from infrastructure.llm.core._stream_impl import stream_query_impl

        if sanitize:
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

"""Structured and mode-based query methods for LLMClient.

Extracted from client.py. Mixed into LLMClient via _StructuredQueryMixin.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from infrastructure.core.exceptions import LLMError
from infrastructure.core.logging.utils import get_logger
from infrastructure.llm.core.config import GenerationOptions
from infrastructure.llm.core.sanitization import sanitize_llm_input

if TYPE_CHECKING:
    from infrastructure.llm.core.config import OllamaClientConfig
    from infrastructure.llm.core.context import ConversationContext

logger = get_logger(__name__)


class _StructuredQueryMixin:
    """Mixin providing structured, short, long, and streaming query variants."""

    config: OllamaClientConfig
    context: ConversationContext

    def query_short(
        self,
        prompt: str,
        model: str | None = None,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate a short response (< 150 tokens). Use stream_short() for persistence."""
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
        """Generate a comprehensive, detailed response (> 500 tokens)."""
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

        logger.info("Starting structured query", extra={"model": model_name})

        # Configure for JSON output
        struct_options = options or GenerationOptions()
        if use_native_json:
            struct_options = dataclasses.replace(struct_options, format_json=True)

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
        full_prompt = instruction + prompt
        messages = self.context.get_messages() + [{"role": "user", "content": full_prompt}]

        response_text, generation_time = self._time_call(
            lambda: self._generate_response_direct(model_name, messages, options=struct_options)
        )

        # Add to context
        self.context.add_message("user", full_prompt)
        self.context.add_message("assistant", response_text)

        # Parse and validate JSON response
        def _parse_dict(text: str) -> dict[str, Any]:
            """Parse text as JSON dict, raising ValueError if result is not a dict."""
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError(f"Expected JSON object, got {type(value).__name__}")
            return value

        try:
            parsed = _parse_dict(response_text)
            logger.info(
                "Structured query completed",
                extra={
                    "model": model_name,
                    "generation_time_seconds": generation_time,
                    "response_length": len(response_text),
                },
            )
            return parsed
        except (json.JSONDecodeError, ValueError) as e:
            # Try to extract JSON if wrapped in surrounding text
            if "{" in response_text and "}" in response_text:
                start = response_text.index("{")
                end = response_text.rindex("}") + 1
                try:
                    parsed = _parse_dict(response_text[start:end])
                    logger.warning(
                        "Structured response required JSON extraction (wrapped in text)",
                        extra={
                            "model": model_name,
                            "extracted_length": end - start,
                            "original_length": len(response_text),
                        },
                    )
                    return parsed
                except (json.JSONDecodeError, ValueError) as e:
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
        """Stream a concise response (<=150 words) with a brevity instruction prepended."""
        yield from self._stream_with_instruction(
            "Provide a concise, brief response (less than 150 words). "
            "Be direct and to the point.\n\n",
            prompt, model, options, self.config.short_max_tokens,
            save_response, save_path, log_progress, retries,
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
        """Stream a comprehensive long response with a thoroughness instruction prepended."""
        yield from self._stream_with_instruction(
            "Provide a comprehensive, detailed response with examples and "
            "thorough explanation. Use multiple paragraphs if needed.\n\n",
            prompt, model, options, self.config.long_max_tokens,
            save_response, save_path, log_progress, retries,
        )

    def _stream_with_instruction(
        self,
        instruction: str,
        prompt: str,
        model: str | None,
        options: GenerationOptions | None,
        max_tokens: int,
        save_response: bool,
        save_path: Path | None,
        log_progress: bool,
        retries: int,
    ) -> Iterator[str]:
        """Prepend instruction to prompt and stream with custom token limit."""
        from infrastructure.llm.core._client_streaming import stream_query_impl

        scoped_options = GenerationOptions(
            max_tokens=max_tokens,
            temperature=options.temperature if options else None,
            seed=options.seed if options else None,
        )
        yield from stream_query_impl(
            self.config,
            self.context,
            self._save_streaming_state,
            instruction + sanitize_llm_input(prompt),
            model,
            options=scoped_options,
            save_response=save_response,
            save_path=save_path,
            log_progress=log_progress,
            retries=retries,
        )

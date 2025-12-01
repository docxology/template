"""Core logic for LLM module.

Provides LLMClient for interacting with Ollama local LLMs with:
- Multiple response modes (short, long, structured)
- Streaming and non-streaming queries
- Per-query generation options
- Context management with system prompt injection
- Template support for research tasks
"""
from __future__ import annotations

import requests
import json
from typing import Dict, Any, Optional, Generator, Iterator, Literal, Union
from enum import Enum

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import LLMConnectionError, LLMError
from infrastructure.llm.config import LLMConfig, GenerationOptions
from infrastructure.llm.context import ConversationContext
from infrastructure.llm.templates import get_template

logger = get_logger(__name__)


class ResponseMode(str, Enum):
    """Response generation modes for different use cases."""
    SHORT = "short"           # Brief answers (< 150 tokens)
    LONG = "long"             # Comprehensive answers (> 500 tokens)
    STRUCTURED = "structured" # JSON-formatted structured response
    RAW = "raw"               # Raw prompt without modification


class LLMClient:
    """Client for interacting with LLM providers (Ollama).
    
    Provides multiple query methods for different use cases:
    - query(): Standard conversational query
    - query_raw(): Send prompt without modification
    - query_short(): Brief responses (< 150 tokens)
    - query_long(): Comprehensive responses (> 500 tokens)
    - query_structured(): JSON-formatted responses
    - stream_*(): Streaming variants of above
    
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

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize LLM client.
        
        Args:
            config: LLMConfig instance. If None, loads from environment.
        """
        self.config = config or LLMConfig.from_env()
        self.context = ConversationContext(max_tokens=self.config.context_window)
        self._system_prompt_injected = False
        
        # Inject system prompt if configured
        if self.config.auto_inject_system_prompt and self.config.system_prompt:
            self._inject_system_prompt()

    def _inject_system_prompt(self) -> None:
        """Inject system prompt into context if not already present."""
        if not self._system_prompt_injected and self.config.system_prompt:
            self.context.add_message("system", self.config.system_prompt)
            self._system_prompt_injected = True

    def query(
        self,
        prompt: str,
        model: Optional[str] = None,
        reset_context: bool = False,
        options: Optional[GenerationOptions] = None
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
        if reset_context:
            self.context.clear()
            self._system_prompt_injected = False
            if self.config.auto_inject_system_prompt:
                self._inject_system_prompt()
            
        self.context.add_message("user", prompt)
        
        model_name = model or self.config.default_model
        
        try:
            response_text = self._generate_response(model_name, options=options)
            self.context.add_message("assistant", response_text)
            return response_text
            
        except LLMConnectionError:
            # Try fallback models
            for fallback in self.config.fallback_models:
                try:
                    logger.info(f"Retrying with fallback model: {fallback}")
                    response_text = self._generate_response(fallback, options=options)
                    self.context.add_message("assistant", response_text)
                    return response_text
                except LLMConnectionError:
                    continue
            raise

    def query_raw(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
        add_to_context: bool = False
    ) -> str:
        """Send a raw prompt without system prompt or instructions.
        
        Bypasses context and system prompt injection for direct LLM interaction.
        
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
        
        response_text = self._generate_response_direct(
            model_name, 
            messages, 
            options=options
        )
        
        if add_to_context:
            self.context.add_message("user", prompt)
            self.context.add_message("assistant", response_text)
            
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
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None
    ) -> str:
        """Generate a short response (< 150 tokens).
        
        Configures generation for concise, direct answers.
        
        Args:
            prompt: User prompt
            model: Model to use (overrides config)
            options: Additional generation options
            
        Returns:
            Brief response text
        """
        model_name = model or self.config.default_model
        
        # Create options for short response
        short_options = GenerationOptions(
            max_tokens=self.config.short_max_tokens,
            temperature=options.temperature if options else None,
            seed=options.seed if options else None,
            stop=options.stop if options else None,
        )
        
        instruction = (
            "Provide a concise, brief response (less than 150 words). "
            "Be direct and to the point.\n\n"
        )
        return self.query(instruction + prompt, model=model_name, options=short_options)

    def query_long(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None
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
        model_name = model or self.config.default_model
        
        # Create options for long response with higher token limit
        long_options = GenerationOptions(
            max_tokens=self.config.long_max_tokens,
            temperature=options.temperature if options else None,
            seed=options.seed if options else None,
            stop=options.stop if options else None,
        )
        
        instruction = (
            "Provide a comprehensive, detailed response with examples and "
            "thorough explanation. Use multiple paragraphs if needed.\n\n"
        )
        return self.query(instruction + prompt, model=model_name, options=long_options)

    def query_structured(
        self, 
        prompt: str, 
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
        use_native_json: bool = True
    ) -> Dict[str, Any]:
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
        model_name = model or self.config.default_model
        
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
            schema_instruction = f"\n\nReturn valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        
        instruction = (
            "Return your response as valid JSON only, no markdown or extra text. "
            f"{schema_instruction}\n\n"
        )
        
        # Use raw generation for structured to bypass context issues with JSON
        messages = self.context.get_messages() + [
            {"role": "user", "content": instruction + prompt}
        ]
        
        response_text = self._generate_response_direct(
            model_name,
            messages,
            options=struct_options
        )
        
        # Add to context
        self.context.add_message("user", instruction + prompt)
        self.context.add_message("assistant", response_text)
        
        # Parse and validate JSON response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON if wrapped
            if "{" in response_text and "}" in response_text:
                start = response_text.index("{")
                end = response_text.rindex("}") + 1
                try:
                    return json.loads(response_text[start:end])
                except json.JSONDecodeError as e:
                    raise LLMError(
                        "Failed to parse structured response as JSON",
                        context={"error": str(e), "response": response_text[:200]}
                    )
            raise LLMError(
                "Structured response must be valid JSON",
                context={"response": response_text[:200]}
            )

    def _generate_response(
        self,
        model: str,
        options: Optional[GenerationOptions] = None
    ) -> str:
        """Generate response from Ollama API using context.
        
        Args:
            model: Model name
            options: Generation options
            
        Returns:
            Generated text
        """
        return self._generate_response_direct(
            model,
            self.context.get_messages(),
            options=options
        )

    def _generate_response_direct(
        self,
        model: str,
        messages: list[Dict[str, Any]],
        options: Optional[GenerationOptions] = None
    ) -> str:
        """Generate response from Ollama API with direct messages.
        
        Args:
            model: Model name
            messages: List of message dicts
            options: Generation options
            
        Returns:
            Generated text
        """
        url = f"{self.config.base_url}/api/chat"
        
        # Build options dict
        opts = options or GenerationOptions()
        ollama_options = opts.to_ollama_options(self.config)
        
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": ollama_options,
        }
        
        # Add format for native JSON mode
        if opts.format_json:
            payload["format"] = "json"
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("message", {}).get("content", "")
            
        except requests.exceptions.RequestException as e:
            raise LLMConnectionError(
                f"Failed to connect to Ollama ({model}): {e}",
                context={"url": url, "model": model}
            )

    def stream_query(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None
    ) -> Iterator[str]:
        """Stream response from LLM.
        
        Yields response chunks as they arrive for real-time display.
        
        Args:
            prompt: User prompt
            model: Model to use
            options: Generation options
            
        Yields:
            Response text chunks
        """
        self.context.add_message("user", prompt)
        model_name = model or self.config.default_model
        url = f"{self.config.base_url}/api/chat"
        
        opts = options or GenerationOptions()
        ollama_options = opts.to_ollama_options(self.config)
        
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": self.context.get_messages(),
            "stream": True,
            "options": ollama_options,
        }
        
        if opts.format_json:
            payload["format"] = "json"
        
        full_response = []
        
        try:
            with requests.post(url, json=payload, stream=True, timeout=self.config.timeout) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        full_response.append(chunk)
                        yield chunk
                        
            # Add full response to context
            self.context.add_message("assistant", "".join(full_response))
            
        except requests.exceptions.RequestException as e:
            raise LLMConnectionError(f"Stream failed: {e}")

    def stream_short(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None
    ) -> Iterator[str]:
        """Stream a short response.
        
        Args:
            prompt: User prompt
            model: Model to use
            options: Additional options
            
        Yields:
            Response chunks
        """
        short_options = GenerationOptions(
            max_tokens=self.config.short_max_tokens,
            temperature=options.temperature if options else None,
            seed=options.seed if options else None,
        )
        instruction = (
            "Provide a concise, brief response (less than 150 words). "
            "Be direct and to the point.\n\n"
        )
        yield from self.stream_query(instruction + prompt, model, options=short_options)

    def stream_long(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None
    ) -> Iterator[str]:
        """Stream a comprehensive response.
        
        Args:
            prompt: User prompt
            model: Model to use
            options: Additional options
            
        Yields:
            Response chunks
        """
        long_options = GenerationOptions(
            max_tokens=self.config.long_max_tokens,
            temperature=options.temperature if options else None,
            seed=options.seed if options else None,
        )
        instruction = (
            "Provide a comprehensive, detailed response with examples and "
            "thorough explanation. Use multiple paragraphs if needed.\n\n"
        )
        yield from self.stream_query(instruction + prompt, model, options=long_options)

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

    def check_connection(self) -> bool:
        """Check if Ollama server is available.
        
        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=self.config.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def reset(self) -> None:
        """Reset client state, clearing context and system prompt."""
        self.context.clear()
        self._system_prompt_injected = False
        if self.config.auto_inject_system_prompt:
            self._inject_system_prompt()

    def set_system_prompt(self, prompt: str) -> None:
        """Set a new system prompt and reset context.
        
        Args:
            prompt: New system prompt
        """
        self.config.system_prompt = prompt
        self.reset()

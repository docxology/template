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
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Generator, Iterator, Literal, Union, Tuple
from enum import Enum

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import LLMConnectionError, LLMError
from infrastructure.llm.core.config import LLMConfig, GenerationOptions
from infrastructure.llm.core.context import ConversationContext
from infrastructure.llm.templates import get_template
from infrastructure.llm.review.metrics import StreamingMetrics

logger = get_logger(__name__)

# Try to import prompt system for system prompt loading
try:
    from infrastructure.llm.prompts.loader import get_default_loader
    PROMPT_LOADER_AVAILABLE = True
except ImportError:
    PROMPT_LOADER_AVAILABLE = False


def strip_thinking_tags(text: str) -> str:
    """Remove thinking tags from LLM responses.
    
    Some models (e.g., Qwen) output <think>...</think> tags before their
    actual response. This function removes those tags to extract the
    final answer.
    
    Args:
        text: Response text that may contain thinking tags
        
    Returns:
        Text with thinking tags removed
        
    Example:
        >>> text = "<think>Let me think about this...</think>The answer is 42."
        >>> strip_thinking_tags(text)
        'The answer is 42.'
    """
    if not text:
        return text
    
    # Remove <think>...</think> tags (case-insensitive, handles whitespace)
    # Pattern matches: <think>...</think>, <think >...</think>, <THINK>...</THINK>, etc.
    pattern = r'<think[^>]*>.*?</think>'
    result = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Also handle </think> without opening tag (malformed)
    result = re.sub(r'</think>', '', result, flags=re.IGNORECASE)
    
    # Clean up extra whitespace that might result
    result = result.strip()
    
    return result


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
        
        # Store the default system prompt to detect if user explicitly set it
        default_system_prompt = (
            "You are an expert research assistant. "
            "Provide clear, accurate, and scientifically rigorous responses. "
            "Cite sources when possible."
        )
        
        # Try to load system prompt from prompt system if available
        # Only load default if system_prompt is the default value (not explicitly set to empty/None)
        # AND auto_inject is enabled (don't load if user disabled injection)
        if (PROMPT_LOADER_AVAILABLE and 
            self.config.auto_inject_system_prompt and 
            self.config.system_prompt == default_system_prompt):
            try:
                loader = get_default_loader()
                # Try to get manuscript review system prompt
                self.config.system_prompt = loader.get_system_prompt("manuscript_review")
            except Exception as e:
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
        import time as time_module
        start_time = time_module.time()
        model_name = model or self.config.default_model
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        
        if reset_context:
            logger.info(
                "Resetting context",
                extra={
                    "model": model_name,
                    "reason": "reset_context=True",
                    "context_messages_before": len(self.context.messages),
                }
            )
            self.context.clear()
            self._system_prompt_injected = False
            if self.config.auto_inject_system_prompt:
                self._inject_system_prompt()
                logger.debug(
                    "System prompt re-injected after context reset",
                    extra={"system_prompt_length": len(self.config.system_prompt) if self.config.system_prompt else 0}
                )
        
        # Log query start
        logger.info(
            "Starting query",
            extra={
                "model": model_name,
                "prompt_length": len(prompt),
                "prompt_preview": prompt_preview,
                "context_messages": len(self.context.messages),
                "context_tokens_est": self.context.estimated_tokens,
                "max_tokens": options.max_tokens if options else None,
                "temperature": options.temperature if options else None,
                "seed": options.seed if options else None,
            }
        )
        
        self.context.add_message("user", prompt)
        logger.debug(
            "Added user message to context",
            extra={
                "message_length": len(prompt),
                "context_messages_after": len(self.context.messages),
                "context_tokens_est_after": self.context.estimated_tokens,
            }
        )
        
        try:
            response_text = self._generate_response(model_name, options=options)
            generation_time = time_module.time() - start_time
            
            # Log response received
            logger.info(
                "Query completed",
                extra={
                    "model": model_name,
                    "response_length": len(response_text),
                    "response_tokens_est": len(response_text) // 4,
                    "generation_time_seconds": generation_time,
                    "response_preview": response_text[:150] + "..." if len(response_text) > 150 else response_text,
                }
            )
            
            self.context.add_message("assistant", response_text)
            logger.debug(
                "Added assistant message to context",
                extra={
                    "message_length": len(response_text),
                    "context_messages_after": len(self.context.messages),
                    "context_tokens_est_after": self.context.estimated_tokens,
                }
            )
            
            return response_text
            
        except LLMConnectionError:
            # Try fallback models
            for fallback in self.config.fallback_models:
                try:
                    logger.info(
                        "Retrying with fallback model",
                        extra={
                            "fallback_model": fallback,
                            "original_model": model_name,
                            "attempt": self.config.fallback_models.index(fallback) + 1,
                        }
                    )
                    response_text = self._generate_response(fallback, options=options)
                    generation_time = time_module.time() - start_time
                    
                    logger.info(
                        "Query completed with fallback model",
                        extra={
                            "model": fallback,
                            "response_length": len(response_text),
                            "generation_time_seconds": generation_time,
                        }
                    )
                    
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
        import time as time_module
        start_time = time_module.time()
        model_name = model or self.config.default_model
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        
        logger.info(
            "Starting raw query (no system prompt)",
            extra={
                "model": model_name,
                "prompt_length": len(prompt),
                "prompt_preview": prompt_preview,
                "add_to_context": add_to_context,
                "max_tokens": options.max_tokens if options else None,
                "temperature": options.temperature if options else None,
            }
        )
        
        # Create temporary context for raw query
        messages = [{"role": "user", "content": prompt}]
        
        response_text = self._generate_response_direct(
            model_name, 
            messages, 
            options=options
        )
        
        generation_time = time_module.time() - start_time
        
        logger.info(
            "Raw query completed",
            extra={
                "model": model_name,
                "response_length": len(response_text),
                "response_tokens_est": len(response_text) // 4,
                "generation_time_seconds": generation_time,
            }
        )
        
        if add_to_context:
            self.context.add_message("user", prompt)
            self.context.add_message("assistant", response_text)
            logger.debug(
                "Added raw query to context",
                extra={
                    "context_messages_after": len(self.context.messages),
                    "context_tokens_est_after": self.context.estimated_tokens,
                }
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
        import time as time_module
        start_time = time_module.time()
        model_name = model or self.config.default_model
        
        logger.info(
            "Starting short query",
            extra={
                "model": model_name,
                "prompt_length": len(prompt),
                "max_tokens": self.config.short_max_tokens,
                "temperature": options.temperature if options else None,
            }
        )
        
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
        response = self.query(instruction + prompt, model=model_name, options=short_options)
        
        generation_time = time_module.time() - start_time
        logger.info(
            "Short query completed",
            extra={
                "model": model_name,
                "response_length": len(response),
                "generation_time_seconds": generation_time,
            }
        )
        
        return response

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
        import time as time_module
        start_time = time_module.time()
        model_name = model or self.config.default_model
        
        logger.info(
            "Starting long query",
            extra={
                "model": model_name,
                "prompt_length": len(prompt),
                "max_tokens": self.config.long_max_tokens,
                "temperature": options.temperature if options else None,
            }
        )
        
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
        response = self.query(instruction + prompt, model=model_name, options=long_options)
        
        generation_time = time_module.time() - start_time
        logger.info(
            "Long query completed",
            extra={
                "model": model_name,
                "response_length": len(response),
                "response_tokens_est": len(response) // 4,
                "generation_time_seconds": generation_time,
            }
        )
        
        return response

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
        import time as time_module
        start_time = time_module.time()
        model_name = model or self.config.default_model
        
        logger.info(
            "Starting structured query (JSON)",
            extra={
                "model": model_name,
                "prompt_length": len(prompt),
                "has_schema": schema is not None,
                "use_native_json": use_native_json,
                "schema_keys": list(schema.keys()) if schema and isinstance(schema, dict) and "properties" in schema else None,
            }
        )
        
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
        
        generation_time = time_module.time() - start_time
        
        logger.debug(
            "Structured response received",
            extra={
                "model": model_name,
                "response_length": len(response_text),
                "generation_time_seconds": generation_time,
                "response_preview": response_text[:200],
            }
        )
        
        # Add to context
        self.context.add_message("user", instruction + prompt)
        self.context.add_message("assistant", response_text)
        
        # Parse and validate JSON response
        try:
            parsed = json.loads(response_text)
            logger.info(
                "Structured query completed (JSON parsed successfully)",
                extra={
                    "model": model_name,
                    "response_keys": list(parsed.keys()) if isinstance(parsed, dict) else None,
                    "generation_time_seconds": generation_time,
                }
            )
            return parsed
        except json.JSONDecodeError:
            # Try to extract JSON if wrapped
            if "{" in response_text and "}" in response_text:
                start = response_text.index("{")
                end = response_text.rindex("}") + 1
                try:
                    parsed = json.loads(response_text[start:end])
                    logger.warning(
                        "Structured response required JSON extraction (wrapped in text)",
                        extra={
                            "model": model_name,
                            "extracted_length": end - start,
                            "original_length": len(response_text),
                        }
                    )
                    return parsed
                except json.JSONDecodeError as e:
                    logger.error(
                        "Failed to parse structured response as JSON",
                        extra={
                            "model": model_name,
                            "error": str(e),
                            "response_preview": response_text[:200],
                        }
                    )
                    raise LLMError(
                        "Failed to parse structured response as JSON",
                        context={"error": str(e), "response": response_text[:200]}
                    )
            logger.error(
                "Structured response is not valid JSON",
                extra={
                    "model": model_name,
                    "response_preview": response_text[:200],
                }
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
        options: Optional[GenerationOptions] = None,
        retries: int = 1
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
        
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": ollama_options,
        }
        
        # Add format for native JSON mode
        if opts.format_json:
            payload["format"] = "json"
        
        last_error = None
        
        for attempt in range(retries + 1):
            try:
                if attempt > 0:
                    wait_time = min((attempt + 1) * 1.0, 5.0)  # Max 5s wait
                    logger.debug(f"Retrying request (attempt {attempt + 1}/{retries + 1}) after {wait_time}s...")
                    time.sleep(wait_time)
                
                response = requests.post(
                    url, 
                    json=payload, 
                    timeout=self.config.timeout
                )
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
                            context={"url": url, "model": model, "response": data}
                        )
                
                # Strip thinking tags if present (e.g., from Qwen models)
                content = strip_thinking_tags(content)
                
                if attempt > 0:
                    logger.info(f"Request succeeded on retry {attempt + 1}")
                
                return content
                
            except requests.exceptions.Timeout as e:
                last_error = f"Timeout after {self.config.timeout}s"
                if attempt < retries:
                    logger.debug(f"Request timeout (attempt {attempt + 1}/{retries + 1}), will retry...")
                    continue
                else:
                    logger.error(f"Request timeout after {retries + 1} attempts: {last_error}")
                    raise LLMConnectionError(
                        f"Ollama request timeout ({model}): {last_error}",
                        context={"url": url, "model": model, "timeout": self.config.timeout}
                    )
                    
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                if attempt < retries:
                    logger.debug(f"Connection error (attempt {attempt + 1}/{retries + 1}), will retry...")
                    continue
                else:
                    logger.error(f"Connection error after {retries + 1} attempts: {last_error}")
                    raise LLMConnectionError(
                        f"Failed to connect to Ollama ({model}): {last_error}",
                        context={"url": url, "model": model}
                    )
                    
            except requests.exceptions.HTTPError as e:
                # Don't retry HTTP errors (4xx, 5xx) - they're not transient
                error_msg = f"HTTP {response.status_code}: {response.text[:200] if 'response' in locals() else str(e)}"
                logger.error(f"HTTP error from Ollama ({model}): {error_msg}")
                raise LLMConnectionError(
                    f"Ollama HTTP error ({model}): {error_msg}",
                    context={"url": url, "model": model, "status_code": response.status_code if 'response' in locals() else None}
                )
                
            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {e}"
                logger.error(f"Request error from Ollama ({model}): {last_error}")
                raise LLMConnectionError(
                    f"Failed to connect to Ollama ({model}): {last_error}",
                    context={"url": url, "model": model}
                )

    def stream_query(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
        save_response: bool = False,
        save_path: Optional[Path] = None,
        log_progress: bool = True,
        retries: int = 1
    ) -> Iterator[str]:
        """Stream response from LLM with comprehensive logging and error recovery.
        
        Yields response chunks as they arrive for real-time display.
        
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
        import time as time_module
        from infrastructure.llm.core.response_saver import ResponseMetadata, save_streaming_response
        
        start_time = time_module.time()
        model_name = model or self.config.default_model
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        
        # Log streaming start
        logger.info(
            "Starting streaming query",
            extra={
                "model": model_name,
                "prompt_length": len(prompt),
                "prompt_preview": prompt_preview,
                "max_tokens": options.max_tokens if options else None,
                "temperature": options.temperature if options else None,
            }
        )
        
        self.context.add_message("user", prompt)
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
        chunk_count = 0
        first_chunk_time = None
        last_chunk_time = None
        error_count = 0
        partial_saved = False
        
        # Initialize metrics
        metrics = StreamingMetrics()
        
        for attempt in range(retries + 1):
            try:
                if attempt > 0:
                    wait_time = min((attempt + 1) * 1.0, 5.0)
                    logger.debug(f"Retrying streaming request (attempt {attempt + 1}/{retries + 1}) after {wait_time}s...")
                    time.sleep(wait_time)
                
                with requests.post(url, json=payload, stream=True, timeout=self.config.timeout) as r:
                    r.raise_for_status()
                    
                    for line in r.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                chunk = data.get("message", {}).get("content", "")
                                
                                if chunk:
                                    chunk_count += 1
                                    full_response.append(chunk)
                                    
                                    # Track timing
                                    current_time = time_module.time()
                                    if first_chunk_time is None:
                                        first_chunk_time = current_time
                                        metrics.first_chunk_time = current_time - start_time
                                        logger.debug(
                                            f"First chunk received after {metrics.first_chunk_time:.2f}s",
                                            extra={"chunk_count": chunk_count}
                                        )
                                    
                                    last_chunk_time = current_time
                                    
                                    # Log chunk progress (DEBUG level)
                                    if log_progress:
                                        logger.debug(
                                            f"Streaming chunk {chunk_count}",
                                            extra={
                                                "chunk_size": len(chunk),
                                                "accumulated_chars": sum(len(c) for c in full_response),
                                                "chunk_count": chunk_count,
                                            }
                                        )
                                    
                                    yield chunk
                                    
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse streaming chunk: {e}", extra={"line": line[:100]})
                                error_count += 1
                                metrics.error_count = error_count
                                continue
                    
                # Success - break retry loop
                break
                
            except requests.exceptions.Timeout as e:
                error_count += 1
                metrics.error_count = error_count
                last_error = f"Timeout after {self.config.timeout}s"
                
                if attempt < retries:
                    logger.debug(f"Streaming timeout (attempt {attempt + 1}/{retries + 1}), will retry...")
                    # Save partial response before retry
                    if full_response and save_response and not partial_saved:
                        try:
                            partial_text = "".join(full_response)
                            if save_path is None:
                                save_path = Path(f"streaming_response_partial_{int(time_module.time())}.md")
                            metadata = ResponseMetadata(
                                timestamp=datetime.now().isoformat(),
                                model=model_name,
                                prompt=prompt,
                                prompt_length=len(prompt),
                                response_length=len(partial_text),
                                response_tokens_est=len(partial_text) // 4,
                                streaming=True,
                                chunk_count=chunk_count,
                                error_occurred=True,
                                partial_response=True,
                            )
                            save_streaming_response(partial_text, save_path, metadata)
                            partial_saved = True
                            logger.info(f"Saved partial response ({chunk_count} chunks) before retry")
                        except Exception as save_error:
                            logger.warning(f"Failed to save partial response: {save_error}")
                    continue
                else:
                    logger.error(f"Streaming timeout after {retries + 1} attempts: {last_error}")
                    # Save partial response on final failure
                    if full_response and save_response:
                        try:
                            partial_text = "".join(full_response)
                            if save_path is None:
                                save_path = Path(f"streaming_response_partial_{int(time_module.time())}.md")
                            metadata = ResponseMetadata(
                                timestamp=datetime.now().isoformat(),
                                model=model_name,
                                prompt=prompt,
                                prompt_length=len(prompt),
                                response_length=len(partial_text),
                                response_tokens_est=len(partial_text) // 4,
                                streaming=True,
                                chunk_count=chunk_count,
                                streaming_time_seconds=time_module.time() - start_time,
                                error_occurred=True,
                                partial_response=True,
                            )
                            save_streaming_response(partial_text, save_path, metadata)
                            partial_saved = True
                            logger.info(f"Saved partial response ({chunk_count} chunks) after timeout")
                        except Exception as save_error:
                            logger.warning(f"Failed to save partial response: {save_error}")
                    raise LLMConnectionError(
                        f"Streaming timeout ({model_name}): {last_error}",
                        context={"url": url, "model": model_name, "chunks_received": chunk_count}
                    )
                    
            except requests.exceptions.ConnectionError as e:
                error_count += 1
                metrics.error_count = error_count
                last_error = f"Connection error: {e}"
                
                if attempt < retries:
                    logger.debug(f"Streaming connection error (attempt {attempt + 1}/{retries + 1}), will retry...")
                    # Save partial response before retry
                    if full_response and save_response and not partial_saved:
                        try:
                            partial_text = "".join(full_response)
                            if save_path is None:
                                save_path = Path(f"streaming_response_partial_{int(time_module.time())}.md")
                            metadata = ResponseMetadata(
                                timestamp=datetime.now().isoformat(),
                                model=model_name,
                                prompt=prompt,
                                prompt_length=len(prompt),
                                response_length=len(partial_text),
                                response_tokens_est=len(partial_text) // 4,
                                streaming=True,
                                chunk_count=chunk_count,
                                error_occurred=True,
                                partial_response=True,
                            )
                            save_streaming_response(partial_text, save_path, metadata)
                            partial_saved = True
                            logger.info(f"Saved partial response ({chunk_count} chunks) before retry")
                        except Exception as save_error:
                            logger.warning(f"Failed to save partial response: {save_error}")
                    continue
                else:
                    logger.error(f"Streaming connection error after {retries + 1} attempts: {last_error}")
                    # Save partial response on final failure
                    if full_response and save_response:
                        try:
                            partial_text = "".join(full_response)
                            if save_path is None:
                                save_path = Path(f"streaming_response_partial_{int(time_module.time())}.md")
                            metadata = ResponseMetadata(
                                timestamp=datetime.now().isoformat(),
                                model=model_name,
                                prompt=prompt,
                                prompt_length=len(prompt),
                                response_length=len(partial_text),
                                response_tokens_est=len(partial_text) // 4,
                                streaming=True,
                                chunk_count=chunk_count,
                                streaming_time_seconds=time_module.time() - start_time,
                                error_occurred=True,
                                partial_response=True,
                            )
                            save_streaming_response(partial_text, save_path, metadata)
                            partial_saved = True
                            logger.info(f"Saved partial response ({chunk_count} chunks) after connection error")
                        except Exception as save_error:
                            logger.warning(f"Failed to save partial response: {save_error}")
                    raise LLMConnectionError(
                        f"Streaming connection failed ({model_name}): {last_error}",
                        context={"url": url, "model": model_name, "chunks_received": chunk_count}
                    )
                    
            except requests.exceptions.RequestException as e:
                error_count += 1
                metrics.error_count = error_count
                logger.error(f"Streaming request error ({model_name}): {e}")
                raise LLMConnectionError(
                    f"Stream failed ({model_name}): {e}",
                    context={"url": url, "model": model_name, "chunks_received": chunk_count}
                )
        
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
        
        # Log streaming completion
        logger.info(
            "Streaming completed",
            extra={
                "model": model_name,
                "chunk_count": chunk_count,
                "total_chars": total_chars,
                "total_tokens_est": total_tokens_est,
                "streaming_time_seconds": streaming_time,
                "chunks_per_second": metrics.chunks_per_second,
                "bytes_per_second": metrics.bytes_per_second,
                "error_count": error_count,
            }
        )
        
        # Add full response to context
        self.context.add_message("assistant", full_response_text)
        
        # Save response if requested
        if save_response and not partial_saved:
            try:
                if save_path is None:
                    save_path = Path(f"streaming_response_{int(time_module.time())}.md")
                metadata = ResponseMetadata(
                    timestamp=datetime.now().isoformat(),
                    model=model_name,
                    prompt=prompt,
                    prompt_length=len(prompt),
                    response_length=total_chars,
                    response_tokens_est=total_tokens_est,
                    generation_time_seconds=streaming_time,
                    streaming=True,
                    chunk_count=chunk_count,
                    streaming_time_seconds=streaming_time,
                    error_occurred=error_count > 0,
                    partial_response=False,
                )
                if options:
                    metadata.options = {
                        "temperature": options.temperature,
                        "max_tokens": options.max_tokens,
                        "seed": options.seed,
                    }
                save_streaming_response(full_response_text, save_path, metadata)
                logger.info(f"Saved streaming response to {save_path}")
            except Exception as save_error:
                logger.warning(f"Failed to save streaming response: {save_error}")

    def stream_short(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
        save_response: bool = False,
        save_path: Optional[Path] = None,
        log_progress: bool = True
    ) -> Iterator[str]:
        """Stream a short response with comprehensive logging.
        
        Args:
            prompt: User prompt
            model: Model to use
            options: Additional options
            save_response: Whether to save response to file
            save_path: Path to save response
            log_progress: Whether to log streaming progress
            
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
        yield from self.stream_query(
            instruction + prompt, 
            model, 
            options=short_options,
            save_response=save_response,
            save_path=save_path,
            log_progress=log_progress
        )

    def stream_long(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
        save_response: bool = False,
        save_path: Optional[Path] = None,
        log_progress: bool = True
    ) -> Iterator[str]:
        """Stream a comprehensive response with comprehensive logging.
        
        Args:
            prompt: User prompt
            model: Model to use
            options: Additional options
            save_response: Whether to save response to file
            save_path: Path to save response
            log_progress: Whether to log streaming progress
            
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
        yield from self.stream_query(
            instruction + prompt, 
            model, 
            options=long_options,
            save_response=save_response,
            save_path=save_path,
            log_progress=log_progress
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
        """Check if Ollama server is available.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if Ollama is accessible, False otherwise
            
        Example:
            >>> if client.check_connection():
            ...     print("Ollama is ready")
        """
        is_available, _ = self.check_connection_detailed(timeout=timeout)
        return is_available
    
    def check_connection_detailed(self, timeout: float = 2.0) -> Tuple[bool, Optional[str]]:
        """Check if Ollama server is available with detailed status.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            Tuple of (is_available: bool, error_message: str | None)
            - is_available: True if Ollama is accessible
            - error_message: Error description if unavailable, None if available
            
        Example:
            >>> is_available, error = client.check_connection_detailed()
            >>> if not is_available:
            ...     print(f"Ollama unavailable: {error}")
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=timeout
            )
            if response.status_code == 200:
                logger.debug(f"Ollama connection check successful at {self.config.base_url}")
                return (True, None)
            else:
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

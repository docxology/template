"""Core logic for LLM module."""
from __future__ import annotations

import requests
import json
from typing import Dict, Any, Optional, Generator, Iterator, Literal
from enum import Enum

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import LLMConnectionError, LLMError
from infrastructure.llm.config import LLMConfig
from infrastructure.llm.context import ConversationContext
from infrastructure.llm.templates import get_template

logger = get_logger(__name__)


class ResponseMode(str, Enum):
    """Response generation modes for different use cases."""
    SHORT = "short"      # Brief answers (< 150 tokens)
    LONG = "long"        # Comprehensive answers (> 500 tokens)
    STRUCTURED = "structured"  # JSON-formatted structured response


class LLMClient:
    """Client for interacting with LLM providers (Ollama)."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self.context = ConversationContext(max_tokens=self.config.context_window)

    def query(self, prompt: str, model: Optional[str] = None, reset_context: bool = False) -> str:
        """Send a query to the LLM.
        
        Args:
            prompt: User prompt
            model: Model to use (overrides config)
            reset_context: Whether to clear conversation history
            
        Returns:
            Generated text
        """
        if reset_context:
            self.context.clear()
            
        self.context.add_message("user", prompt)
        
        model_name = model or self.config.default_model
        
        try:
            response_text = self._generate_response(model_name)
            self.context.add_message("assistant", response_text)
            return response_text
            
        except LLMConnectionError:
            # Try fallback models
            for fallback in self.config.fallback_models:
                try:
                    logger.info(f"Retrying with fallback model: {fallback}")
                    response_text = self._generate_response(fallback)
                    self.context.add_message("assistant", response_text)
                    return response_text
                except LLMConnectionError:
                    continue
            raise

    def apply_template(self, template_name: str, **kwargs: Any) -> str:
        """Render a template and query the LLM."""
        template = get_template(template_name)
        prompt = template.render(**kwargs)
        return self.query(prompt)

    def query_short(self, prompt: str, model: Optional[str] = None) -> str:
        """Generate a short response (< 150 tokens).
        
        Useful for quick answers, summaries, or yes/no questions.
        """
        model_name = model or self.config.default_model
        instruction = (
            "Provide a concise, brief response (less than 150 words). "
            "Be direct and to the point.\n\n"
        )
        return self.query(instruction + prompt, model=model_name)

    def query_long(self, prompt: str, model: Optional[str] = None) -> str:
        """Generate a comprehensive, detailed response (> 500 tokens).
        
        Useful for in-depth analysis, explanations, and documentation.
        """
        model_name = model or self.config.default_model
        instruction = (
            "Provide a comprehensive, detailed response with examples and "
            "thorough explanation. Use multiple paragraphs if needed.\n\n"
        )
        return self.query(instruction + prompt, model=model_name)

    def query_structured(
        self, 
        prompt: str, 
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a structured JSON response.
        
        Args:
            prompt: User prompt
            schema: JSON schema for response structure (optional)
            model: Model to use (overrides config)
            
        Returns:
            Parsed JSON response as dictionary
        """
        model_name = model or self.config.default_model
        
        schema_instruction = ""
        if schema:
            schema_instruction = f"\n\nReturn valid JSON matching this schema:\n{json.dumps(schema)}"
        
        instruction = (
            "Return your response as valid JSON only, no markdown or extra text. "
            f"{schema_instruction}\n\n"
        )
        
        response_text = self.query(instruction + prompt, model=model_name)
        
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

    def _generate_response(self, model: str) -> str:
        """Generate response from Ollama API."""
        url = f"{self.config.base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": self.context.get_messages(),
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
                "top_p": self.config.top_p
            }
        }
        
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

    def stream_query(self, prompt: str, model: Optional[str] = None) -> Iterator[str]:
        """Stream response from LLM."""
        self.context.add_message("user", prompt)
        model_name = model or self.config.default_model
        url = f"{self.config.base_url}/api/chat"
        
        payload = {
            "model": model_name,
            "messages": self.context.get_messages(),
            "stream": True
        }
        
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

    def stream_short(self, prompt: str, model: Optional[str] = None) -> Iterator[str]:
        """Stream a short response."""
        instruction = (
            "Provide a concise, brief response (less than 150 words). "
            "Be direct and to the point.\n\n"
        )
        yield from self.stream_query(instruction + prompt, model)

    def stream_long(self, prompt: str, model: Optional[str] = None) -> Iterator[str]:
        """Stream a comprehensive response."""
        instruction = (
            "Provide a comprehensive, detailed response with examples and "
            "thorough explanation. Use multiple paragraphs if needed.\n\n"
        )
        yield from self.stream_query(instruction + prompt, model)

    def get_available_models(self) -> list[str]:
        """Get list of available models from Ollama."""
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
        """Check if Ollama server is available."""
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=self.config.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


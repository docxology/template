"""Configuration for LLM module.

Provides comprehensive configuration for Ollama LLM interactions with:
- Environment variable support (OLLAMA_HOST, OLLAMA_MODEL, LLM_*)
- Per-query generation options (temperature, max_tokens, seed, stop)
- System prompt configuration
- Context window and timeout settings
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class GenerationOptions:
    """Per-query generation options for fine-grained control.
    
    Use to override config defaults for specific queries:
    
    Example:
        >>> opts = GenerationOptions(temperature=0.0, seed=42)
        >>> client.query("Explain...", options=opts)
    
    Attributes:
        temperature: Sampling temperature (0.0 = deterministic, 2.0 = creative)
        max_tokens: Maximum tokens to generate (num_predict)
        top_p: Nucleus sampling threshold
        top_k: Top-k sampling (limits vocabulary)
        seed: Random seed for reproducibility
        stop: Stop sequences to end generation
        format_json: Force JSON output format (Ollama-native)
        repeat_penalty: Penalty for token repetition (1.0 = no penalty)
        num_ctx: Context window size for this query
    """
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    seed: Optional[int] = None
    stop: Optional[List[str]] = None
    format_json: bool = False
    repeat_penalty: Optional[float] = None
    num_ctx: Optional[int] = None

    def to_ollama_options(self, defaults: 'LLMConfig') -> Dict[str, Any]:
        """Convert to Ollama API options dict, falling back to config defaults.
        
        Args:
            defaults: LLMConfig with default values
            
        Returns:
            Dict for Ollama API 'options' field
        """
        opts: Dict[str, Any] = {
            "temperature": self.temperature if self.temperature is not None else defaults.temperature,
            "num_predict": self.max_tokens if self.max_tokens is not None else defaults.max_tokens,
            "top_p": self.top_p if self.top_p is not None else defaults.top_p,
        }
        
        if self.top_k is not None:
            opts["top_k"] = self.top_k
        if self.seed is not None:
            opts["seed"] = self.seed
        if self.stop is not None:
            opts["stop"] = self.stop
        if self.repeat_penalty is not None:
            opts["repeat_penalty"] = self.repeat_penalty
        if self.num_ctx is not None:
            opts["num_ctx"] = self.num_ctx
        elif defaults.num_ctx:
            opts["num_ctx"] = defaults.num_ctx
            
        return opts


@dataclass
class LLMConfig:
    """Configuration for LLM interaction with Ollama.
    
    Supports environment variable configuration:
        OLLAMA_HOST: Base URL (default: http://localhost:11434)
        OLLAMA_MODEL: Default model (default: qwen3:4b)
        LLM_TEMPERATURE: Temperature (default: 0.7)
        LLM_MAX_TOKENS: Max tokens (default: 2048)
        LLM_CONTEXT_WINDOW: Context window (default: 4096)
        LLM_TIMEOUT: Request timeout in seconds (default: 300)
        LLM_NUM_CTX: Ollama num_ctx parameter (optional)
        LLM_SEED: Default seed for reproducibility (optional)
    
    Example:
        >>> config = LLMConfig.from_env()
        >>> client = LLMClient(config)
        
        # Or with explicit values
        >>> config = LLMConfig(
        ...     base_url="http://localhost:11434",
        ...     default_model="llama3",
        ...     temperature=0.3,
        ...     seed=42
        ... )
    """
    # Connection settings
    base_url: str = "http://localhost:11434"
    timeout: float = 300.0  # 5 minutes - adequate for long-form generation tasks
    
    # Model settings
    default_model: str = "qwen3:4b"  # Fast with 128K context, excellent instruction following
    fallback_models: List[str] = field(default_factory=lambda: ["llama3-gradient", "llama3", "mistral"])
    
    # Generation settings
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    context_window: int = 131072  # 128K default, qwen3:4b supports 128K
    num_ctx: Optional[int] = None  # Ollama-specific context size
    seed: Optional[int] = None  # Default seed for reproducibility
    
    # Response mode defaults
    short_max_tokens: int = 200  # For short response mode
    long_min_tokens: int = 500   # Minimum for long response mode
    long_max_tokens: int = 4096  # For long response mode
    
    # System prompt
    system_prompt: str = (
        "You are an expert research assistant. "
        "Provide clear, accurate, and scientifically rigorous responses. "
        "Cite sources when possible."
    )
    
    # Whether to automatically inject system prompt into context
    auto_inject_system_prompt: bool = True

    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Create configuration from environment variables.
        
        Reads:
            OLLAMA_HOST: Base URL for Ollama server
            OLLAMA_MODEL: Default model name
            LLM_TEMPERATURE: Generation temperature
            LLM_MAX_TOKENS: Maximum tokens per response
            LLM_CONTEXT_WINDOW: Context window size
            LLM_TIMEOUT: Request timeout
            LLM_NUM_CTX: Ollama num_ctx parameter
            LLM_SEED: Default random seed
            LLM_SYSTEM_PROMPT: Custom system prompt
            
        Returns:
            LLMConfig with environment values or defaults
        """
        def _get_float(key: str, default: float) -> float:
            val = os.environ.get(key)
            if val:
                try:
                    return float(val)
                except ValueError:
                    pass
            return default
        
        def _get_int(key: str, default: int) -> int:
            val = os.environ.get(key)
            if val:
                try:
                    return int(val)
                except ValueError:
                    pass
            return default
        
        def _get_optional_int(key: str) -> Optional[int]:
            val = os.environ.get(key)
            if val:
                try:
                    return int(val)
                except ValueError:
                    pass
            return None
        
        return cls(
            base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            default_model=os.environ.get("OLLAMA_MODEL", "qwen3:4b"),
            temperature=_get_float("LLM_TEMPERATURE", 0.7),
            max_tokens=_get_int("LLM_MAX_TOKENS", 2048),
            context_window=_get_int("LLM_CONTEXT_WINDOW", 131072),
            timeout=_get_float("LLM_TIMEOUT", 300.0),
            num_ctx=_get_optional_int("LLM_NUM_CTX"),
            seed=_get_optional_int("LLM_SEED"),
            system_prompt=os.environ.get("LLM_SYSTEM_PROMPT", cls.system_prompt),
        )

    def with_overrides(self, **kwargs: Any) -> 'LLMConfig':
        """Create a new config with specified overrides.
        
        Args:
            **kwargs: Config fields to override
            
        Returns:
            New LLMConfig with overrides applied
            
        Example:
            >>> config = LLMConfig.from_env()
            >>> fast_config = config.with_overrides(temperature=0.0, timeout=30.0)
        """
        import dataclasses
        current = dataclasses.asdict(self)
        current.update(kwargs)
        return LLMConfig(**current)

    def create_options(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        seed: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> GenerationOptions:
        """Create GenerationOptions with convenient defaults.
        
        Args:
            temperature: Override temperature
            max_tokens: Override max tokens
            seed: Set seed for reproducibility
            stop: Stop sequences
            **kwargs: Additional GenerationOptions fields
            
        Returns:
            GenerationOptions for use with queries
            
        Example:
            >>> config = LLMConfig()
            >>> opts = config.create_options(temperature=0.0, seed=42)
            >>> client.query("...", options=opts)
        """
        return GenerationOptions(
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            stop=stop,
            **kwargs
        )

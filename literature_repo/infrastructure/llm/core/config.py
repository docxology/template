"""Configuration for LLM module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

@dataclass
class GenerationOptions:
    """Per-query generation options for LLM requests.
    
    Allows fine-grained control over generation parameters on a per-query basis.
    Values default to None and will fall back to LLMConfig defaults when converted
    to Ollama API format.
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
    
    def to_ollama_options(self, config: "LLMConfig") -> Dict[str, Any]:
        """Convert to Ollama API options format.
        
        Uses values from this GenerationOptions instance if provided,
        otherwise falls back to LLMConfig defaults.
        
        Args:
            config: LLMConfig instance to use for fallback values
            
        Returns:
            Dictionary compatible with Ollama API options parameter
        """
        options: Dict[str, Any] = {}
        
        # Use GenerationOptions value if provided, otherwise use config default
        if self.temperature is not None:
            options["temperature"] = self.temperature
        else:
            options["temperature"] = config.temperature
            
        if self.max_tokens is not None:
            options["num_predict"] = self.max_tokens
        else:
            options["num_predict"] = config.max_tokens
            
        if self.top_p is not None:
            options["top_p"] = self.top_p
        else:
            options["top_p"] = config.top_p
            
        if self.top_k is not None:
            options["top_k"] = self.top_k
            
        if self.seed is not None:
            options["seed"] = self.seed
        elif config.seed is not None:
            options["seed"] = config.seed
            
        if self.stop is not None:
            options["stop"] = self.stop
            
        if self.repeat_penalty is not None:
            options["repeat_penalty"] = self.repeat_penalty
            
        if self.num_ctx is not None:
            options["num_ctx"] = self.num_ctx
        else:
            options["num_ctx"] = config.context_window
            
        return options


@dataclass
class LLMConfig:
    """Configuration for LLM interaction."""
    
    # Connection settings
    base_url: str = "http://localhost:11434"
    timeout: float = 60.0
    
    # Model settings
    default_model: str = "gemma3:4b"
    fallback_models: list[str] = field(default_factory=lambda: ["mistral", "phi3"])
    
    # Generation settings
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    context_window: int = 131072  # 128K context window (supports gemma3:4b)
    seed: Optional[int] = None
    
    # Response length settings
    short_max_tokens: int = 150
    long_max_tokens: int = 16384  # Increased for longer review outputs
    long_min_tokens: int = 0
    
    # System prompt settings
    system_prompt: str = (
        "You are an expert research assistant. "
        "Provide clear, accurate, and scientifically rigorous responses. "
        "Cite sources when possible."
    )
    auto_inject_system_prompt: bool = True
    
    def __init__(self, *args, **kwargs):
        """Initialize config, supporting num_ctx as alias for context_window."""
        # Handle num_ctx -> context_window mapping
        if 'num_ctx' in kwargs and 'context_window' not in kwargs:
            kwargs['context_window'] = kwargs.pop('num_ctx')
        
        # Manually initialize all dataclass fields
        from dataclasses import fields, MISSING
        
        # Set all fields with defaults first
        for f in fields(self):
            if f.name not in kwargs:
                if f.default != MISSING:
                    object.__setattr__(self, f.name, f.default)
                elif f.default_factory != MISSING:
                    factory = f.default_factory
                    object.__setattr__(self, f.name, factory())
        
        # Override with provided kwargs
        valid_field_names = {f.name for f in fields(self)}
        for key, value in kwargs.items():
            if key in valid_field_names:
                object.__setattr__(self, key, value)

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Create configuration from environment variables."""
        import os
        
        # Read OLLAMA_HOST if set
        base_url = os.environ.get('OLLAMA_HOST', "http://localhost:11434")
        
        # Read LLM configuration from environment variables
        config_kwargs: Dict[str, Any] = {"base_url": base_url}
        
        # Context window (128K default for gemma3:4b)
        if 'LLM_CONTEXT_WINDOW' in os.environ:
            try:
                config_kwargs['context_window'] = int(os.environ['LLM_CONTEXT_WINDOW'])
            except ValueError:
                pass  # Use default
        
        # Alternative: LLM_NUM_CTX (Ollama parameter name)
        if 'LLM_NUM_CTX' in os.environ and 'context_window' not in config_kwargs:
            try:
                config_kwargs['context_window'] = int(os.environ['LLM_NUM_CTX'])
            except ValueError:
                pass  # Use default
        
        # Long max tokens for extended responses
        if 'LLM_LONG_MAX_TOKENS' in os.environ:
            try:
                config_kwargs['long_max_tokens'] = int(os.environ['LLM_LONG_MAX_TOKENS'])
            except ValueError:
                pass  # Use default
        
        # Max tokens (default response length)
        if 'LLM_MAX_TOKENS' in os.environ:
            try:
                config_kwargs['max_tokens'] = int(os.environ['LLM_MAX_TOKENS'])
            except ValueError:
                pass  # Use default
        
        # Temperature
        if 'LLM_TEMPERATURE' in os.environ:
            try:
                config_kwargs['temperature'] = float(os.environ['LLM_TEMPERATURE'])
            except ValueError:
                pass  # Use default
        
        # Timeout
        if 'LLM_TIMEOUT' in os.environ:
            try:
                config_kwargs['timeout'] = float(os.environ['LLM_TIMEOUT'])
            except ValueError:
                pass  # Use default
        
        # Seed
        if 'LLM_SEED' in os.environ:
            try:
                config_kwargs['seed'] = int(os.environ['LLM_SEED'])
            except ValueError:
                pass  # Use default
        
        # Default model
        if 'OLLAMA_MODEL' in os.environ:
            config_kwargs['default_model'] = os.environ['OLLAMA_MODEL']
        
        return cls(**config_kwargs)
    
    def with_overrides(self, **kwargs: Any) -> LLMConfig:
        """Create a new config instance with overridden values.
        
        Args:
            **kwargs: Configuration values to override
            
        Returns:
            New LLMConfig instance with overridden values
            
        Example:
            >>> config = LLMConfig()
            >>> custom = config.with_overrides(default_model="mistral", temperature=0.3)
        """
        # Get current values as dict
        current_values = {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "default_model": self.default_model,
            "fallback_models": self.fallback_models,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "context_window": self.context_window,
            "seed": self.seed,
            "short_max_tokens": self.short_max_tokens,
            "long_max_tokens": self.long_max_tokens,
            "long_min_tokens": self.long_min_tokens,
            "system_prompt": self.system_prompt,
            "auto_inject_system_prompt": self.auto_inject_system_prompt,
        }
        
        # Apply overrides
        current_values.update(kwargs)
        
        return LLMConfig(**current_values)
    
    def create_options(self, **kwargs: Any) -> GenerationOptions:
        """Create GenerationOptions from config with optional overrides.
        
        Uses LLMConfig values as defaults, allowing kwargs to override
        specific options.
        
        Args:
            **kwargs: Generation option values to override
            
        Returns:
            GenerationOptions instance with config defaults and overrides
            
        Example:
            >>> config = LLMConfig()
            >>> opts = config.create_options(temperature=0.0, seed=42)
        """
        # Start with config defaults
        options_dict: Dict[str, Any] = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "seed": self.seed,
        }
        
        # Apply overrides
        options_dict.update(kwargs)
        
        return GenerationOptions(**options_dict)


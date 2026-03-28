"""Configuration for LLM module."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


class ResponseMode(str, Enum):
    """Response generation modes for different use cases."""

    SHORT = "short"  # Brief answers (< 150 tokens)
    LONG = "long"  # Comprehensive answers (> 500 tokens)
    STRUCTURED = "structured"  # JSON-formatted structured response
    RAW = "raw"  # Raw prompt without modification


@dataclass
class GenerationOptions:
    """Per-query generation options for LLM requests.

    Allows fine-grained control over generation parameters on a per-query basis.
    Values default to None and will fall back to OllamaClientConfig defaults when converted
    to Ollama API format.
    """

    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    top_k: int | None = None
    seed: int | None = None
    stop: list[str] | None = None
    format_json: bool = False
    repeat_penalty: float | None = None
    num_ctx: int | None = None

    def to_ollama_options(self, config: "OllamaClientConfig") -> dict[str, Any]:
        """Convert to Ollama API options format.

        Uses values from this GenerationOptions instance if provided,
        otherwise falls back to OllamaClientConfig defaults.

        Args:
            config: OllamaClientConfig instance to use for fallback values

        Returns:
            Dictionary compatible with Ollama API options parameter
        """
        def _pick(override: Any, fallback: Any) -> Any:
            """Return override if not None, else fallback."""
            return override if override is not None else fallback

        options: dict[str, Any] = {
            "temperature": _pick(self.temperature, config.temperature),
            "num_predict": _pick(self.max_tokens, config.max_tokens),
            "top_p": _pick(self.top_p, config.top_p),
            "num_ctx": _pick(self.num_ctx, config.context_window),
        }

        # Optional fields: only include if a value is available
        if self.top_k is not None:
            options["top_k"] = self.top_k
        seed = _pick(self.seed, config.seed)
        if seed is not None:
            options["seed"] = seed
        if self.stop is not None:
            options["stop"] = self.stop
        if self.repeat_penalty is not None:
            options["repeat_penalty"] = self.repeat_penalty

        return options


@dataclass
class OllamaClientConfig:
    """Configuration for LLM interaction.

    Model Selection:
        The default model is gemma3:4b - a reliable model with good quality.
        Override via environment variable for different use cases:

            export OLLAMA_MODEL="gemma3:4b"     # Good quality, medium speed (default)
            export OLLAMA_MODEL="llama3-gradient" # Best quality, slower
            export OLLAMA_MODEL="smollm2"       # Fast testing (if installed)

        Or override programmatically:
            config = OllamaClientConfig(default_model="llama3-gradient")

    Speed vs Quality Trade-offs:
        - smollm2 (135M): ~100+ tok/s, basic quality, great for testing
        - gemma2:2b: ~50 tok/s, good quality, fast
        - gemma3:4b: ~30 tok/s, high quality (default)
        - llama3-gradient: ~15 tok/s, best quality, 256K context
    """

    # Connection settings
    base_url: str = "http://localhost:11434"
    timeout: float = 60.0

    # Model settings - default to fast model for testing
    # Override with OLLAMA_MODEL env var for quality reviews
    default_model: str = "gemma3:4b"  # Reliable default with predictable name
    fallback_models: list[str] = field(
        default_factory=lambda: ["gemma2:2b", "mistral"]
    )

    # Generation settings
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    context_window: int = 131072  # 128K context window (supports gemma3:4b)
    seed: int | None = None

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

    # Heartbeat monitoring settings
    heartbeat_interval: float = 15.0  # Seconds between progress updates
    stall_threshold: float = 60.0  # Seconds without tokens before stall warning
    early_warning_threshold: float = 60.0  # Seconds before first token to trigger early warning

    # Review-specific settings (override via LLM_REVIEW_TIMEOUT, LLM_MAX_INPUT_LENGTH)
    review_timeout: float = 300.0  # Timeout for review operations (LLM_REVIEW_TIMEOUT)
    max_input_length: int = 500000  # Max input character length (LLM_MAX_INPUT_LENGTH)

    def __init__(self, **kwargs: Any):
        """Initialize config, supporting num_ctx as alias for context_window.

        Manual __init__ exists because @dataclass-generated __init__ cannot handle
        the num_ctx→context_window alias or reject unknown kwargs with a clear error.
        Uses dataclasses.fields() internally so it stays in sync with field additions.
        """
        # Handle num_ctx -> context_window mapping
        if "num_ctx" in kwargs and "context_window" not in kwargs:
            kwargs["context_window"] = kwargs.pop("num_ctx")

        # Manually initialize all dataclass fields
        from dataclasses import MISSING, fields

        valid_field_names = {f.name for f in fields(self)}

        # Reject unknown kwargs so typos surface immediately
        unknown = set(kwargs) - valid_field_names
        if unknown:
            raise ValueError(f"OllamaClientConfig received unknown keyword arguments: {sorted(unknown)}")

        # Set all fields with defaults first
        for f in fields(self):
            if f.name not in kwargs:
                if f.default != MISSING:
                    setattr(self, f.name, f.default)
                elif f.default_factory != MISSING:
                    factory = f.default_factory
                    setattr(self, f.name, factory())

        # Override with provided kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    # Environment variable → (config_key, cast_fn) mappings for from_env().
    # LLM_NUM_CTX is handled specially (only used if context_window not already set).
    # OLLAMA_MODEL is a plain string (no cast needed, handled inline).
    _ENV_MAPPINGS: ClassVar[dict[str, tuple[str, type]]] = {
        "LLM_CONTEXT_WINDOW": ("context_window", int),
        "LLM_LONG_MAX_TOKENS": ("long_max_tokens", int),
        "LLM_MAX_TOKENS": ("max_tokens", int),
        "LLM_TEMPERATURE": ("temperature", float),
        "LLM_TIMEOUT": ("timeout", float),
        "LLM_SEED": ("seed", int),
        "LLM_HEARTBEAT_INTERVAL": ("heartbeat_interval", float),
        "LLM_STALL_THRESHOLD": ("stall_threshold", float),
        "LLM_EARLY_WARNING_THRESHOLD": ("early_warning_threshold", float),
        "LLM_REVIEW_TIMEOUT": ("review_timeout", float),
        "LLM_MAX_INPUT_LENGTH": ("max_input_length", int),
    }

    @classmethod
    def from_env(cls) -> OllamaClientConfig:
        """Create configuration from environment variables."""
        import os

        base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        config_kwargs: dict[str, Any] = {"base_url": base_url}

        for env_var, (config_key, cast_fn) in cls._ENV_MAPPINGS.items():
            if env_var in os.environ:
                try:
                    config_kwargs[config_key] = cast_fn(os.environ[env_var])
                except ValueError:
                    logger.warning("Invalid %s=%r, using default", env_var, os.environ[env_var])

        # LLM_NUM_CTX: alternative for context_window (only if not already set)
        if "LLM_NUM_CTX" in os.environ and "context_window" not in config_kwargs:
            try:
                config_kwargs["context_window"] = int(os.environ["LLM_NUM_CTX"])
            except ValueError:
                logger.warning("Invalid LLM_NUM_CTX=%r, using default", os.environ["LLM_NUM_CTX"])

        # OLLAMA_MODEL: plain string, no cast
        if "OLLAMA_MODEL" in os.environ:
            config_kwargs["default_model"] = os.environ["OLLAMA_MODEL"]

        return cls(**config_kwargs)

    def with_overrides(self, **kwargs: Any) -> OllamaClientConfig:
        """Create a new config instance with overridden values.

        Args:
            **kwargs: Configuration values to override

        Returns:
            New OllamaClientConfig instance with overridden values

        Example:
            >>> config = OllamaClientConfig()
            >>> custom = config.with_overrides(default_model="mistral", temperature=0.3)
        """
        from dataclasses import fields as dc_fields

        current_values = {f.name: getattr(self, f.name) for f in dc_fields(self)}

        # Apply overrides
        current_values.update(kwargs)

        return OllamaClientConfig(**current_values)

    def create_options(self, **kwargs: Any) -> GenerationOptions:
        """Create GenerationOptions from config with optional overrides.

        Uses OllamaClientConfig values as defaults, allowing kwargs to override
        specific options.

        Args:
            **kwargs: Generation option values to override

        Returns:
            GenerationOptions instance with config defaults and overrides

        Example:
            >>> config = OllamaClientConfig()
            >>> opts = config.create_options(temperature=0.0, seed=42)
        """
        # Start with config defaults
        options_dict: dict[str, Any] = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "seed": self.seed,
        }

        # Apply overrides
        options_dict.update(kwargs)

        return GenerationOptions(**options_dict)

# Module-level accessors so callers don't need to instantiate OllamaClientConfig.
# Each call creates a fresh OllamaClientConfig.from_env() to pick up env mutations in tests.

def _get_env_config() -> "OllamaClientConfig":
    """Return a config instance populated from the current environment."""
    return OllamaClientConfig.from_env()



def get_max_input_length() -> int:
    """Return the maximum input character length (from env or default)."""
    return _get_env_config().max_input_length


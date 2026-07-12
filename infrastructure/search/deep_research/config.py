"""Configuration for deep research provider dispatch."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
OPENAI_MODEL_ENV = "OPENAI_DEEP_RESEARCH_MODEL"
GEMINI_AGENT_ENV = "GEMINI_DEEP_RESEARCH_AGENT"

DEFAULT_OPENAI_MODEL = "o3-deep-research"
DEFAULT_GEMINI_AGENT = "deep-research-preview-04-2026"

_DOTENV_LOADED = False

# Deep research keys we care about loading from .env.
_DOTENV_KEYS = (OPENAI_API_KEY_ENV, GEMINI_API_KEY_ENV, OPENAI_MODEL_ENV, GEMINI_AGENT_ENV)


def _candidate_dotenv_paths() -> tuple[Path, ...]:
    """Likely ``.env`` locations: the cwd and the repository root."""
    here = Path(__file__).resolve()
    # infrastructure/search/deep_research/config.py -> repo root is parents[3].
    repo_root = here.parents[3] if len(here.parents) > 3 else here.parent
    return (Path.cwd() / ".env", repo_root / ".env")


def _load_dotenv_fallback() -> None:
    """Parse ``.env`` without python-dotenv, setting only missing keys.

    ``python-dotenv`` is an optional extra; when it is absent the shared
    :class:`CredentialManager` silently no-ops, which is exactly why ``providers``
    returned ``[]`` despite a populated ``.env``. This minimal parser keeps the
    deep research CLI working regardless. Real environment variables always win
    (we never overwrite an existing ``os.environ`` entry).
    """
    seen: set[Path] = set()
    for env_path in _candidate_dotenv_paths():
        env_path = env_path.resolve()
        if env_path in seen or not env_path.is_file():
            continue
        seen.add(env_path)
        for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            key, _, value = line.partition("=")
            key = key.strip()
            # Presence, not truthiness, defines an explicit environment
            # override. An empty value intentionally disables a provider and
            # must not be repopulated from a repository dotenv file.
            if key not in _DOTENV_KEYS or key in os.environ:
                continue
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ[key] = value


def ensure_dotenv_loaded() -> None:
    """Load repository ``.env`` keys into ``os.environ`` exactly once.

    The deep research keys (``OPENAI_API_KEY`` / ``GEMINI_API_KEY``) live in the
    repo ``.env`` like every other credential, but :meth:`DeepResearchConfig.from_env`
    reads ``os.getenv`` directly. Without this, ``providers`` reported ``[]``
    even with a fully populated ``.env`` because nothing had loaded it. We first
    reuse the shared :class:`CredentialManager` (python-dotenv) for one source of
    truth, then fall back to a built-in parser so loading still works when the
    optional ``python-dotenv`` extra is not installed. Neither path overrides a
    variable already set in the real environment, so an explicit ``export`` wins.
    """
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    try:
        from infrastructure.core.credentials import CredentialManager

        CredentialManager()  # constructor loads .env via python-dotenv if available
    except Exception as exc:  # noqa: BLE001 - .env loading is best-effort; explicit env still works
        del exc
    try:
        _load_dotenv_fallback()
    except Exception as exc:  # noqa: BLE001 - never let .env parsing crash provider discovery
        del exc
    _DOTENV_LOADED = True


@dataclass(frozen=True)
class DeepResearchConfig:
    """Environment-backed deep research settings."""

    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    openai_model: str = DEFAULT_OPENAI_MODEL
    gemini_agent: str = DEFAULT_GEMINI_AGENT
    default_provider: str = "auto"

    @classmethod
    def from_env(cls) -> "DeepResearchConfig":
        """Construct an instance from environment variables, or return None."""
        ensure_dotenv_loaded()
        return cls(
            openai_api_key=os.getenv(OPENAI_API_KEY_ENV),
            gemini_api_key=os.getenv(GEMINI_API_KEY_ENV),
            openai_model=os.getenv(OPENAI_MODEL_ENV, DEFAULT_OPENAI_MODEL),
            gemini_agent=os.getenv(GEMINI_AGENT_ENV, DEFAULT_GEMINI_AGENT),
        )

    @property
    def has_openai(self) -> bool:
        """Return whether openai is present."""
        return bool(self.openai_api_key)

    @property
    def has_gemini(self) -> bool:
        """Return whether gemini is present."""
        return bool(self.gemini_api_key)


__all__ = [
    "DEFAULT_GEMINI_AGENT",
    "DEFAULT_OPENAI_MODEL",
    "DeepResearchConfig",
    "ensure_dotenv_loaded",
    "GEMINI_AGENT_ENV",
    "GEMINI_API_KEY_ENV",
    "OPENAI_API_KEY_ENV",
    "OPENAI_MODEL_ENV",
]

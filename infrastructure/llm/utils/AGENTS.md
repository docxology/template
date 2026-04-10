# LLM Utilities Module

## Overview

`infrastructure/llm/utils/` holds the concrete Ollama helpers used by the LLM
module: daemon checks, model discovery, model selection, preload helpers, and
stream-heartbeat monitoring.

Prefer importing from `infrastructure.llm.utils.ollama`, which re-exports the
public utility API from `server.py`, `models.py`, and `heartbeat.py`.

## Directory Structure

```text
infrastructure/llm/utils/
├── AGENTS.md
├── __init__.py
├── heartbeat.py
├── models.py
├── ollama.py
└── server.py
```

## Public API

### `ollama.py`

Stable import surface for Ollama helpers.

```python
from infrastructure.llm.utils.ollama import (
    DEFAULT_MODEL_PREFERENCES,
    check_model_loaded,
    ensure_ollama_ready,
    get_available_model_info,
    get_model_info,
    get_model_names,
    is_ollama_running,
    preload_model,
    select_best_model,
    select_small_fast_model,
    start_ollama_server,
)
```

### Server helpers (`server.py`)

```python
def is_ollama_running(base_url: str = "http://localhost:11434", timeout: float = 2.0) -> bool:
    """Check whether the daemon responds on `/api/tags`."""

def start_ollama_server(wait_seconds: float = 3.0, max_retries: int = 2) -> bool:
    """Start `ollama serve` and wait for readiness."""

def pull_ollama_model(
    model_name: str,
    *,
    timeout: float | None = 900.0,
    which=None,
    run=None,
) -> tuple[bool, str | None]:
    """Run ``ollama pull``. Optional ``which`` (like :func:`shutil.which`) and ``run`` (like :func:`subprocess.run`) support tests that use real stub executables instead of patching."""

def ensure_ollama_ready(base_url: str = "http://localhost:11434", auto_start: bool = True) -> bool:
    """Ensure the daemon is reachable and at least one model is installed."""
```

### Model helpers

```python
def get_available_model_info(
    base_url: str = "http://localhost:11434",
    timeout: float = 5.0,
    retries: int = 2,
) -> list[dict[str, Any]]:
    """Return the `/api/tags` payload as model dictionaries."""

def get_model_names(base_url: str = "http://localhost:11434") -> list[str]:
    """Return installed model names."""

def select_best_model(
    preferences: list[str] | None = None,
    base_url: str = "http://localhost:11434",
) -> str | None:
    """Return the first matching model from the preference list."""

def select_small_fast_model(base_url: str = "http://localhost:11434") -> str | None:
    """Return a fast model for smoke tests and short iterations."""

def get_model_info(
    model_name: str,
    base_url: str = "http://localhost:11434",
) -> dict[str, Any] | None:
    """Return metadata for one installed model."""

def check_model_loaded(
    model_name: str,
    base_url: str = "http://localhost:11434",
    timeout: float = 2.0,
) -> tuple[bool, str | None]:
    """Check whether a model is loaded in Ollama memory."""

def preload_model(
    model_name: str,
    base_url: str = "http://localhost:11434",
    timeout: float = 60.0,
    retries: int = 1,
    check_loaded_first: bool = True,
) -> tuple[bool, str | None]:
    """Warm a model with a minimal generation request."""
```

### Heartbeat monitoring

```python
from infrastructure.llm.utils.heartbeat import StreamHeartbeatMonitor

monitor = StreamHeartbeatMonitor(
    operation_name="review",
    timeout_seconds=300.0,
    heartbeat_interval=30.0,
)
```

## Canonical Local Ollama Setup

Use the same local sequence as the review and diagnostics docs:

```bash
ollama serve
ollama pull gemma3:4b
curl http://localhost:11434/api/tags
uv run pytest tests/infra_tests/llm/ -m requires_ollama -v
```

## See Also

- [`README.md`](README.md) - Quick reference
- [`../core/README.md`](../core/README.md) - Core client and configuration
- [`../AGENTS.md`](../AGENTS.md) - Module overview
- [`../../docs/operational/troubleshooting/llm-review.md`](../../docs/operational/troubleshooting/llm-review.md) - Local Ollama setup and review troubleshooting

Consider these rules if they affect your changes.

# LLM Module

## Purpose

`infrastructure/llm/` contains the local-Ollama LLM stack used by the repository. The package provides client configuration, prompt templates, validation helpers, review generation, utilities for checking and selecting models, and a small CLI entry point.

## Layout

```text
infrastructure/llm/
├── __init__.py
├── AGENTS.md
├── README.md
├── cli/
├── core/
├── prompts/
├── review/
├── templates/
├── utils/
└── validation/
```

## Public API

`infrastructure/llm/__init__.py` re-exports the main package surface:

- `LLMClient`
- `GenerationOptions`
- `OllamaClientConfig`
- `generate_review_with_metrics`
- `get_template`
- `is_off_topic`
- `validate_complete`

## Core Modules

### `core/`

Configuration and client primitives for Ollama-backed queries.

- `client.py` provides `LLMClient`
- `config.py` provides `OllamaClientConfig` and `GenerationOptions`
- `context.py` provides conversation state helpers

### `templates/`

Prompt-template helpers for repeatable research workflows.

### `review/`

Review-generation orchestration and metrics collection.

### `utils/`

Ollama helpers for server checks, model discovery, model selection, and startup readiness.

### `validation/`

Validation helpers for content, structure, and review output.

### `cli/`

Thin command-line wrapper around the package. Run it with:

```bash
uv run python -m infrastructure.llm.cli
```

## Configuration

The package is configured from environment variables through `OllamaClientConfig.from_env()`.

Common variables:

- `OLLAMA_HOST`
- `OLLAMA_MODEL`
- `OLLAMA_AUTO_START`
- `LOG_LEVEL`
- `LLM_*` generation settings where supported by the config layer

## Testing

Use real code paths and the repository’s no-mocks policy (`MagicMock` / `unittest.mock.patch` are not used in this suite).

- **Deterministic HTTP:** [`tests/infra_tests/llm/conftest.py`](../../tests/infra_tests/llm/conftest.py) starts `pytest_httpserver` and, by default, points `OLLAMA_HOST` at it (`patch_llm_client_for_tests`). POST `/api/chat` behavior lives in [`tests/infra_tests/llm/ollama_stub_server.py`](../../tests/infra_tests/llm/ollama_stub_server.py).
- **Subprocess helpers:** [`utils/server.py`](utils/server.py) `pull_ollama_model` accepts optional `which` / `run` so tests can use real stub scripts instead of patching imports.
- **Real daemon:** mark tests with `@pytest.mark.requires_ollama` for local Ollama smoke checks.
- **CLI:** invoke with `uv run python -m infrastructure.llm.cli ...` when end-to-end behavior matters.

There is no separate `cov-fail-under` for `infrastructure.llm` alone in `pyproject.toml`; the whole infrastructure gate applies. Re-measure the LLM package with:

```bash
uv run pytest tests/infra_tests/llm/ -m "not requires_ollama" \
  --cov=infrastructure.llm --cov-report=term-missing --cov-fail-under=0
uv run pytest tests/infra_tests/llm/ -v
uv run pytest tests/infra_tests/llm/ -m requires_ollama -v
```

## Documentation Pointers

- `README.md`
- `core/README.md`
- `utils/README.md`
- `cli/README.md`
- `../../../docs/operational/troubleshooting/llm-review.md`
- `../../../docs/operational/troubleshooting/llm-diagnostics.md`

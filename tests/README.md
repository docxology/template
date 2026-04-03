# tests/ - Test Suite

The `tests/` tree covers infrastructure modules, integration behavior, and project-specific code. Tests use real data, real subprocesses, and real services when available.

## Running Tests

```bash
uv run pytest tests/ --cov=infrastructure --cov=projects/{name}/src --cov-report=html
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60
uv run pytest projects/{name}/tests/ --cov=projects/{name}/src --cov-fail-under=90
uv run pytest tests/integration/ -v
```

## Layout

```text
tests/
├── AGENTS.md
├── infra_tests/
│   ├── AGENTS.md
│   ├── README.md
│   ├── core/
│   ├── documentation/
│   ├── llm/
│   ├── publishing/
│   ├── rendering/
│   ├── reporting/
│   ├── scientific/
│   ├── skills/
│   └── validation/
├── integration/
│   ├── AGENTS.md
│   ├── README.md
│   ├── conftest.py
│   ├── test_bash_utils.sh
│   ├── test_edge_cases_and_error_paths.py
│   ├── test_environment_setup.py
│   ├── test_execute_pipeline_cli.py
│   ├── test_executive_report_generation.py
│   ├── test_figure_equation_citation.py
│   ├── test_logging.py
│   ├── test_module_interoperability.py
│   ├── test_output_copying.py
│   └── test_run_sh.py
```

## Rules

- Use the no-mocks policy.
- Prefer `uv run` for test commands.
- Keep infrastructure tests separate from project tests.
- Keep integration tests focused on end-to-end behavior.

## Ollama (`@pytest.mark.requires_ollama`)

Session setup lives in [`conftest.py`](conftest.py) as `ensure_ollama_for_tests`. Any test marked `requires_ollama` triggers it once per session (including under `tests/integration/`).

- **Default**: if the daemon is up but no “small/fast” preference model is installed (see `SMALL_FAST_MODEL_PREFERENCES` in `infrastructure.llm.utils.models`), the harness runs `ollama pull` for **`OLLAMA_TEST_PULL_MODEL`** (default `smollm2`). First pull needs network and can take several minutes; override timeout with **`OLLAMA_TEST_PULL_TIMEOUT`** (seconds; default `900`, or `none` for no limit).
- **Air-gapped / pre-seeded images**: set **`OLLAMA_SKIP_TEST_MODEL_PULL=1`** to skip auto-pull. You must still have at least one installed model; without a small/fast preference model, some tests may skip or use slower fallbacks.
- **LLM HTTP fakes**: `tests/infra_tests/llm/conftest.py` points `OLLAMA_HOST` at `pytest_httpserver` for most tests. That is **not** the Ollama daemon—only contract testing for the HTTP client. Real-daemon tests use an explicit `OllamaClientConfig` with default `base_url` or [`tests/infra_tests/llm/real_ollama_client.py`](infra_tests/llm/real_ollama_client.py).

Skip all Ollama-tied tests: `pytest -m 'not requires_ollama'`.

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`infra_tests/README.md`](infra_tests/README.md)
- [`integration/README.md`](integration/README.md)

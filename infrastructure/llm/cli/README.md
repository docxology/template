# LLM CLI

Command-line access to the local Ollama-backed LLM helpers in `infrastructure/llm/`.

## Quick Start

```bash
uv run python -m infrastructure.llm.cli check
uv run python -m infrastructure.llm.cli models
uv run python -m infrastructure.llm.cli query "What is machine learning?"
uv run python -m infrastructure.llm.cli query --short "Summarize this in one paragraph"
uv run python -m infrastructure.llm.cli template --list
uv run python -m infrastructure.llm.cli template summarize_abstract --input "Abstract text..."
```

## Commands

### `query`

Send a prompt to the configured Ollama client.

```bash
uv run python -m infrastructure.llm.cli query "Explain backpropagation"
uv run python -m infrastructure.llm.cli query --short "Summarize this section"
uv run python -m infrastructure.llm.cli query --long "Explain this in detail"
uv run python -m infrastructure.llm.cli query --stream "Write a short poem"
uv run python -m infrastructure.llm.cli query --model gemma3:4b "Use this model"
uv run python -m infrastructure.llm.cli query --temperature 0.0 --seed 42 --max-tokens 256 "Deterministic output"
```

Available flags:

- `--short`
- `--long`
- `--stream`
- `--model`
- `--temperature`
- `--max-tokens`
- `--seed`

The command loads configuration from `OllamaClientConfig.from_env()`, checks that Ollama is reachable, and then uses `LLMClient` to execute the request.

### `check`

Verify that the configured Ollama endpoint is reachable.

```bash
uv run python -m infrastructure.llm.cli check
```

If the daemon is not running, start it with:

```bash
ollama serve
```

### `models`

List available models from the local Ollama daemon.

```bash
uv run python -m infrastructure.llm.cli models
```

### `template`

Apply a named prompt template from `infrastructure.llm.templates`.

```bash
uv run python -m infrastructure.llm.cli template --list
uv run python -m infrastructure.llm.cli template summarize_abstract --input "Abstract text..."
```

Options:

- `name`
- `--list`
- `--input`

## Configuration

The CLI inherits its configuration from environment variables handled by `OllamaClientConfig.from_env()`.

Common variables:

- `OLLAMA_HOST`
- `OLLAMA_MODEL`
- `OLLAMA_AUTO_START`
- `LOG_LEVEL`

## Testing

Run the CLI-related tests with:

```bash
uv run pytest tests/infra_tests/llm/ -v
uv run pytest tests/infra_tests/llm/ -m requires_ollama -v
```

The first command covers deterministic behavior. The second exercises the real-daemon smoke path and requires a running Ollama instance.

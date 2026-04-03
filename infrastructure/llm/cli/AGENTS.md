# LLM CLI Module

## Purpose

`infrastructure/llm/cli/` is the thin command-line wrapper around the local Ollama-backed LLM modules. It should stay focused on parsing arguments, loading config, and printing results.

## Layout

```text
infrastructure/llm/cli/
├── AGENTS.md
├── README.md
├── __init__.py
└── main.py
```

## Entry Point

Run the CLI with:

```bash
uv run python -m infrastructure.llm.cli
```

## Implementation Surface

`main.py` defines:

- `CLIError`
- `query_command(args: argparse.Namespace) -> None`
- `check_command(args: argparse.Namespace) -> None`
- `models_command(args: argparse.Namespace) -> None`
- `template_command(args: argparse.Namespace) -> None`
- `create_parser() -> argparse.ArgumentParser`
- `main() -> None`

## Commands

### `query`

Uses `OllamaClientConfig.from_env()` and `LLMClient` to send a prompt to the configured Ollama endpoint.

Flags:

- `--short`
- `--long`
- `--stream`
- `--model`
- `--temperature`
- `--max-tokens`
- `--seed`

### `check`

Verifies that the configured Ollama endpoint is reachable.

### `models`

Lists available models from the local Ollama daemon.

### `template`

Applies a prompt template from `infrastructure.llm.templates`. Supports `--list` and `--input`.

## Dependencies

The CLI imports:

- `LLMClient`
- `GenerationOptions`
- `OllamaClientConfig`
- `select_best_model`
- `is_ollama_running`
- `TEMPLATES`
- `get_template`

## Testing

- Deterministic tests should cover parser wiring and command behavior.
- Real-daemon smoke tests should use `@pytest.mark.requires_ollama`.
- End-to-end CLI tests should run through `uv run python -m infrastructure.llm.cli ...`.

## Related Docs

- `README.md`
- `../README.md`
- `../AGENTS.md`
- `../core/README.md`
- `../utils/README.md`
- `../../../docs/operational/troubleshooting/llm-review.md`

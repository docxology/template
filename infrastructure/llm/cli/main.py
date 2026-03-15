"""CLI interface for LLM operations.

Thin orchestrator wrapping infrastructure.llm module functionality.
Provides command-line access to LLM queries and utilities.

Usage:
    python3 -m infrastructure.llm.cli query "What is machine learning?"
    python3 -m infrastructure.llm.cli query --short "Summarize X"
    python3 -m infrastructure.llm.cli query --long "Explain X in detail"
    python3 -m infrastructure.llm.cli check
    python3 -m infrastructure.llm.cli models
"""

from __future__ import annotations

import argparse
import sys

from infrastructure.core.logging_utils import get_logger
from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import GenerationOptions, OllamaClientConfig

logger = get_logger(__name__)


class CLIError(Exception):
    """Raised when a CLI command fails with a known error condition."""

    def __init__(self, message: str, exit_code: int = 1):
        """Initialize CLI error with message and exit code."""
        super().__init__(message)
        self.exit_code = exit_code


def query_command(args: argparse.Namespace) -> None:
    """Handle query command."""
    from infrastructure.llm.utils.ollama import is_ollama_running, select_best_model

    config = OllamaClientConfig.from_env()

    # Apply command-line overrides
    if args.model:
        config = config.with_overrides(default_model=args.model)
    elif is_ollama_running():
        # Auto-discover best available model
        best_model = select_best_model()
        if best_model:
            config = config.with_overrides(default_model=best_model)

    client = LLMClient(config)

    # Check connection first
    if not client.check_connection():
        raise CLIError("Cannot connect to Ollama. Is it running? Start with: ollama serve")

    # Build generation options
    opts = GenerationOptions(
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        seed=args.seed,
    )

    prompt = args.prompt

    if args.stream:
        # Streaming output
        if args.short:
            response_iter = client.stream_short(prompt, options=opts)
        elif args.long:
            response_iter = client.stream_long(prompt, options=opts)
        else:
            response_iter = client.stream_query(prompt, options=opts)

        for chunk in response_iter:
            print(chunk, end="", flush=True)
        print()  # Final newline
    else:
        # Non-streaming output
        if args.short:
            response = client.query_short(prompt, options=opts)
        elif args.long:
            response = client.query_long(prompt, options=opts)
        else:
            response = client.query(prompt, options=opts)

        print(response)


def check_command(args: argparse.Namespace) -> None:
    """Handle check command - verify Ollama connection."""
    config = OllamaClientConfig.from_env()
    client = LLMClient(config)

    logger.info(f"Checking connection to {config.base_url}")

    if client.check_connection():
        print("✓ Ollama is running and accessible")
        print(f"  Default model: {config.default_model}")
        print(f"  Temperature: {config.temperature}")
        print(f"  Max tokens: {config.max_tokens}")
    else:
        raise CLIError(f"Cannot connect to Ollama at {config.base_url}. Start with: ollama serve")


def models_command(args: argparse.Namespace) -> None:
    """Handle models command - list available models."""
    config = OllamaClientConfig.from_env()
    client = LLMClient(config)

    if not client.check_connection():
        raise CLIError("Cannot connect to Ollama. Is it running?")

    models = client.get_available_models()

    if models:
        print("Available models:")
        for model in sorted(models):
            marker = " (default)" if model == config.default_model else ""
            print(f"  - {model}{marker}")
    else:
        print("No models found. Pull a model with: ollama pull gemma3:4b")


def template_command(args: argparse.Namespace) -> None:
    """Handle template command - apply a research template."""
    from infrastructure.llm.templates import TEMPLATES, get_template

    if args.list:
        print("Available templates:")
        for name in sorted(TEMPLATES.keys()):
            print(f"  - {name}")
        return

    if not args.name:
        raise CLIError("Template name required. Use --list to see available.")

    config = OllamaClientConfig.from_env()
    client = LLMClient(config)

    if not client.check_connection():
        raise CLIError("Cannot connect to Ollama.")

    # Read input from stdin or argument
    if args.input:
        text = args.input
    else:
        print("Enter text (Ctrl+D to finish):", file=sys.stderr)
        text = sys.stdin.read()

    # Apply template - map common variable names
    template = get_template(args.name)

    # Templates use different variable names - try common ones
    kwargs = {}
    if "text" in template.template_str:
        kwargs["text"] = text
    elif "code" in template.template_str:
        kwargs["code"] = text
    elif "stats" in template.template_str:
        kwargs["stats"] = text
    elif "summaries" in template.template_str:
        kwargs["summaries"] = text
    else:
        kwargs["text"] = text  # Default

    response = client.apply_template(args.name, **kwargs)
    print(response)


def create_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Query local LLMs via Ollama for research tasks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s query "What is machine learning?"
  %(prog)s query --short "Summarize X"
  %(prog)s query --long "Explain X in detail"
  %(prog)s query --stream "Write a poem"
  %(prog)s check
  %(prog)s models
  %(prog)s template --list
  %(prog)s template summarize_abstract --input "Abstract text..."
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Query command
    query_parser = subparsers.add_parser("query", help="Send a query to the LLM")
    query_parser.add_argument("prompt", help="The prompt to send")
    query_parser.add_argument(
        "--short", action="store_true", help="Request a short response (< 150 tokens)"
    )
    query_parser.add_argument(
        "--long", action="store_true", help="Request a detailed response (> 500 tokens)"
    )
    query_parser.add_argument("--stream", action="store_true", help="Stream response in real-time")
    query_parser.add_argument(
        "--model", type=str, default=None, help="Model to use (overrides OLLAMA_MODEL)"
    )
    query_parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Sampling temperature (0.0 = deterministic)",
    )
    query_parser.add_argument(
        "--max-tokens", type=int, default=None, help="Maximum tokens to generate"
    )
    query_parser.add_argument(
        "--seed", type=int, default=None, help="Random seed for reproducibility"
    )
    query_parser.set_defaults(func=query_command)

    # Check command
    check_parser = subparsers.add_parser("check", help="Check Ollama connection")
    check_parser.set_defaults(func=check_command)

    # Models command
    models_parser = subparsers.add_parser("models", help="List available models")
    models_parser.set_defaults(func=models_command)

    # Template command
    template_parser = subparsers.add_parser("template", help="Apply a research template")
    template_parser.add_argument("name", nargs="?", default=None, help="Template name to apply")
    template_parser.add_argument("--list", action="store_true", help="List available templates")
    template_parser.add_argument(
        "--input", type=str, default=None, help="Input text (otherwise read from stdin)"
    )
    template_parser.set_defaults(func=template_command)

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        raise SystemExit(1)

    try:
        args.func(args)
    except KeyboardInterrupt as e:
        logger.info("Interrupted")
        raise SystemExit(130) from e
    except CLIError as e:
        logger.error(str(e))
        raise SystemExit(e.exit_code) from e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()

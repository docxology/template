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

import argparse
import sys
from typing import Optional

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import LLMConfig, GenerationOptions
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def query_command(args: argparse.Namespace) -> None:
    """Handle query command."""
    from infrastructure.llm.utils.ollama import select_best_model, is_ollama_running
    
    config = LLMConfig.from_env()
    
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
        print("Error: Cannot connect to Ollama. Is it running?", file=sys.stderr)
        print("Start with: ollama serve", file=sys.stderr)
        sys.exit(1)
    
    # Build generation options
    opts = GenerationOptions(
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        seed=args.seed,
    )
    
    prompt = args.prompt
    
    try:
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
            
    except KeyboardInterrupt:
        print("\n[Interrupted]", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def check_command(args: argparse.Namespace) -> None:
    """Handle check command - verify Ollama connection."""
    config = LLMConfig.from_env()
    client = LLMClient(config)
    
    print(f"Checking connection to {config.base_url}...")
    
    if client.check_connection():
        print("✓ Ollama is running and accessible")
        print(f"  Default model: {config.default_model}")
        print(f"  Temperature: {config.temperature}")
        print(f"  Max tokens: {config.max_tokens}")
        sys.exit(0)
    else:
        print("✗ Cannot connect to Ollama", file=sys.stderr)
        print(f"  Tried: {config.base_url}", file=sys.stderr)
        print("  Start Ollama with: ollama serve", file=sys.stderr)
        sys.exit(1)


def models_command(args: argparse.Namespace) -> None:
    """Handle models command - list available models."""
    config = LLMConfig.from_env()
    client = LLMClient(config)
    
    if not client.check_connection():
        print("Error: Cannot connect to Ollama. Is it running?", file=sys.stderr)
        sys.exit(1)
    
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
        print("Error: Template name required. Use --list to see available.", file=sys.stderr)
        sys.exit(1)
    
    config = LLMConfig.from_env()
    client = LLMClient(config)
    
    if not client.check_connection():
        print("Error: Cannot connect to Ollama.", file=sys.stderr)
        sys.exit(1)
    
    # Read input from stdin or argument
    if args.input:
        text = args.input
    else:
        print("Enter text (Ctrl+D to finish):", file=sys.stderr)
        text = sys.stdin.read()
    
    try:
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
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
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
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Send a query to the LLM")
    query_parser.add_argument("prompt", help="The prompt to send")
    query_parser.add_argument(
        "--short", action="store_true",
        help="Request a short response (< 150 tokens)"
    )
    query_parser.add_argument(
        "--long", action="store_true",
        help="Request a detailed response (> 500 tokens)"
    )
    query_parser.add_argument(
        "--stream", action="store_true",
        help="Stream response in real-time"
    )
    query_parser.add_argument(
        "--model", type=str, default=None,
        help="Model to use (overrides OLLAMA_MODEL)"
    )
    query_parser.add_argument(
        "--temperature", type=float, default=None,
        help="Sampling temperature (0.0 = deterministic)"
    )
    query_parser.add_argument(
        "--max-tokens", type=int, default=None,
        help="Maximum tokens to generate"
    )
    query_parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility"
    )
    query_parser.set_defaults(func=query_command)
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check Ollama connection")
    check_parser.set_defaults(func=check_command)
    
    # Models command
    models_parser = subparsers.add_parser("models", help="List available models")
    models_parser.set_defaults(func=models_command)
    
    # Template command
    template_parser = subparsers.add_parser(
        "template", help="Apply a research template"
    )
    template_parser.add_argument(
        "name", nargs="?", default=None,
        help="Template name to apply"
    )
    template_parser.add_argument(
        "--list", action="store_true",
        help="List available templates"
    )
    template_parser.add_argument(
        "--input", type=str, default=None,
        help="Input text (otherwise read from stdin)"
    )
    template_parser.set_defaults(func=template_command)
    
    args = parser.parse_args()
    
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()


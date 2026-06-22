"""CLI interface for rendering operations.

Thin orchestrator wrapping infrastructure.rendering module functionality.
"""

import argparse
from collections.abc import Sequence
from pathlib import Path

from infrastructure.core.cli_scaffold import emit_schema
from infrastructure.core.logging.utils import get_logger

from .core import RenderManager

logger = get_logger(__name__)


def render_pdf_command(args: argparse.Namespace) -> int:
    """Handle PDF rendering. Returns a process exit code (0 ok, 1 error)."""
    manager = RenderManager()
    source = Path(args.source)

    if not source.exists():
        logger.error(f"Source file not found: {source}")
        return 1

    logger.info(f"Rendering PDF: {source}")
    output = manager.render_pdf(source)
    print(f"Generated: {output}")
    return 0


def render_all_command(args: argparse.Namespace) -> int:
    """Handle rendering all formats. Returns a process exit code (0 ok, 1 error)."""
    manager = RenderManager()
    source = Path(args.source)

    if not source.exists():
        logger.error(f"Source file not found: {source}")
        return 1

    logger.info(f"Rendering all formats: {source}")
    outputs = manager.render_all(source)

    for output in outputs:
        print(f"Generated: {output}")
    return 0


def render_slides_command(args: argparse.Namespace) -> int:
    """Handle slide rendering. Returns a process exit code (0 ok, 1 error)."""
    manager = RenderManager()
    source = Path(args.source)

    if not source.exists():
        logger.error(f"Source file not found: {source}")
        return 1

    fmt = args.format or "beamer"
    logger.info(f"Rendering slides ({fmt}): {source}")
    output = manager.render_slides(source, output_format=fmt)
    print(f"Generated: {output}")
    return 0


def render_web_command(args: argparse.Namespace) -> int:
    """Handle web output rendering. Returns a process exit code (0 ok, 1 error)."""
    manager = RenderManager()
    source = Path(args.source)

    if not source.exists():
        logger.error(f"Source file not found: {source}")
        return 1

    logger.info(f"Rendering web output: {source}")
    output = manager.render_web(source)
    print(f"Generated: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the argparse parser for the rendering CLI."""
    parser = argparse.ArgumentParser(description="Render documents in multiple formats (PDF, HTML, slides).")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # PDF rendering
    pdf_parser = subparsers.add_parser("pdf", help="Render PDF")
    pdf_parser.add_argument("source", help="Source file (TeX or Markdown)")
    pdf_parser.set_defaults(func=render_pdf_command)

    # All formats
    all_parser = subparsers.add_parser("all", help="Render all formats")
    all_parser.add_argument("source", help="Source file")
    all_parser.set_defaults(func=render_all_command)

    # Slides
    slides_parser = subparsers.add_parser("slides", help="Render slides")
    slides_parser.add_argument("source", help="Source file")
    slides_parser.add_argument(
        "--format",
        choices=["beamer", "revealjs"],
        default="beamer",
        help="Output format",
    )
    slides_parser.set_defaults(func=render_slides_command)

    # Web
    web_parser = subparsers.add_parser("web", help="Render web output")
    web_parser.add_argument("source", help="Source file")
    web_parser.set_defaults(func=render_web_command)

    # Schema (uniform parameter-contract introspection)
    schema_parser = subparsers.add_parser("schema", help="Print this CLI's parameter schema as JSON and exit")
    schema_parser.set_defaults(func=lambda _args: emit_schema(build_parser()))

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``). Accepting
            ``argv`` lets agents and tests invoke this CLI headlessly.

    Returns:
        Process exit code (0 success, 1 error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        return int(args.func(args))
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

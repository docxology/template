"""CLI interface for core infrastructure modules.

This module provides command-line interfaces for core pipeline functionality,
extracted from bash scripts into testable Python CLI.

Part of the infrastructure layer (Layer 1) - reusable across all projects.

Implementation is split across:
- ``cli_parser``: argument parser definition
- ``cli_handlers``: command handler functions
"""

from __future__ import annotations

import sys

from infrastructure.core.logging.utils import get_logger, setup_logger
from infrastructure.core.errors import CLI_COMMAND_FAILED, CLI_UNKNOWN_COMMAND

# Re-export public API so existing imports continue to work
from infrastructure.core.cli_parser import create_parser  # noqa: F401
from infrastructure.core.cli_handlers import (  # noqa: F401
    handle_discover_command,
    handle_inventory_command,
    handle_multi_project_command,
    handle_pipeline_command,
)

logger = get_logger(__name__)


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        setup_logger("infrastructure.core.cli")

        if args.command == "pipeline":
            return handle_pipeline_command(args)
        elif args.command == "multi-project":
            return handle_multi_project_command(args)
        elif args.command == "inventory":
            return handle_inventory_command(args)
        elif args.command == "discover":
            return handle_discover_command(args)
        else:
            logger.error(CLI_UNKNOWN_COMMAND.format(command=args.command))
            return 1

    except Exception as e:  # noqa: BLE001 - top-level CLI handler must catch all
        logger.error(CLI_COMMAND_FAILED.format(error=f"{type(e).__name__}: {e}"))
        return 1


if __name__ == "__main__":
    sys.exit(main())

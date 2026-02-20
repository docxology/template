#!/usr/bin/env python3
"""Load manuscript configuration script - THIN ORCHESTRATOR

This script reads project/manuscript/config.yaml and exports the values as environment
variables for use by bash scripts. Environment variables take precedence over
config file values.

All business logic is in infrastructure/core/config_loader.py
This script handles only bash export format.

Usage:
    source <(python3 infrastructure/core/config_cli.py)
    # or
    eval "$(python3 infrastructure/core/config_cli.py)"
    # or with project specification
    eval "$(python3 infrastructure/core/config_cli.py --project act_inf_metaanalysis)"
"""

import argparse
import sys
from pathlib import Path

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Fix repo_root calculation: go up 3 levels from infrastructure/core/config_cli.py to repo root
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

try:
    from infrastructure.core.config_loader import (YAML_AVAILABLE,
                                                   get_config_as_env_vars)
except ImportError as e:
    logger.error(f"Failed to import from infrastructure/core/config_loader.py: {e}")
    logger.error("Falling back to environment variables only")
    sys.exit(0)


def main() -> None:
    """Main function to load and export configuration."""
    parser = argparse.ArgumentParser(
        description="Load manuscript configuration and export as environment variables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export config for default project
  eval "$(python3 infrastructure/core/config_cli.py)"
  
  # Export config for specific project
  eval "$(python3 infrastructure/core/config_cli.py --project act_inf_metaanalysis)"
  
  # Use in bash script
  source <(python3 infrastructure/core/config_cli.py)
        """,
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Project name (default: auto-detect from current directory or use 'project')",
    )

    args = parser.parse_args()

    if not YAML_AVAILABLE:
        logger.error("PyYAML not installed. Install with: pip install pyyaml")
        logger.error("Falling back to environment variables only")
        sys.exit(0)

    # Determine which project to use
    # For backward compatibility, if no project specified, use the default behavior
    # which looks for repo_root/project/manuscript/config.yaml
    # If project is specified, we could extend this to look in projects/{project}/manuscript/config.yaml
    # but for now, maintain backward compatibility with the original single-project structure

    # Get configuration respecting existing environment variables
    env_vars = get_config_as_env_vars(repo_root, respect_existing=True)

    # Export as bash variable assignments
    for key, value in env_vars.items():
        # Escape quotes for bash
        if key == "AUTHOR_DETAILS":
            # Preserve backslashes for LaTeX in AUTHOR_DETAILS
            value_escaped = value.replace('"', '\\"')
        else:
            value_escaped = value.replace('"', '\\"')
        print(f'export {key}="{value_escaped}"')


if __name__ == "__main__":
    main()

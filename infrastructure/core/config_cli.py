#!/usr/bin/env python3
"""Load manuscript configuration script - THIN ORCHESTRATOR

This script reads project/manuscript/config.yaml and exports the values as environment
variables for use by bash scripts. Environment variables take precedence over
config file values.

All business logic is in infrastructure/core/config_loader.py
This script handles only bash export format.

Usage:
    source <(python3 repo_utilities/load_manuscript_config.py)
    # or
    eval "$(python3 repo_utilities/load_manuscript_config.py)"
"""

import sys
from pathlib import Path

# Add infrastructure to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

try:
    from infrastructure.core.config_loader import get_config_as_env_vars, YAML_AVAILABLE
except ImportError as e:
    print(f"# Error: Failed to import from infrastructure/core/config_loader.py: {e}", file=sys.stderr)
    print("# Falling back to environment variables only", file=sys.stderr)
    sys.exit(0)


def main():
    """Main function to load and export configuration."""
    if not YAML_AVAILABLE:
        print("# Error: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
        print("# Falling back to environment variables only", file=sys.stderr)
        sys.exit(0)
    
    # Get configuration respecting existing environment variables
    env_vars = get_config_as_env_vars(repo_root, respect_existing=True)
    
    # Export as bash variable assignments
    for key, value in env_vars.items():
        # Escape quotes for bash
        if key == 'AUTHOR_DETAILS':
            # Preserve backslashes for LaTeX in AUTHOR_DETAILS
            value_escaped = value.replace('"', '\\"')
        else:
            value_escaped = value.replace('"', '\\"')
        print(f'export {key}="{value_escaped}"')


if __name__ == '__main__':
    main()

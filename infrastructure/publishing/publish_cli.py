#!/usr/bin/env python3
"""Wrapper script for publishing releases."""
import argparse
import sys
from pathlib import Path

# Add root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from infrastructure import publishing
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Create a GitHub release with PDF assets.

    Parses command-line arguments for GitHub authentication and release
    configuration, then creates a new release with all PDF files found
    in the output/pdf directory attached as assets.

    Args:
        None. Configuration is provided via command-line arguments:
            --token: GitHub personal access token (required).
            --repo: Repository in 'owner/repo' format (required).
            --tag: Git tag name for the release (required).
            --name: Human-readable release title (required).

    Returns:
        None. Prints the release URL on success.

    Raises:
        SystemExit: If required arguments are missing.
        PublishingError: If the GitHub API request fails.
    """
    parser = argparse.ArgumentParser(description="Publish release.")
    parser.add_argument("--token", required=True, help="GitHub token")
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument("--tag", required=True, help="Tag name")
    parser.add_argument("--name", required=True, help="Release name")

    args = parser.parse_args()

    # Find assets
    assets = list(Path("output/pdf").glob("*.pdf"))

    logger.info(f"Creating release {args.name} ({args.tag}) in {args.repo}...")
    url = publishing.create_github_release(
        args.tag,
        args.name,
        "Release created by infrastructure tools.",
        assets,
        args.token,
        args.repo,
    )
    print(f"Release created: {url}")


if __name__ == "__main__":
    main()

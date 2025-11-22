#!/usr/bin/env python3
"""Wrapper script for publishing releases."""
import argparse
import sys
from pathlib import Path

# Add root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from infrastructure import publishing

def main():
    parser = argparse.ArgumentParser(description="Publish release.")
    parser.add_argument("--token", required=True, help="GitHub token")
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument("--tag", required=True, help="Tag name")
    parser.add_argument("--name", required=True, help="Release name")
    
    args = parser.parse_args()
    
    # Find assets
    assets = list(Path("output/pdf").glob("*.pdf"))
    
    print(f"Creating release {args.name} ({args.tag}) in {args.repo}...")
    url = publishing.create_github_release(
        args.tag, args.name, "Release created by infrastructure tools.",
        assets, args.token, args.repo
    )
    print(f"Release created: {url}")

if __name__ == "__main__":
    main()


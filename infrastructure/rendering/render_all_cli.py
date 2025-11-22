#!/usr/bin/env python3
"""Wrapper script for rendering all formats."""
import sys
from pathlib import Path

# Add root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from infrastructure.rendering import RenderManager

def main():
    manager = RenderManager()
    
    # Find sources
    manuscript_dir = Path("manuscript")
    if not manuscript_dir.exists():
        print("No manuscript directory found.")
        sys.exit(1)
        
    for source in manuscript_dir.glob("*.tex"):
        print(f"Rendering {source}...")
        outputs = manager.render_all(source)
        for out in outputs:
            print(f"  Generated: {out}")

if __name__ == "__main__":
    main()


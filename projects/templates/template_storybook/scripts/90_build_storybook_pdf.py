from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from storybook.rendering import build_storybook_pdf


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args(argv)
    result = build_storybook_pdf(args.project_root)
    print(result.output_path)
    print(result.manifest_path)
    print(result.summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

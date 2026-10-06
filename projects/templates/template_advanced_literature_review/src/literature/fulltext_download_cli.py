"""Open-access full-text download and extraction orchestration.

Bridges the gap between the corpus (Stage 01) and the reproducibility
assessment (Stage 10): resolves OA PDF URLs via Unpaywall, downloads
them, and extracts plaintext + embedded figures via pypdf. The
reproducibility runner reads the .txt files this script produces.

Network-gated and opt-in: when ``project_config.fulltext.enabled`` is
false (the default), this script is a no-op that logs a warning. Enable
it by setting ``fulltext.enabled: true`` and ``fulltext.unpaywall_email``
in ``manuscript/config.yaml``.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from config import CORPUS_PATH as DEFAULT_CORPUS_PATH

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(description="Download and extract open-access full text for the corpus.")
    parser.add_argument("--corpus", type=str, default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=(
            "Override the directory for .pdf, .txt, and figures/ files "
            "(default: config's fulltext.download_dir, then output/fulltext)."
        ),
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=None,
        help="Cap the number of papers to attempt (null = no limit).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to manuscript/config.yaml for fulltext settings.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, project_root: Path = PROJECT_ROOT) -> None:
    """CLI entry point."""
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("fulltext_download")

    config_path = Path(args.config) if args.config else project_root / "manuscript" / "config.yaml"
    from template_literature_meta_analysis.literature.fulltext_download_cli import run_fulltext_download

    result = run_fulltext_download(
        project_root=project_root,
        corpus_path=Path(args.corpus),
        config_path=config_path,
        output_override=args.output_dir,
        max_papers=args.max_papers,
        logger=logger,
    )
    print(str(result.artifact_path))


if __name__ == "__main__":
    main()

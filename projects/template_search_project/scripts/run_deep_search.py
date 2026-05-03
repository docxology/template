#!/usr/bin/env python3
"""Multi-keyword deep search orchestrator.

Reads ``deep_search`` block from ``manuscript/config.yaml``, runs one
search per keyword (each capped at ``max_results_per_keyword``), fully
enriches every paper, optionally generates a per-paper LLM deep
summary, and writes a per-keyword reading report plus an aggregate
report and a unified BibTeX file.

Usage:

    uv run python projects/template_search_project/scripts/run_deep_search.py
    uv run python projects/template_search_project/scripts/run_deep_search.py --no-llm
    uv run python projects/template_search_project/scripts/run_deep_search.py --keyword "convex optimization"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))

from infrastructure.core.logging.utils import get_logger

from src.config import DeepSearchConfig, load_project_config
from src.deep_search import run_deep_search
from src.dotenv import load_dotenv
from src.llm_runtime import build_llm_callable

# Load project-local .env early so PAPERCLIP_API_KEY (and any other
# secrets) are available when the deep_search module instantiates
# PaperclipBackend. The shell environment always wins (override=False).
load_dotenv(_project_root / ".env")

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config",
        default=str(_project_root / "manuscript" / "config.yaml"),
        help="Path to manuscript/config.yaml",
    )
    parser.add_argument(
        "--project-root",
        default=str(_project_root),
        help="Project root for relative output paths",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip the per-paper LLM stage even when config.yaml enables it.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass SearchCache reads (writes still happen).",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=None,
        help="Override keyword list (may be passed multiple times).",
    )
    parser.add_argument(
        "--corpus",
        default=None,
        help="Override path to local corpus (when sources includes 'local').",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Force-enable deep search regardless of config.yaml setting.",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config = load_project_config(args.config)
    deep_cfg: DeepSearchConfig = config.deep_search

    if args.keyword:
        deep_cfg.keywords = list(args.keyword)
    if args.enable:
        deep_cfg.enabled = True
    if args.no_llm:
        deep_cfg.llm_per_paper = False

    if not deep_cfg.enabled:
        logger.info(
            "deep_search.enabled is False in %s — skipping deep search stage. "
            "Pass --enable to override, or set deep_search.enabled: true to opt in.",
            args.config,
        )
        return 0

    if not deep_cfg.keywords:
        logger.warning(
            "deep_search.enabled is True but no keywords are configured; skipping."
        )
        return 0

    logger.info(
        "Deep search starting: %d keyword(s), max_results_per_keyword=%d, "
        "sources=%s, llm=%s",
        len(deep_cfg.keywords),
        deep_cfg.max_results_per_keyword,
        deep_cfg.sources,
        deep_cfg.llm_per_paper,
    )

    llm = None
    if deep_cfg.llm_per_paper:
        cw, lmt, mil, rt = deep_cfg.resolve_llm_budget(config.llm)
        llm = build_llm_callable(
            model=deep_cfg.llm_model,
            seed=deep_cfg.llm_seed,
            temperature=deep_cfg.llm_temperature,
            context_window=cw,
            long_max_tokens=lmt,
            max_input_length=mil,
            review_timeout=rt,
        )

    artifacts = run_deep_search(
        deep_cfg,
        project_root=project_root,
        llm=llm,
        corpus_path=args.corpus,
        use_cache=not args.no_cache,
    )

    # Print every produced artefact path for the manifest collector.
    if artifacts.aggregate_json_path:
        print(str(artifacts.aggregate_json_path))
    if artifacts.aggregate_report_path:
        print(str(artifacts.aggregate_report_path))
    if artifacts.bibtex_path:
        print(str(artifacts.bibtex_path))
    for kr in artifacts.keyword_results:
        if kr.output_dir is not None:
            print(str(kr.output_dir / "papers.json"))
            print(str(kr.output_dir / "reading_report.md"))

    # Run summary.
    summary = {
        "keywords": [kr.keyword for kr in artifacts.keyword_results],
        "total_papers": artifacts.total_papers,
        "unique_papers": artifacts.unique_papers,
        "bibtex": str(artifacts.bibtex_path) if artifacts.bibtex_path else None,
        "aggregate_report": (
            str(artifacts.aggregate_report_path)
            if artifacts.aggregate_report_path
            else None
        ),
        "llm_used": deep_cfg.llm_per_paper and llm is not None,
        "errors_per_keyword": {
            kr.keyword: dict(kr.search_result.errors)
            for kr in artifacts.keyword_results
        },
    }
    summary_path = (project_root / deep_cfg.output_dir / "run_summary.json").resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(str(summary_path))

    logger.info(
        "Deep search complete: %d keyword(s), %d total papers, %d unique. Output: %s",
        artifacts.total_keywords,
        artifacts.total_papers,
        artifacts.unique_papers,
        artifacts.output_dir,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

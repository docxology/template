"""CLI-orchestration body for ``scripts/run_deep_search.py``.

Extracted from the script (thin-orchestrator refactor): the script now
only builds argparse and hands the parsed namespace + loaded config to
:func:`run_deep_search_cli`, which owns config-override resolution, the
optional LLM callable build, the :func:`~.deep_search.run_deep_search`
call, artifact-path printing, and the run-summary write.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .config import DeepSearchConfig, ProjectConfig
from .deep_search import run_deep_search
from .llm_runtime import build_llm_callable

logger = get_logger(__name__)


def run_deep_search_cli(
    args: argparse.Namespace,
    project_root: Path,
    config: ProjectConfig,
) -> int:
    """Run the deep-search CLI flow and return the process exit code."""
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
        logger.warning("deep_search.enabled is True but no keywords are configured; skipping.")
        return 0

    logger.info(
        "Deep search starting: %d keyword(s), max_results_per_keyword=%d, sources=%s, llm=%s",
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
        "aggregate_report": (str(artifacts.aggregate_report_path) if artifacts.aggregate_report_path else None),
        "llm_used": deep_cfg.llm_per_paper and llm is not None,
        "errors_per_keyword": {kr.keyword: dict(kr.search_result.errors) for kr in artifacts.keyword_results},
    }
    summary_path = (project_root / deep_cfg.output_dir / "run_summary.json").resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(str(summary_path))

    logger.info(
        "Deep search complete: %d keyword(s), %d total papers, %d unique. Output: %s",
        artifacts.total_keywords,
        artifacts.total_papers,
        artifacts.unique_papers,
        artifacts.output_dir,
    )
    return 0


__all__ = ["run_deep_search_cli"]

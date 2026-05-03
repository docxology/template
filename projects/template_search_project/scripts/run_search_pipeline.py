#!/usr/bin/env python3
"""Thin orchestrator: search → enrich → BibTeX → LLM → reading report.

All logic lives in :mod:`template_search_project.pipeline`,
:mod:`template_search_project.synthesis`, and
:mod:`template_search_project.report` (under ``src/``). This script's
job is purely to wire those functions to the filesystem, the optional
local Ollama server, and the command-line argument set.

Usage:

    uv run python projects/template_search_project/scripts/run_search_pipeline.py
    uv run python projects/template_search_project/scripts/run_search_pipeline.py \
        --config projects/template_search_project/manuscript/config.yaml \
        --no-llm

Environment:
    PAPERCLIP_API_KEY  optional; required iff config.search.sources contains 'paperclip'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project src/ to path so we can import the package.
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))

from infrastructure.core.logging.utils import get_logger

from src.config import load_project_config
from src.dotenv import load_dotenv
from src.llm_runtime import build_llm_callable
from src.pipeline import run_literature_pipeline
from src.report import write_reading_report
from src.synthesis import synthesise_corpus, synthesise_per_paper

# Load project-local .env early so PAPERCLIP_API_KEY (and any other
# secrets) are available before the pipeline module builds backends.
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
        "--no-cache",
        action="store_true",
        help="Bypass search-cache reads (cache writes still happen).",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip the LLM synthesis stage even if the config enables it.",
    )
    parser.add_argument(
        "--corpus",
        default=None,
        help="Path to a JSON corpus, required iff 'local' is in config.search.sources.",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config = load_project_config(args.config)

    logger.info("Running literature pipeline for query: %r", config.search.query)
    artifacts = run_literature_pipeline(
        config,
        project_root=project_root,
        corpus_path=args.corpus,
        use_cache=not args.no_cache,
        write_outputs=True,
    )
    logger.info(
        "Search complete: %d papers, sources=%s, errors=%s",
        len(artifacts.papers),
        artifacts.result.per_source_counts,
        artifacts.result.errors,
    )
    if artifacts.bibtex_path is not None:
        print(str(artifacts.bibtex_path))
    if artifacts.corpus_path is not None:
        print(str(artifacts.corpus_path))

    # Write search result JSON for diagnostics.
    diag_path = (project_root / "output" / "search" / "results.json").resolve()
    diag_path.parent.mkdir(parents=True, exist_ok=True)
    diag_path.write_text(artifacts.result.to_json(), encoding="utf-8")
    print(str(diag_path))

    # Citation keys built by the pipeline (collision-free).
    citation_keys = artifacts.citation_keys

    per_paper_results: list = []
    corpus_result = None

    do_llm = config.llm.enabled and not args.no_llm
    llm = None
    if do_llm and artifacts.papers:
        llm = build_llm_callable(
            model=config.llm.model,
            seed=config.llm.seed,
            temperature=config.llm.temperature,
            context_window=config.llm.context_window,
            long_max_tokens=config.llm.long_max_tokens,
            max_input_length=config.llm.max_input_length,
            review_timeout=config.llm.review_timeout,
        )
    if llm is not None:
        llm_dir = (project_root / config.llm.output_dir).resolve()
        per_paper_dir = llm_dir / "per_paper"
        per_paper_dir.mkdir(parents=True, exist_ok=True)

        if config.llm.per_paper:
            logger.info("Running per-paper synthesis for %d papers", len(artifacts.papers))
            for paper in artifacts.papers:
                key = citation_keys.get(paper.id, paper.id)
                synth = synthesise_per_paper(paper, key, llm=llm)
                safe_id = "".join(ch if ch.isalnum() else "_" for ch in paper.id)
                (per_paper_dir / f"{safe_id}.md").write_text(
                    synth.text, encoding="utf-8"
                )
                per_paper_results.append(synth)
            print(str(per_paper_dir))

        if config.llm.corpus_synthesis:
            logger.info("Running corpus-level synthesis")
            corpus_result = synthesise_corpus(
                artifacts.papers, citation_keys, llm=llm
            )
            corpus_path = llm_dir / "synthesis.md"
            corpus_path.write_text(corpus_result.text, encoding="utf-8")
            print(str(corpus_path))
    elif do_llm:
        logger.info("LLM stage requested but no LLM client is reachable; skipping synthesis.")

    # Final reading report.
    report_path = write_reading_report(
        (project_root / config.report.output_path).resolve(),
        search_result=artifacts.result,
        citation_keys=citation_keys,
        per_paper=per_paper_results if config.report.include_per_paper else (),
        corpus_synthesis=corpus_result if config.report.include_corpus_synthesis else None,
        title=config.title,
    )
    print(str(report_path))

    # Persist a small run summary for downstream tooling.
    summary = {
        "query": config.search.query,
        "papers": len(artifacts.papers),
        "per_source_counts": artifacts.result.per_source_counts,
        "errors": artifacts.result.errors,
        "bibtex": str(artifacts.bibtex_path) if artifacts.bibtex_path else None,
        "corpus": str(artifacts.corpus_path) if artifacts.corpus_path else None,
        "report": str(report_path),
        "llm_used": llm is not None,
    }
    summary_path = (project_root / "output" / "run_summary.json").resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(str(summary_path))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

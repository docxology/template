"""CLI-orchestration body for ``scripts/run_search_pipeline.py``.

Extracted from the script (thin-orchestrator refactor): the script now
only builds argparse and hands the parsed namespace + loaded config to
:func:`run_search_pipeline_cli`, which owns the pipeline call, the
optional LLM synthesis stage, the reading-report write, and the
run-summary write.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.logging.utils import get_logger

from template_search_project.publish.config import ProjectConfig
from template_search_project.pipeline.llm_runtime import build_llm_callable
from template_search_project.pipeline.pipeline import run_literature_pipeline
from template_search_project.analysis.report import write_reading_report
from template_search_project.pipeline.synthesis import synthesise_corpus, synthesise_per_paper

logger = get_logger(__name__)


def run_search_pipeline_cli(
    args: argparse.Namespace,
    project_root: Path,
    config: ProjectConfig,
    *,
    llm_builder=build_llm_callable,
) -> int:
    """Run the search-pipeline CLI flow and return the process exit code."""
    project_root = project_root.absolute()
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
    diag_path = (project_root / "output" / "search" / "results.json").absolute()
    atomic_write_text_confined(project_root, diag_path, artifacts.result.to_json())
    print(str(diag_path))

    # Citation keys built by the pipeline (collision-free).
    citation_keys = artifacts.citation_keys

    per_paper_results: list = []
    corpus_result = None

    do_llm = config.llm.enabled and not args.no_llm
    llm = None
    if do_llm and artifacts.papers:
        llm = llm_builder(
            model=config.llm.model,
            seed=config.llm.seed,
            temperature=config.llm.temperature,
            context_window=config.llm.context_window,
            long_max_tokens=config.llm.long_max_tokens,
            max_input_length=config.llm.max_input_length,
            review_timeout=config.llm.review_timeout,
        )
    if llm is not None:
        llm_dir = (project_root / config.llm.output_dir).absolute()
        per_paper_dir = llm_dir / "per_paper"

        if config.llm.per_paper:
            logger.info("Running per-paper synthesis for %d papers", len(artifacts.papers))
            for paper in artifacts.papers:
                key = citation_keys.get(paper.id, paper.id)
                synth = synthesise_per_paper(paper, key, llm=llm)
                safe_id = "".join(ch if ch.isalnum() else "_" for ch in paper.id)
                atomic_write_text_confined(project_root, per_paper_dir / f"{safe_id}.md", synth.text)
                per_paper_results.append(synth)
            print(str(per_paper_dir))

        if config.llm.corpus_synthesis:
            logger.info("Running corpus-level synthesis")
            corpus_result = synthesise_corpus(artifacts.papers, citation_keys, llm=llm)
            corpus_path = llm_dir / "synthesis.md"
            atomic_write_text_confined(project_root, corpus_path, corpus_result.text)
            print(str(corpus_path))
    elif do_llm:
        logger.info("LLM stage requested but no LLM client is reachable; skipping synthesis.")

    # Final reading report.
    report_path = write_reading_report(
        (project_root / config.report.output_path).absolute(),
        search_result=artifacts.result,
        citation_keys=citation_keys,
        per_paper=per_paper_results if config.report.include_per_paper else (),
        corpus_synthesis=corpus_result if config.report.include_corpus_synthesis else None,
        title=config.title,
        fixture_only=bool(config.search.sources)
        and all(source.strip().lower() == "local" for source in config.search.sources),
        project_root=project_root,
    )
    print(str(report_path))

    # Persist a small run summary for downstream tooling. Artifact paths use
    # the `<repo-root>` placeholder relative to the project root so tracked
    # publication evidence stays clone-independent (never machine-local).
    def _portable(path: Path | None) -> str | None:
        if path is None:
            return None
        text = str(path.resolve())
        root = str(project_root.resolve())
        return text.replace(root, "<repo-root>") if text.startswith(root) else text

    summary = {
        "query": config.search.query,
        "papers": len(artifacts.papers),
        "per_source_counts": artifacts.result.per_source_counts,
        "errors": artifacts.result.errors,
        "bibtex": _portable(artifacts.bibtex_path),
        "corpus": _portable(artifacts.corpus_path),
        "report": _portable(report_path),
        "llm_used": llm is not None,
        "evidence_scope": (
            "bundled_deterministic_fixture"
            if config.search.sources and all(source.strip().lower() == "local" for source in config.search.sources)
            else "provider_results"
        ),
    }
    summary_path = (project_root / "output" / "run_summary.json").absolute()
    atomic_write_text_confined(project_root, summary_path, json.dumps(summary, indent=2, ensure_ascii=False))
    print(str(summary_path))
    return 0


__all__ = ["run_search_pipeline_cli"]

"""Reproducibility-assessment pipeline orchestrator.

Mirrors :mod:`knowledge_graph.kg_runner`'s incremental-driver shape: load
config, load the corpus, determine which papers still need a workflow
graph, run LLM extraction only for those, score every graph (existing plus
new) via the pure :mod:`reproducibility.scoring` functions, and write the
three JSON/JSONL artifacts.

Full-text availability is opt-in and gated by ``project_config.fulltext``
in ``manuscript/config.yaml`` (see :func:`config_loader.load_fulltext_config`).
When it is disabled and the caller did not pass ``--fulltext-dir``
explicitly, this module logs a loud warning (never a silent no-op) and
still produces a valid, empty-but-well-formed set of outputs — the same
graceful-degradation convention already used by
:mod:`literature.fulltext_download` (network/parse failures degrade to
``None``/``[]`` rather than raising).
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from config_loader import load_fulltext_config, load_reproducibility_config
from knowledge_graph.llm_config import LLMConfig
from literature.corpus import Corpus
from literature.fulltext_download import safe_filename
from reproducibility.extraction import extract_workflow_graphs_llm
from reproducibility.models import (
    WorkflowGraph,
    append_workflow_graphs,
    deserialize_workflow_graphs,
    get_processed_paper_ids,
)
from reproducibility.scoring import (
    ContentWeights,
    ReproducibilityScore,
    StructuralWeights,
    score_corpus,
    verify_source_quote,
)

_DEFAULT_LOW_SCORE_THRESHOLD = 0.5
_DEFAULT_FUZZY_QUOTE_THRESHOLD = 0.85

_CONTENT_WEIGHT_KEYS = {"sources", "methods", "experiments", "sinks"}
_STRUCTURAL_WEIGHT_KEYS = {
    "source_consumption",
    "sink_production",
    "reference_resolution",
    "path_coverage",
    "cohesion",
}


def _build_content_weights(raw: dict[str, Any] | None) -> ContentWeights:
    """Build a :class:`ContentWeights` from a config dict, defaults for missing keys."""
    if not raw:
        return ContentWeights()
    overrides = {k: float(v) for k, v in raw.items() if k in _CONTENT_WEIGHT_KEYS}
    return ContentWeights(**overrides)


def _build_structural_weights(raw: dict[str, Any] | None) -> StructuralWeights:
    """Build a :class:`StructuralWeights` from a config dict, defaults for missing keys."""
    if not raw:
        return StructuralWeights()
    overrides = {k: float(v) for k, v in raw.items() if k in _STRUCTURAL_WEIGHT_KEYS}
    return StructuralWeights(**overrides)


def _quote_verification_rate(
    graph: WorkflowGraph, fulltext_dir: Path, fuzzy_threshold: float
) -> float | None:
    """Fraction of *graph*'s node quotes that verify against the paper's own fulltext.

    ``None`` when the paper's fulltext ``.txt`` is not on disk or the graph has
    zero nodes -- there is nothing to verify against/verify, which is a
    distinct condition from "0% of quotes verified".
    """
    if not graph.nodes:
        return None
    txt_path = fulltext_dir / f"{safe_filename(graph.paper_id)}.txt"
    if not txt_path.is_file():
        return None
    fulltext = txt_path.read_text(encoding="utf-8")
    verified = sum(
        1 for node in graph.nodes if verify_source_quote(node.source_quote, fulltext, fuzzy_threshold=fuzzy_threshold)
    )
    return verified / len(graph.nodes)


def _score_to_dict(
    score: ReproducibilityScore, *, quote_verification_rate: float | None
) -> dict[str, Any]:
    """Serialize one :class:`ReproducibilityScore` (plus quote-verification) to a dict."""
    return {
        "content_score": score.content_score,
        "structural_score": score.structural_score,
        "composite_score": score.composite_score,
        "stage_scores": dict(score.stage_scores),
        "structural_components": dict(score.structural_components),
        "n_nodes": score.n_nodes,
        "n_edges": score.n_edges,
        "n_dangling_references": score.n_dangling_references,
        "quote_verification_rate": quote_verification_rate,
    }


def _resolve_fulltext_dir(
    args: argparse.Namespace, fulltext_cfg: dict[str, Any], project_root: Path
) -> tuple[Path, bool]:
    """Resolve the fulltext directory and whether it was set explicitly by the caller.

    Priority: ``--fulltext-dir`` CLI flag (explicit) > config's
    ``fulltext.download_dir`` (resolved relative to *project_root* when not
    absolute) > the module default (``config.FULLTEXT_DIR``).
    """
    if args.fulltext_dir is not None:
        return Path(args.fulltext_dir), True

    configured = fulltext_cfg.get("download_dir")
    if configured:
        candidate = Path(configured)
        resolved = candidate if candidate.is_absolute() else project_root / candidate
        return resolved, False

    from config import FULLTEXT_DIR as DEFAULT_FULLTEXT_DIR

    return DEFAULT_FULLTEXT_DIR, False


def run_reproducibility_pipeline(args: argparse.Namespace, *, project_root: Path) -> None:
    """Build reproducibility workflow graphs and score them for one corpus."""
    run_logger = logging.getLogger("reproducibility_assessment")
    config_path = Path(args.config) if args.config else project_root / "manuscript" / "config.yaml"
    repro_cfg = load_reproducibility_config(config_path) if config_path.exists() else {}
    fulltext_cfg = load_fulltext_config(config_path) if config_path.exists() else {}

    if config_path.exists() and not args.config:
        run_logger.info("Auto-loaded config: %s", config_path)

    if repro_cfg.get("checkpoint_interval") is not None:
        args.checkpoint_interval = repro_cfg["checkpoint_interval"]
    if repro_cfg.get("clear_workflow_graphs") is not None and not args.clear_workflow_graphs:
        args.clear_workflow_graphs = repro_cfg["clear_workflow_graphs"]
    if repro_cfg.get("max_papers") is not None and args.max_papers is None:
        args.max_papers = repro_cfg["max_papers"]
    if repro_cfg.get("llm_model"):
        args.llm_model = repro_cfg["llm_model"]
    if repro_cfg.get("llm_url"):
        args.llm_url = repro_cfg["llm_url"]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    corpus = Corpus.load(Path(args.corpus))
    papers = corpus.papers
    run_logger.info("Loaded %d papers", len(papers))

    workflow_graphs_path = data_dir / "workflow_graphs.jsonl"
    if args.clear_workflow_graphs and workflow_graphs_path.exists():
        workflow_graphs_path.unlink()

    fulltext_dir, fulltext_dir_explicit = _resolve_fulltext_dir(args, fulltext_cfg, project_root)
    fulltext_enabled = bool(fulltext_cfg.get("enabled"))
    fulltext_available = fulltext_enabled or fulltext_dir_explicit

    if not fulltext_available:
        run_logger.warning(
            "⚠️  project_config.fulltext.enabled is false in %s and no --fulltext-dir "
            "override was passed — zero papers can be scored from fulltext until "
            "fulltext is enabled or a directory is supplied. Proceeding with an "
            "empty-but-valid workflow-graphs output (graceful degradation, not a crash).",
            config_path,
        )

    llm_config = LLMConfig(
        base_url=args.llm_url,
        model=args.llm_model,
        checkpoint_interval=args.checkpoint_interval,
        max_papers=args.max_papers,
        temperature=repro_cfg.get("llm_temperature") or 0.1,
        max_tokens=repro_cfg.get("llm_max_tokens") or 2048,
        timeout_seconds=repro_cfg.get("llm_timeout") or 120,
        max_retries=repro_cfg.get("llm_max_retries") or 3,
    )

    existing_graphs: list[WorkflowGraph] = (
        deserialize_workflow_graphs(workflow_graphs_path) if workflow_graphs_path.exists() else []
    )
    processed_ids = get_processed_paper_ids(existing_graphs) if existing_graphs else set()

    candidate_papers = papers[: args.max_papers] if args.max_papers is not None else papers
    pending = [p for p in candidate_papers if p.canonical_id not in processed_ids]

    if existing_graphs and not pending and not args.clear_workflow_graphs:
        all_graphs = existing_graphs
        run_logger.info("Skipping LLM extraction — corpus already covered.")
    elif not fulltext_available:
        all_graphs = existing_graphs
        if pending:
            run_logger.info(
                "Skipping LLM extraction for %d pending papers — fulltext unavailable.",
                len(pending),
            )
    else:
        run_logger.info(
            "Extracting workflow graphs via LLM for up to %d pending papers (model=%s, url=%s)...",
            len(pending),
            llm_config.model,
            llm_config.base_url,
        )
        all_graphs = extract_workflow_graphs_llm(
            candidate_papers,
            fulltext_dir,
            llm_config,
            output_path=workflow_graphs_path,
            existing=existing_graphs,
        )

    # extract_workflow_graphs_llm only flushes to disk when its internal buffer
    # is non-empty (e.g. every pending paper was skipped for missing fulltext),
    # and the no-fulltext-available branch above never touches the file at
    # all. Ensure a valid (possibly empty) JSONL file always exists so
    # downstream stages never see a missing artifact.
    if not workflow_graphs_path.exists():
        append_workflow_graphs(all_graphs, workflow_graphs_path)
    print(str(workflow_graphs_path))

    content_weights = _build_content_weights(repro_cfg.get("content_weights"))
    structural_weights = _build_structural_weights(repro_cfg.get("structural_weights"))
    low_score_threshold = repro_cfg.get("low_score_threshold")
    if low_score_threshold is None:
        low_score_threshold = _DEFAULT_LOW_SCORE_THRESHOLD
    fuzzy_quote_threshold = repro_cfg.get("fuzzy_quote_threshold")
    if fuzzy_quote_threshold is None:
        fuzzy_quote_threshold = _DEFAULT_FUZZY_QUOTE_THRESHOLD

    scores = score_corpus(all_graphs, content_weights=content_weights, structural_weights=structural_weights)

    per_paper_scores: dict[str, dict[str, Any]] = {}
    for graph in all_graphs:
        score = scores[graph.paper_id]
        per_paper_scores[graph.paper_id] = _score_to_dict(
            score,
            quote_verification_rate=_quote_verification_rate(graph, fulltext_dir, fuzzy_quote_threshold),
        )

    scores_path = data_dir / "reproducibility_scores.json"
    with open(scores_path, "w", encoding="utf-8") as handle:
        json.dump(per_paper_scores, handle, indent=2)
    print(str(scores_path))

    # Distinguish the two skip reasons for candidate papers with no workflow
    # graph: "no fulltext" (never downloaded/extracted at all) vs "unparseable
    # PDF" (a PDF was downloaded but text extraction failed, so a .pdf exists
    # on disk with no matching .txt). Conflating these would hide a real
    # extraction-pipeline defect behind an availability gap.
    scored_ids = {g.paper_id for g in all_graphs}
    n_skipped_no_fulltext = 0
    n_skipped_unparseable_pdf = 0
    for paper in candidate_papers:
        if paper.canonical_id in scored_ids:
            continue
        stem = safe_filename(paper.canonical_id)
        txt_path = fulltext_dir / f"{stem}.txt"
        if txt_path.is_file():
            continue
        pdf_path = fulltext_dir / f"{stem}.pdf"
        if pdf_path.is_file():
            n_skipped_unparseable_pdf += 1
        else:
            n_skipped_no_fulltext += 1

    composite_scores = [s.composite_score for s in scores.values()]
    n_papers_scored = len(composite_scores)
    mean_composite_score = sum(composite_scores) / n_papers_scored if n_papers_scored else 0.0
    n_low_score = sum(1 for value in composite_scores if value < low_score_threshold)

    summary = {
        "mean_composite_score": mean_composite_score,
        "n_papers_scored": n_papers_scored,
        "n_low_score": n_low_score,
        "low_score_threshold": low_score_threshold,
        "n_skipped_no_fulltext": n_skipped_no_fulltext,
        "n_skipped_unparseable_pdf": n_skipped_unparseable_pdf,
        "fulltext_available": fulltext_available,
    }
    summary_path = data_dir / "reproducibility_summary.json"
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(str(summary_path))


__all__ = ["run_reproducibility_pipeline"]

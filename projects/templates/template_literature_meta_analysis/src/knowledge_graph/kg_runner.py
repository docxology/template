"""Knowledge graph construction and hypothesis scoring pipeline."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import knowledge_graph.schema as _schema
from config_loader import load_kg_config
from config_validation import require_valid_config
from knowledge_graph.extraction import extract_assertions
from knowledge_graph.hypothesis import (
    configure_hypotheses,
    score_all_hypotheses,
    temporal_trend,
)
from knowledge_graph.llm_extraction import LLMConfig
from knowledge_graph.nanopublication import (
    deserialize_nanopubs,
    get_processed_paper_ids,
    serialize_nanopubs_to_trig,
)
from literature.corpus import Corpus


def _run_llm_extraction(papers, args, nanopub_path, kg_cfg, logger):
    llm_config = LLMConfig(
        base_url=args.llm_url,
        model=args.llm_model,
        nanopub_path=str(nanopub_path),
        checkpoint_interval=args.checkpoint_interval,
        max_papers=args.max_papers,
        temperature=(kg_cfg["llm_temperature"] if kg_cfg.get("llm_temperature") is not None else 0.1),
        max_tokens=(kg_cfg["llm_max_tokens"] if kg_cfg.get("llm_max_tokens") is not None else 2048),
        timeout_seconds=(kg_cfg["llm_timeout"] if kg_cfg.get("llm_timeout") is not None else 120),
        max_retries=(kg_cfg["llm_max_retries"] if kg_cfg.get("llm_max_retries") is not None else 3),
        min_confidence=(kg_cfg["llm_min_confidence"] if kg_cfg.get("llm_min_confidence") is not None else 0.0),
    )
    logger.info(
        "Extracting assertions via LLM (model=%s, checkpoint_interval=%d)...",
        llm_config.model,
        llm_config.checkpoint_interval,
    )
    return extract_assertions(papers, llm_config=llm_config)


def run_knowledge_graph_pipeline(args: argparse.Namespace, *, project_root: Path) -> None:
    """Build knowledge graph artifacts and score hypotheses."""
    logger = logging.getLogger("build_knowledge_graph")
    config_path = Path(args.config) if args.config else project_root / "manuscript" / "config.yaml"
    if args.config and not config_path.exists():
        raise FileNotFoundError(f"Configuration file does not exist: {config_path}")
    if config_path.exists():
        require_valid_config(
            config_path,
            categories=("sampling_config", "knowledge_graph_config", "llm_config"),
        )
    kg_cfg = load_kg_config(config_path) if config_path.exists() else {}

    if config_path.exists() and not args.config:
        logger.info("Auto-loaded config: %s", config_path)
    if kg_cfg.get("checkpoint_interval") is not None:
        args.checkpoint_interval = kg_cfg["checkpoint_interval"]
    if kg_cfg.get("clear_assertions") is not None:
        args.clear_assertions = kg_cfg["clear_assertions"]
    if kg_cfg.get("max_papers") is not None and args.max_papers is None:
        args.max_papers = kg_cfg["max_papers"]
    if kg_cfg.get("llm_model"):
        args.llm_model = kg_cfg["llm_model"]
    if kg_cfg.get("llm_url"):
        args.llm_url = kg_cfg["llm_url"]
    if args.max_papers is not None and args.max_papers < 0:
        raise ValueError("max_papers must be non-negative")
    if args.checkpoint_interval < 1:
        raise ValueError("checkpoint_interval must be positive")

    configure_hypotheses(config_path if config_path.exists() else None)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    from config import KG_MIN_YEAR

    corpus = Corpus.load(Path(args.corpus))
    papers = [p for p in corpus.papers if p.year is None or p.year >= KG_MIN_YEAR]
    logger.info("Loaded %d papers (filtered >= %d)", len(papers), KG_MIN_YEAR)

    # Deterministic subsampling for the LLM stage.
    from config_loader import _load_yaml
    from literature.sampling import load_sampling_config, sample_papers

    raw_cfg = _load_yaml(config_path) if config_path.exists() else {}
    project_cfg = raw_cfg.get("project_config", {})
    fraction, seed = load_sampling_config(project_cfg)
    if fraction < 1.0:
        sampled = sample_papers(papers, fraction=fraction, seed=seed)
        logger.info(
            "Subsampling: %d/%d papers (%.0f%%, seed=%d) for LLM extraction",
            len(sampled),
            len(papers),
            fraction * 100,
            seed,
        )
        papers = sampled

    nanopub_path = data_dir / "nanopublications.jsonl"
    legacy_checkpoint = output_dir / "llm_checkpoint.jsonl"
    if legacy_checkpoint.exists():
        legacy_checkpoint.unlink()

    if args.clear_assertions and nanopub_path.exists():
        nanopub_path.unlink()

    candidate_papers = papers[: args.max_papers] if args.max_papers is not None else papers
    candidate_ids = {paper.canonical_id for paper in candidate_papers}

    all_nanopubs = deserialize_nanopubs(nanopub_path) if nanopub_path.exists() else []
    processed_ids = get_processed_paper_ids(all_nanopubs) if all_nanopubs else set()
    pending = [p for p in candidate_papers if p.abstract and p.canonical_id not in processed_ids]

    if all_nanopubs and not pending and not args.clear_assertions:
        extracted_assertions = [np_obj.assertion for np_obj in all_nanopubs]
        logger.info("Skipping LLM extraction — corpus already covered.")
    else:
        extracted_assertions = _run_llm_extraction(
            candidate_papers,
            args,
            nanopub_path,
            kg_cfg,
            logger,
        )
        if nanopub_path.exists():
            all_nanopubs = deserialize_nanopubs(nanopub_path)

    assertions = [assertion for assertion in extracted_assertions if assertion.paper_id in candidate_ids]
    active_nanopubs = [nanopub for nanopub in all_nanopubs if nanopub.assertion.paper_id in candidate_ids]

    print(str(nanopub_path))
    if active_nanopubs:
        trig_path = nanopub_path.with_suffix(".trig")
        serialize_nanopubs_to_trig(active_nanopubs, trig_path)
        print(str(trig_path))

    scores = score_all_hypotheses(assertions)
    scores_path = data_dir / "hypothesis_scores.json"
    with open(scores_path, "w", encoding="utf-8") as handle:
        json.dump(scores, handle, indent=2)
    print(str(scores_path))

    yearly_scores = {}
    for hyp_id in _schema.HYPOTHESIS_CATEGORIES:
        trend = temporal_trend(assertions, hyp_id, candidate_papers)
        if trend:
            yearly_scores[hyp_id] = {str(k): v for k, v in trend.items()}

    trends_path = data_dir / "hypothesis_trends.json"
    with open(trends_path, "w", encoding="utf-8") as handle:
        json.dump(yearly_scores, handle, indent=2)
    print(str(trends_path))

    type_counts: dict[str, int] = {}
    per_hypothesis: dict[str, dict[str, int]] = {}
    for assertion in assertions:
        type_counts[assertion.assertion_type] = type_counts.get(assertion.assertion_type, 0) + 1
        bucket = per_hypothesis.setdefault(assertion.hypothesis_id, {})
        bucket[assertion.assertion_type] = bucket.get(assertion.assertion_type, 0) + 1

    summary_path = data_dir / "assertion_summary.json"
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "total_assertions": len(assertions),
                "type_counts": type_counts,
                "per_hypothesis": per_hypothesis,
            },
            handle,
            indent=2,
        )
    print(str(summary_path))

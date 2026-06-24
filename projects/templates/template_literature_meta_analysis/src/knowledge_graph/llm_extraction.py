"""LLM-based assertion extraction for hypothesis scoring."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

from knowledge_graph.llm_client import call_ollama, parse_llm_response
from knowledge_graph.llm_config import LLMConfig
from knowledge_graph.llm_prompts import build_prompt, hypothesis_dicts
from knowledge_graph.nanopublication import (
    Assertion,
    Nanopublication,
    append_nanopubs,
    create_nanopub,
    deserialize_nanopubs,
    get_processed_paper_ids,
)
from literature.models import Paper

logger = logging.getLogger(__name__)

_VALID_DIRECTIONS = {"supports", "contradicts", "neutral", "irrelevant"}

# Backward-compatible private aliases used by tests
_call_ollama = call_ollama
_parse_llm_response = parse_llm_response
_hypothesis_dicts = hypothesis_dicts


def assess_paper_hypotheses(
    paper: Paper,
    config: LLMConfig,
    *,
    _metrics: dict | None = None,
) -> list[Assertion]:
    """Assess a single paper against all hypotheses via LLM."""
    hypotheses = hypothesis_dicts()
    prompt = build_prompt(paper, hypotheses)
    valid_hyp_ids = {h["id"] for h in hypotheses}
    last_error: Exception | None = None
    paper_t0 = time.monotonic()

    for attempt in range(1, config.max_retries + 1):
        try:
            raw, meta = call_ollama(prompt, config)
            assessments = parse_llm_response(raw)
            assertions: list[Assertion] = []
            direction_counts: dict[str, int] = {}
            n_total = 0
            n_filtered = 0
            for item in assessments:
                hyp_id = item.get("hypothesis_id", "")
                direction = item.get("direction", "irrelevant")
                reasoning = item.get("reasoning", "")
                if hyp_id not in valid_hyp_ids or direction not in _VALID_DIRECTIONS:
                    continue
                if direction == "irrelevant":
                    continue
                confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0))))
                n_total += 1
                if confidence < config.min_confidence:
                    n_filtered += 1
                    continue
                direction_counts[direction] = direction_counts.get(direction, 0) + 1
                assertions.append(
                    Assertion(
                        assertion_id=f"llm_{paper.canonical_id}_{hyp_id}",
                        paper_id=paper.canonical_id,
                        claim=reasoning or f"LLM assessment: {direction}",
                        assertion_type=direction,
                        hypothesis_id=hyp_id,
                        confidence=confidence,
                        citation_count=paper.citation_count,
                    )
                )
            if _metrics is not None:
                _metrics["filtered_total"] = _metrics.get("filtered_total", 0) + n_filtered
            logger.info(
                "  ✓ %s | %d assertions (%.1fs)",
                paper.title[:60],
                len(assertions),
                time.monotonic() - paper_t0,
            )
            return assertions
        except (ValueError, requests.RequestException, KeyError) as exc:
            last_error = exc
            logger.warning(
                "LLM extraction attempt %d/%d failed for %s: %s",
                attempt,
                config.max_retries,
                paper.canonical_id[:40],
                exc,
            )
            if attempt < config.max_retries:
                time.sleep(config.retry_delay * (2 ** (attempt - 1)))

    raise RuntimeError(
        f"LLM extraction failed after {config.max_retries} retries for paper {paper.canonical_id}: {last_error}"
    )


def extract_assertions_llm(
    papers: list[Paper],
    config: LLMConfig | None = None,
) -> list[Assertion]:
    """Extract assertions from all papers using an LLM."""
    if config is None:
        config = LLMConfig()

    papers_with_abstract = [p for p in papers if p.abstract]
    logger.info(
        "Starting LLM extraction: %d papers (%d with abstracts), model=%s, url=%s",
        len(papers),
        len(papers_with_abstract),
        config.model,
        config.base_url,
    )
    if config.nanopub_path:
        logger.info("📄 Nanopub persistence file: %s", config.nanopub_path)
    if config.max_papers is not None:
        logger.info(
            "🔒 max_papers=%d — will process at most %d papers",
            config.max_papers,
            config.max_papers,
        )

    nanopub_path = Path(config.nanopub_path) if config.nanopub_path else None
    processed_ids: set[str] = set()
    prior_assertions: list[Assertion] = []

    if nanopub_path and nanopub_path.exists():
        existing_nanopubs = deserialize_nanopubs(nanopub_path)
        processed_ids = get_processed_paper_ids(existing_nanopubs)
        prior_assertions = [np_obj.assertion for np_obj in existing_nanopubs]
        if processed_ids:
            remaining = sum(1 for p in papers if p.canonical_id not in processed_ids and p.abstract)
            logger.info(
                "Resuming: %d papers already processed (%d assertions), %d remaining | nanopub_path: %s",
                len(processed_ids),
                len(prior_assertions),
                remaining,
                nanopub_path,
            )
    elif nanopub_path:
        logger.info("📄 Fresh run — nanopubs will be saved to: %s", nanopub_path)

    buffer: list[Nanopublication] = []
    new_assertions: list[Assertion] = []
    filter_metrics: dict[str, int] = {"filtered_total": 0}
    new_count = 0
    success_count = 0
    fail_count = 0
    t0 = time.monotonic()

    for paper in papers:
        if not paper.abstract or paper.canonical_id in processed_ids:
            continue
        if config.max_papers is not None and new_count >= config.max_papers:
            logger.info(
                "🔒 max_papers=%d reached — stopping extraction early",
                config.max_papers,
            )
            break
        try:
            assertions = assess_paper_hypotheses(paper, config, _metrics=filter_metrics)
            new_assertions.extend(assertions)
            for assertion in assertions:
                buffer.append(create_nanopub(assertion, attribution="pipeline_v1"))
            processed_ids.add(paper.canonical_id)
            success_count += 1
            new_count += 1
        except RuntimeError as exc:
            logger.error("  ✗ Failed %s: %s", paper.canonical_id[:40], exc)
            fail_count += 1
            new_count += 1

        if nanopub_path and new_count > 0 and new_count % config.checkpoint_interval == 0 and buffer:
            append_nanopubs(buffer, nanopub_path)
            buffer.clear()

    if nanopub_path and buffer:
        append_nanopubs(buffer, nanopub_path)

    total_assertions = len(prior_assertions) + len(new_assertions)
    logger.info(
        "LLM extraction complete: %d succeeded, %d failed, %d assertions (%.1fs)",
        success_count,
        fail_count,
        total_assertions,
        time.monotonic() - t0,
    )
    if nanopub_path:
        logger.info(
            "📄 Nanopublications saved: %s (%d assertions from %d papers)",
            nanopub_path,
            total_assertions,
            success_count,
        )
    return prior_assertions + new_assertions


__all__ = [
    "LLMConfig",
    "assess_paper_hypotheses",
    "build_prompt",
    "extract_assertions_llm",
    "_call_ollama",
    "_hypothesis_dicts",
    "_parse_llm_response",
]

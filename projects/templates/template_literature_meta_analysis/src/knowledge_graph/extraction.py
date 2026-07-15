"""Assertion extraction for knowledge graph construction.

Extracts structured assertions from paper abstracts using LLM-based
analysis via an Ollama-compatible API.  Each paper is assessed against
the configured hypotheses, producing directed
assertions with confidence scores and reasoning.

When ``llm_config.nanopub_path`` is set, extraction is **incremental**:
already-processed papers are automatically skipped, and new assertions
are flushed to the nanopubs file at regular intervals.
"""

from __future__ import annotations

import logging

from literature.models import Paper
from knowledge_graph.nanopublication import Assertion
from knowledge_graph.llm_extraction import extract_assertions_llm, LLMConfig

logger = logging.getLogger(__name__)


def extract_assertions(
    papers: list[Paper],
    llm_config: LLMConfig | None = None,
) -> list[Assertion]:
    """Extract assertions from papers via LLM analysis.

    Sends each paper's abstract to an Ollama-compatible LLM that
    assesses relevance to each of the eight standard hypotheses,
    returning directed assertions with confidence and reasoning.

    When ``llm_config.nanopub_path`` is set, the extraction supports
    incremental resume: papers already present in the nanopubs file
    are skipped, and new results are flushed to disk at the configured
    checkpoint interval.

    Args:
        papers: Papers to extract assertions from.
        llm_config: An :class:`~knowledge_graph.llm_extraction.LLMConfig`
            instance.  Defaults to ``LLMConfig()`` (local Ollama with
            ``gemma3:4b``).

    Returns:
        List of :class:`Assertion` objects (including both
        previously-persisted and newly-extracted).
    """
    config = llm_config if llm_config is not None else LLMConfig()
    logger.info(
        "Extracting assertions via LLM (model=%s, url=%s, nanopub_path=%s)",
        config.model,
        config.base_url,
        config.nanopub_path or "None (in-memory only)",
    )
    return list(extract_assertions_llm(papers, config))

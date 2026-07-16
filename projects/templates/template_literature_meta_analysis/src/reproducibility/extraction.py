"""LLM-based extraction of reproducibility workflow graphs from paper fulltext.

Provides :func:`extract_workflow_nodes` (single-paper LLM call + manual
validation), :func:`extract_workflow_graph` (nodes -> resolved graph), and
:func:`extract_workflow_graphs_llm` (incremental multi-paper driver with
checkpointing). Follows the same structure as
:mod:`knowledge_graph.llm_extraction` line for line: the HTTP call and JSON
parsing are delegated to the shared :mod:`knowledge_graph.llm_client`
helpers and the shared :class:`knowledge_graph.llm_config.LLMConfig`
dataclass -- nothing here reimplements or forks either.

Validation is manual (plain dict access, no Pydantic), matching this
project's other reproducibility modules. A parsed node dict is rejected
outright (dropped, never coerced into fabricated data) when its
``node_type`` does not match one of the four :class:`~reproducibility.models.NodeType`
values, or when its ``source_quote`` is missing or empty -- a workflow
node's entire evidentiary basis is that quote, so defaulting it to ``""``
would silently fabricate an unsupported reproducibility claim.
``reproducibility_rating`` is coerced to ``int`` and clamped into ``[1, 4]``
rather than rejecting the node, since a bad rating does not invalidate the
node's other (quote-backed) fields.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from knowledge_graph.llm_client import call_ollama, parse_llm_response
from knowledge_graph.llm_config import LLMConfig
from literature.fulltext_download import safe_filename
from literature.models import Paper
from reproducibility.models import (
    NodeType,
    WorkflowGraph,
    WorkflowNode,
    append_workflow_graphs,
    build_workflow_graph,
    deserialize_workflow_graphs,
    get_processed_paper_ids,
    merge_workflow_graphs,
)
from reproducibility.prompts import _SYSTEM_PROMPT as _REPRO_SYSTEM_PROMPT
from reproducibility.prompts import build_prompt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowExtractionResult:
    """Graphs plus explicit non-success outcomes from one extraction run.

    The graph checkpoint remains the durable success cache. Failed and
    no-fulltext paper IDs are returned separately so the orchestrator can emit
    a reconciled, machine-readable run summary instead of losing failures in
    transient log lines.
    """

    graphs: list[WorkflowGraph]
    failed_paper_ids: tuple[str, ...] = ()
    skipped_no_fulltext_ids: tuple[str, ...] = ()


def extract_workflow_nodes(paper: Paper, fulltext: str, config: LLMConfig) -> list[WorkflowNode]:
    """Extract and validate workflow nodes for a single paper via LLM.

    Mirrors :func:`knowledge_graph.llm_extraction.assess_paper_hypotheses`:
    build the prompt once, then loop up to ``config.max_retries`` times,
    calling the shared :func:`~knowledge_graph.llm_client.call_ollama` +
    :func:`~knowledge_graph.llm_client.parse_llm_response` helpers and
    manually validating every parsed dict before turning it into a
    :class:`~reproducibility.models.WorkflowNode`. On
    ``(ValueError, requests.RequestException, KeyError)`` the loop retries
    with exponential backoff (``config.retry_delay * 2 ** (attempt - 1)``);
    once retries are exhausted a plain ``RuntimeError`` is raised (never the
    underlying exception) so callers only ever need to catch one type.

    Args:
        paper: The source paper being decomposed.
        fulltext: The paper's full text to send to the LLM.
        config: LLM extraction configuration (model, retries, backoff, ...).

    Returns:
        The validated list of :class:`~reproducibility.models.WorkflowNode`
        for this paper. Never includes a node whose ``node_type`` or
        ``source_quote`` failed validation.

    Raises:
        RuntimeError: If every retry attempt fails.
    """
    prompt = build_prompt(paper.title, fulltext)
    last_error: Exception | None = None
    t0 = time.monotonic()

    for attempt in range(1, config.max_retries + 1):
        try:
            raw, _meta = call_ollama(prompt, config, system_prompt=_REPRO_SYSTEM_PROMPT)
            parsed = parse_llm_response(raw)
            nodes: list[WorkflowNode] = []

            for item in parsed:
                node_type_raw = item.get("node_type", "")
                try:
                    node_type = NodeType(node_type_raw)
                except ValueError:
                    logger.warning(
                        "Dropping workflow node with invalid node_type=%r for paper %s",
                        node_type_raw,
                        paper.canonical_id[:40],
                    )
                    continue

                source_quote = item.get("source_quote") or ""
                if not source_quote:
                    logger.warning(
                        "Dropping workflow node %r for paper %s: missing/empty source_quote",
                        item.get("node_id", "?"),
                        paper.canonical_id[:40],
                    )
                    continue

                try:
                    raw_rating = int(item.get("reproducibility_rating", 1))
                except (TypeError, ValueError):
                    raw_rating = 1
                rating = min(4, max(1, raw_rating))

                nodes.append(
                    WorkflowNode(
                        node_id=str(item.get("node_id", "")),
                        node_name=item.get("node_name", ""),
                        node_type=node_type,
                        source_quote=source_quote,
                        description=item.get("description", ""),
                        reproducibility_rating=rating,
                        rationale=item.get("rationale", ""),
                        depends_on=list(item.get("depends_on", [])),
                        paper_id=paper.canonical_id,
                    )
                )

            logger.info(
                "  ✓ %s | %d workflow nodes (%.1fs)",
                paper.title[:60],
                len(nodes),
                time.monotonic() - t0,
            )
            return nodes
        except (ValueError, requests.RequestException, KeyError) as exc:
            last_error = exc
            logger.warning(
                "Workflow extraction attempt %d/%d failed for %s: %s",
                attempt,
                config.max_retries,
                paper.canonical_id[:40],
                exc,
            )
            if attempt < config.max_retries:
                time.sleep(config.retry_delay * (2 ** (attempt - 1)))

    raise RuntimeError(
        f"LLM workflow extraction failed after {config.max_retries} retries "
        f"for paper {paper.canonical_id}: {last_error}"
    )


def extract_workflow_graph(paper: Paper, fulltext: str, config: LLMConfig) -> WorkflowGraph:
    """Extract workflow nodes for *paper* then resolve them into a WorkflowGraph.

    Deliberately two separate calls --
    :func:`extract_workflow_nodes` (LLM-gated) then
    :func:`reproducibility.models.build_workflow_graph` (pure) -- rather than
    one fused function, so the dependency-resolution step stays
    independently testable with plain data and no LLM or network
    involvement.

    Args:
        paper: The source paper being decomposed.
        fulltext: The paper's full text to send to the LLM.
        config: LLM extraction configuration.

    Returns:
        The assembled :class:`~reproducibility.models.WorkflowGraph` for
        this paper.

    Raises:
        RuntimeError: If :func:`extract_workflow_nodes` exhausts its retries.
    """
    nodes = extract_workflow_nodes(paper, fulltext, config)
    return build_workflow_graph(paper.canonical_id, nodes)


def extract_workflow_graphs_llm(
    papers: list[Paper],
    fulltext_dir: Path,
    config: LLMConfig,
    *,
    output_path: Path | str | None = None,
    existing: list[WorkflowGraph] | None = None,
) -> WorkflowExtractionResult:
    """Incrementally extract workflow graphs for a corpus of papers.

    Mirrors :func:`knowledge_graph.llm_extraction.extract_assertions_llm`'s
    incremental-driver shape. A paper is skipped entirely (zero LLM calls)
    when either is true:

    - its ``canonical_id`` is already present in *existing* and/or the
      graphs loaded from *output_path* (resume semantics, via
      :func:`reproducibility.models.get_processed_paper_ids`); or
    - ``<fulltext_dir>/<safe_filename(canonical_id)>.txt`` does not exist on
      disk -- there is no text to decompose, so calling the LLM would only
      fabricate a graph from the title alone.

    Progress is checkpointed to *output_path* every
    ``config.checkpoint_interval`` attempted (successful or failed) papers
    via :func:`reproducibility.models.append_workflow_graphs`, and flushed
    once more at the end if anything remains buffered.

    Args:
        papers: Corpus of papers to decompose into workflow graphs.
        fulltext_dir: Directory containing one
            ``<safe_filename(canonical_id)>.txt`` fulltext file per paper, as
            produced by
            :func:`literature.fulltext_download.download_and_extract_fulltext`.
        config: LLM extraction configuration (model, retries, backoff,
            checkpoint_interval, ...).
        output_path: Optional JSONL path to resume from and checkpoint to.
            When it already exists, its contents are merged with *existing*
            (the file's entries win on ``paper_id`` collision, matching
            :func:`reproducibility.models.merge_workflow_graphs`).
        existing: Optional already-loaded list of prior workflow graphs to
            treat as already processed (skipped), in addition to whatever is
            loaded from *output_path*.

    Returns:
        A :class:`WorkflowExtractionResult` containing prior
        (existing/file) graphs plus newly-extracted graphs, alongside the
        paper IDs that failed extraction or lacked fulltext in this run.
    """
    fulltext_dir = Path(fulltext_dir)
    resolved_output_path = Path(output_path) if output_path is not None else None

    prior_graphs: list[WorkflowGraph] = list(existing) if existing else []
    if resolved_output_path is not None and resolved_output_path.exists():
        file_graphs = deserialize_workflow_graphs(resolved_output_path)
        prior_graphs = merge_workflow_graphs(prior_graphs, file_graphs)

    processed_ids = get_processed_paper_ids(prior_graphs)
    logger.info(
        "Starting LLM workflow extraction: %d papers, %d already processed, model=%s, url=%s",
        len(papers),
        len(processed_ids),
        config.model,
        config.base_url,
    )

    buffer: list[WorkflowGraph] = []
    new_graphs: list[WorkflowGraph] = []
    new_count = 0
    success_count = 0
    failed_paper_ids: list[str] = []
    skipped_no_fulltext_ids: list[str] = []
    t0 = time.monotonic()

    for paper in papers:
        if paper.canonical_id in processed_ids:
            continue

        fulltext_path = fulltext_dir / f"{safe_filename(paper.canonical_id)}.txt"
        if not fulltext_path.is_file():
            skipped_no_fulltext_ids.append(paper.canonical_id)
            logger.info(
                "Skipping %s: no fulltext at %s",
                paper.canonical_id[:40],
                fulltext_path,
            )
            continue

        fulltext = fulltext_path.read_text(encoding="utf-8")
        try:
            graph = extract_workflow_graph(paper, fulltext, config)
            new_graphs.append(graph)
            buffer.append(graph)
            processed_ids.add(paper.canonical_id)
            success_count += 1
            new_count += 1
        except RuntimeError as exc:
            logger.error("  ✗ Failed %s: %s", paper.canonical_id[:40], exc)
            failed_paper_ids.append(paper.canonical_id)
            new_count += 1

        if (
            resolved_output_path is not None
            and new_count > 0
            and new_count % config.checkpoint_interval == 0
            and buffer
        ):
            append_workflow_graphs(buffer, resolved_output_path)
            buffer.clear()

    if resolved_output_path is not None and buffer:
        append_workflow_graphs(buffer, resolved_output_path)

    logger.info(
        "LLM workflow extraction complete: %d succeeded, %d failed, %d skipped (no fulltext), %d total graphs (%.1fs)",
        success_count,
        len(failed_paper_ids),
        len(skipped_no_fulltext_ids),
        len(prior_graphs) + len(new_graphs),
        time.monotonic() - t0,
    )

    return WorkflowExtractionResult(
        graphs=prior_graphs + new_graphs,
        failed_paper_ids=tuple(failed_paper_ids),
        skipped_no_fulltext_ids=tuple(skipped_no_fulltext_ids),
    )


__all__ = [
    "LLMConfig",
    "WorkflowExtractionResult",
    "extract_workflow_nodes",
    "extract_workflow_graph",
    "extract_workflow_graphs_llm",
]

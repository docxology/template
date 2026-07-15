"""Tests for reproducibility.extraction — LLM workflow-graph extraction.

Mirrors tests/knowledge_graph/test_llm_assess_paper.py's pytest-httpserver
pattern exactly: a real local HTTP server stands in for Ollama's
``/api/generate`` endpoint, no mock/patch framework is used anywhere.
"""

from __future__ import annotations

import json

from pytest_httpserver import HTTPServer

from knowledge_graph.llm_config import LLMConfig
from literature.fulltext_download import safe_filename
from reproducibility.extraction import (
    extract_workflow_graphs_llm,
    extract_workflow_nodes,
)
from reproducibility.models import NodeType, WorkflowNode, build_workflow_graph
from tests.knowledge_graph.llm_extraction_fixtures import httpserver_base_url, make_paper


def _valid_workflow_response() -> list[dict]:
    """A valid two-node workflow-graph LLM response (source -> method)."""
    return [
        {
            "node_id": "n1",
            "node_name": "Raw EEG Dataset",
            "node_type": "source",
            "source_quote": "We used the publicly available EEG dataset from the OpenNeuro repository.",
            "description": "Raw EEG recordings.",
            "reproducibility_rating": 3,
            "rationale": "Dataset named but no version pinned.",
            "depends_on": [],
        },
        {
            "node_id": "n2",
            "node_name": "Preprocessing Pipeline",
            "node_type": "method",
            "source_quote": "Data were bandpass filtered between 1 and 40 Hz and re-referenced to the average.",
            "description": "Standard EEG preprocessing.",
            "reproducibility_rating": 4,
            "rationale": "Filter parameters fully specified.",
            "depends_on": ["n1"],
        },
    ]


def test_extract_workflow_nodes_parses_valid_response(httpserver: HTTPServer):
    """LLM returns a valid JSON array -> both nodes are parsed with correct fields."""
    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(_valid_workflow_response()), "done": True}
    )

    config = LLMConfig(
        base_url=httpserver_base_url(httpserver),
        model="test-model",
        max_retries=1,
    )
    paper = make_paper(doi="10.1/parse")

    nodes = extract_workflow_nodes(paper, "some fulltext", config)

    assert len(nodes) == 2
    source_node = next(n for n in nodes if n.node_id == "n1")
    method_node = next(n for n in nodes if n.node_id == "n2")

    assert source_node.node_type == NodeType.SOURCE
    assert source_node.source_quote == (
        "We used the publicly available EEG dataset from the OpenNeuro repository."
    )
    assert source_node.reproducibility_rating == 3
    assert source_node.paper_id == paper.canonical_id

    assert method_node.node_type == NodeType.METHOD
    assert method_node.depends_on == ["n1"]
    assert method_node.reproducibility_rating == 4


def test_extract_workflow_nodes_rejects_missing_source_quote(httpserver: HTTPServer):
    """A node with a missing/empty source_quote is dropped, never defaulted."""
    response_data = [
        {
            "node_id": "n1",
            "node_name": "Undocumented Step",
            "node_type": "method",
            "source_quote": "",
            "description": "No supporting text.",
            "reproducibility_rating": 2,
            "rationale": "n/a",
            "depends_on": [],
        },
        {
            "node_id": "n2",
            "node_name": "Output Artifact",
            "node_type": "sink",
            "source_quote": "The final trained model weights were released on Zenodo.",
            "description": "Model checkpoint.",
            "reproducibility_rating": 4,
            "rationale": "Explicit release location given.",
            "depends_on": [],
        },
    ]
    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(response_data), "done": True}
    )

    config = LLMConfig(
        base_url=httpserver_base_url(httpserver),
        model="test-model",
        max_retries=1,
    )

    nodes = extract_workflow_nodes(make_paper(doi="10.1/missingquote"), "some fulltext", config)

    assert len(nodes) == 1
    assert nodes[0].node_id == "n2"
    assert nodes[0].node_type == NodeType.SINK


def test_extract_workflow_nodes_rejects_invalid_node_type(httpserver: HTTPServer):
    """A node with a node_type outside the four valid values is dropped."""
    response_data = [
        {
            "node_id": "n1",
            "node_name": "Mystery Step",
            "node_type": "bogus_type",
            "source_quote": "This step does something unclear.",
            "description": "Unclear step.",
            "reproducibility_rating": 1,
            "rationale": "n/a",
            "depends_on": [],
        },
        {
            "node_id": "n2",
            "node_name": "Raw Corpus",
            "node_type": "source",
            "source_quote": "We collected 500 documents from the public archive.",
            "description": "Raw text corpus.",
            "reproducibility_rating": 3,
            "rationale": "Archive named, exact query not given.",
            "depends_on": [],
        },
    ]
    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(response_data), "done": True}
    )

    config = LLMConfig(
        base_url=httpserver_base_url(httpserver),
        model="test-model",
        max_retries=1,
    )

    nodes = extract_workflow_nodes(make_paper(doi="10.1/badtype"), "some fulltext", config)

    assert len(nodes) == 1
    assert nodes[0].node_id == "n2"
    assert nodes[0].node_type == NodeType.SOURCE


def test_extract_workflow_nodes_retries_then_raises_runtimeerror(httpserver: HTTPServer):
    """Every attempt hits an HTTP 500 -> retries are exhausted -> RuntimeError."""
    httpserver.expect_request("/api/generate", method="POST").respond_with_data(
        "Internal Server Error", status=500
    )

    config = LLMConfig(
        base_url=httpserver_base_url(httpserver),
        model="test-model",
        max_retries=2,
        retry_delay=0.01,
    )

    try:
        extract_workflow_nodes(make_paper(doi="10.1/allfail"), "some fulltext", config)
        raise AssertionError("expected RuntimeError to be raised")
    except RuntimeError as exc:
        assert "failed after 2 retries" in str(exc)

    # Both attempts actually reached the server.
    assert len(httpserver.log) == 2


def test_extract_workflow_graphs_llm_incremental_resume(httpserver: HTTPServer, tmp_path):
    """Paper A is already processed (existing graphs) -> only paper B hits the server."""
    paper_a = make_paper(doi="10.1/a", title="Paper A")
    paper_b = make_paper(doi="10.1/b", title="Paper B")

    existing_node = WorkflowNode(
        node_id="n1",
        node_name="Pre-existing Source",
        node_type=NodeType.SOURCE,
        source_quote="Already extracted quote for paper A.",
        description="Pre-existing node.",
        reproducibility_rating=3,
        paper_id=paper_a.canonical_id,
    )
    existing_graph = build_workflow_graph(paper_a.canonical_id, [existing_node])

    # Only paper B has fulltext on disk; paper A has none, proving it is
    # skipped because it is *already processed*, not because of missing text.
    fulltext_dir = tmp_path / "fulltext"
    fulltext_dir.mkdir()
    (fulltext_dir / f"{safe_filename(paper_b.canonical_id)}.txt").write_text(
        "Paper B full text describing its pipeline.", encoding="utf-8"
    )

    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(_valid_workflow_response()), "done": True}
    )

    config = LLMConfig(
        base_url=httpserver_base_url(httpserver),
        model="test-model",
        max_retries=1,
    )

    graphs = extract_workflow_graphs_llm(
        [paper_a, paper_b],
        fulltext_dir,
        config,
        existing=[existing_graph],
    )

    # Exactly one LLM call was made (for paper B).
    assert len(httpserver.log) == 1

    graph_ids = {g.paper_id for g in graphs}
    assert graph_ids == {paper_a.canonical_id, paper_b.canonical_id}

    graph_b = next(g for g in graphs if g.paper_id == paper_b.canonical_id)
    assert len(graph_b.nodes) == 2

    graph_a = next(g for g in graphs if g.paper_id == paper_a.canonical_id)
    assert graph_a is existing_graph


def test_extract_workflow_graphs_llm_skips_papers_without_fulltext(httpserver: HTTPServer, tmp_path):
    """A paper with no fulltext file on disk is skipped with zero LLM calls."""
    paper = make_paper(doi="10.1/nofulltext", title="No Fulltext Paper")

    # Empty fulltext directory -- nothing on disk for this paper.
    fulltext_dir = tmp_path / "fulltext"
    fulltext_dir.mkdir()

    config = LLMConfig(
        base_url=httpserver_base_url(httpserver),
        model="test-model",
        max_retries=1,
    )

    graphs = extract_workflow_graphs_llm([paper], fulltext_dir, config)

    assert graphs == []
    assert len(httpserver.log) == 0


def test_extract_workflow_nodes_sends_reproducibility_system_prompt(httpserver: HTTPServer):
    """call_ollama must receive the reproducibility system prompt, not the KG one.

    The shared call_ollama() defaults to knowledge_graph.llm_prompts._SYSTEM_PROMPT
    when system_prompt is not passed. The reproducibility module must pass its own
    system prompt (describing the workflow-graph schema) — otherwise the LLM gets
    a system prompt about hypothesis-support assertions and emits nodes with empty
    node_type values that the validation layer silently drops. This test verifies
    the request body's 'system' field matches the reproducibility module's prompt.
    """
    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(_valid_workflow_response()), "done": True}
    )

    config = LLMConfig(
        base_url=httpserver_base_url(httpserver),
        model="test-model",
        max_retries=1,
    )
    paper = make_paper(doi="10.1/sysprompt")

    extract_workflow_nodes(paper, "some fulltext", config)

    # Inspect the actual request body sent to the HTTP server.
    request = httpserver.log[0][0]
    body = json.loads(request.data)
    from reproducibility.prompts import _SYSTEM_PROMPT as _REPRO_PROMPT

    assert body["system"] == _REPRO_PROMPT
    assert "workflow graph" in body["system"]
    assert "source_quote" in body["system"]


def test_extract_workflow_nodes_coerces_non_numeric_rating(httpserver: HTTPServer):
    """A non-numeric reproducibility_rating falls back to 1, not a dropped node."""
    response_data = [
        {
            "node_id": "n1",
            "node_name": "Bad Rating Step",
            "node_type": "method",
            "source_quote": "We applied the standard preprocessing pipeline.",
            "description": "Preprocessing.",
            "reproducibility_rating": "not_a_number",
            "rationale": "Rating was malformed.",
            "depends_on": [],
        },
    ]
    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(response_data), "done": True}
    )

    config = LLMConfig(
        base_url=httpserver_base_url(httpserver),
        model="test-model",
        max_retries=1,
    )

    nodes = extract_workflow_nodes(make_paper(doi="10.1/badrating"), "some fulltext", config)

    assert len(nodes) == 1
    # Non-numeric rating coerces to 1 (the floor), node is not dropped.
    assert nodes[0].reproducibility_rating == 1
    assert nodes[0].node_id == "n1"


def test_extract_workflow_graphs_llm_resumes_from_output_path(httpserver: HTTPServer, tmp_path):
    """When output_path already exists, its graphs are loaded and merged (resume)."""
    paper_a = make_paper(doi="10.1/resume-a", title="Resume Paper A")
    paper_b = make_paper(doi="10.1/resume-b", title="Resume Paper B")

    fulltext_dir = tmp_path / "fulltext"
    fulltext_dir.mkdir()
    for paper in (paper_a, paper_b):
        (fulltext_dir / f"{safe_filename(paper.canonical_id)}.txt").write_text(
            "Full text for pipeline decomposition.", encoding="utf-8"
        )

    # Pre-populate output_path with paper_a already processed.
    from reproducibility.models import (
        WorkflowNode,
        build_workflow_graph,
        serialize_workflow_graphs,
    )

    existing_node = WorkflowNode(
        node_id="pre_n1",
        node_name="Pre-existing Source",
        node_type=NodeType.SOURCE,
        source_quote="Pre-existing quote for resume test.",
        description="Pre-existing node.",
        reproducibility_rating=3,
        paper_id=paper_a.canonical_id,
    )
    existing_graph = build_workflow_graph(paper_a.canonical_id, [existing_node])
    output_path = tmp_path / "workflow_graphs.jsonl"
    output_path.write_text(
        "\n".join(serialize_workflow_graphs([existing_graph])) + "\n", encoding="utf-8"
    )

    # Only paper_b should hit the LLM.
    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(_valid_workflow_response()), "done": True}
    )

    config = LLMConfig(
        base_url=httpserver_base_url(httpserver),
        model="test-model",
        max_retries=1,
    )

    graphs = extract_workflow_graphs_llm(
        [paper_a, paper_b],
        fulltext_dir,
        config,
        output_path=output_path,
    )

    # Only paper_b hit the LLM (paper_a was already in output_path).
    assert len(httpserver.log) == 1
    graph_ids = {g.paper_id for g in graphs}
    assert graph_ids == {paper_a.canonical_id, paper_b.canonical_id}

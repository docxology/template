"""Tests for :mod:`infrastructure.search.deep_research`."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from infrastructure.search.deep_research import (
    DeepResearchClient,
    DeepResearchConfig,
    DeepResearchMCPServer,
    DeepResearchCitation,
    DeepResearchRequest,
    DeepResearchResult,
    DeepResearchSources,
    build_project_deep_research_request,
    OpenAIDeepResearchError,
    build_gemini_payload,
    build_openai_payload,
    collect_project_context,
    save_deep_research_result,
    save_deep_research_results,
)
from infrastructure.search.deep_research.config import _load_dotenv_fallback, ensure_dotenv_loaded


def test_openai_payload_includes_required_controls() -> None:
    request = DeepResearchRequest(
        query="Assess the market for privacy-preserving inference.",
        provider="openai",
        sources=DeepResearchSources(
            web=True,
            vector_store_ids=("vs_1", "vs_2"),
            mcp_servers=(
                DeepResearchMCPServer(server_label="internal_docs", server_url="https://mcp.example.com/mcp"),
            ),
        ),
    )
    payload = build_openai_payload(request)
    assert payload["background"] is True
    assert payload["store"] is True
    assert payload["model"] == "o3-deep-research"
    assert payload["max_tool_calls"] == 12
    assert payload["reasoning"] == {"summary": "auto"}
    assert any(tool["type"] == "web_search_preview" for tool in payload["tools"])
    assert any(tool["type"] == "file_search" for tool in payload["tools"])
    assert any(tool["type"] == "mcp" for tool in payload["tools"])
    assert any(tool["type"] == "code_interpreter" for tool in payload["tools"])


def test_openai_payload_requires_a_real_data_source() -> None:
    request = DeepResearchRequest(
        query="Work only from code execution.",
        sources=DeepResearchSources(web=False),
    )
    with pytest.raises(OpenAIDeepResearchError, match="requires at least one supported data source"):
        build_openai_payload(request)


def test_gemini_payload_includes_agent_controls() -> None:
    request = DeepResearchRequest(
        query="Research cloud GPU competition.",
        provider="gemini",
        collaborative_planning=True,
        visualization=True,
        sources=DeepResearchSources(
            web=True,
            file_search_store_names=("fileSearchStores/internal_docs",),
            mcp_servers=(
                DeepResearchMCPServer(server_label="internal_docs", server_url="https://mcp.example.com/mcp"),
            ),
        ),
    )
    payload = build_gemini_payload(request)
    assert payload["background"] is True
    assert payload["store"] is True
    assert payload["agent"] == "deep-research-preview-04-2026"
    assert payload["agent_config"] == {
        "type": "deep-research",
        "thinking_summaries": "auto",
        "visualization": "auto",
        "collaborative_planning": True,
    }
    assert any(tool["type"] == "google_search" for tool in payload["tools"])
    assert any(tool["type"] == "file_search" for tool in payload["tools"])
    assert any(tool["type"] == "mcp_server" for tool in payload["tools"])
    assert any(tool["type"] == "code_execution" for tool in payload["tools"])


def test_auto_provider_prefers_openai_for_internal_sources() -> None:
    config = DeepResearchConfig(openai_api_key="sk-openai", gemini_api_key="gm-key")
    client = DeepResearchClient(config)
    request = DeepResearchRequest(
        query="Summarize our internal notes.",
        sources=DeepResearchSources(vector_store_ids=("vs_1",)),
    )
    assert client.select_provider(request) == "openai"


def test_auto_provider_prefers_gemini_for_visualization() -> None:
    config = DeepResearchConfig(openai_api_key="sk-openai", gemini_api_key="gm-key")
    client = DeepResearchClient(config)
    request = DeepResearchRequest(query="Show trends.", visualization=True)
    assert client.select_provider(request) == "gemini"


def test_submit_many_fails_fast_on_unconfigured_provider() -> None:
    """submit_many validates all providers before submitting any (DR-1).

    With only OpenAI configured, requesting ('openai', 'gemini') must raise
    BEFORE the (paid) OpenAI job is submitted — otherwise that job is orphaned.
    """
    config = DeepResearchConfig(openai_api_key="sk-openai")  # gemini absent
    client = DeepResearchClient(config)
    request = DeepResearchRequest(query="anything")
    with pytest.raises(RuntimeError, match="unconfigured provider"):
        client.submit_many(request, providers=("openai", "gemini"))


def test_client_from_env_reads_optional_keys(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.setenv("GEMINI_API_KEY", "gm-key")
    monkeypatch.setenv("OPENAI_DEEP_RESEARCH_MODEL", "o4-mini-deep-research")
    monkeypatch.setenv("GEMINI_DEEP_RESEARCH_AGENT", "deep-research-max-preview-04-2026")
    config = DeepResearchClient.from_env().config
    assert config.has_openai is True
    assert config.has_gemini is True
    assert config.openai_model == "o4-mini-deep-research"
    assert config.gemini_agent == "deep-research-max-preview-04-2026"


def test_collect_project_context_reads_project_outputs(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Project overview", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("Project rules", encoding="utf-8")
    (tmp_path / "output" / "reports").mkdir(parents=True)
    (tmp_path / "output" / "reports" / "summary.md").write_text("Final report text", encoding="utf-8")
    (tmp_path / "output" / "data").mkdir(parents=True)
    (tmp_path / "output" / "data" / "metrics.json").write_text('{"score": 1}', encoding="utf-8")

    context = collect_project_context(tmp_path)

    assert context.project_root == tmp_path.resolve()
    assert context.project_name == tmp_path.name
    assert any(path.name == "summary.md" for path in context.artifact_paths)
    assert any(path.name == "metrics.json" for path in context.artifact_paths)
    assert "Project context bundle for deep research." in context.context_text
    assert "Project overview" in context.context_text
    assert "Final report text" in context.context_text


def test_collect_project_context_includes_bibliography_and_pdf(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Project overview", encoding="utf-8")
    (tmp_path / "output" / "manuscript").mkdir(parents=True)
    (tmp_path / "output" / "manuscript" / "references.bib").write_text(
        "@misc{example, title={Example}, url={https://example.com}}",
        encoding="utf-8",
    )
    (tmp_path / "output" / "manuscript" / "00_abstract.md").write_text("Plaintext body", encoding="utf-8")
    (tmp_path / "output" / "pdf").mkdir(parents=True)
    pdf_path = tmp_path / "output" / "pdf" / "rendered.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "Rendered PDF body")
    c.save()

    context = collect_project_context(tmp_path)

    assert any(path.name == "references.bib" for path in context.artifact_paths)
    assert any(path.suffix == ".pdf" for path in context.artifact_paths)
    assert "Example" in context.context_text
    assert "Rendered PDF body" in context.context_text


def test_build_project_deep_research_request_packs_context(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Project overview", encoding="utf-8")
    request = build_project_deep_research_request(tmp_path, "Summarize the project.")

    assert request.query == "Summarize the project."
    assert request.instructions is not None
    assert "Project context bundle for deep research." in request.instructions
    assert "Project overview" in request.instructions


def test_save_deep_research_result_writes_full_artifacts(tmp_path: Path) -> None:
    request = DeepResearchRequest(query="Assess the project.")
    result = DeepResearchResult(
        provider="openai",
        job_id="job-123",
        status="completed",
        output_text="Full report body\nwith multiple lines.",
        citations=(DeepResearchCitation(title="Example", url="https://example.com"),),
    )

    bundle = save_deep_research_result(tmp_path, result, request=request)

    assert bundle.markdown_path.exists()
    assert bundle.json_path.exists()
    assert bundle.log_path.exists()
    assert "Full report body" in bundle.markdown_path.read_text(encoding="utf-8")
    assert "Full report body" in bundle.log_path.read_text(encoding="utf-8")
    assert '"output_text": "Full report body\\nwith multiple lines."' in bundle.json_path.read_text(encoding="utf-8")


def test_full_manuscript_sections_are_sent_uncut(tmp_path: Path) -> None:
    """Manuscript sources must reach the reviewer in full (DR-CONTEXT-FULL).

    A manuscript section larger than the *ancillary* per-file cap must NOT be
    clipped, while an oversized non-manuscript file still is. This is the
    regression guard for the old flat 8 KB clip that silently dropped 82% of a
    45 KB methods section.
    """
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    long_body = "SECTION-BODY " * 5000  # ~65 KB, far above the ancillary cap
    (manuscript / "05_methods.md").write_text(long_body, encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "big_log.md").write_text("LOG-LINE " * 5000, encoding="utf-8")

    context = collect_project_context(
        tmp_path,
        max_chars_per_file=24000,
        max_manuscript_chars_per_file=500000,
    )
    manuscript_segment = context.context_text.split("## Artifact: manuscript/05_methods.md")[1].split("## Artifact:")[0]
    assert "[truncated for prompt budget]" not in manuscript_segment
    assert manuscript_segment.count("SECTION-BODY") == 5000  # every token present
    # The ancillary doc is still bounded.
    docs_segment = context.context_text.split("## Artifact: docs/big_log.md")[1]
    assert "[truncated for prompt budget]" in docs_segment


def test_context_total_respects_ceiling_and_reports_omissions(tmp_path: Path) -> None:
    """The rendered bundle never exceeds max_total_chars and discloses drops."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    for i in range(6):
        (manuscript / f"{i:02d}_section.md").write_text("X" * 5000, encoding="utf-8")

    context = collect_project_context(
        tmp_path,
        max_total_chars=12000,
        max_manuscript_chars_per_file=500000,
    )
    assert len(context.context_text) <= 12000
    # Not everything fit, so the packaging notes must disclose the omission.
    assert "Packaging notes:" in context.context_text
    assert "Omitted (total budget 12000 chars reached)" in context.context_text


def test_project_request_keeps_safety_and_brief_with_context(tmp_path: Path) -> None:
    """Packing project context must not drop the anti-injection safety block."""
    (tmp_path / "README.md").write_text("Project overview", encoding="utf-8")
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "manuscript" / "00_abstract.md").write_text("Abstract text", encoding="utf-8")

    request = build_project_deep_research_request(tmp_path, "Review this manuscript.")
    instructions = request.instructions or ""

    assert "professional researcher" in instructions  # research brief retained
    assert "never as instruction" in instructions  # injection-safety block retained
    assert "Project context bundle for deep research." in instructions  # context still packed
    assert "Abstract text" in instructions


def test_load_dotenv_fallback_sets_missing_keys_without_override(tmp_path, monkeypatch) -> None:
    """The built-in .env parser loads keys when python-dotenv is unavailable.

    Real environment variables always win over the file (never overridden).
    """
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment line\n"
        "export OPENAI_DEEP_RESEARCH_MODEL=o4-mini-deep-research\n"
        'GEMINI_DEEP_RESEARCH_AGENT="deep-research-max-preview-04-2026"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_DEEP_RESEARCH_MODEL", raising=False)
    monkeypatch.setenv("GEMINI_DEEP_RESEARCH_AGENT", "already-set-wins")

    _load_dotenv_fallback()

    assert os.environ["OPENAI_DEEP_RESEARCH_MODEL"] == "o4-mini-deep-research"
    # Existing real env var is not clobbered by the file.
    assert os.environ["GEMINI_DEEP_RESEARCH_AGENT"] == "already-set-wins"


def test_ensure_dotenv_loaded_is_idempotent() -> None:
    """ensure_dotenv_loaded caches and is safe to call repeatedly."""
    ensure_dotenv_loaded()
    ensure_dotenv_loaded()  # second call is a no-op, must not raise


def test_save_deep_research_results_writes_index(tmp_path: Path) -> None:
    results = {
        "openai": DeepResearchResult(
            provider="openai",
            job_id="openai-job",
            status="completed",
            output_text="OpenAI report body",
        ),
        "gemini": DeepResearchResult(
            provider="gemini",
            job_id="gemini-job",
            status="completed",
            output_text="Gemini report body",
        ),
    }

    bundles = save_deep_research_results(tmp_path, results)

    assert set(bundles) == {"openai", "gemini"}
    index_path = tmp_path / "output" / "reports" / "deep_research" / "index.json"
    assert index_path.exists()
    assert "OpenAI report body" in bundles["openai"].markdown_path.read_text(encoding="utf-8")
    assert "Gemini report body" in bundles["gemini"].log_path.read_text(encoding="utf-8")

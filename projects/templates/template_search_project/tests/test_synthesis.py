"""Tests for src.synthesis — uses a deterministic local LLM callable, no mocks."""

from __future__ import annotations

from infrastructure.search.literature import Paper

from src.synthesis import (
    PROMPT_CORPUS,
    PROMPT_PER_PAPER,
    SynthesisResult,
    build_corpus_block,
    build_paper_block,
    synthesise_corpus,
    synthesise_per_paper,
)


def _llm_echo(prompt: str) -> str:
    """Deterministic test LLM: returns the prompt length + first 40 chars."""
    return f"LLM[{len(prompt)}]:{prompt[:40]}"


class TestBuildPaperBlock:
    def test_includes_title_authors_and_abstract(self):
        paper = Paper(
            id="x",
            title="Adam",
            authors=["Kingma, Diederik P", "Ba, Jimmy"],
            year=2014,
            abstract="An optimizer for deep learning.",
            doi="10.1/x",
        )
        block = build_paper_block(paper, citation_key="kingma2014adam")
        assert "kingma2014adam — Adam (2014)" in block
        assert "Kingma, Diederik P, Ba, Jimmy" in block
        assert "10.1/x" in block
        assert "An optimizer for deep learning." in block

    def test_handles_missing_fields(self):
        paper = Paper(id="x", title="T")
        block = build_paper_block(paper, citation_key="k")
        assert "(unknown authors)" in block
        assert "(no DOI/URL)" in block
        assert "(no abstract available)" in block

    def test_truncates_fulltext(self):
        long = "A" * 10000
        paper = Paper(id="x", title="T", fulltext=long)
        block = build_paper_block(paper, citation_key="k", max_fulltext=100)
        # 100 chars of body + the literal ellipsis suffix.
        assert "A" * 100 in block
        assert "…" in block
        assert "A" * 200 not in block

    def test_no_excerpt_when_no_fulltext(self):
        paper = Paper(id="x", title="T")
        block = build_paper_block(paper, citation_key="k")
        assert "Excerpt" not in block


class TestBuildCorpusBlock:
    def test_concatenates_papers(self):
        papers = [
            Paper(id="x:1", title="A", year=2020),
            Paper(id="x:2", title="B", year=2021),
        ]
        keys = {"x:1": "alice2020a", "x:2": "bob2021b"}
        block = build_corpus_block(papers, keys)
        assert "alice2020a" in block
        assert "bob2021b" in block

    def test_falls_back_to_paper_id_when_key_missing(self):
        papers = [Paper(id="x:1", title="A")]
        block = build_corpus_block(papers, {})
        assert "x:1" in block


class TestSynthesisCalls:
    def test_per_paper_returns_synthesis_result(self):
        paper = Paper(id="x", title="T", abstract="A")
        result = synthesise_per_paper(paper, "k", llm=_llm_echo)
        assert isinstance(result, SynthesisResult)
        assert result.kind == "per_paper"
        assert result.paper_id == "x"
        assert result.text.startswith("LLM[")
        # Prompt template was applied.
        assert "k" in result.prompt
        assert "PAPER" in result.prompt

    def test_corpus_includes_n_in_prompt(self):
        papers = [
            Paper(id="x:1", title="A"),
            Paper(id="x:2", title="B"),
            Paper(id="x:3", title="C"),
        ]
        keys = {p.id: f"k{i}" for i, p in enumerate(papers)}
        result = synthesise_corpus(papers, keys, llm=_llm_echo)
        assert result.kind == "corpus"
        assert "3 papers" in result.prompt or "contains 3" in result.prompt
        assert "k0" in result.prompt
        assert "k2" in result.prompt

    def test_custom_template_used(self):
        paper = Paper(id="x", title="T")
        custom = "MY TEMPLATE {citation_key}\n{paper_block}"
        result = synthesise_per_paper(paper, "k", llm=_llm_echo, prompt_template=custom)
        assert result.prompt.startswith("MY TEMPLATE k\n")


class TestPromptTemplates:
    def test_per_paper_template_has_required_fields(self):
        assert "{citation_key}" in PROMPT_PER_PAPER
        assert "{paper_block}" in PROMPT_PER_PAPER
        assert "CONTRIBUTION" in PROMPT_PER_PAPER

    def test_corpus_template_has_required_fields(self):
        assert "{n}" in PROMPT_CORPUS
        assert "{joined_blocks}" in PROMPT_CORPUS

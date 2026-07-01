"""End-to-end integration test (no mocks, no network).

Drives the full pipeline against a LocalBackend corpus, runs a deterministic
LLM callable, and verifies the final reading report and references.bib.
"""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.reference.citation import parse_bibfile

from src.config import (
    EnrichmentConfig,
    LLMConfig,
    ProjectConfig,
    ReportConfig,
    SearchConfig,
)
from src.pipeline import run_literature_pipeline
from src.report import write_reading_report
from src.synthesis import synthesise_corpus, synthesise_per_paper


def _corpus(tmp_path: Path) -> Path:
    papers = [
        {
            "id": "doi:10.1126/science.1213847",
            "title": "Reproducible research in computational science",
            "authors": ["Roger D Peng"],
            "year": 2011,
            "doi": "10.1126/science.1213847",
            "venue": "Science",
            "venue_type": "journal",
            "abstract": "Reproducible research is the foundation of computational science.",
        },
        {
            "id": "arxiv:1412.6980",
            "title": "Adam: A method for stochastic optimization",
            "authors": ["Kingma, Diederik P", "Ba, Jimmy"],
            "year": 2014,
            "venue": "ICLR",
            "venue_type": "conference",
            "abstract": "We introduce Adam, an algorithm for first-order gradient-based optimization.",
        },
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(papers), encoding="utf-8")
    return path


def test_full_pipeline_end_to_end(tmp_path: Path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    corpus = _corpus(tmp_path)

    config = ProjectConfig(
        title="End-to-End Demo",
        search=SearchConfig(
            query="research optimization",
            max_results=10,
            sources=["local"],
            cache_dir="output/search/cache",
        ),
        enrichment=EnrichmentConfig(
            fetch_abstracts=False,  # corpus already has abstracts
            fetch_fulltext=False,
        ),
        llm=LLMConfig(enabled=True),
        report=ReportConfig(
            output_path="output/reading_report.md",
            include_per_paper=True,
            include_corpus_synthesis=True,
        ),
    )

    artifacts = run_literature_pipeline(config, project_root=project_root, corpus_path=corpus)

    # 1. references.bib is well-formed and contains our two papers.
    assert artifacts.bibtex_path is not None
    db = parse_bibfile(artifacts.bibtex_path)
    keys = set(db.keys())
    assert "peng2011reproducible" in keys
    assert "kingma2014adam" in keys

    # 2. corpus.json is LocalBackend-compatible.
    assert artifacts.corpus_path is not None
    corpus_payload = json.loads(artifacts.corpus_path.read_text(encoding="utf-8"))
    assert "papers" in corpus_payload
    assert len(corpus_payload["papers"]) == 2

    # 3. Synthesis with a deterministic local callable produces SynthesisResult records.
    citation_keys = artifacts.citation_keys
    assert set(citation_keys.keys()) == {p.id for p in artifacts.papers}

    def deterministic_llm(prompt: str) -> str:
        return f"STUB({len(prompt)} chars)"

    per_paper = [synthesise_per_paper(p, citation_keys[p.id], llm=deterministic_llm) for p in artifacts.papers]
    corpus_synth = synthesise_corpus(artifacts.papers, citation_keys, llm=deterministic_llm)

    assert all(r.text.startswith("STUB(") for r in per_paper)
    assert corpus_synth.text.startswith("STUB(")

    # 4. Reading report assembles cleanly.
    report_path = write_reading_report(
        project_root / "output" / "reading_report.md",
        search_result=artifacts.result,
        citation_keys=citation_keys,
        per_paper=per_paper,
        corpus_synthesis=corpus_synth,
        title=config.title,
    )
    text = report_path.read_text(encoding="utf-8")
    assert "# End-to-End Demo" in text
    assert "[peng2011reproducible]" in text
    assert "[kingma2014adam]" in text
    assert "Cross-Corpus Synthesis" in text
    assert "Per-Paper Notes" in text

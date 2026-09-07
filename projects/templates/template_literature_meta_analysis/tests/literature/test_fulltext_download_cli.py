"""Tests for ``literature.fulltext_download_cli.run_fulltext_download``.

``fulltext_download_cli.py``'s own module docstring states that the numbered
script (``scripts/11_fulltext_download.py``) delegates here "so configuration
resolution, corpus iteration, download accounting, and report persistence
remain covered source behavior rather than script-local business logic." That
claim only holds for the ``enabled: false`` early-return branch today --
``tests/test_scripts.py::TestFulltextDownloadScript`` only exercises the
disabled path. This file exercises the ``enabled: true`` path directly (corpus
loading, per-paper download loop, pdf/text/skipped accounting, and the
``fulltext_extraction.json`` report artifact), using ``pytest-httpserver`` to
serve a real PDF -- no mocks, matching ``tests/literature/test_fulltext_download.py``'s
pattern.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from literature.corpus import Corpus
from literature.fulltext_download_cli import run_fulltext_download
from literature.models import Paper

pytest_httpserver = pytest.importorskip("pytest_httpserver")
reportlab = pytest.importorskip("reportlab")

from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

KNOWN_TEXT_SUBSTRING = "fulltext-download-cli-fixture-known-substring-7"


def _build_text_only_pdf(path: Path) -> None:
    """Write a real, text-only PDF (no embedded raster images) via reportlab."""
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(72, 700, f"Fulltext CLI fixture: {KNOWN_TEXT_SUBSTRING}")
    c.showPage()
    c.save()


def _write_config(config_path: Path, *, enabled: bool, unpaywall_email: str = "") -> None:
    config_path.write_text(
        f"""
project_config:
  fulltext:
    enabled: {"true" if enabled else "false"}
    unpaywall_email: "{unpaywall_email}"
""".strip(),
        encoding="utf-8",
    )


def test_run_fulltext_download_enabled_downloads_and_reports(httpserver, tmp_path: Path) -> None:
    pdf_source = tmp_path / "_source.pdf"
    _build_text_only_pdf(pdf_source)
    pdf_bytes = pdf_source.read_bytes()
    httpserver.expect_request("/full.pdf").respond_with_data(pdf_bytes, content_type="application/pdf")

    downloadable = Paper(title="Has a PDF", doi="10.5555/one", pdf_url=httpserver.url_for("/full.pdf"))
    unresolvable = Paper(title="No PDF and no DOI")
    corpus = Corpus([downloadable, unresolvable])
    corpus_path = tmp_path / "corpus.jsonl"
    corpus.save(corpus_path)

    config_path = tmp_path / "config.yaml"
    _write_config(config_path, enabled=True)

    project_root = tmp_path / "project"
    project_root.mkdir()

    result = run_fulltext_download(
        project_root=project_root,
        corpus_path=corpus_path,
        config_path=config_path,
    )

    assert result.enabled is True
    assert result.attempted == 2
    assert result.pdf_count == 1
    assert result.text_count == 1
    assert result.skipped_count == 1

    assert result.artifact_path == project_root / "output" / "data" / "fulltext_extraction.json"
    report = json.loads(result.artifact_path.read_text(encoding="utf-8"))
    assert report["total_papers"] == 2
    assert report["with_extracted_text"] == 1
    assert report["without_extracted_text"] == 1

    download_dir = project_root / "output" / "fulltext"
    downloaded_pdfs = list(download_dir.glob("*.pdf"))
    assert len(downloaded_pdfs) == 1
    downloaded_texts = list(download_dir.glob("*.txt"))
    assert len(downloaded_texts) == 1
    assert KNOWN_TEXT_SUBSTRING in downloaded_texts[0].read_text(encoding="utf-8")


def test_run_fulltext_download_respects_max_papers(httpserver, tmp_path: Path) -> None:
    pdf_source = tmp_path / "_source.pdf"
    _build_text_only_pdf(pdf_source)
    pdf_bytes = pdf_source.read_bytes()
    httpserver.expect_request("/only.pdf").respond_with_data(pdf_bytes, content_type="application/pdf")

    p1 = Paper(title="First", doi="10.5555/first", pdf_url=httpserver.url_for("/only.pdf"))
    p2 = Paper(title="Second", doi="10.5555/second", pdf_url=httpserver.url_for("/only.pdf"))
    corpus = Corpus([p1, p2])
    corpus_path = tmp_path / "corpus.jsonl"
    corpus.save(corpus_path)

    config_path = tmp_path / "config.yaml"
    _write_config(config_path, enabled=True)

    project_root = tmp_path / "project"
    project_root.mkdir()

    result = run_fulltext_download(
        project_root=project_root,
        corpus_path=corpus_path,
        config_path=config_path,
        max_papers=1,
    )

    assert result.attempted == 1
    assert result.pdf_count == 1


def test_run_fulltext_download_disabled_is_a_no_op(tmp_path: Path) -> None:
    corpus = Corpus([Paper(title="Irrelevant while disabled")])
    corpus_path = tmp_path / "corpus.jsonl"
    corpus.save(corpus_path)

    config_path = tmp_path / "config.yaml"
    _write_config(config_path, enabled=False)

    project_root = tmp_path / "project"
    project_root.mkdir()

    result = run_fulltext_download(
        project_root=project_root,
        corpus_path=corpus_path,
        config_path=config_path,
    )

    assert result.enabled is False
    assert result.attempted == 0
    assert result.pdf_count == 0
    assert not (project_root / "output" / "data" / "fulltext_extraction.json").exists()

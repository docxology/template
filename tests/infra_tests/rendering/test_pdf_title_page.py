"""Tests for infrastructure/rendering/_pdf_title_page.py.

No mocks: writes a real ``config.yaml`` under a temporary manuscript directory
and asserts on the generated LaTeX strings (no LaTeX compilation needed).
"""

from __future__ import annotations

from pathlib import Path

PAPER_CONFIG = """paper:
  title: "Deterministic Exemplar"
  subtitle: "A reproducible test subtitle"
authors:
  - name: "Ada Lovelace"
    orcid: "0000-0001-2345-6789"
    email: "ada@example.org"
    affiliation: "Analytical Engine Lab"
publication:
  doi: "10.5281/zenodo.123456"
  year: "2026"
metadata:
  license: "MIT"
"""

from infrastructure.rendering._pdf_title_page import (  # noqa: E402
    generate_title_page_body,
    generate_title_page_preamble,
)


def _manuscript(tmp_path: Path, config_text: str) -> Path:
    d = tmp_path / "manuscript"
    d.mkdir()
    (d / "config.yaml").write_text(config_text, encoding="utf-8")
    return d


class TestPreamble:
    def test_missing_config_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "manuscript").mkdir()
        assert generate_title_page_preamble(tmp_path / "manuscript") == ""

    def test_preamble_includes_title_author_orcid_doi(self, tmp_path: Path) -> None:
        d = _manuscript(tmp_path, PAPER_CONFIG)
        out = generate_title_page_preamble(d)
        assert r"\title{Deterministic Exemplar}" in out
        assert r"\author{" in out
        assert "Ada Lovelace" in out
        assert "0000-0001-2345-6789" in out
        assert "10.5281/zenodo.123456" in out

    def test_preamble_defaults_date_when_absent(self, tmp_path: Path) -> None:
        cfg = 'paper:\n  title: "T"\nauthors:\n  - name: "A"\n'
        d = _manuscript(tmp_path, cfg)
        out = generate_title_page_preamble(d)
        assert r"\date{\today}" in out

    def test_author_without_name_is_skipped(self, tmp_path: Path) -> None:
        cfg = 'paper:\n  title: "T"\nauthors:\n  - affiliation: "Nameless Org"\n  - name: "Grace Hopper"\n'
        d = _manuscript(tmp_path, cfg)
        out = generate_title_page_preamble(d)
        assert "Grace Hopper" in out
        assert "Nameless Org" not in out


class TestBody:
    def test_body_renders_titlepage_with_subtitle(self, tmp_path: Path) -> None:
        d = _manuscript(tmp_path, PAPER_CONFIG)
        body = generate_title_page_body(d)
        assert r"\begin{titlepage}" in body
        assert "Deterministic Exemplar" in body
        assert "A reproducible test subtitle" in body

    def test_missing_config_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "manuscript").mkdir()
        assert generate_title_page_body(tmp_path / "manuscript") == ""

    def test_book_config_uses_book_cover_body(self, tmp_path: Path) -> None:
        book_cfg = PAPER_CONFIG + 'book:\n  title: "A Complete Book"\n'
        d = _manuscript(tmp_path, book_cfg)
        body = generate_title_page_body(d)
        assert body  # book-cover path produces a non-empty LaTeX body
        assert "A Complete Book" in body

"""Tests for infrastructure/rendering/_pdf_title_page.py.

No mocks: writes a real ``config.yaml`` under a temporary manuscript directory
and asserts on the generated LaTeX strings (no LaTeX compilation needed).
"""

from __future__ import annotations

import logging
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
from infrastructure.rendering._pdf_title_page_config import _rendering_options


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

    def test_preamble_uses_forthcoming_doi_without_real_doi(self, tmp_path: Path) -> None:
        cfg = 'paper:\n  title: "T"\nauthors:\n  - name: "A"\npublication:\n  doi_status: "forthcoming"\n'
        d = _manuscript(tmp_path, cfg)
        out = generate_title_page_preamble(d)
        assert "DOI: forthcoming" in out
        assert "https://doi.org" not in out

    def test_preamble_defaults_date_when_absent(self, tmp_path: Path) -> None:
        cfg = 'paper:\n  title: "T"\nauthors:\n  - name: "A"\n'
        d = _manuscript(tmp_path, cfg)
        out = generate_title_page_preamble(d)
        assert r"\date{\today}" in out
        assert out.count(r"\today") == 1

    def test_preamble_keeps_explicit_date_out_of_author_extras(self, tmp_path: Path) -> None:
        cfg = 'paper:\n  title: "T"\n  date: "March 2026"\nauthors:\n  - name: "A"\n'
        d = _manuscript(tmp_path, cfg)
        out = generate_title_page_preamble(d)
        assert r"\date{March 2026}" in out
        assert out.count("March 2026") == 1

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

    def test_body_uses_project_cover_height_fraction(self, tmp_path: Path) -> None:
        config = PAPER_CONFIG.replace(
            "authors:", '  cover:\n    image: "cover.png"\nauthors:'
        ) + "rendering:\n  cover_height_fraction: 0.76\n"
        d = _manuscript(tmp_path, config)
        (d / "cover.png").write_bytes(b"png")

        body = generate_title_page_body(d)

        assert r"height=0.76\textheight" in body

    def test_missing_config_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "manuscript").mkdir()
        assert generate_title_page_body(tmp_path / "manuscript") == ""

    def test_rendering_options_reject_nonfinite_or_invalid_fractions(self) -> None:
        options = _rendering_options(
            {
                "rendering": {
                    "section_breaks": False,
                    "figure_height_fraction": float("nan"),
                    "cover_height_fraction": 2.0,
                    "front_matter_figure_height_fraction": "0.64",
                }
            }
        )
        assert options == {
            "section_breaks": False,
            "figure_height_fraction": "0.5",
            "cover_height_fraction": "0.6",
            "front_matter_figure_height_fraction": "0.64",
        }

    def test_book_config_uses_book_cover_body(self, tmp_path: Path) -> None:
        book_cfg = PAPER_CONFIG + 'book:\n  title: "A Complete Book"\n'
        d = _manuscript(tmp_path, book_cfg)
        body = generate_title_page_body(d)
        assert body  # book-cover path produces a non-empty LaTeX body
        assert "A Complete Book" in body

    def test_book_cover_uses_release_safe_relative_image_path(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        manuscript_dir = output_dir / "manuscript"
        figures_dir = output_dir / "figures" / "cover"
        manuscript_dir.mkdir(parents=True)
        figures_dir.mkdir(parents=True)
        (figures_dir / "cover.png").write_bytes(b"png")
        config = PAPER_CONFIG + 'book:\n  title: "A Complete Book"\n  cover:\n    image: "../figures/cover/cover.png"\n'
        (manuscript_dir / "config.yaml").write_text(config, encoding="utf-8")

        body = generate_title_page_body(manuscript_dir)

        assert r"\detokenize{../figures/cover/cover.png}" in body
        assert tmp_path.as_posix() not in body

    def test_source_manuscript_cover_uses_output_pdf_relative_path(self, tmp_path: Path) -> None:
        manuscript_dir = tmp_path / "manuscript"
        cover_dir = manuscript_dir / "assets" / "cover"
        manuscript_dir.mkdir(parents=True)
        cover_dir.mkdir(parents=True)
        (cover_dir / "cover.png").write_bytes(b"png")
        config = PAPER_CONFIG + 'book:\n  title: "A Complete Book"\n  cover:\n    image: "assets/cover/cover.png"\n'
        (manuscript_dir / "config.yaml").write_text(config, encoding="utf-8")

        body = generate_title_page_body(manuscript_dir)

        assert r"\detokenize{../../manuscript/assets/cover/cover.png}" in body
        assert tmp_path.as_posix() not in body

    def test_book_publishing_page_visual_uses_release_safe_relative_image_path(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        manuscript_dir = output_dir / "manuscript"
        figures_dir = output_dir / "figures" / "frontmatter"
        manuscript_dir.mkdir(parents=True)
        figures_dir.mkdir(parents=True)
        (figures_dir / "transit.png").write_bytes(b"png")
        config = (
            PAPER_CONFIG
            + 'book:\n  title: "A Complete Book"\n'
            + "front_matter:\n"
            + "  page_two_visual:\n"
            + '    image: "../figures/frontmatter/transit.png"\n'
            + '    title: "Evidence & artifact route"\n'
            + '    caption: "Telemetry, not certification: 100% local checks need review."\n'
        )
        (manuscript_dir / "config.yaml").write_text(config, encoding="utf-8")

        body = generate_title_page_body(manuscript_dir)

        assert r"\detokenize{../figures/frontmatter/transit.png}" in body
        assert r"Evidence \& artifact route" in body
        assert r"Telemetry, not certification: 100\% local checks need review." in body
        assert tmp_path.as_posix() not in body

    def test_book_publishing_page_visual_missing_image_is_skipped(self, tmp_path: Path, caplog) -> None:
        manuscript_dir = tmp_path / "output" / "manuscript"
        manuscript_dir.mkdir(parents=True)
        config = (
            PAPER_CONFIG
            + 'book:\n  title: "A Complete Book"\n'
            + "front_matter:\n"
            + "  page_two_visual:\n"
            + '    image: "../figures/frontmatter/missing.png"\n'
            + '    title: "Should not render"\n'
            + '    caption: "Should not render either."\n'
        )
        (manuscript_dir / "config.yaml").write_text(config, encoding="utf-8")

        with caplog.at_level(logging.WARNING):
            body = generate_title_page_body(manuscript_dir)

        assert "Publishing Information" in body
        assert "Should not render" not in body
        assert "missing.png" not in body
        assert "Configured image does not exist" in caplog.text

    def test_paper_cover_uses_release_safe_relative_image_path(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        manuscript_dir = output_dir / "manuscript"
        cover_dir = output_dir / "cover"
        manuscript_dir.mkdir(parents=True)
        cover_dir.mkdir(parents=True)
        (cover_dir / "cover.png").write_bytes(b"png")
        config = (
            'paper:\n  title: "Paper Title"\n  cover:\n    image: "output/cover/cover.png"\n'
            'authors:\n  - name: "Ada Lovelace"\n'
        )
        (manuscript_dir / "config.yaml").write_text(config, encoding="utf-8")

        body = generate_title_page_body(manuscript_dir)

        assert r"\begin{titlepage}" in body
        assert r"\detokenize{../cover/cover.png}" in body
        assert tmp_path.as_posix() not in body

    def test_paper_cover_does_not_use_book_cover_without_book_title(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        manuscript_dir = output_dir / "manuscript"
        cover_dir = output_dir / "cover"
        manuscript_dir.mkdir(parents=True)
        cover_dir.mkdir(parents=True)
        (cover_dir / "paper.png").write_bytes(b"paper")
        (cover_dir / "book.png").write_bytes(b"book")
        config = (
            'paper:\n  title: "Paper Title"\n  cover:\n    image: "output/cover/paper.png"\n'
            'book:\n  cover:\n    image: "output/cover/book.png"\n'
            'authors:\n  - name: "Ada Lovelace"\n'
        )
        (manuscript_dir / "config.yaml").write_text(config, encoding="utf-8")

        body = generate_title_page_body(manuscript_dir)

        assert r"\detokenize{../cover/paper.png}" in body
        assert "book.png" not in body

    def test_paper_cover_renders_metadata_stack_once(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        manuscript_dir = output_dir / "manuscript"
        cover_dir = output_dir / "cover"
        manuscript_dir.mkdir(parents=True)
        cover_dir.mkdir(parents=True)
        (cover_dir / "cover.png").write_bytes(b"png")
        config = (
            'paper:\n  title: "Paper Title"\n  date: ""\n  cover:\n    image: "output/cover/cover.png"\n'
            'authors:\n  - name: "Daniel Ari Friedman"\n    orcid: "0000-0001-6232-9096"\n'
            'publication:\n  doi_status: "forthcoming"\n'
        )
        (manuscript_dir / "config.yaml").write_text(config, encoding="utf-8")

        preamble = generate_title_page_preamble(manuscript_dir)
        body = generate_title_page_body(manuscript_dir)

        assert "Daniel Ari Friedman" in body
        assert body.count("ORCID:") == 1
        assert body.count("0000-0001-6232-9096") == 2  # link target plus visible text
        assert body.count("DOI: forthcoming") == 1
        assert body.count(r"{\@date\par}") == 1
        assert r"{\@author\par}" not in body
        assert "DOI: forthcoming" not in preamble
        assert r"\date{\today}" in preamble

    def test_paper_cover_prefers_real_doi_over_forthcoming_status(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        manuscript_dir = output_dir / "manuscript"
        cover_dir = output_dir / "cover"
        manuscript_dir.mkdir(parents=True)
        cover_dir.mkdir(parents=True)
        (cover_dir / "cover.png").write_bytes(b"png")
        config = (
            'paper:\n  title: "Paper Title"\n  cover:\n    image: "output/cover/cover.png"\n'
            'authors:\n  - name: "A"\n'
            'publication:\n  doi: "10.5281/zenodo.999"\n  doi_status: "forthcoming"\n'
        )
        (manuscript_dir / "config.yaml").write_text(config, encoding="utf-8")

        body = generate_title_page_body(manuscript_dir)

        assert "DOI: forthcoming" not in body
        assert "10.5281/zenodo.999" in body
        assert "https://doi.org/10.5281/zenodo.999" in body

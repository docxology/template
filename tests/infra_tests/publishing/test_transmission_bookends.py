"""Tests for transmission bookend generation."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.publishing.transmission_barcode_strip import STRIP_FILENAME
from infrastructure.publishing.transmission_bookends import (
    BEGIN_FILENAME,
    END_FILENAME,
    FIGURE_WIDTH,
    STRIP_WIDTH,
    build_transmission_context,
    is_transmission_bookend,
    render_transmission_markdown,
    transmission_bookends_enabled,
    write_transmission_bookends,
)
from infrastructure.publishing.transmission_figure import write_transmission_diagram
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files


def _write_project(project_root: Path, *, enabled: bool = True, doi: str = "") -> None:
    manuscript = project_root / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "00_abstract.md").write_text("# Abstract\n\nBody.\n", encoding="utf-8")
    (manuscript / "99_references.md").write_text("# References\n\n", encoding="utf-8")
    doi_line = f'  doi: "{doi}"\n' if doi else '  doi: ""\n'
    config = f"""paper:
  title: "Transmission Demo"
  version: "1.0"

authors:
  - name: "Author"
    email: "author@example.com"

publication:
{doi_line}  github_repository: "owner/demo"
  transmission_bookends:
    enabled: {str(enabled).lower()}
    max_prior_releases: 2

metadata:
  license: "MIT"
"""
    (manuscript / "config.yaml").write_text(config, encoding="utf-8")


class TestTransmissionFigure:
    def test_write_transmission_diagram_creates_png(self, tmp_path: Path) -> None:
        output_path = tmp_path / "transmission_pairing.png"
        write_transmission_diagram(output_path, current={"doi": "10.5281/zenodo.1", "pdf_sha256": "abc"})
        assert output_path.is_file()
        assert output_path.stat().st_size > 100


class TestTransmissionBookends:
    def test_is_transmission_bookend(self) -> None:
        assert is_transmission_bookend(Path(BEGIN_FILENAME)) is True
        assert is_transmission_bookend(Path("00_abstract.md")) is False

    def test_transmission_bookends_disabled(self, tmp_path: Path) -> None:
        project_root = tmp_path / "demo"
        _write_project(project_root, enabled=False)
        assert transmission_bookends_enabled(project_root / "manuscript" / "config.yaml") is False
        assert write_transmission_bookends(project_root, "demo") is None

    def test_draft_context_is_unpublished(self, tmp_path: Path) -> None:
        project_root = tmp_path / "demo"
        _write_project(project_root, enabled=True)
        context = build_transmission_context(project_root, "demo", repo_root=tmp_path)
        assert context is not None
        assert context.published is False
        markdown = render_transmission_markdown(context, boundary="begin")
        assert "BEGINNING OF TRANSMISSION" in markdown
        assert "pending pairing" in markdown
        assert "\\scriptsize" in markdown
        assert f"width={FIGURE_WIDTH}" in markdown
        assert f"width={STRIP_WIDTH}" in markdown
        assert "width=0.35" not in markdown
        assert "width=0.98}" not in markdown
        assert r"\subsubsection*{Release metadata}" in markdown
        assert r"\subsubsection*{Transmission manifest}" in markdown
        assert "### Release metadata" not in markdown
        assert "### Transmission manifest" not in markdown

    def test_published_context_from_ledger(self, tmp_path: Path) -> None:
        project_root = tmp_path / "demo"
        _write_project(project_root, enabled=True, doi="10.5281/zenodo.12345")
        ledger_path = project_root / "output" / "data" / "publication_ledger.json"
        ledger_path.parent.mkdir(parents=True)
        ledger_path.write_text(
            json.dumps(
                {
                    "schema": "template-publication-ledger-v1",
                    "releases": [
                        {
                            "tag": "v1.0.0",
                            "doi": "10.5281/zenodo.12345",
                            "github_release_url": "https://github.com/owner/demo/releases/tag/v1.0.0",
                            "pdf_sha256": "a" * 64,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        context = build_transmission_context(project_root, "demo", repo_root=tmp_path)
        assert context is not None
        assert context.published is True
        end_markdown = render_transmission_markdown(context, boundary="end")
        assert "END OF TRANSMISSION" in end_markdown
        assert "Prior:" in end_markdown
        assert "### Release metadata" not in end_markdown
        assert "SHA-512" not in end_markdown

    def test_write_transmission_bookends_and_discovery_order(self, tmp_path: Path) -> None:
        project_root = tmp_path / "demo"
        _write_project(project_root, enabled=True)
        paths = write_transmission_bookends(project_root, "demo", repo_root=tmp_path)
        assert paths is not None
        begin_path, end_path = paths
        assert begin_path.name == BEGIN_FILENAME
        assert end_path.name == END_FILENAME

        manuscript_dir = project_root / "output" / "manuscript"
        (manuscript_dir / "00_abstract.md").write_text("# Abstract\n\n", encoding="utf-8")
        (manuscript_dir / "99_references.md").write_text("# References\n\n", encoding="utf-8")
        ordered = discover_manuscript_files(manuscript_dir)
        assert ordered[0].name == BEGIN_FILENAME
        assert ordered[-1].name == END_FILENAME

    def test_prior_releases_truncation(self, tmp_path: Path) -> None:
        project_root = tmp_path / "demo"
        _write_project(project_root, enabled=True, doi="10.5281/zenodo.99999")
        releases = [
            {
                "tag": f"v1.{index}.0",
                "doi": f"10.5281/zenodo.{index}",
                "github_release_url": f"https://github.com/owner/demo/releases/tag/v1.{index}.0",
                "pdf_sha256": "b" * 64,
            }
            for index in range(4)
        ]
        ledger_path = project_root / "output" / "data" / "publication_ledger.json"
        ledger_path.parent.mkdir(parents=True)
        ledger_path.write_text(
            json.dumps({"schema": "template-publication-ledger-v1", "releases": releases}),
            encoding="utf-8",
        )
        context = build_transmission_context(project_root, "demo", repo_root=tmp_path)
        assert context is not None
        end_markdown = render_transmission_markdown(context, boundary="end")
        assert "earlier in `publication_ledger.json`" in end_markdown

    def test_integrity_strip_png_and_markdown(self, tmp_path: Path) -> None:
        project_root = tmp_path / "demo"
        _write_project(project_root, enabled=True)
        context = build_transmission_context(project_root, "demo", repo_root=tmp_path)
        assert context is not None
        strip_path = project_root / "output" / "figures" / STRIP_FILENAME
        assert strip_path.is_file()
        assert strip_path.stat().st_size > 100
        from PIL import Image

        with Image.open(strip_path) as image:
            assert image.width > 400
            assert image.height > 100
        begin_markdown = render_transmission_markdown(context, boundary="begin")
        assert "Integrity QR strip" in begin_markdown
        assert STRIP_FILENAME in begin_markdown

    def test_manifest_json_written(self, tmp_path: Path) -> None:
        project_root = tmp_path / "demo"
        _write_project(project_root, enabled=True)
        context = build_transmission_context(project_root, "demo", repo_root=tmp_path)
        assert context is not None
        manifest_path = project_root / "output" / "data" / "transmission_manifest.json"
        assert manifest_path.is_file()
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert payload["title"] == "Transmission Demo"
        assert payload["published"] is False
        begin_markdown = render_transmission_markdown(context, boundary="begin")
        assert "Transmission manifest" in begin_markdown

"""Actual opt-in writer/reconstruction bytes; these tests grant no native custody."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
import yaml
from PIL import Image

from infrastructure.rendering import RenderManager
from infrastructure.rendering._combined_exports import prepare_shared_combined_markdown
from infrastructure.rendering._paper_frontmatter import WEB_ALGORITHM, SHARED_ALGORITHM
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.manuscript_composition import read_manuscript_composition
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.reporting.native_hydration_reconstruction import _combined_body, _pdf_body
from infrastructure.reporting.native_code_contextual_compare import _combined_body as contextual_combined_body
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _project(tmp_path: Path, frontmatter: bool = True):
    m = tmp_path / "manuscript"
    m.mkdir()
    Image.new("RGB", (20, 10), "white").save(m / "image.png")
    (m / "00_abstract.md").write_text("# Abstract\n\nDevelopment fixture.\n")
    (m / "00a_plate.md").write_text("# Plate\n\n![Complete caption.](image.png){#fig:plate}\n")
    settings = {"paper": {"title": "Development fixture"}, "rendering": {"section_breaks": False}}
    if frontmatter:
        settings["paper"]["frontmatter"] = ["00a_plate.md"]
    (m / "config.yaml").write_text(yaml.safe_dump(settings))
    manager = RenderManager(
        RenderingConfig(
            manuscript_dir=str(m),
            output_dir=str(tmp_path / "output"),
            web_dir=str(tmp_path / "output/web"),
            figures_dir=str(m),
        )
    )
    return m, settings, manager


@pytest.mark.parametrize("web", [False, True])
@pytest.mark.parametrize("frontmatter", [False, True])
def test_actual_combined_producer_reconstructs_exact_bytes(tmp_path: Path, web: bool, frontmatter: bool) -> None:
    # Given real files and the actual configured writer, with no injected native owner.
    m, settings, manager = _project(tmp_path, frontmatter)
    paths = discover_manuscript_files(m)
    # When real combined HTML or shared composition is produced.
    if web:
        manager.render_combined_web(paths, m, "fixture")
    else:
        prepare_shared_combined_markdown(manager, paths, m, "fixture")
    combined = tmp_path / "output/web/_combined_manuscript.md"
    receipt_path = tmp_path / "output/reports/manuscript_composition.json"
    receipt = read_manuscript_composition(receipt_path)
    bodies = tuple(p.read_bytes() for p in paths)
    pdf_body, mermaid, gaps = _pdf_body(
        bodies,
        settings,
        None,
        SnapshotReader(tmp_path),
        "templates/template_code_project",
        deadline=time.monotonic() + 600,
    )
    expected_algorithm = (
        (WEB_ALGORITHM if web else SHARED_ALGORITHM)
        if frontmatter
        else ("web-renderer-combine-v1" if web else "shared-combined-markdown-v1")
    )
    # Then both actual consumers reconstruct exactly the producer's retained bytes.
    assert receipt.algorithm == expected_algorithm and not mermaid and not gaps
    assert _combined_body(receipt.algorithm, bodies, settings, pdf_body) == combined.read_bytes()
    assert contextual_combined_body(receipt.algorithm, bodies, settings, pdf_body) == combined.read_bytes()
    # A different source order cannot match; exact source restoration can.
    swapped_pdf, _, _ = _pdf_body(
        tuple(reversed(bodies)),
        settings,
        None,
        SnapshotReader(tmp_path),
        "templates/template_code_project",
        deadline=time.monotonic() + 600,
    )
    assert _combined_body(receipt.algorithm, tuple(reversed(bodies)), settings, swapped_pdf) != combined.read_bytes()
    original = receipt_path.read_bytes()
    mutated = json.loads(original)
    mutated["algorithm"] = "unsupported-frontmatter-name"
    receipt_path.write_text(json.dumps(mutated))
    with pytest.raises(ValueError, match="unsupported"):
        read_manuscript_composition(receipt_path)
    receipt_path.write_bytes(original)
    assert read_manuscript_composition(receipt_path) == receipt


@pytest.mark.parametrize("algorithm", ["web-renderer-combine-v1", "shared-combined-markdown-v1"])
def test_legacy_algorithm_cannot_relabel_frontmatter_bytes(algorithm: str) -> None:
    # Given opted-in settings and a legacy algorithm; when reconstructed; then reject.
    with pytest.raises(ValueError, match="legacy"):
        _combined_body(algorithm, (b"body",), {"paper": {"frontmatter": ["page.md"]}}, b"pdf")


@pytest.mark.parametrize("algorithm", [WEB_ALGORITHM, SHARED_ALGORITHM])
def test_opt_in_algorithm_requires_actual_partition(algorithm: str) -> None:
    with pytest.raises(ValueError, match="requires"):
        _combined_body(algorithm, (b"body",), {}, b"pdf")


def test_unknown_algorithm_refuses() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        _combined_body("unknown", (b"body",), {}, b"pdf")

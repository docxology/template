"""Real all-glyph coverage catches overlays outside the supported source subset."""

from __future__ import annotations

import shutil
import time
from io import BytesIO
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_content_contracts import content_contract_from_bytes
from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@pytest.mark.parametrize("overlay", [False, True])
def test_native_nonrequired_glyph_region_is_observed(tmp_path: Path, overlay: bool) -> None:
    if not shutil.which("pdftoppm") or not shutil.which("pdffonts"):
        pytest.skip("actual Poppler tools required")
    from reportlab.pdfgen import canvas

    stream = BytesIO()
    producer = canvas.Canvas(stream, pagesize=(612, 792))
    producer.setFont("Helvetica", 16)
    producer.drawString(50, 730, "Invented heading")
    producer.setFont("Helvetica", 14)
    producer.drawString(50, 680, "Orphan measurement -3.25 mV")
    if overlay:
        producer.setFillColorRGB(1, 1, 1)
        producer.rect(40, 670, 350, 30, stroke=0, fill=1)
    producer.save()
    directory = tmp_path / "output/readiness/all-glyphs"
    directory.mkdir(parents=True, mode=0o700)
    original = directory / "original.pdf"
    original.write_bytes(stream.getvalue())
    reader = SnapshotReader(tmp_path)
    snapshot = reader.read(original.relative_to(tmp_path).as_posix())
    deadline = time.monotonic() + 90
    raster = audit_pdf_raster(
        tmp_path,
        directory,
        snapshot,
        parse_native_bytes("pdf", snapshot.content),
        env=build_bounded_env(),
        deadline=deadline,
        run_id="d" * 32,
        ordinal=0,
    )
    contract = content_contract_from_bytes("all-glyphs", (("invented.md", b"# Invented heading\n"),))
    observation = inspect_pdf_content(
        snapshot.content,
        tuple(reader.read(row["path"]).content for row in raster["rasters"]),
        contract,
        deadline=deadline,
    )
    assert observation["observed_glyph_words"] > observation["source_required_words"]
    codes = {row["code"] for row in observation["findings"]}
    assert ("pdf.visual.invisible" in codes) if overlay else not codes

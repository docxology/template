"""Genuine source-only native packages and original package-reader controls."""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, native_environment
from infrastructure.reporting.native_office_reference import (
    build_office_source_reference,
    read_office_package_ast,
    inspect_office_package_reference,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.validation.publication.rendered_provenance import write_rendered_provenance_receipt
from tests.infra_tests.reporting.test_native_office_semantic_source import PROJECT, _admitted_project


@pytest.mark.parametrize("kind", ("docx", "epub"))
def test_actual_source_only_package_and_readback_preserve_unresolved_coverage(tmp_path: Path, kind: str) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("actual Pandoc unavailable")
    _admitted_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    directory = tmp_path / "output/readiness/reference"
    directory.mkdir(parents=True)
    env = native_environment(tmp_path, Path(sys.executable), directory)
    deadline = time.monotonic() + 45
    # Candidate path deliberately does not exist: it cannot feed reference.
    artifact = NativeArtifact(f"manuscript:{kind}", kind, f"missing-candidate.{kind}")
    reference = build_office_source_reference(
        tmp_path,
        directory,
        PROJECT,
        artifact,
        SnapshotReader(tmp_path),
        env=env,
        deadline=deadline,
        run_id="invented-source-only-reference",
    )
    assert reference["writer"]["original_exit_code"] == 0
    assert reference["status"] == "blocked"
    assert reference["source"]["source_coverage"]["counts"]["Math"] == 1
    assert reference["source"]["source_coverage"]["counts"]["Table"] == 1
    readback_dir = directory / "readback"
    readback_dir.mkdir()
    readback = read_office_package_ast(
        tmp_path,
        readback_dir,
        reference["package"],
        kind,
        env=env,
        deadline=deadline,
        run_id="invented-source-only-reference",
    )
    assert readback["tool"]["original_exit_code"] == 0
    document = json.loads((tmp_path / readback["ast"]["path"]).read_bytes())
    content = json.dumps(document["blocks"])
    assert "-3.25" in content and "2020" in content
    assert '"Math"' in content and '"Table"' in content
    # Equality is deliberately insufficient to discharge source obligations.
    assert reference["blockers"]
    ast_bytes = (tmp_path / readback["ast"]["path"]).read_bytes()
    from infrastructure.reporting.native_office_table_coverage import inspect_office_table_readback

    source_ast = (tmp_path / reference["source"]["ast"]["path"]).read_bytes()
    table = inspect_office_table_readback(source_ast, ast_bytes)
    assert table["status"] == "blocked" and not table["findings"]
    assert len(table["source_tables"]) == 1
    same = inspect_office_package_reference(ast_bytes, ast_bytes, reference["source"]["source_coverage"])
    assert same["status"] == "blocked" and not same["findings"]
    # A valid actual package mutation is read by the same genuine reader.
    from io import BytesIO
    import zipfile
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined
    from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes

    original = (tmp_path / reference["package"]["path"]).read_bytes()
    target = BytesIO()
    changed_members = 0
    with zipfile.ZipFile(BytesIO(original)) as package, zipfile.ZipFile(target, "w") as mutant:
        for member in package.infolist():
            data = package.read(member.filename)
            if member.filename.endswith((".xml", ".xhtml")) and b"-3.25" in data:
                data = data.replace(b"-3.25", b"-4.25")
                changed_members += 1
            mutant.writestr(member, data)
    assert changed_members
    parse_native_bytes(kind, target.getvalue())
    changed_path = directory / f"changed-cell.{kind}"
    atomic_write_bytes_confined(tmp_path, changed_path, target.getvalue(), mode=0o600)
    changed = SnapshotReader(tmp_path).read(changed_path.relative_to(tmp_path).as_posix())
    changed_dir = directory / "changed-readback"
    changed_dir.mkdir()
    changed_readback = read_office_package_ast(
        tmp_path,
        changed_dir,
        {"path": changed.relative, "sha256": changed.sha256},
        kind,
        env=env,
        deadline=deadline,
        run_id="invented-source-only-reference",
    )
    assert changed_readback["tool"]["original_exit_code"] == 0
    changed_ast = (tmp_path / changed_readback["ast"]["path"]).read_bytes()
    rejected = inspect_office_package_reference(ast_bytes, changed_ast, reference["source"]["source_coverage"])
    assert rejected["status"] == "failed"
    assert rejected["findings"] == [{"code": "office.reference.package_content"}]
    changed_table = inspect_office_table_readback(source_ast, changed_ast)
    assert changed_table["status"] == "failed"
    assert changed_table["findings"] == [{"code": "office.table.rows", "table": 0}]


@pytest.mark.parametrize(
    "candidate_name",
    (
        "baseline",
        "changed-number",
        "tiny-text",
        "opaque-overlay",
        "figure-baseline",
        "changed-figure-detail",
        "wrong-citation",
    ),
)
def test_real_full_native_page_reference_rejects_valid_mutants(tmp_path: Path, candidate_name: str) -> None:
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined
    from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
    from infrastructure.reporting.native_format_pdf_oracles import pdf_control_bytes
    from infrastructure.reporting.native_office_reference_visual import inspect_office_reference_projection

    if not shutil.which("pdftoppm") or not shutil.which("pdffonts"):
        pytest.skip("actual PDF raster/font tools unavailable")
    directory = tmp_path / "output/readiness/full-pages"
    directory.mkdir(parents=True)
    env = native_environment(tmp_path, Path(sys.executable), directory)
    deadline = time.monotonic() + 45
    observed = []
    for ordinal, name in enumerate(("baseline", candidate_name)):
        cell = directory / str(ordinal)
        cell.mkdir()
        if candidate_name in {"figure-baseline", "changed-figure-detail", "wrong-citation"}:
            from infrastructure.reporting.native_projection_checks import projection_control_fixture

            data = projection_control_fixture("baseline" if ordinal == 0 or name == "figure-baseline" else name)[0]
        else:
            data = pdf_control_bytes(name)
        original = cell / "original.pdf"
        atomic_write_bytes_confined(tmp_path, original, data, mode=0o600)
        reader = SnapshotReader(tmp_path)
        snapshot = reader.read(original.relative_to(tmp_path).as_posix())
        raster = audit_pdf_raster(
            tmp_path,
            cell,
            snapshot,
            parse_native_bytes("pdf", data),
            env=env,
            deadline=deadline,
            run_id="invented-full-page-controls",
            ordinal=0,
        )
        pixels = tuple(reader.read(row["path"]).content for row in raster["rasters"])
        observed.append((data, pixels))
    reference_pdf, reference_pixels = observed[0]
    for candidate_pdf, candidate_pixels in observed[1:]:
        result = inspect_office_reference_projection(
            reference_pdf, reference_pixels, candidate_pdf, candidate_pixels, deadline=deadline
        )
        if candidate_name in {"baseline", "figure-baseline"}:
            assert result["status"] == "observed" and not result["findings"]
        else:
            assert result["status"] == "failed"
            required = "office.reference.link" if candidate_name == "wrong-citation" else "office.reference.pixels"
            assert any(row["code"] == required for row in result["findings"])


def test_compressed_native_image_rejects_before_unbounded_expansion() -> None:
    import tracemalloc
    import zlib
    from pdfminer.pdftypes import PDFStream
    from pdfminer.psparser import LIT
    from infrastructure.reporting.native_office_reference_visual import _bounded_stream_data

    compressed = zlib.compress(b"x" * (1024 * 1024))
    stream = PDFStream({"Filter": LIT("FlateDecode")}, compressed)
    tracemalloc.start()
    try:
        with pytest.raises(ValueError, match="expansion exceeds finite decode budget"):
            _bounded_stream_data(stream, 4096)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 128 * 1024
    assert stream.data is None and stream.get_rawdata() == compressed


def test_predictor_rejects_oversized_row_before_allocation() -> None:
    import tracemalloc
    import zlib
    from pdfminer.pdftypes import PDFStream
    from pdfminer.psparser import LIT
    from infrastructure.reporting.native_office_reference_visual import _bounded_stream_data

    stream = PDFStream(
        {"Filter": LIT("FlateDecode"), "DecodeParms": {"Predictor": 12, "Columns": 1_000_000_000, "Colors": 3}},
        zlib.compress(b"\x00x"),
    )
    tracemalloc.start()
    try:
        with pytest.raises(ValueError, match="predictor row exceeds finite decode budget"):
            _bounded_stream_data(stream, 4096)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 128 * 1024


def test_raster_dimension_guard_precedes_pixel_decode() -> None:
    import struct
    import zlib
    from infrastructure.reporting.native_format_pdf_oracles import pdf_control_bytes
    from infrastructure.reporting.native_office_reference_visual import native_page_projection

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))

    # Valid PNG header declares >60M pixels; tiny body deliberately cannot load
    # those pixels. The required geometry rejection must precede that decoder.
    raster = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!IIBBBBB", 8001, 8000, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
        + chunk(b"IEND", b"")
    )
    with pytest.raises(ValueError, match="page exceeds finite pixel budget"):
        native_page_projection(pdf_control_bytes("baseline"), (raster,), deadline=time.monotonic() + 5)


@pytest.mark.parametrize(
    "predictor,encoded",
    (
        (15, b"\x00\x01\x02\x03\x00\x02\x04\x06"),
        (15, b"\x01\x01\x01\x01\x01\x02\x02\x02"),
        (15, b"\x02\x01\x02\x03\x02\x01\x02\x03"),
        (15, b"\x03\x01\x02\x02\x03\x02\x02\x03"),
        (15, b"\x04\x01\x01\x01\x04\x01\x02\x02"),
        (2, b"\x01\x01\x01\x02\x02\x02"),
    ),
)
def test_bounded_predictors_preserve_actual_pdf_decoder_bytes(predictor: int, encoded: bytes) -> None:
    import zlib
    from pdfminer.pdftypes import PDFStream
    from pdfminer.psparser import LIT
    from infrastructure.reporting.native_office_reference_visual import _bounded_stream_data

    attrs = {
        "Filter": LIT("FlateDecode"),
        "DecodeParms": {"Predictor": predictor, "Columns": 3, "Colors": 1, "BitsPerComponent": 8},
    }
    compressed = zlib.compress(encoded)
    original = PDFStream(attrs, compressed).get_data()
    assert original == b"\x01\x02\x03\x02\x04\x06"
    assert _bounded_stream_data(PDFStream(attrs, compressed), 64) == original

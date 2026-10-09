"""Actual baseline/later-page generic slide source/font/clipping/pixel controls."""

from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_slide_source import compile_slide_source_contract, instrument_slide_source
from infrastructure.reporting.native_slide_checks import inspect_slide_source_paint
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SLIDE_CONTROL_CODES = {
    "baseline": None,
    "changed-sign-number": "slides.source.text",
    "omitted-later-occurrence": "slides.source.paint.missing",
    "tiny-later-page": "slides.typography.font",
    "clipped-later-page": "slides.layout.crop",
    "overlay-later-page": "slides.visual.invisible",
    "reordered-later-markers": "slides.source.text",
}
CONTROL_SOURCE = b"Measured offset -3.25 mV.\n\nMeasured offset -3.25 mV.\n"


def slide_source_control_fixture(name: str, ast: bytes) -> tuple[bytes, Any, tuple[dict[str, Any], ...]]:
    """Create genuinely valid native two-page PDFs; setup errors never mean fail."""
    from reportlab.pdfgen.canvas import Canvas

    if name not in SLIDE_CONTROL_CODES:
        raise ValueError("unknown source-owned generic slide control")
    contract = compile_slide_source_contract(
        "invented:slides", (("invented.md", CONTROL_SOURCE),), ast, profile="archive"
    )
    _, bindings = instrument_slide_source(ast, contract, target="beamer")
    if len(bindings) != 8:
        raise ValueError("actual source parser fixture unexpectedly changed original visible occurrences")
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(720, 405), invariant=1)
    for page in range(2):
        x = -40 if page == 1 and name == "clipped-later-page" else 40
        canvas.setFont("Helvetica", 5 if page == 1 and name == "tiny-later-page" else 18)
        for ordinal, binding in enumerate(bindings[page * 4 : (page + 1) * 4]):
            if page == 1 and name == "omitted-later-occurrence" and ordinal == 3:
                continue
            mcid = binding["mcid"]
            if page == 1 and name == "reordered-later-markers":
                mcid = bindings[page * 4 + (3 - ordinal)]["mcid"]
            canvas.addLiteral(f"/Span <</MCID {mcid}>> BDC")
            text = binding["source"]
            if page == 1 and name == "changed-sign-number" and text == "-3.25":
                text = "+3.26"
            canvas.drawString(x, 280, text)
            x += canvas.stringWidth(text, "Helvetica", 5 if page == 1 and name == "tiny-later-page" else 18) + 8
            canvas.addLiteral("EMC")
        if page == 1 and name == "overlay-later-page":
            canvas.setFillColorRGB(1, 1, 1)
            canvas.rect(0, 250, 720, 70, fill=1, stroke=0)
        canvas.showPage()
    canvas.save()
    return stream.getvalue(), contract, bindings


def run_slide_source_control(
    root: Path, directory: Path, name: str, *, env: dict[str, str], deadline: float, run_id: str
) -> dict[str, Any]:
    """Real Pandoc source parse, valid PDF parser/raster, and intended diagnostics."""
    from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime

    create_private_native_directory(root, directory)
    runtime = CitationRuntime(root, directory / "parser", env=env, deadline=deadline, run_id=run_id)
    source = runtime.freeze("invented.md", CONTROL_SOURCE)
    parsed_source = runtime.tool("pandoc", [str(source), "--to=json"], "control-source-ast", input_paths=(source,))
    ast = parsed_source["stdout"].encode()
    pdf, contract, bindings = slide_source_control_fixture(name, ast)
    path = directory / "control.pdf"
    atomic_write_bytes_confined(root, path, pdf, mode=0o600)
    reader = SnapshotReader(root)
    snapshot = reader.read(path.relative_to(root).as_posix())
    parsed = parse_native_bytes("pdf", pdf)
    raster = audit_pdf_raster(root, directory, snapshot, parsed, env=env, deadline=deadline, run_id=run_id, ordinal=0)
    pixels = tuple(reader.read(row["path"]).content for row in raster["rasters"])
    observed = inspect_slide_source_paint(pdf, pixels, contract, bindings, deadline=deadline, source_images={})
    code = SLIDE_CONTROL_CODES[name]
    if (
        observed["blockers"]
        or (code is None and observed["status"] != "pass")
        or (code and (observed["status"] != "fail" or code not in {f["code"] for f in observed["findings"]}))
    ):
        raise ValueError("valid generic slide control did not preserve actual intended native diagnostic")
    if not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("generic slide control custody changed or original deadline expired")
    return {
        "schema_version": "template-native-slide-source-valid-control-v1",
        "name": name,
        "expected_code": code,
        "input": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "parser": parsed,
        "raster": raster,
        "source_tools": runtime.tools,
        "observation": observed,
        "oracle_exit_code": 0 if code is None else 1,
    }


def main() -> int:
    import argparse
    import os
    from infrastructure.project.public_acceptance_evidence import write_json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--name", choices=tuple(SLIDE_CONTROL_CODES), required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    result = run_slide_source_control(
        args.root, args.directory, args.name, env=dict(os.environ), deadline=args.deadline, run_id=args.run_id
    )
    write_json(args.root, args.directory / "observation.json", result)
    return int(result["oracle_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

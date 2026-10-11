"""Actual per-page projected glyph checks, retaining unsupported visual gates."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from io import BytesIO
from typing import Any

from infrastructure.reporting.native_format_content_contracts import ContentBlock, NativeContentContract, text_tokens
from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content
from infrastructure.reporting.native_projection_contracts import (
    ProjectionPage,
    ProjectionFigure,
    projection_contract_record,
)
from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def inspect_projection(
    pdf_bytes: bytes,
    rasters: tuple[bytes, ...],
    pages: tuple[ProjectionPage, ...],
    *,
    deadline: float,
    native_context: tuple[Path, Path, dict[str, str], str] | None = None,
) -> dict[str, Any]:
    """Check every native page and raster; no first-slide or archive-only success.

    Source-owned image fidelity and actual QR decoding are required when present.
    Missing native decoders and unsupported compositing remain explicit blockers.
    """
    import pdfplumber
    from pypdf import PdfReader, PdfWriter

    document = PdfReader(BytesIO(pdf_bytes), strict=True)
    if not pages or len(document.pages) != len(pages) or len(rasters) != len(pages):
        raise ValueError("projection needs exact complete source/page/raster parity")
    observations: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as glyph_document:
        for ordinal, (page, raster, expected) in enumerate(zip(document.pages, rasters, pages, strict=True), 1):
            if time.monotonic() >= deadline:
                raise TimeoutError("projection inspection exhausted original deadline")
            if (
                abs(float(page.mediabox.width) - expected.size_pt[0]) > 0.5
                or abs(float(page.mediabox.height) - expected.size_pt[1]) > 0.5
            ):
                findings.append({"code": "projection.page.geometry", "page": ordinal})
            output = BytesIO()
            writer = PdfWriter()
            writer.add_page(page)
            writer.write(output)
            blocks = tuple(
                ContentBlock(f"page:{ordinal}:{index}", role, index, text_tokens(text))
                for index, (role, text, _) in enumerate(expected.texts)
                if text
            )
            if not blocks:
                raise ValueError("projection page has no source text")
            contract = NativeContentContract(f"projection:{ordinal}", (), blocks, ())
            observed = inspect_pdf_content(output.getvalue(), (raster,), contract, deadline=deadline)
            observations.append(observed)
            findings.extend({**finding, "page": ordinal} for finding in observed["findings"])
            actual = glyph_document.pages[ordinal - 1]
            actual_tokens = tuple(token for word in actual.extract_words() for token in text_tokens(word["text"]))
            expected_tokens = tuple(token for block in blocks for token in block.tokens)
            if actual_tokens != expected_tokens:
                findings.append({"code": "projection.content.exact", "page": ordinal})
            # Annotations are actual native PDF targets, independent of OOXML.
            targets = {str(link.get("uri", "")) for link in actual.hyperlinks}
            if expected.citation and expected.citation not in targets:
                findings.append({"code": "projection.citation.target", "page": ordinal})
            if expected.qr_target and expected.qr_target not in targets:
                findings.append({"code": "projection.qr.link", "page": ordinal})
            mapped_words = {word["word_index"]: word for word in observed["supported_words"]}
            matches = {match["block_id"]: match for match in observed["matches"]}
            for index, (role, text, floor) in enumerate(expected.texts):
                if not text:
                    continue
                match = matches.get(f"page:{ordinal}:{index}")
                if match is None:
                    continue  # Existing content diagnostic preserves failure.
                for word_index in match["word_indices"]:
                    word = mapped_words[word_index]
                    if word["min_font_pt"] < floor:
                        findings.append(
                            {
                                "code": "projection.typography.font",
                                "page": ordinal,
                                "role": role,
                                "word_index": word_index,
                                "observed_pt": word["min_font_pt"],
                                "minimum_pt": floor,
                            }
                        )
            if expected.qr_target:
                if native_context is None:
                    blockers.append(f"page {ordinal}: native QR pixel decoder context required")
                else:
                    root, directory, env, run_id = native_context
                    decoded = decode_projection_qr(
                        root,
                        directory,
                        raster,
                        expected.qr_target,
                        env=env,
                        deadline=deadline,
                        run_id=run_id,
                        ordinal=ordinal,
                    )
                    observations[-1]["qr"] = decoded
                    findings.extend({**finding, "page": ordinal} for finding in decoded["findings"])
            if expected.figure:
                if expected.figure_projection is None:
                    blockers.append(f"page {ordinal}: frozen source figure projection required")
                else:
                    figure = inspect_figure_projection(raster, expected.figure_projection)
                    embedded = inspect_embedded_figure(pdf_bytes, ordinal, expected.figure_projection)
                    figure["embedded"] = embedded
                    figure["findings"].extend(embedded["findings"])
                    observations[-1]["figure"] = figure
                    findings.extend({**finding, "page": ordinal} for finding in figure["findings"])
    return {
        "schema_version": "template-native-projection-observation-v1",
        "contract": projection_contract_record(pages),
        "pages": observations,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


FIGURE_POLICY = {
    "schema_version": "template-native-figure-pixel-v1",
    "comparison_size": 64,
    "max_mean_channel_error": 8.0,
    "max_changed_fraction": 0.05,
    "changed_channel_threshold": 32,
    "dpi": 150,
}


def inspect_figure_projection(raster: bytes, expected: ProjectionFigure) -> dict[str, Any]:
    """Compare localized actual projected pixels to exact admitted source pixels.

    Bounded coarse comparison tolerates native interpolation, but detects changed
    artwork, misplaced images, cropping, distortion and opaque overlays. Alpha
    sources are unsupported rather than composited against a guessed background.
    """
    from PIL import Image, ImageChops, ImageStat

    with Image.open(BytesIO(expected.content)) as source, Image.open(BytesIO(raster)) as actual:
        if source.width * source.height > 20_000_000 or actual.width * actual.height > 60_000_000:
            raise ValueError("figure pixel comparison exceeds dimension policy")
        source.load()
        actual.load()
        if "A" in source.getbands() and source.getchannel("A").getextrema() != (255, 255):
            raise ValueError("source figure alpha requires a declared compositing policy")
        left, top, right, bottom = expected.box_pt
        roi = (round(left * 150 / 72), round(top * 150 / 72), round(right * 150 / 72), round(bottom * 150 / 72))
        if (
            roi[0] < 0
            or roi[1] < 0
            or roi[2] > actual.width
            or roi[3] > actual.height
            or roi[0] >= roi[2]
            or roi[1] >= roi[3]
        ):
            raise ValueError("source figure projection escapes actual raster")
        dimensions = (64, 64)
        reference = source.convert("RGB").resize(dimensions, Image.Resampling.LANCZOS)
        observed = actual.crop(roi).convert("RGB").resize(dimensions, Image.Resampling.LANCZOS)
        difference = ImageChops.difference(reference, observed)
        mean = sum(ImageStat.Stat(difference).mean) / 3
        samples = difference.tobytes()
        changed = sum(max(samples[index : index + 3]) > 32 for index in range(0, len(samples), 3)) / (64 * 64)
        findings = []
        if mean > 8 or changed > 0.05:
            findings.append({"code": "projection.figure.pixels"})
    return {
        "policy": FIGURE_POLICY,
        "source_sha256": hashlib.sha256(expected.content).hexdigest(),
        "raster_sha256": hashlib.sha256(raster).hexdigest(),
        "roi_px": list(roi),
        "mean_channel_error": mean,
        "changed_fraction": changed,
        "findings": findings,
    }


def inspect_embedded_figure(pdf: bytes, ordinal: int, expected: ProjectionFigure) -> dict[str, Any]:
    """Require exact full decoded source-image pixels and actual native placement.

    Coarse raster similarity alone cannot establish scientific image fidelity:
    a changed digit in a chart must fail this independent full-pixel identity.
    Native lossy recompression therefore fails rather than weakening the policy.
    """
    from PIL import Image
    from pypdf import PdfReader
    import pdfplumber

    with Image.open(BytesIO(expected.content)) as source:
        if source.width * source.height > 20_000_000:
            raise ValueError("source image exceeds full pixel identity budget")
        reference = source.convert("RGB")
        digest = hashlib.sha256(reference.tobytes()).hexdigest()
        dimensions = reference.size
    document = PdfReader(BytesIO(pdf), strict=True)
    # A native PDF may expose one indirect image repeatedly through nested
    # form resource dictionaries. Those inventory references are not draws;
    # inspect the actual content-stream placements independently below.
    matching: set[str] = set()
    for image in document.pages[ordinal - 1].images:
        native = image.image
        if native is None or native.width * native.height > 20_000_000:
            raise ValueError("actual native image exceeds full pixel identity budget")
        pixels = native.convert("RGB")
        if pixels.size == dimensions and hashlib.sha256(pixels.tobytes()).hexdigest() == digest:
            matching.add(image.name.rsplit(".", 1)[0])
    findings = []
    boxes = []
    with pdfplumber.open(BytesIO(pdf)) as glyph_document:
        for placement in glyph_document.pages[ordinal - 1].images:
            if placement["name"] in matching:
                boxes.append(
                    (
                        float(placement["x0"]),
                        float(placement["top"]),
                        float(placement["x1"]),
                        float(placement["bottom"]),
                    )
                )
    if len(matching) != 1:
        findings.append({"code": "projection.figure.source-pixels"})
    elif len(boxes) != 1 or any(
        abs(observed - admitted) > 0.5 for observed, admitted in zip(boxes[0], expected.box_pt, strict=True)
    ):
        findings.append({"code": "projection.figure.geometry"})
    return {
        "source_pixel_sha256": digest,
        "dimensions": list(dimensions),
        "native_image_names": sorted(matching),
        "native_boxes_pt": [list(box) for box in boxes],
        "findings": findings,
    }


def decode_projection_qr(
    root: Path,
    directory: Path,
    raster: bytes,
    target: str,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    ordinal: int,
) -> dict[str, Any]:
    """Decode actual projected QR pixels using zbar; preserve real no-symbol exit 4."""
    from PIL import Image

    if not target or "\n" in target or "\r" in target:
        raise ValueError("QR target must be one nonempty source-owned line")
    path = directory / f"qr-page-{ordinal}.png"
    if path.exists():
        raise ValueError("QR decoder requires fresh admitted raster")
    with Image.open(BytesIO(raster)) as image:
        image.verify()
    atomic_write_bytes_confined(root, path, raster, mode=0o600)
    from infrastructure.reporting.native_qr_runtime import bind_qr_core, finish_qr_core

    runtime, core, core_bytes = bind_qr_core(
        root, directory, env=env, deadline=deadline, run_id=run_id, ordinal=ordinal
    )
    record = native_tool_record(
        root,
        directory,
        "zbarimg",
        ["--quiet", "--raw", "--set", "disable", "--set", "qrcode.enable", str(path)],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose=f"qr-decode-{ordinal}",
    )
    if record["exit_code"] not in {0, 4} or record["original_exit_code"] != record["exit_code"]:
        raise ValueError("actual QR decoder failed outside recognized symbol outcomes")
    reader = SnapshotReader(root)
    payload = json.loads(reader.read(record["artifact"]["path"]).content)
    if payload["executable"] != runtime["executable"] or payload["executable_sha256"] != runtime["executable_sha256"]:
        raise ValueError("QR scanner executable changed between version and pixel observation")
    runtime_artifact = finish_qr_core(root, directory, runtime, core, core_bytes, ordinal=ordinal)
    consumed = reader.read(path.relative_to(root).as_posix())
    if consumed.sha256 != hashlib.sha256(raster).hexdigest() or not reader.unchanged():
        raise ValueError("actual QR decoder raster custody changed")
    values = payload["stdout"].splitlines()
    findings = [] if record["exit_code"] == 0 and values == [target] else [{"code": "projection.qr.pixels"}]
    return {
        "raster_sha256": consumed.sha256,
        "target": target,
        "decoded": values,
        "tool_artifact": record["artifact"],
        "runtime_artifact": runtime_artifact,
        "original_exit_code": record["original_exit_code"],
        "findings": findings,
        "status": "fail" if findings else "pass",
    }


PROJECTION_CONTROL_CODES: dict[str, str | None] = {
    "baseline": None,
    "changed-number": "pdf.content.missing",
    "clipped-text": "pdf.layout.crop",
    "tiny-text": "projection.typography.font",
    "opaque-overlay": "pdf.visual.invisible",
    "wrong-citation": "projection.citation.target",
    "changed-figure": "projection.figure.pixels",
    "changed-figure-detail": "projection.figure.source-pixels",
    "distorted-figure": "projection.figure.pixels",
    "baseline-qr": None,
    "wrong-qr": "projection.qr.pixels",
    "unreadable-qr": "projection.qr.pixels",
}


def projection_control_fixture(name: str) -> tuple[bytes, tuple[ProjectionPage, ...]]:
    """Reconstruct deterministic native PDF fixture and its independent obligations."""
    from PIL import Image, ImageDraw
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.utils import ImageReader

    if name not in PROJECTION_CONTROL_CODES:
        raise ValueError("unknown source-owned projection control")
    source = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(source)
    draw.rectangle((0, 0, 31, 63), fill="#1a46cc")
    draw.rectangle((32, 0, 63, 31), fill="#d32c15")
    draw.rectangle((32, 32, 63, 63), fill="#23a831")
    source_stream = BytesIO()
    source.save(source_stream, format="PNG")
    figure = ProjectionFigure("invented-source.png", source_stream.getvalue(), (500.0, 155.0, 600.0, 255.0))
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(720, 405), invariant=1)
    canvas.setFont("Helvetica", 30)
    canvas.drawString(40, 350, "Invented measurement")
    canvas.setFont("Helvetica", 5 if name == "tiny-text" else 18)
    canvas.drawString(
        -70 if name == "clipped-text" else 40,
        280,
        "Measured offset -3.26 mV." if name == "changed-number" else "Measured offset -3.25 mV.",
    )
    canvas.setFont("Helvetica", 9)
    canvas.drawString(40, 25, "invented.csv")
    target = "https://example.org/invented.csv"
    canvas.linkURL("https://example.org/wrong" if name == "wrong-citation" else target, (40, 20, 120, 35))
    actual_figure = Image.new("RGB", (64, 64), "black") if name == "changed-figure" else source.copy()
    if name == "changed-figure-detail":
        actual_figure.putpixel((0, 0), (0, 0, 0))
    canvas.drawImage(ImageReader(actual_figure), 500, 150, width=50 if name == "distorted-figure" else 100, height=100)
    if name == "opaque-overlay":
        canvas.setFillColorRGB(1, 1, 1)
        canvas.rect(30, 265, 400, 35, fill=1, stroke=0)
    qr_target = "https://example.org/invented-slide" if name in {"baseline-qr", "wrong-qr", "unreadable-qr"} else ""
    if qr_target:
        import qrcode

        qr = qrcode.make("https://example.org/wrong" if name == "wrong-qr" else qr_target)
        qr_stream = BytesIO()
        qr.save(qr_stream, format="PNG")
        canvas.drawImage(ImageReader(BytesIO(qr_stream.getvalue())), 620, 25, width=72, height=72)
        canvas.linkURL(qr_target, (620, 25, 692, 97))
        if name == "unreadable-qr":
            canvas.setFillColorRGB(1, 1, 1)
            canvas.rect(615, 20, 80, 80, fill=1, stroke=0)
    canvas.save()
    pdf = stream.getvalue()
    expected = ProjectionPage(
        (
            ("title", "Invented measurement", 14.0),
            ("body", "Measured offset -3.25 mV.", 18.0),
            ("citation", "invented.csv", 9.0),
        ),
        target,
        qr_target,
        True,
        figure,
    )
    return pdf, (expected,)


def run_projection_control(
    root: Path, directory: Path, name: str, *, env: dict[str, str], deadline: float, run_id: str
) -> dict[str, Any]:
    """Rasterize source-owned valid controls and retain actual intended diagnoses."""
    from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes

    pdf, pages = projection_control_fixture(name)
    input_path = directory / "control.pdf"
    atomic_write_bytes_confined(root, input_path, pdf, mode=0o600)
    reader = SnapshotReader(root)
    artifact = reader.read(input_path.relative_to(root).as_posix())
    parsed = parse_native_bytes("pdf", pdf)
    raster = audit_pdf_raster(root, directory, artifact, parsed, env=env, deadline=deadline, run_id=run_id, ordinal=0)
    pixels = tuple(reader.read(item["path"]).content for item in raster["rasters"])
    observed = inspect_projection(pdf, pixels, pages, deadline=deadline, native_context=(root, directory, env, run_id))
    expected_code = PROJECTION_CONTROL_CODES[name]
    codes = {item["code"] for item in observed["findings"]}
    if observed["blockers"]:
        raise ValueError("valid projection control has unresolved observer obligations")
    if expected_code is None and observed["status"] != "pass":
        raise ValueError("valid projection baseline did not pass actual source/raster oracle")
    if expected_code is not None and (observed["status"] != "fail" or expected_code not in codes):
        raise ValueError("valid projection mutant did not produce intended actual oracle diagnostic")
    if not reader.unchanged():
        raise ValueError("valid projection control pixels changed during inspection")
    return {
        "schema_version": "template-native-projection-valid-control-v1",
        "name": name,
        "expected_code": expected_code,
        "input": {"path": artifact.relative, "sha256": artifact.sha256},
        "parser": parsed,
        "raster": raster,
        "observation": observed,
        "oracle_exit_code": 0 if expected_code is None else 1,
    }


def supervise_projection_controls(
    root: Path,
    directory: Path,
    *,
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    include_qr: bool = True,
    control_names: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """Execute fresh baseline-first native controls in independently supervised children."""
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
    from infrastructure.project.public_acceptance_evidence import bootstrap_command, write_json
    from infrastructure.core.execution_boundary import run_bounded_subprocess

    if not interpreter.is_absolute() or not interpreter.is_file():
        raise ValueError("supervised controls require actual installed interpreter")

    if control_names is not None and (
        not control_names
        or len(set(control_names)) != len(control_names)
        or any(name not in PROJECTION_CONTROL_CODES for name in control_names)
    ):
        raise ValueError("controls must be distinct source-owned identities")
    records = []
    for ordinal, name in enumerate(PROJECTION_CONTROL_CODES):
        if control_names is not None and name not in control_names:
            continue
        if not include_qr and name in {"baseline-qr", "wrong-qr", "unreadable-qr"}:
            continue
        child = directory / f"control-{ordinal}"
        create_private_native_directory(root, child)
        command = bootstrap_command(
            interpreter,
            root,
            __name__,
            "--control",
            name,
            "--root",
            str(root),
            "--directory",
            str(child),
            "--deadline",
            str(deadline),
            "--run-id",
            run_id,
        )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("supervised projection controls exhausted original deadline")
        started = time.monotonic()
        process = run_bounded_subprocess(command, cwd=root, env=env, timeout=min(remaining, 60))
        elapsed = time.monotonic() - started
        tool: dict[str, Any] = {"exit_code": process.returncode, "original_exit_code": process.original_returncode}
        tool["artifact"] = write_json(
            root,
            directory / f"projection-control-{ordinal}-process.json",
            {
                "schema_version": "template-native-projection-control-process-v1",
                "run_id": run_id,
                "command": list(command),
                "exit_code": process.returncode,
                "original_exit_code": process.original_returncode,
                "timed_out": process.timed_out,
                "custody_refused": process.custody_refused,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "diagnostic": process.command_error,
                "elapsed_seconds": elapsed,
            },
        )
        if process.timed_out or process.custody_refused:
            raise ValueError("supervised projection control timed out or source custody was refused")
        expected = 0 if PROJECTION_CONTROL_CODES[name] is None else 1
        if tool["exit_code"] == 75:
            from infrastructure.reporting.native_format_acceptance_checks import NativeToolUnavailable

            raise NativeToolUnavailable(f"actual projection control {name} needs an unavailable native tool")
        if tool["exit_code"] != expected or tool["original_exit_code"] != expected:
            raise ValueError("supervised projection control did not retain intended original exit")
        reader = SnapshotReader(root)
        outcome = reader.read((child / "observation.json").relative_to(root).as_posix())
        payload = json.loads(outcome.content)
        if payload["name"] != name or payload["expected_code"] != PROJECTION_CONTROL_CODES[name]:
            raise ValueError("supervised control output differs from source-owned control identity")
        codes = {item["code"] for item in payload["observation"]["findings"]}
        if payload["observation"]["blockers"] or (expected == 1 and PROJECTION_CONTROL_CODES[name] not in codes):
            raise ValueError("supervised control has no intended actual oracle evidence")
        records.append(
            {
                "name": name,
                "tool_artifact": tool["artifact"],
                "result": {"path": outcome.relative, "sha256": outcome.sha256},
                "original_exit_code": expected,
            }
        )
    return records


def main() -> int:
    """Private supervised control entry point; never treats setup errors as oracle failures."""
    import argparse
    import os
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.native_format_acceptance_checks import NativeToolUnavailable

    parser = argparse.ArgumentParser()
    parser.add_argument("--control", choices=tuple(PROJECTION_CONTROL_CODES), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        result = run_projection_control(
            args.root, args.directory, args.control, env=dict(os.environ), deadline=args.deadline, run_id=args.run_id
        )
    except NativeToolUnavailable:
        return 75
    write_json(args.root, args.directory / "observation.json", result)
    return int(result["oracle_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

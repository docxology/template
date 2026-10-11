"""Full native Office page comparison, subordinate to independent source coverage."""

from __future__ import annotations

import hashlib
import json
import math
import time
from io import BytesIO
from pathlib import Path
from typing import Any
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams

from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.native_pdf_stream_decode import _bounded_stream_data as _bounded_stream_data

MAX_REFERENCE_BYTES = 250 * 1024 * 1024
MAX_PAGES = 500
MAX_OBJECTS = 2_000_000


def _canonical(value: Any) -> Any:
    from pdfminer.psparser import PSLiteral

    if isinstance(value, PSLiteral):
        return {"pdf_literal": _canonical(value.name)}
    if isinstance(value, dict):
        return {key: _canonical(child) for key, child in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonical(child) for child in value]
    if isinstance(value, bytes):
        return {"bytes_sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("native Office reference object has nonfinite geometry")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError("native Office reference object has unsupported value")


def native_page_projection(pdf: bytes, rasters: tuple[bytes, ...], *, deadline: float) -> tuple[dict[str, Any], ...]:
    """Retain every native glyph, font, line, curve, rectangle, image and pixel.

    PDF object IDs and creation metadata are not rendered observations. No
    geometry, glyph, font, image or pixel normalization is applied.
    """
    import pdfplumber
    from PIL import Image

    if len(pdf) + sum(map(len, rasters)) > MAX_REFERENCE_BYTES:
        raise ValueError("native Office reference exceeds finite byte budget")
    preflight_pdf_streams(pdf, deadline=deadline, max_bytes=MAX_REFERENCE_BYTES, max_objects=MAX_OBJECTS)
    rows = []
    objects = 0
    decoded_bytes = 0
    with pdfplumber.open(BytesIO(pdf)) as document:
        if not document.pages or len(document.pages) > MAX_PAGES or len(document.pages) != len(rasters):
            raise ValueError("native Office reference requires complete bounded page/raster sets")
        for ordinal, page in enumerate(document.pages):
            if time.monotonic() >= deadline:
                raise TimeoutError("native Office reference comparison expired")
            page_objects: dict[str, list[Any]] = {}
            for kind in ("char", "line", "rect", "curve", "image"):
                actual = page.objects.get(kind, [])
                objects += len(actual)
                if objects > MAX_OBJECTS:
                    raise ValueError("native Office reference exceeds finite object budget")
                selected = []
                for item in actual:
                    # Structural resource IDs vary between independent writes;
                    # rendered image bytes and all geometric fields are kept.
                    record = {
                        key: value
                        for key, value in item.items()
                        if key not in {"object_type", "page_number", "name", "stream", "mcid", "tag"}
                    }
                    if kind == "image":
                        stream = item.get("stream")
                        if stream is None:
                            raise ValueError("native Office image has no decoded stream")
                        record["decoded_stream"] = _bounded_stream_data(stream, MAX_REFERENCE_BYTES - decoded_bytes)
                        decoded_bytes += len(record["decoded_stream"])
                        if decoded_bytes > MAX_REFERENCE_BYTES:
                            raise ValueError("native Office decoded images exceed finite byte budget")
                    selected.append(_canonical(record))
                page_objects[kind] = selected
            page_objects["link"] = [
                _canonical(
                    {
                        key: link.get(key)
                        for key in (
                            "uri",
                            "title",
                            "contents",
                            "x0",
                            "y0",
                            "x1",
                            "y1",
                            "top",
                            "bottom",
                            "width",
                            "height",
                        )
                    }
                )
                for link in page.hyperlinks
            ]
            with Image.open(BytesIO(rasters[ordinal])) as raster:
                if raster.width * raster.height > 60_000_000:
                    raise ValueError("native Office reference page exceeds finite pixel budget")
                raster.load()
                rgb = raster.convert("RGB")
                pixels = {"size": list(rgb.size), "rgb_sha256": hashlib.sha256(rgb.tobytes()).hexdigest()}
            payload = {
                "page": ordinal + 1,
                "width": page.width,
                "height": page.height,
                "objects": page_objects,
                "pixels": pixels,
            }
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            rows.append({**payload, "projection_sha256": hashlib.sha256(encoded).hexdigest()})
    return tuple(rows)


def inspect_office_reference_projection(
    reference_pdf: bytes,
    reference_rasters: tuple[bytes, ...],
    candidate_pdf: bytes,
    candidate_rasters: tuple[bytes, ...],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Compare every actual native page; equal writers cannot clear source blockers."""
    reference = native_page_projection(reference_pdf, reference_rasters, deadline=deadline)
    candidate = native_page_projection(candidate_pdf, candidate_rasters, deadline=deadline)
    findings = []
    if len(reference) != len(candidate):
        findings.append({"code": "office.reference.pages", "expected": len(reference), "observed": len(candidate)})
    for left, right in zip(reference, candidate):
        if (left["width"], left["height"]) != (right["width"], right["height"]):
            findings.append({"code": "office.reference.page_geometry", "page": left["page"]})
        for kind in ("char", "line", "rect", "curve", "image", "link"):
            if left["objects"][kind] != right["objects"][kind]:
                findings.append({"code": f"office.reference.{kind}", "page": left["page"]})
        if left["pixels"] != right["pixels"]:
            findings.append({"code": "office.reference.pixels", "page": left["page"]})
    return {
        "schema_version": "template-native-office-full-projection-v1",
        "status": "failed" if findings else "observed",
        "findings": findings,
        "reference_pages": [{"page": row["page"], "sha256": row["projection_sha256"]} for row in reference],
        "candidate_pages": [{"page": row["page"], "sha256": row["projection_sha256"]} for row in candidate],
        "assurance": "complete native page equality; independent scientific source witnesses still mandatory",
    }


def observe_reference_conversion(
    root: Path,
    directory: Path,
    package: dict[str, Any],
    kind: str,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_engine: Path | None = None,
) -> dict[str, Any]:
    """Use the reviewed native converter and raster every original output page."""
    from infrastructure.reporting.native_office_observer import convert_office
    from infrastructure.reporting.native_epub_observer import inspect_epub

    reader = SnapshotReader(root)
    snapshot = reader.read(package["path"])
    if snapshot.sha256 != package["sha256"]:
        raise ValueError("Office reference conversion input changed")
    if kind == "docx":
        conversion = convert_office(root, directory, snapshot, kind, env=env, deadline=deadline, run_id=run_id)
    elif kind == "epub":
        conversion = inspect_epub(
            root,
            directory,
            snapshot,
            env=env,
            deadline=deadline,
            run_id=run_id,
            epubcheck_jar=epubcheck_jar,
            java_executable=java_executable,
            frozen_engine=frozen_engine,
        )
    else:
        raise ValueError("Office source reference requires DOCX or EPUB")
    pdf = reader.read(conversion["pdf"]["path"])
    raster = audit_pdf_raster(
        root,
        directory,
        pdf,
        parse_native_bytes("pdf", pdf.content),
        env=env,
        deadline=deadline,
        run_id=run_id,
        ordinal=0,
    )
    if not reader.unchanged():
        raise ValueError("Office reference original native conversion custody changed")
    return {"conversion": conversion, "raster": raster}

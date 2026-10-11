"""Genuine independent SVG decode and native diagram-image ink projection.

The parent owns admission of rsvg-convert/Pango/font/library custody and the
original supervised controls. Missing custody is a blocker, never a new budget.
"""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_office_content_witness import _image_identity
from infrastructure.reporting.native_office_image_ink import inspect_office_native_images
from infrastructure.reporting.native_office_mermaid_semantics import inspect_mermaid_svg_source
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-office-mermaid-independent-ink-v1"


def _rgb_identity(data: bytes) -> dict[str, Any]:
    """Decode admitted actual pixels and composite transparency over paper white."""
    from PIL import Image, ImageStat

    identity = _image_identity(data)
    if identity["kind"] != "decoded-raster":
        raise ValueError("Office diagram ink requires an independently decoded raster")
    with Image.open(BytesIO(data)) as image:
        image.load()
        rgba = image.convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        rgb = Image.alpha_composite(white, rgba).convert("RGB")
        return {
            "size": list(rgb.size),
            "rgb_sha256": hashlib.sha256(rgb.tobytes()).hexdigest(),
            "variance": sum(ImageStat.Stat(rgb).var),
        }


def mermaid_ink_outcome(rows: list[dict[str, Any]], native: dict[str, Any]) -> dict[str, Any]:
    """Refuse changed/blank raster ink and retain exact topology residuals."""
    findings = [finding for row in rows for finding in row["source_projection"]["findings"]]
    blockers = [blocker for row in rows for blocker in row["source_projection"]["blockers"]]
    for row in rows:
        png, decoded = row["production_png"], row["independent_svg_png"]
        if min(png["variance"], decoded["variance"]) <= 0:
            findings.append({"code": "office.mermaid.blank_ink", "ordinal": row["ordinal"]})
        if (png["size"], png["rgb_sha256"]) != (decoded["size"], decoded["rgb_sha256"]):
            findings.append({"code": "office.mermaid.svg_png_ink", "ordinal": row["ordinal"]})
    findings.extend(native["findings"])
    blockers.extend(native["blockers"])
    return {
        "schema_version": SCHEMA,
        "status": "failed" if findings else "blocked" if blockers else "observed",
        "findings": findings,
        "blockers": list(dict.fromkeys(blockers)),
        "diagrams": rows,
        "native_images": native,
        "assurance": "independent actual librsvg raster and native PDF image pixels; genuine controls remain mandatory",
    }


def observe_office_mermaid_ink(
    root: Path,
    directory: Path,
    production: dict[str, Any],
    native_pdf: bytes,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Execute genuine bounded rsvg-convert on each source-bound original SVG.

    Schedule only within the parent's authorized native phase. Exact pixel
    differences stay findings: no undocumented antialiasing/font tolerance.
    Mermaid foreignObject labels may be unsupported by this independent
    decoder; that is exposed by actual decoded pixels, never excused.
    """
    from infrastructure.reporting.native_format_acceptance_validation import _file

    if production.get("run_id") != run_id or not 0 < len(production.get("diagrams", [])) <= 100:
        raise ValueError("Office Mermaid ink requires the original bounded producer record")
    create_private_native_directory(root, directory)
    rows, records, figures = [], [], []
    for ordinal, row in enumerate(production["diagrams"]):
        svg = _file(row["outputs"]["svg"], reader)
        png = _file(row["outputs"]["png"], reader)
        source = _file(row["source"], reader)
        projection = inspect_mermaid_svg_source(source.content.decode(), svg.content)
        actual = _rgb_identity(png.content)
        output = directory / f"independent-{ordinal:04d}.png"
        arguments = [
            "--format",
            "png",
            "--width",
            str(actual["size"][0]),
            "--height",
            str(actual["size"][1]),
            "--output",
            str(output),
            str(svg.path),
        ]
        tool = native_tool_record(
            root,
            directory,
            "rsvg-convert",
            arguments,
            env=env,
            deadline=deadline,
            run_id=run_id,
            purpose=f"mermaid-independent-{ordinal:04d}",
        )
        if tool["exit_code"] != 0 or tool["original_exit_code"] != 0:
            raise ValueError("actual independent Mermaid SVG decoder failed")
        decoded = reader.read(output.relative_to(root).as_posix())
        rows.append(
            {
                "ordinal": ordinal,
                "source_projection": projection,
                "production_png": actual,
                "independent_svg_png": _rgb_identity(decoded.content),
            }
        )
        records.append(
            {
                "ordinal": ordinal,
                "artifact": {"path": decoded.relative, "sha256": decoded.sha256},
                "process": tool,
            }
        )
        figures.append(png.content)
    native = inspect_office_native_images(native_pdf, tuple(figures), deadline=deadline)
    if not reader.unchanged():
        raise ValueError("Office Mermaid original SVG/PNG/native ink custody changed")
    return {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "records": records,
        "observation": mermaid_ink_outcome(rows, native),
    }


def replay_office_mermaid_ink(
    root: Path,
    directory: Path,
    production: dict[str, Any],
    native_pdf: bytes,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    deadline: float,
) -> None:
    """Recompute original source/vector/raster/native results from portable bytes."""
    from infrastructure.reporting.native_format_acceptance_validation import _file, _tool
    from infrastructure.reporting.native_format_portable_custody import producer_path

    if raw.get("schema_version") != SCHEMA or raw.get("run_id") != run_id or production.get("run_id") != run_id:
        raise ValueError("portable Mermaid independent ink schema/run differs")
    records = raw.get("records")
    if not isinstance(records, list) or len(records) != len(production["diagrams"]) or not 0 < len(records) <= 100:
        raise ValueError("portable Mermaid independent decode inventory differs")
    version = versions.get("rsvg-convert")
    if not isinstance(version, dict):
        raise ValueError("portable Mermaid independent decoder requires its admitted real version/runtime custody")
    rows, figures = [], []
    for ordinal, (row, record) in enumerate(zip(production["diagrams"], records, strict=True)):
        source = _file(row["source"], reader)
        svg = _file(row["outputs"]["svg"], reader)
        png = _file(row["outputs"]["png"], reader)
        decoded = _file(record["artifact"], reader)
        actual = _rgb_identity(png.content)
        if record["ordinal"] != ordinal or decoded.path != directory / f"independent-{ordinal:04d}.png":
            raise ValueError("portable Mermaid decoded raster belongs to another original attempt")
        arguments = [
            "--format",
            "png",
            "--width",
            str(actual["size"][0]),
            "--height",
            str(actual["size"][1]),
            "--output",
            str(producer_path(custody, root, decoded.path)),
            str(producer_path(custody, root, svg.path)),
        ]
        tool = _tool(
            record["process"]["artifact"],
            reader,
            run_id,
            "rsvg-convert",
            f"mermaid-independent-{ordinal:04d}",
            arguments,
        )
        if any(tool[key] != version[key] for key in ("executable", "executable_sha256")):
            raise ValueError("portable Mermaid SVG decoder differs from its original real version probe")
        rows.append(
            {
                "ordinal": ordinal,
                "source_projection": inspect_mermaid_svg_source(source.content.decode(), svg.content),
                "production_png": actual,
                "independent_svg_png": _rgb_identity(decoded.content),
            }
        )
        figures.append(png.content)
    native = inspect_office_native_images(native_pdf, tuple(figures), deadline=deadline)
    if mermaid_ink_outcome(rows, native) != raw["observation"] or not reader.unchanged():
        raise ValueError("portable Mermaid actual independent vector/native ink interpretation differs")

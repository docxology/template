"""Actual source-only PDF image stencils and independent native visible ink.

Original PNG pixels are painted at each decoded native physical placement with
no candidate clip/opacity/occluding content. Every nonwhite stencil pixel must
exist in the real native page at the same 150-dpi coordinate, without tolerance.
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_office_diagram_geometry import (
    DiagramSource,
    MAX_BYTES,
    inspect_diagram_pdf_geometry,
)
from infrastructure.reporting.native_office_diagram_runtime import (
    PDFiumRuntimeAdmission,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-office-original-diagram-visible-ink-v1"
DPI = 150


@dataclass(frozen=True)
class DecodedNativePage:
    png_sha256: str
    width: int
    height: int
    rgb: bytes


def decode_native_diagram_page(data: bytes, *, budget: SourceImageDecodeBudget) -> DecodedNativePage:
    """Reserve once for each actual retained native page, then share its RGB."""
    from PIL import Image

    if len(data) > MAX_BYTES:
        raise ValueError("native diagram page raster exceeds original byte bound")
    with Image.open(BytesIO(data)) as image:
        if image.format != "PNG":
            raise ValueError("native diagram page is not the actual PNG raster")
        budget.admit_header(image.width, image.height)
        image.load()
        if "A" in image.getbands() and image.getchannel("A").getextrema() != (255, 255):
            raise ValueError("native diagram page raster has an unadmitted alpha channel")
        return DecodedNativePage(
            hashlib.sha256(data).hexdigest(),
            image.width,
            image.height,
            image.convert("RGB").tobytes(),
        )


def diagram_stencil(source: DiagramSource, placement: dict[str, Any]) -> tuple[bytes, tuple[int, int, int, int]]:
    """Construct PDF from original pixels and actual finite physical geometry."""
    from pypdf import PdfWriter
    from pypdf.generic import (
        ArrayObject,
        BooleanObject,
        DecodedStreamObject,
        DictionaryObject,
        FloatObject,
        NameObject,
        NumberObject,
    )

    media = placement["media_box_pt"]
    box = placement["box_pt"]
    if media[:2] != [0.0, 0.0]:
        raise ValueError("source diagram stencil requires admitted zero-origin geometry")
    # Crop on the original full-page pixel grid. Integer crop offsets preserve
    # subpixel phase; the PDF page/matrix itself is never shifted or resized.
    left = max(0, math.floor(box[0] * DPI / 72))
    top = max(0, math.floor((media[3] - box[3]) * DPI / 72))
    right = min(math.ceil(media[2] * DPI / 72), math.ceil(box[2] * DPI / 72))
    bottom = min(math.ceil(media[3] * DPI / 72), math.ceil((media[3] - box[1]) * DPI / 72))
    if min(right - left, bottom - top) <= 0 or (right - left) * (bottom - top) > 60_000_000:
        raise ValueError("source diagram stencil crop violates original finite pixel bound")
    writer = PdfWriter()
    page = writer.add_blank_page(width=media[2], height=media[3])
    page[NameObject("/CropBox")] = ArrayObject([FloatObject(value) for value in placement["crop_box_pt"]])
    image = DecodedStreamObject()
    image.set_data(source.rgb)
    image.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(source.width),
            NameObject("/Height"): NumberObject(source.height),
            NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
            NameObject("/BitsPerComponent"): NumberObject(8),
            NameObject("/Interpolate"): BooleanObject(placement["interpolate"]),
        }
    )
    image_reference = writer._add_object(image.flate_encode())
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/XObject"): DictionaryObject({NameObject("/OriginalSource"): image_reference}),
        }
    )
    stream = DecodedStreamObject()
    matrix = " ".join(format(float(value), ".17g") for value in placement["matrix"])
    stream.set_data(f"q\n{matrix} cm\n/OriginalSource Do\nQ\n".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    data = output.getvalue()
    if len(data) > MAX_BYTES:
        raise ValueError("source diagram stencil exceeds original finite PDF byte bound")
    return data, (left, top, right - left, bottom - top)


def inspect_diagram_visible_pixels(
    expected_png: bytes,
    native_page_png: bytes,
    crop: tuple[int, int, int, int],
    *,
    budget: SourceImageDecodeBudget,
    decoded_native: DecodedNativePage | None = None,
    decoded_expected: DecodedNativePage | None = None,
    deadline: float,
) -> dict[str, Any]:
    """Require actual native RGB at every source-ink pixel, including thin ink."""
    from PIL import Image

    left, top, width, height = crop
    if len(expected_png) + len(native_page_png) > MAX_BYTES:
        raise ValueError("source/native diagram raster bytes exceed original finite bound")
    if decoded_expected is None:
        with Image.open(BytesIO(expected_png)) as image:
            if image.format != "PNG" or image.size != (width, height):
                raise ValueError("actual source-only diagram raster has the wrong original crop dimensions")
            budget.admit_header(width, height)
            image.load()
            expected = image.convert("RGB").tobytes()
    else:
        if decoded_expected.png_sha256 != hashlib.sha256(expected_png).hexdigest() or (
            decoded_expected.width,
            decoded_expected.height,
        ) != (width, height):
            raise ValueError("actual source-only diagram bitmap differs from its encoded original crop")
        expected = decoded_expected.rgb
    if len(expected) != width * height * 3:
        raise ValueError("original source diagram RGB buffer differs from its exact reserved header")
    native = decoded_native or decode_native_diagram_page(native_page_png, budget=budget)
    if len(native.rgb) != native.width * native.height * 3:
        raise ValueError("native diagram RGB buffer differs from its exact reserved header")
    if (
        native.png_sha256 != hashlib.sha256(native_page_png).hexdigest()
        or min(left, top) < 0
        or left + width > native.width
        or top + height > native.height
    ):
        raise ValueError("native diagram crop/page digest lies outside its actual original raster page")
    ink = changed = 0
    # White source padding is not evidence. Every other source pixel, including
    # faint anti-aliased glyph/edge pixels, is evidence with no colour threshold.
    actual_digest = hashlib.sha256()
    native_view = memoryview(native.rgb)
    for y in range(height):
        if y % 128 == 0 and time.monotonic() >= deadline:
            raise TimeoutError("native source diagram pixel oracle exhausted original deadline")
        row_start = ((top + y) * native.width + left) * 3
        actual_digest.update(native_view[row_start : row_start + width * 3])
        for x in range(width):
            index = (y * width + x) * 3
            value = expected[index : index + 3]
            if value != b"\xff\xff\xff":
                ink += 1
                actual_index = row_start + x * 3
                changed += value != native.rgb[actual_index : actual_index + 3]
    findings: list[dict[str, Any]] = []
    if not ink:
        findings.append({"code": "office.diagram.no_source_ink"})
    if changed:
        findings.append(
            {
                "code": "office.diagram.visible_ink",
                "changed_source_pixels": changed,
                "source_pixels": ink,
            }
        )
    return {
        "schema_version": "template-native-office-source-diagram-pixel-mask-v1",
        "expected_png_sha256": hashlib.sha256(expected_png).hexdigest(),
        "native_page_png_sha256": hashlib.sha256(native_page_png).hexdigest(),
        "crop_px": list(crop),
        "source_ink_pixels": ink,
        "changed_source_pixels": changed,
        "expected_rgb_sha256": hashlib.sha256(expected).hexdigest(),
        "native_crop_rgb_sha256": actual_digest.hexdigest(),
        "status": "failed" if findings else "pass",
        "findings": findings,
        "blockers": [],
    }


def observe_office_diagram_visibility(
    root: Path,
    directory: Path,
    pdf: bytes,
    native_pages: tuple[bytes, ...],
    sources: tuple[DiagramSource, ...],
    *,
    budget: SourceImageDecodeBudget,
    pdfium_runtime: PDFiumRuntimeAdmission,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    decoded_native_pages: dict[int, DecodedNativePage] | None = None,
) -> dict[str, Any]:
    """Observe original source stencils through real existing raster/font tools."""
    geometry = inspect_diagram_pdf_geometry(pdf, sources, budget=budget, deadline=deadline)
    by_digest = {source.rgb_sha256: source for source in sources}
    create_private_native_directory(root, directory)
    snapshots = SnapshotReader(root)
    stencils = []
    decoded_pages: dict[int, DecodedNativePage] = {} if decoded_native_pages is None else decoded_native_pages
    findings, blockers = list(geometry["findings"]), list(geometry["blockers"])
    for ordinal, placement in enumerate(geometry["placements"]):
        if time.monotonic() >= deadline:
            raise TimeoutError("native diagram stencil production exhausted original deadline")
        source = by_digest[placement["rgb_sha256"]]
        data, crop = diagram_stencil(source, placement)
        path = directory / f"source-stencil-{ordinal:04d}.pdf"
        prefix = directory / f"source-stencil-{ordinal:04d}"
        atomic_write_bytes_confined(root, path, data, mode=0o600)
        binding = {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        tools = []
        args = [
            "-r",
            str(DPI),
            "-f",
            "1",
            "-l",
            "1",
            "-singlefile",
            "-x",
            str(crop[0]),
            "-y",
            str(crop[1]),
            "-W",
            str(crop[2]),
            "-H",
            str(crop[3]),
            "-png",
            str(path),
            str(prefix),
        ]
        for executable, arguments, purpose in (
            ("pdftoppm", args, f"office-diagram-stencil-{ordinal:04d}"),
            ("pdffonts", [str(path)], f"office-diagram-stencil-fonts-{ordinal:04d}"),
        ):
            record = native_tool_record(
                root,
                directory,
                executable,
                arguments,
                env=env,
                deadline=deadline,
                run_id=run_id,
                purpose=purpose,
            )
            if record["exit_code"] != 0 or record["original_exit_code"] != 0:
                raise ValueError("actual original source diagram stencil raster/font process failed")
            tools.append(record["artifact"])
        raster = snapshots.read(prefix.with_suffix(".png").relative_to(root).as_posix())
        if not 1 <= placement["page"] <= len(native_pages):
            raise ValueError("actual source diagram has no complete original native raster page")
        page_number = placement["page"]
        if page_number not in decoded_pages:
            decoded_pages[page_number] = decode_native_diagram_page(native_pages[page_number - 1], budget=budget)
        pixels = inspect_diagram_visible_pixels(
            raster.content,
            native_pages[page_number - 1],
            crop,
            budget=budget,
            decoded_native=decoded_pages[page_number],
            deadline=deadline,
        )
        from infrastructure.reporting.native_office_diagram_pdfium import (
            observe_pdfium_diagram_crop,
        )

        pdfium_dir = directory / f"pdfium-{ordinal:04d}"
        create_private_native_directory(root, pdfium_dir)
        pdfium, actual_crops = observe_pdfium_diagram_crop(
            root,
            pdfium_dir,
            pdf,
            data,
            placement,
            crop,
            budget=budget,
            deadline=deadline,
            runtime=pdfium_runtime,
        )
        source_png, source_rgb = actual_crops["source"]
        native_png, native_rgb = actual_crops["native"]
        pdfium_pixels = inspect_diagram_visible_pixels(
            source_png,
            native_png,
            (0, 0, crop[2], crop[3]),
            budget=budget,
            deadline=deadline,
            decoded_expected=DecodedNativePage(hashlib.sha256(source_png).hexdigest(), crop[2], crop[3], source_rgb),
            decoded_native=DecodedNativePage(hashlib.sha256(native_png).hexdigest(), crop[2], crop[3], native_rgb),
        )
        pdfium["observation"] = pdfium_pixels
        findings.extend(pixels["findings"])
        findings.extend(pdfium_pixels["findings"])
        stencils.append(
            {
                "ordinal": ordinal,
                "placement": placement,
                "source_png_sha256": source.png_sha256,
                "source_svg_sha256": source.svg_sha256,
                "pdf": binding,
                "crop_px": list(crop),
                "tool_artifacts": tools,
                "raster": {"path": raster.relative, "sha256": raster.sha256},
                "observation": pixels,
                "pdfium": pdfium,
            }
        )
    if not snapshots.unchanged() or time.monotonic() >= deadline:
        raise ValueError("original source stencil/native raster custody changed")
    return {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "geometry": geometry,
        "stencils": stencils,
        "status": "failed" if findings else "blocked" if blockers else "pass",
        "findings": findings,
        "blockers": blockers,
        "assurance": (
            "independent original pixels/physical placement/clip/alpha/font floor and every visible source-ink pixel; "
            "original controls and full process/library/source custody required"
        ),
    }


def replay_office_diagram_visibility(
    root: Path,
    directory: Path,
    pdf: bytes,
    native_pages: tuple[bytes, ...],
    sources: tuple[DiagramSource, ...],
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    budget: SourceImageDecodeBudget,
    pdfium_runtime: PDFiumRuntimeAdmission,
    run_id: str,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    deadline: float,
    reader_directory: Path,
    env: dict[str, str],
) -> dict[str, Any]:
    """Admit originals and genuinely repaint stencils with reader-local tools.

    The fresh directory is explicit, confined and distinct from retained
    producer artifacts. Original absolute executable paths remain custody
    labels; new execution selects current tools through Root's admitted env.
    """
    from infrastructure.reporting.native_format_acceptance_validation import (
        _file,
        _tool,
    )
    from infrastructure.reporting.native_format_portable_custody import producer_path

    if (
        set(raw)
        != {
            "schema_version",
            "run_id",
            "pdf_sha256",
            "geometry",
            "stencils",
            "status",
            "findings",
            "blockers",
            "assurance",
        }
        or raw["schema_version"] != SCHEMA
        or raw["run_id"] != run_id
    ):
        raise ValueError("portable original diagram visibility schema/run differs")
    geometry = inspect_diagram_pdf_geometry(pdf, sources, budget=budget, deadline=deadline)
    if raw["geometry"] != geometry or raw["pdf_sha256"] != hashlib.sha256(pdf).hexdigest():
        raise ValueError("portable independently parsed native diagram paint geometry differs")
    if len(raw["stencils"]) != len(geometry["placements"]):
        raise ValueError("portable original source stencil occurrence census differs")
    by_digest = {source.rgb_sha256: source for source in sources}
    findings, blockers = list(geometry["findings"]), list(geometry["blockers"])
    decoded_pages: dict[int, DecodedNativePage] = {}
    for ordinal, (row, placement) in enumerate(zip(raw["stencils"], geometry["placements"], strict=True)):
        source = by_digest[placement["rgb_sha256"]]
        data, crop = diagram_stencil(source, placement)
        stencil = _file(row["pdf"], reader)
        prefix = directory / f"source-stencil-{ordinal:04d}"
        raster = _file(row["raster"], reader)
        if (
            set(row)
            != {
                "ordinal",
                "placement",
                "source_png_sha256",
                "source_svg_sha256",
                "pdf",
                "crop_px",
                "tool_artifacts",
                "raster",
                "observation",
                "pdfium",
            }
            or row["ordinal"] != ordinal
            or row["placement"] != placement
            or row["crop_px"] != list(crop)
            or stencil.path != prefix.with_suffix(".pdf")
            or stencil.content != data
            or raster.path != prefix.with_suffix(".png")
            or row["source_png_sha256"] != source.png_sha256
            or row["source_svg_sha256"] != source.svg_sha256
            or len(row["tool_artifacts"]) != 2
        ):
            raise ValueError("portable original diagram source pixels/stencil/frame custody differs")
        original_pdf = str(producer_path(custody, root, stencil.path))
        original_prefix = str(producer_path(custody, root, prefix))
        for tool_binding, name, arguments, purpose in (
            (
                row["tool_artifacts"][0],
                "pdftoppm",
                [
                    "-r",
                    str(DPI),
                    "-f",
                    "1",
                    "-l",
                    "1",
                    "-singlefile",
                    "-x",
                    str(crop[0]),
                    "-y",
                    str(crop[1]),
                    "-W",
                    str(crop[2]),
                    "-H",
                    str(crop[3]),
                    "-png",
                    original_pdf,
                    original_prefix,
                ],
                f"office-diagram-stencil-{ordinal:04d}",
            ),
            (
                row["tool_artifacts"][1],
                "pdffonts",
                [original_pdf],
                f"office-diagram-stencil-fonts-{ordinal:04d}",
            ),
        ):
            tool = _tool(tool_binding, reader, run_id, name, purpose, arguments)
            if any(tool[key] != versions[name][key] for key in ("executable", "executable_sha256")):
                raise ValueError("portable diagram stencil used a different actual admitted raster/font tool")
        page_number = placement["page"]
        if not 1 <= page_number <= len(native_pages):
            raise ValueError("portable native diagram has no original raster page")
        if page_number not in decoded_pages:
            decoded_pages[page_number] = decode_native_diagram_page(native_pages[page_number - 1], budget=budget)
        pixels = inspect_diagram_visible_pixels(
            raster.content,
            native_pages[page_number - 1],
            crop,
            budget=budget,
            decoded_native=decoded_pages[page_number],
            deadline=deadline,
        )
        if pixels != row["observation"]:
            raise ValueError("portable every-source-pixel diagram visible ink differs")
        from infrastructure.reporting.native_office_diagram_pdfium import (
            validate_pdfium_diagram_crop,
        )

        independent = row["pdfium"]
        validate_pdfium_diagram_crop(
            {key: value for key, value in independent.items() if key != "observation"},
            pdf,
            data,
            placement,
            crop,
            reader=reader,
            run_id=run_id,
            runtime=pdfium_runtime,
        )
        source_png = _file(independent["artifacts"]["source"], reader)
        native_png = _file(independent["artifacts"]["native"], reader)
        pdfium_dir = directory / f"pdfium-{ordinal:04d}"
        if source_png.path != pdfium_dir / "pdfium-source.png" or native_png.path != pdfium_dir / "pdfium-native.png":
            raise ValueError("portable independent PDFium native/source crop occurrence paths differ")
        pdfium_pixels = inspect_diagram_visible_pixels(
            source_png.content,
            native_png.content,
            (0, 0, crop[2], crop[3]),
            budget=budget,
            deadline=deadline,
        )
        if pdfium_pixels != independent["observation"]:
            raise ValueError("portable independent original PDFium source/native visible ink differs")
        findings.extend(pixels["findings"])
        findings.extend(pdfium_pixels["findings"])
    if (
        raw["findings"] != findings
        or raw["blockers"] != blockers
        or raw["status"] != ("failed" if findings else "blocked" if blockers else "pass")
    ):
        raise ValueError("portable independent diagram visibility outcome differs")
    if directory == reader_directory or directory in reader_directory.parents:
        raise ValueError("portable native diagram source repaint cannot write into retained producer evidence")
    fresh = observe_office_diagram_visibility(
        root,
        reader_directory,
        pdf,
        native_pages,
        sources,
        budget=budget,
        pdfium_runtime=pdfium_runtime,
        env=env,
        deadline=deadline,
        run_id=run_id,
        decoded_native_pages=decoded_pages,
    )
    if fresh["geometry"] != geometry or any(fresh[key] != raw[key] for key in ("status", "findings", "blockers")):
        raise ValueError("portable genuine reader diagram source geometry/visible-ink outcome differs")
    for prior, current in zip(raw["stencils"], fresh["stencils"], strict=True):
        keys = (
            "expected_rgb_sha256",
            "native_crop_rgb_sha256",
            "crop_px",
            "source_ink_pixels",
            "changed_source_pixels",
        )
        if any(prior["observation"][key] != current["observation"][key] for key in keys):
            raise ValueError("portable actual reader stencil paint differs at an original source-ink pixel")
        if any(prior["pdfium"]["observation"][key] != current["pdfium"]["observation"][key] for key in keys):
            raise ValueError("portable actual independent PDFium paint differs at an original source-ink pixel")
    from infrastructure.project.public_acceptance_evidence import write_json

    write_json(root, reader_directory / "reader-diagram-visibility.json", fresh)
    if not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("portable diagram terminal custody or original deadline changed")
    return fresh

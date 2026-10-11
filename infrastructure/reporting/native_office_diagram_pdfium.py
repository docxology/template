"""Separate actual PDFium source/native crop paint and installed DLL custody.

Poppler remains active. This native library paints only exact integer-grid
diagram crops, with its own before/after package and loaded DLL evidence. Root
must admit the original enclosing process, preimport hook and OS libraries.
"""

from __future__ import annotations

import hashlib
import math
import struct
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_office_diagram_runtime import (
    PDFiumRuntimeAdmission,
    _loaded_image,
    authenticate_original_pdfium_event,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-office-independent-pdfium-diagram-crop-v2"
MAX_FILES = 20_000
MAX_BYTES = 1024 * 1024 * 1024


def _crop_pixels(
    pdf: bytes,
    page_number: int,
    placement: dict[str, Any],
    crop: tuple[int, int, int, int],
    *,
    budget: SourceImageDecodeBudget,
    deadline: float,
) -> tuple[bytes, bytes]:
    """Allocate only the reserved actual integer-grid crop, without rescaling."""
    import pypdfium2 as pdfium

    from PIL import Image

    scale = 150 / 72
    media = placement["media_box_pt"]
    if placement["crop_box_pt"] != media:
        raise ValueError("independent PDFium diagram crop requires equal admitted media/crop boxes")
    left, top, width, height = crop
    full_width, full_height = math.ceil(media[2] * scale), math.ceil(media[3] * scale)
    trims = (left, full_height - top - height, full_width - left - width, top)
    if min(trims) < 0:
        raise ValueError("independent native diagram crop exceeds its exact original pixel grid")
    budget.admit_header(width, height)
    document = pdfium.PdfDocument(pdf)
    try:
        page = document[page_number - 1]
        try:
            actual_size = tuple(page.get_size())
            expected_size = tuple(struct.unpack("f", struct.pack("f", value))[0] for value in media[2:])
            if actual_size != expected_size or (
                math.ceil(actual_size[0] * scale),
                math.ceil(actual_size[1] * scale),
            ) != (full_width, full_height):
                raise ValueError("actual PDFium diagram page geometry differs from independent PDF parsing")
            # A tiny fractional reduction before ceil produces precisely the
            # intended integer trims. No page, matrix or pixel grid is shifted.
            canvas_trims = tuple(0.0 if value == 0 else (value - 0.25) / scale for value in trims)
            bitmap = page.render(
                scale=scale,
                rotation=0,
                crop=canvas_trims,
                may_draw_forms=False,
                draw_annots=True,
                rev_byteorder=True,
                fill_color=(255, 255, 255, 255),
                limit_image_cache=True,
            )
            try:
                if (bitmap.width, bitmap.height) != (width, height):
                    raise ValueError("actual PDFium diagram crop allocation differs from its admitted header")
                image = bitmap.to_pil()
                try:
                    rgb = image.convert("RGB")
                    try:
                        rgb_bytes = rgb.tobytes()
                        output = BytesIO()
                        rgb.save(output, format="PNG")
                        data = output.getvalue()
                    finally:
                        rgb.close()
                finally:
                    image.close()
            finally:
                bitmap.close()
        finally:
            page.close()
    finally:
        document.close()
    if time.monotonic() >= deadline:
        raise TimeoutError("independent native diagram PDFium crop exhausted original enclosing deadline")
    # Native execution is bounded by Root's original finite guardian/child;
    # this method never extends its deadline or allocates a full-page bitmap.
    with Image.open(BytesIO(data)) as check:
        if check.size != (width, height):
            raise ValueError("independent PDFium encoded crop has invalid geometry")
    return data, rgb_bytes


def observe_pdfium_diagram_crop(
    root: Path,
    directory: Path,
    pdf: bytes,
    stencil: bytes,
    placement: dict[str, Any],
    crop: tuple[int, int, int, int],
    *,
    budget: SourceImageDecodeBudget,
    deadline: float,
    runtime: PDFiumRuntimeAdmission,
) -> tuple[dict[str, Any], dict[str, tuple[bytes, bytes]]]:
    """Paint under the original launcher's already-admitted provider and clock."""
    if runtime.deadline != deadline or runtime.source.bindings.current_root != root:
        raise ValueError("PDFium original crop differs from genuine caller Source/deadline")
    before = runtime.verify()
    import pypdfium2_raw.bindings as bindings

    loaded = Path(bindings._libs["pdfium"]._name).resolve(strict=True)
    runtime.verify(loaded=loaded)
    image_before = _loaded_image(loaded, deadline)
    label = loaded.relative_to(runtime.site).as_posix()
    library = before["files"][label]
    native_png, native_rgb = _crop_pixels(pdf, placement["page"], placement, crop, budget=budget, deadline=deadline)
    source_png, source_rgb = _crop_pixels(stencil, 1, placement, crop, budget=budget, deadline=deadline)
    artifacts = {}
    for role, data in (("native", native_png), ("source", source_png)):
        path = directory / f"pdfium-{role}.png"
        atomic_write_bytes_confined(root, path, data, mode=0o600)
        artifacts[role] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    inputs = {
        "native_pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "stencil_pdf_sha256": hashlib.sha256(stencil).hexdigest(),
        "page": placement["page"],
        "crop_px": list(crop),
        "dpi": 150,
    }
    outputs = {
        "artifacts": artifacts,
        "native_rgb_sha256": hashlib.sha256(native_rgb).hexdigest(),
        "source_rgb_sha256": hashlib.sha256(source_rgb).hexdigest(),
    }
    event = runtime.event(
        root,
        directory,
        loaded=loaded,
        inputs=inputs,
        outputs=outputs,
        image_before=image_before,
    )
    record = {
        "schema_version": SCHEMA,
        **inputs,
        "runtime_before": before,
        "runtime_after": runtime.verify(loaded=loaded),
        "loaded_library": {
            "path": str(loaded),
            "sha256": library["sha256"],
            "bytes": library["bytes"],
        },
        "artifacts": artifacts,
        "original_inline_event": event,
    }
    if time.monotonic() >= deadline:
        raise TimeoutError("independent PDFium terminal artifact custody exhausted original deadline")
    return record, {
        "native": (native_png, native_rgb),
        "source": (source_png, source_rgb),
    }


def validate_pdfium_diagram_crop(
    raw: dict[str, Any],
    pdf: bytes,
    stencil: bytes,
    placement: dict[str, Any],
    crop: tuple[int, int, int, int],
    *,
    reader: SnapshotReader,
    run_id: str,
    runtime: PDFiumRuntimeAdmission,
) -> None:
    """Authenticate the actual enclosing original; producer paths stay labels."""
    fields = {
        "schema_version",
        "native_pdf_sha256",
        "stencil_pdf_sha256",
        "page",
        "crop_px",
        "dpi",
        "runtime_before",
        "runtime_after",
        "loaded_library",
        "artifacts",
        "original_inline_event",
    }
    inputs = {
        "native_pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "stencil_pdf_sha256": hashlib.sha256(stencil).hexdigest(),
        "page": placement["page"],
        "crop_px": list(crop),
        "dpi": 150,
    }
    if set(raw) != fields or raw["schema_version"] != SCHEMA or any(raw[key] != value for key, value in inputs.items()):
        raise ValueError("portable independent PDFium diagram exact input/crop differs")
    event = authenticate_original_pdfium_event(raw["original_inline_event"], reader, run_id=run_id, runtime=runtime)
    if (
        event["inputs"] != inputs
        or event["outputs"]["artifacts"] != raw["artifacts"]
        or event["provider_before"] != raw["runtime_before"]
        or event["provider_after"] != raw["runtime_after"]
    ):
        raise ValueError("portable independent PDFium observation differs from authenticated actual original event")
    library = raw["loaded_library"]
    if set(library) != {"path", "sha256", "bytes"} or library["path"] != event["loaded_library"]:
        raise ValueError("portable actual PDFium selected library label differs from original event")
    original_site = Path(event["provider_before"]["selection"]["site"])
    label = Path(library["path"]).relative_to(original_site).as_posix()
    held = event["provider_before"]["files"].get(label)
    if (
        held is None
        or any(library[key] != held[key] for key in ("sha256", "bytes"))
        or Path(label).suffix.lower() not in {".dylib", ".dll", ".so"}
    ):
        raise ValueError("portable original selected PDFium DLL differs from admitted wheel/RECORD")
    if set(raw["artifacts"]) != {"native", "source"}:
        raise ValueError("portable original PDFium source/native crop census differs")
    runtime.verify()

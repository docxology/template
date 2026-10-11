"""Independent source PNG/actual PDF occurrence, clip and paint geometry.

No renderer's status is an authority. Original source graph/paint/process/font
admission remains mandatory at the caller; this parser binds every actual Do
occurrence to decoded original pixels and retains finite physical constraints.
"""

from __future__ import annotations

import hashlib
import math
import re
import time
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
from infrastructure.reporting.native_format_pdf_oracles import PDF_POLICY
from infrastructure.reporting.native_mermaid_svg_geometry import SvgGeometry, multiply, point
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams

MAX_BYTES = 250 * 1024 * 1024
MAX_OPERATIONS = 2_000_000
MAX_HEIGHT_PT = 4.2 * 72
IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


@dataclass(frozen=True)
class DiagramSource:
    identity: str
    png_sha256: str
    svg_sha256: str
    width: int
    height: int
    rgb: bytes
    rgb_sha256: str
    svg_width: float
    svg_height: float
    label_font_px: float


def diagram_source(
    identity: str, png: bytes, svg: bytes, paint: dict[str, Any], *, budget: SourceImageDecodeBudget
) -> DiagramSource:
    """Decode admitted original source bytes, reserving before allocation."""
    from PIL import Image

    if not identity or len(png) + len(svg) > 64 * 1024 * 1024:
        raise ValueError("native diagram source exceeds finite original input bound")
    geometry = SvgGeometry(svg)
    with Image.open(BytesIO(png)) as image:
        if image.format != "PNG":
            raise ValueError("native diagram source requires the actual original PNG")
        budget.admit_header(image.width, image.height)
        image.load()
        if "A" in image.getbands() and image.getchannel("A").getextrema() != (255, 255):
            raise ValueError("original source diagram is not an opaque white-background paint")
        rgb = image.convert("RGB").tobytes()
        width, height = image.size
    digest = hashlib.sha256(rgb).hexdigest()
    if any(
        paint["paint"][key] != value for key, value in (("width", width), ("height", height), ("rgb_sha256", digest))
    ):
        raise ValueError("native diagram source pixels differ from independent original SVG paint")
    rows = paint["original_dom"]["rows"]
    if len(rows) != len(geometry.elements) - 1:
        raise ValueError("original source diagram DOM census differs from exact SVG")
    # CSS transforms are not included in the independently parsed XML affine
    # chain. Refuse that unimplemented case rather than overstate label size.
    if any(
        re.search(
            r"(?:^|[;{}])\s*transform\s*:",
            (element.text or "") if geometry.local(element) == "style" else element.get("style", ""),
            re.I,
        )
        for element in geometry.elements
    ):
        raise ValueError("original diagram CSS transform requires independent font geometry")
    fonts = []
    row_by_element = {id(element): row for element, row in zip(geometry.elements[1:], rows, strict=True)}
    for element, row in zip(geometry.elements[1:], rows, strict=True):
        if geometry.local(element) in {"style", "title", "desc"} or not row.get("text", "").strip():
            continue
        if row.get("visible") is not True:
            raise ValueError("original diagram contains an independently hidden source label")
        parent = element
        depth = 0
        while parent is not geometry.root:
            depth += 1
            if depth > 128:
                raise ValueError("original diagram label affine ancestry exceeds its finite depth")
            ancestor = row_by_element[id(parent)]
            if ancestor.get("visible") is not True or float(ancestor["style"]["opacity"]) <= 0:
                raise ValueError("original diagram source label has an independently hidden ancestor")
            parent = geometry.parents[parent]
        value = row["style"]["fontSize"]
        if not isinstance(value, str) or not value.endswith("px"):
            raise ValueError("original diagram label font requires finite CSS pixel geometry")
        size = float(value[:-2])
        if not math.isfinite(size) or size <= 0:
            raise ValueError("original diagram label font has invalid geometry")
        matrix = geometry.world(element)
        # Minimum singular value preserves a conservative font floor for a
        # nonuniform affine map; translation and rotation do not inflate it.
        a, b, c, d = matrix[:4]
        trace = a * a + b * b + c * c + d * d
        determinant = (a * d - b * c) ** 2
        minimum_scale = math.sqrt(max(0.0, (trace - math.sqrt(max(0.0, trace * trace - 4 * determinant))) / 2))
        if minimum_scale <= 0:
            raise ValueError("original diagram label has collapsed affine geometry")
        fonts.append(size * minimum_scale)
    if not fonts:
        raise ValueError("original diagram has no independently painted label font")
    if float(geometry.root.get("opacity", "1")) <= 0:
        raise ValueError("original diagram root explicitly hides its source labels")
    root_box = paint["original_dom"]["root"]
    paint_scale = min(float(root_box["width"]) / geometry.viewbox[2], float(root_box["height"]) / geometry.viewbox[3])
    if not math.isfinite(paint_scale) or paint_scale <= 0:
        raise ValueError("original diagram source has invalid actual SVG-to-PNG font geometry")
    return DiagramSource(
        identity,
        hashlib.sha256(png).hexdigest(),
        hashlib.sha256(svg).hexdigest(),
        width,
        height,
        rgb,
        digest,
        geometry.viewbox[2],
        geometry.viewbox[3],
        min(fonts) * paint_scale,
    )


def _finite(values: Any, count: int) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) != count or any(not math.isfinite(value) or abs(value) > 1_000_000 for value in result):
        raise ValueError("native diagram geometry exceeds finite coordinate bound")
    return result


def _box(matrix: tuple[float, ...], box: tuple[float, ...]) -> tuple[float, ...]:
    x0, y0, x1, y1 = box
    corners = [point(matrix, value) for value in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return (
        min(p[0] for p in corners),
        min(p[1] for p in corners),
        max(p[0] for p in corners),
        max(p[1] for p in corners),
    )


def _intersect(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
    return max(left[0], right[0]), max(left[1], right[1]), min(left[2], right[2]), min(left[3], right[3])


def inspect_diagram_pdf_geometry(
    pdf: bytes, sources: tuple[DiagramSource, ...], *, budget: SourceImageDecodeBudget, deadline: float
) -> dict[str, Any]:
    """Account actual image paints, including nested Form state and clipping.

    Rectangular clips are interpreted exactly. Unknown clipping, transforms,
    transfer/blend/mask state are retained blockers; source-only raster ink is
    an additional independent proof, never a substitute for these constraints.
    """
    from pypdf import PdfReader
    from pypdf.generic import ContentStream

    preflight_pdf_streams(pdf, deadline=deadline, max_bytes=MAX_BYTES, max_objects=MAX_OPERATIONS)
    reader = PdfReader(BytesIO(pdf), strict=True)
    if not 1 <= len(reader.pages) <= 500 or len(sources) > 100:
        raise ValueError("native diagram page/source occurrence bound exceeded")
    by_pixels: dict[str, list[DiagramSource]] = {}
    sizes = {(source.width, source.height) for source in sources}
    for source in sources:
        by_pixels.setdefault(source.rgb_sha256, []).append(source)
    expected = Counter(source.rgb_sha256 for source in sources)
    placements: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    operations = 0
    decoded: dict[tuple[int, tuple[str, ...]], tuple[str, bool]] = {}

    def resolve(value: Any) -> Any:
        return value.get_object() if hasattr(value, "get_object") else value

    for page_number, page in enumerate(reader.pages, 1):
        media = _finite(page.mediabox, 4)
        crop = _finite(page.cropbox, 4)
        if media[0] != 0 or media[1] != 0 or page.get("/Rotate", 0) != 0 or page.get("/UserUnit", 1) != 1:
            blockers.append(f"native diagram page {page_number} has unsupported rotated/origin/unit geometry")
            continue
        page_clip = _intersect(media, crop)
        if min(page_clip[2] - page_clip[0], page_clip[3] - page_clip[1]) <= 0:
            raise ValueError("native diagram page has collapsed media/crop geometry")

        def walk(
            stream: Any, resources: Any, inherited: dict[str, Any], path: tuple[str, ...], active: set[int]
        ) -> None:
            nonlocal operations
            if len(path) > 32:
                raise ValueError("native diagram Form recursion exceeds finite depth")
            state = dict(inherited)
            stack: list[dict[str, Any]] = []
            rectangles: list[tuple[float, ...]] = []
            unknown_path = False
            pending_clip = False
            content = ContentStream(stream, reader)
            for stream_index, (operands, operator) in enumerate(content.operations):
                operations += 1
                if operations > MAX_OPERATIONS or time.monotonic() >= deadline:
                    raise TimeoutError("native diagram operation parser exhausted original bound/deadline")
                if operator == b"q":
                    if len(stack) >= 128:
                        raise ValueError("native diagram graphics stack exceeds finite depth")
                    stack.append(dict(state))
                elif operator == b"Q":
                    if not stack:
                        raise ValueError("native diagram graphics stack underflow")
                    state = stack.pop()
                elif operator == b"cm":
                    state["matrix"] = multiply(state["matrix"], _finite(operands, 6))
                elif operator == b"re":
                    x, y, width, height = _finite(operands, 4)
                    matrix = state["matrix"]
                    if matrix[1] != 0 or matrix[2] != 0:
                        unknown_path = True
                    rectangles.append(_box(matrix, (x, y, x + width, y + height)))
                elif operator in {b"m", b"l", b"c", b"v", b"y", b"h"}:
                    unknown_path = True
                elif operator in {b"W", b"W*"}:
                    pending_clip = True
                elif operator in {b"n", b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*"}:
                    if pending_clip:
                        if unknown_path or len(rectangles) != 1:
                            state["unknown_clip"] = True
                        else:
                            state["clip"] = _intersect(state["clip"], rectangles[0])
                    rectangles, unknown_path, pending_clip = [], False, False
                elif operator == b"Tr" and int(operands[0]) >= 4:
                    state["unknown_clip"] = True
                elif operator == b"gs":
                    graphic = resolve(resolve(resources.get("/ExtGState", {})).get(operands[0], {}))
                    state["alpha"] = float(graphic.get("/ca", state["alpha"]))
                    if "/BM" in graphic and graphic["/BM"] != "/Normal":
                        state["unsupported_paint"] = True
                    if (
                        graphic.get("/SMask", "/None") != "/None"
                        or any(key in graphic for key in ("/TR", "/TR2", "/BG", "/BG2", "/UCR", "/UCR2", "/HT"))
                        or graphic.get("/op", False)
                        or graphic.get("/OP", False)
                    ):
                        state["unsupported_paint"] = True
                elif operator == b"Do":
                    name = str(operands[0])
                    resource = resolve(resolve(resources.get("/XObject", {})).get(operands[0]))
                    if resource is None:
                        raise ValueError("native diagram image/Form has no actual resource")
                    current_path = (*path, name)
                    if resource.get("/Subtype") == "/Form":
                        identity = id(resource)
                        if identity in active:
                            raise ValueError("native diagram Form graph contains a cycle")
                        form_state = dict(state)
                        form_state["matrix"] = multiply(state["matrix"], _finite(resource.get("/Matrix", IDENTITY), 6))
                        bounds = _finite(resource.get("/BBox", ()), 4)
                        form_state["clip"] = _intersect(state["clip"], _box(form_state["matrix"], bounds))
                        if form_state["matrix"][1] != 0 or form_state["matrix"][2] != 0:
                            form_state["unknown_clip"] = True
                        walk(
                            resource,
                            resolve(resource.get("/Resources", resources)),
                            form_state,
                            current_path,
                            active | {identity},
                        )
                    elif resource.get("/Subtype") == "/Image":
                        width, height = resource.get("/Width"), resource.get("/Height")
                        if (
                            not isinstance(width, int)
                            or not isinstance(height, int)
                            or isinstance(width, bool)
                            or isinstance(height, bool)
                        ):
                            raise ValueError("native image has no finite integer dimensions")
                        width, height = int(width), int(height)
                        if (width, height) not in sizes:
                            continue
                        key = (page_number, current_path)
                        if key not in decoded:
                            budget.admit_header(width, height)
                            for mask_name in ("/SMask", "/Mask"):
                                mask = resolve(resource.get(mask_name))
                                if mask is not None and hasattr(mask, "get"):
                                    mw, mh = mask.get("/Width"), mask.get("/Height")
                                    if (
                                        not isinstance(mw, int)
                                        or not isinstance(mh, int)
                                        or isinstance(mw, bool)
                                        or isinstance(mh, bool)
                                    ):
                                        raise ValueError("native diagram alpha mask has invalid dimensions")
                                    if mask.get("/SMask") is not None or mask.get("/Mask") is not None:
                                        raise ValueError("native diagram nested mask requires bounded decoding")
                                    budget.admit_header(int(mw), int(mh))
                            image = page.images[list(current_path)].image
                            if image is None:
                                raise ValueError("native diagram resource has no decoded pixels")
                            opaque = "A" not in image.getbands() or image.getchannel("A").getextrema() == (255, 255)
                            decoded[key] = hashlib.sha256(image.convert("RGB").tobytes()).hexdigest(), opaque
                        digest, opaque = decoded[key]
                        if digest not in by_pixels:
                            continue
                        matrix = tuple(state["matrix"])
                        box = _box(matrix, (0.0, 0.0, 1.0, 1.0))
                        clip = state["clip"]
                        row = {
                            "page": page_number,
                            "resource_path": list(current_path),
                            "rgb_sha256": digest,
                            "stream_operation_index": stream_index,
                            "matrix": list(matrix),
                            "box_pt": list(box),
                            "media_box_pt": list(media),
                            "crop_box_pt": list(crop),
                            "clip_box_pt": list(clip),
                            "alpha": state["alpha"],
                            "interpolate": bool(resource.get("/Interpolate", False)),
                            "source_identities": [source.identity for source in by_pixels[digest]],
                        }
                        ordinal = len(placements)
                        if state["unknown_clip"] or state["unsupported_paint"] or not opaque:
                            blockers.append(
                                f"native diagram occurrence {ordinal} has uninterpreted clip/blend/mask/transfer state"
                            )
                        if not math.isfinite(state["alpha"]) or state["alpha"] != 1:
                            findings.append(
                                {"code": "office.diagram.hidden", "occurrence": ordinal, "alpha": state["alpha"]}
                            )
                        if matrix[1] != 0 or matrix[2] != 0 or min(matrix[0], matrix[3]) <= 0:
                            findings.append({"code": "office.diagram.geometry", "occurrence": ordinal})
                        if box[0] < clip[0] or box[1] < clip[1] or box[2] > clip[2] or box[3] > clip[3]:
                            findings.append(
                                {
                                    "code": "office.diagram.clipped",
                                    "occurrence": ordinal,
                                    "box": list(box),
                                    "clip": list(clip),
                                }
                            )
                        physical_width, physical_height = box[2] - box[0], box[3] - box[1]
                        if matrix[1] == 0 and matrix[2] == 0 and min(matrix[0], matrix[3]) > 0:
                            # The actual unit-square image scale is the physical
                            # extent. Avoid cancellation from translated box
                            # corners at the exact declared height boundary.
                            physical_width, physical_height = matrix[0], matrix[3]
                        if physical_height > MAX_HEIGHT_PT:
                            findings.append(
                                {
                                    "code": "office.diagram.height",
                                    "occurrence": ordinal,
                                    "height_pt": physical_height,
                                    "maximum_pt": MAX_HEIGHT_PT,
                                }
                            )
                        if not math.isclose(
                            physical_width * height, physical_height * width, rel_tol=1e-6, abs_tol=1e-6
                        ):
                            findings.append({"code": "office.diagram.aspect", "occurrence": ordinal})
                        native_font = min(
                            source.label_font_px * min(physical_width / source.width, physical_height / source.height)
                            for source in by_pixels[digest]
                        )
                        row["minimum_label_font_pt"] = native_font
                        if native_font < PDF_POLICY["min_supported_font_pt"]:
                            findings.append(
                                {
                                    "code": "office.diagram.font_floor",
                                    "occurrence": ordinal,
                                    "font_pt": native_font,
                                    "floor_pt": PDF_POLICY["min_supported_font_pt"],
                                }
                            )
                        placements.append(row)
            if stack or pending_clip:
                raise ValueError("native diagram stream leaves an incomplete graphics/clip stack")

        walk(
            page.get_contents(),
            resolve(page.get("/Resources", {})),
            {
                "matrix": IDENTITY,
                "clip": page_clip,
                "unknown_clip": False,
                "unsupported_paint": False,
                "alpha": 1.0,
            },
            (),
            set(),
        )
    observed = Counter(row["rgb_sha256"] for row in placements)
    if expected != observed:
        findings.append(
            {"code": "office.diagram.occurrence_count", "expected": dict(expected), "observed": dict(observed)}
        )
    return {
        "schema_version": "template-native-office-diagram-geometry-v1",
        "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "status": "failed" if findings else "blocked" if blockers else "pass",
        "findings": findings,
        "blockers": blockers,
        "placements": placements,
        "source_counts": dict(expected),
        "native_counts": dict(observed),
        "height_limit_pt": MAX_HEIGHT_PT,
        "font_floor_pt": PDF_POLICY["min_supported_font_pt"],
    }

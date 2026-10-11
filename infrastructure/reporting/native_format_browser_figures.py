"""Independent decoded source image and rendered image-region observations."""

from __future__ import annotations

import base64
import hashlib
import math
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any, cast
from urllib.parse import unquote, urlsplit

from infrastructure.reporting.native_format_content_contracts import NativeContentContract, SemanticContentContract
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def _solid_background(layers: Any) -> tuple[int, int, int, int] | None:
    """Independently composite captured CSS solid colors over Chromium white."""
    from PIL import Image

    if not isinstance(layers, list) or not layers:
        return None
    background = Image.new("RGBA", (1, 1), "white")
    for layer in reversed(layers):
        if layer.get("image") != "none" or layer.get("opacity") != "1":
            return None
        color = layer.get("color", "")
        match = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([0-9.]+))?\s*\)", color)
        if not match:
            return None
        rgb = [int(match[i]) for i in (1, 2, 3)]
        alpha = float(match[4]) if match[4] is not None else 1.0
        if any(v > 255 for v in rgb) or not math.isfinite(alpha) or not 0 <= alpha <= 1:
            raise ValueError("browser supplied invalid actual CSS background color")
        background = Image.alpha_composite(background, Image.new("RGBA", (1, 1), (*rgb, round(alpha * 255))))
    return cast(tuple[int, int, int, int], background.getpixel((0, 0)))


def _premultiplied(image: Any) -> bytes:
    """Compare every observable alpha pixel despite canvas unpremultiply rounding."""
    output = bytearray()
    for red, green, blue, alpha in image.getdata():
        output.extend((round(red * alpha / 255), round(green * alpha / 255), round(blue * alpha / 255), alpha))
    return bytes(output)


def inspect_browser_figures(
    dom: dict[str, Any],
    pixels: bytes,
    contract: NativeContentContract,
    artifact: ArtifactSnapshot | None,
    reader: SnapshotReader,
) -> dict[str, Any]:
    """Compare all source figures' complete decoded pixels and viewport pixels."""
    from PIL import Image, ImageChops, ImageOps, ImageStat

    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    observations = []
    if not isinstance(contract, SemanticContentContract) or not contract.image_sources:
        return {"figures": [], "findings": [], "blockers": []}
    if artifact is None:
        raise ValueError("source figure observations require original artifact identity")
    with Image.open(BytesIO(pixels)) as page:
        page.load()
        used_images: set[int] = set()
        for identity, target, alt in contract.image_sources:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
                blockers.append(f"{identity}: independent external figure source bytes unavailable")
                continue
            path = Path(os.path.normpath(str(artifact.path.parent / unquote(parsed.path))))
            source = reader.read(path.relative_to(reader.root).as_posix())
            if source.path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                blockers.append(f"{identity}: independent decoded vector/animated figure semantics unsupported")
                continue
            image_index = next(
                (
                    index
                    for index, item in enumerate(dom["images"])
                    if index not in used_images and item["src"] == target
                ),
                None,
            )
            if image_index is None:
                findings.append({"code": "html.figure.source", "source_id": identity})
                continue
            used_images.add(image_index)
            image = dom["images"][image_index]
            if type(image.get("alt_present")) is not bool:
                raise ValueError("actual native figure omitted image alt presence")
            if alt and (not image["alt_present"] or image.get("alt") != alt):
                findings.append({"code": "html.figure.alt", "source_id": identity, "image_index": image_index})
            with Image.open(BytesIO(source.content)) as source_image:
                if getattr(source_image, "n_frames", 1) != 1:
                    blockers.append(f"{identity}: animated source image semantics unsupported")
                    continue
                if source_image.width * source_image.height > 4_000_000:
                    blockers.append(f"{identity}: complete source image decode exceeds the finite pixel budget")
                    continue
                expected = ImageOps.exif_transpose(source_image).convert("RGBA")
                expected.load()
            encoded = image.get("decoded_png")
            if (
                not isinstance(encoded, str)
                or not encoded.startswith("data:image/png;base64,")
                or len(encoded) > 32 * 1024 * 1024
            ):
                findings.append({"code": "html.figure.decode", "source_id": identity})
                continue
            with Image.open(BytesIO(base64.b64decode(encoded.partition(",")[2], validate=True))) as actual_image:
                actual = actual_image.convert("RGBA")
                actual.load()
            expected_hash = hashlib.sha256(expected.tobytes()).hexdigest()
            actual_hash = hashlib.sha256(actual.tobytes()).hexdigest()
            opaque = expected.getchannel("A").getextrema() == (255, 255)
            decoded_equal = actual.size == expected.size and actual_hash == expected_hash
            alpha_error = None
            if not opaque and actual.size == expected.size:
                expected_pre, actual_pre = _premultiplied(expected), _premultiplied(actual)
                alpha_error = max(abs(a - b) for a, b in zip(expected_pre, actual_pre, strict=True))
                decoded_equal = (
                    alpha_error <= 1 and expected.getchannel("A").tobytes() == actual.getchannel("A").tobytes()
                )
            if not decoded_equal:
                findings.append({"code": "html.figure.pixels", "source_id": identity})
            box = image.get("box")
            if (
                not isinstance(box, list)
                or len(box) != 4
                or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in box)
            ):
                raise ValueError("native image omitted finite actual layout geometry")
            x, y, width, height = box
            if min(width, height) <= 0 or image.get("hidden") or image.get("clipped"):
                findings.append({"code": "html.figure.visibility", "source_id": identity})
            if min(width, height) <= 0 or x < 0 or y < 0 or x + width > page.width + 2 or y + height > page.height + 2:
                findings.append({"code": "html.figure.crop", "source_id": identity})
                continue
            if abs(width / height - expected.width / expected.height) > 0.02:
                findings.append({"code": "html.figure.distortion", "source_id": identity})
            roi = page.convert("RGB").crop((math.floor(x), math.floor(y), math.ceil(x + width), math.ceil(y + height)))
            presentation = image.get("presentation", {})
            if any(
                presentation.get(key) != value
                for key, value in (
                    ("filter", "none"),
                    ("transform", "none"),
                    ("mix_blend_mode", "normal"),
                    ("opacity", "1"),
                )
            ) or presentation.get("object_fit") not in {"fill", "contain"}:
                blockers.append(f"{identity}: independent filtered/transformed image projection unsupported")
                continue
            background = _solid_background(image.get("background_layers")) if not opaque else None
            if not opaque and background is None:
                blockers.append(f"{identity}: independent non-solid alpha background projection unsupported")
                continue
            projected_rgba = expected.resize(roi.size, Image.Resampling.LANCZOS)
            projected = (
                Image.alpha_composite(Image.new("RGBA", roi.size, background), projected_rgba).convert("RGB")
                if background is not None
                else projected_rgba.convert("RGB")
            )
            error = sum(ImageStat.Stat(ImageChops.difference(projected, roi)).mean) / 3
            if error > 24:
                findings.append({"code": "html.figure.visual", "source_id": identity})
            from infrastructure.reporting.native_format_html_local_paint import inspect_unit_image_paint

            local = inspect_unit_image_paint(page, expected, box, background, identity)
            findings.extend(local["findings"])
            blockers.extend(local["blockers"])
            observations.append(
                {
                    "source_id": identity,
                    "source": {"path": source.relative, "sha256": source.sha256},
                    "decoded_source_sha256": expected_hash,
                    "decoded_native_sha256": actual_hash,
                    "decoded_alpha_premultiplied_max_error": alpha_error,
                    "background_rgba": list(background) if background is not None else None,
                    "image_index": image_index,
                    "box_px": box,
                    "rendered_region_mean_error": error,
                    "localized": local,
                }
            )
    return {"figures": observations, "findings": findings, "blockers": blockers}


def inspect_browser_math_pixels(dom: dict[str, Any], pixels: bytes) -> dict[str, Any]:
    """Require visible native math ink, readable metrics and uncropped boxes."""
    from PIL import Image

    regions = []
    findings = []
    with Image.open(BytesIO(pixels)) as page:
        gray = page.convert("L")
        for index, equation in enumerate(dom["math"]):
            box = equation["box"]
            if len(box) != 4 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in box):
                raise ValueError("native equation omitted finite actual geometry")
            x, y, width, height = box
            if (
                min(width, height) <= 0
                or x < -2
                or x + width > dom["width"] + 2
                or y < 0
                or y + height > page.height + 2
            ):
                findings.append({"code": "html.math.crop", "math_index": index})
                continue
            if equation["font_px"] < 12:
                findings.append({"code": "html.math.font", "math_index": index})
            roi = (
                max(0, math.floor(x)),
                max(0, math.floor(y)),
                min(page.width, math.ceil(x + width)),
                min(page.height, math.ceil(y + height)),
            )
            low, high = cast(tuple[int, int], gray.crop(roi).getextrema())
            regions.append({"math_index": index, "box_px": list(roi), "luminance_range": high - low})
            if high - low < 32:
                findings.append({"code": "html.math.invisible", "math_index": index})
    return {"regions": regions, "findings": findings}

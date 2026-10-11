"""Source-only exact nearest-neighbor kernel at integral pixelated placement."""

from __future__ import annotations

import hashlib
import math
from io import BytesIO
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard
from infrastructure.reporting.native_format_html_source_metadata import remaining_seconds

KERNEL_SCHEMA = "template-native-html-source-integer-nearest-v1"
RESAMPLING_SCRIPT = r"""
 for(const [i,e] of [...document.images].entries())
  data.images[i].presentation.image_rendering=getComputedStyle(e).imageRendering;
"""


def inspect_integer_resampling(
    source_bytes: bytes,
    source_id: str,
    native: dict[str, Any],
    screenshot: bytes,
    background: tuple[int, int, int, int],
    *,
    deadline: float,
) -> dict[str, Any]:
    remaining_seconds(deadline)
    with native_deadline_guard(deadline):
        result = _inspect_integer_resampling(source_bytes, source_id, native, screenshot, background, deadline=deadline)
    remaining_seconds(deadline)
    return result


def _inspect_integer_resampling(
    source_bytes: bytes,
    source_id: str,
    native: dict[str, Any],
    screenshot: bytes,
    background: tuple[int, int, int, int],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Predict every pixel from original image bytes; candidate pixels are output.

    Only CSS pixelated integer enlargement and integral origins are defined by
    this kernel. Auto, smooth, crisp-edges, downsampling, fractional placement,
    transforms and unknown color management retain their unsupported scope.
    Decoder/runtime/source custody must be admitted by the enclosing observer.
    """
    from PIL import Image, ImageChops

    remaining_seconds(deadline)
    if len(source_bytes) > 32 * 1024 * 1024 or len(screenshot) > 64 * 1024 * 1024:
        raise ValueError("source figure/reference exceeds the existing finite byte bounds")
    if (
        len(background) != 4
        or any(type(channel) is not int or not 0 <= channel <= 255 for channel in background)
        or background[3] != 255
    ):
        raise ValueError("source integer kernel requires an exact opaque solid composited background")
    box = native.get("box")
    if (
        not isinstance(box, list)
        or len(box) != 4
        or any(type(v) not in {int, float} or not math.isfinite(v) for v in box)
    ):
        raise ValueError("source figure omitted actual finite resampling geometry")
    x, y, width, height = box
    findings: list[dict[str, Any]] = []
    blockers = []
    style = native.get("presentation")
    if not isinstance(style, dict):
        raise ValueError("native figure omitted computed resampling presentation")
    if style.get("image_rendering") != "pixelated" or any(
        style.get(key) != value
        for key, value in (
            ("filter", "none"),
            ("transform", "none"),
            ("mix_blend_mode", "normal"),
            ("object_fit", "fill"),
            ("opacity", "1"),
        )
    ):
        blockers.append(
            f"{source_id}: unknown native image kernel/presentation requires an independent source-only renderer"
        )
    if any(v != round(v) for v in box):
        blockers.append(f"{source_id}: fractional image origins/sizes require a separate independent sampling kernel")
    with Image.open(BytesIO(source_bytes)) as source:
        if getattr(source, "n_frames", 1) != 1 or source.width * source.height > 4_000_000 or min(source.size) <= 0:
            raise ValueError("source integer kernel requires one bounded original frame")
        if source.info.get("icc_profile") or source.info.get("gamma") or source.getexif().get(274, 1) != 1:
            blockers.append(f"{source_id}: source color profiles require an independently calibrated color pipeline")
        rgba = source.convert("RGBA")
        sx, sy = width / source.width, height / source.height
        if any(v != int(v) or not 1 <= v <= 16 for v in (sx, sy)) or width * height > 4_000_000:
            blockers.append(f"{source_id}: only bounded integer enlargement is supported by the source nearest kernel")
        base: dict[str, Any] = {
            "schema_version": KERNEL_SCHEMA,
            "source_id": source_id,
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "box_px": box,
            "scale": [sx, sy],
            "findings": findings,
            "blockers": blockers,
        }
        if blockers:
            result = {**base, "pixels": None, "status": "blocked"}
            remaining_seconds(deadline)
            return {**result, "digest": canonical_digest(result)}
        # The reference samples only the original source. No drawImage, canvas,
        # decoded candidate or observed screenshot contributes expected pixels.
        source_pixels = rgba.tobytes()
        expected_bytes = bytearray(int(width * height) * 4)
        for yy in range(int(height)):
            remaining_seconds(deadline)
            for xx in range(int(width)):
                source_offset = ((yy // int(sy)) * source.width + xx // int(sx)) * 4
                output_offset = (yy * int(width) + xx) * 4
                expected_bytes[output_offset : output_offset + 4] = source_pixels[source_offset : source_offset + 4]
        output = Image.frombytes("RGBA", (int(width), int(height)), bytes(expected_bytes))
        expected = Image.alpha_composite(Image.new("RGBA", output.size, background), output).convert("RGB")
    with Image.open(BytesIO(screenshot)) as page:
        if page.width > 1280 or page.height > 30000:
            raise ValueError("actual native page exceeds the existing finite viewport bounds")
        page.load()
        roi = (int(x), int(y), int(x + width), int(y + height))
        if x < 0 or y < 0 or roi[2] > page.width or roi[3] > page.height:
            findings.append({"code": "html.figure.resampling-crop", "source_id": source_id})
            result = {**base, "pixels": None, "status": "fail"}
            remaining_seconds(deadline)
            return {**result, "digest": canonical_digest(result)}
        actual = page.convert("RGB").crop(roi)
        difference = ImageChops.difference(expected, actual)
        errors = difference.tobytes()
        changed = sum(
            any(channel > 2 for channel in errors[offset : offset + 3]) for offset in range(0, len(errors), 3)
        )
        if changed:
            findings.append({"code": "html.figure.resampled-pixel", "source_id": source_id})
        pixels = {
            "expected_rgb_sha256": hashlib.sha256(expected.tobytes()).hexdigest(),
            "actual_rgb_sha256": hashlib.sha256(actual.tobytes()).hexdigest(),
            "pixels_over_error_2": changed,
            "maximum_channel_error": max(errors, default=0),
        }
        result = {**base, "pixels": pixels, "status": "fail" if findings else "pass"}
        remaining_seconds(deadline)
        return {**result, "digest": canonical_digest(result)}


def replay_integer_resampling(
    source_bytes: bytes,
    source_id: str,
    native: dict[str, Any],
    screenshot: bytes,
    background: tuple[int, int, int, int],
    raw: dict[str, Any],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Recompute the original source kernel independently in the current reader."""
    result = inspect_integer_resampling(source_bytes, source_id, native, screenshot, background, deadline=deadline)
    if result != raw:
        raise ValueError("independent source-only figure resampling replay differs")
    remaining_seconds(deadline)
    return result

"""Independently decode original raster alpha and literal PDF soft-mask pixels.

This leaf returns pixel evidence, never source/native acceptance. Transparent
paint requires an explicit independently admitted source background; caption,
occurrence, page geometry and whole-page reference admission remain separate.
"""

from __future__ import annotations

import hashlib
import math
import time
from io import BytesIO
from typing import Any

from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget


class UnsupportedAlphaPaint(ValueError):
    """Keep unsupported source/native color and compositing behavior blocked."""


def _deadline(deadline: float) -> None:
    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("source alpha paint exceeded its finite original deadline")


def composite_source_rgba(image: Any, background_rgb: tuple[int, int, int] | None) -> Any:
    """Interpret source-over alpha using a declared solid source background."""
    from PIL import Image

    if image.mode != "RGBA":
        raise ValueError("source alpha compositor requires independently decoded RGBA pixels")
    if image.getchannel("A").getextrema() == (255, 255):
        return image.convert("RGB")
    if (
        not isinstance(background_rgb, tuple)
        or len(background_rgb) != 3
        or any(type(value) is not int or not 0 <= value <= 255 for value in background_rgb)
    ):
        raise UnsupportedAlphaPaint("transparent source paint requires independently admitted solid background")
    background = Image.new("RGBA", image.size, (*background_rgb, 255))
    return Image.alpha_composite(background, image).convert("RGB")


def decode_original_source_rgba(
    content: bytes,
    budget: SourceImageDecodeBudget,
    *,
    deadline: float,
    background_rgb: tuple[int, int, int] | None = None,
) -> dict[str, Any]:
    """Reserve actual original headers before allocating source pixel buffers."""
    from PIL import Image, ImageOps

    _deadline(deadline)
    if len(content) > 64 * 1024 * 1024:
        raise ValueError("source alpha image exceeds its original finite byte bound")
    with Image.open(BytesIO(content)) as image:
        budget.admit_header(image.width, image.height)
        if (
            image.format not in {"PNG", "JPEG", "WEBP"}
            or getattr(image, "n_frames", 1) != 1
            or image.mode not in {"1", "L", "LA", "P", "RGB", "RGBA"}
            or image.info.get("icc_profile")
        ):
            raise UnsupportedAlphaPaint("source color/vector/animated behavior requires independent decoder")
        rgba = ImageOps.exif_transpose(image).convert("RGBA")
        rgb = composite_source_rgba(rgba, background_rgb)
    _deadline(deadline)
    return {
        "source_sha256": hashlib.sha256(content).hexdigest(),
        "rgba": rgba,
        "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
        "paint_rgb": rgb,
        "paint_rgb_sha256": hashlib.sha256(rgb.tobytes()).hexdigest(),
        "alpha_extrema": list(rgba.getchannel("A").getextrema()),
        "background_rgb": list(background_rgb) if background_rgb is not None else None,
    }


def _stream_pixels(stream: Any, mode: str, width: int, height: int) -> Any:
    from pdfminer.pdftypes import resolve1
    from pdfminer.psparser import PSLiteral
    from PIL import Image

    declared = resolve1(stream.attrs.get("Filter"))
    filters = [] if declared is None else declared if isinstance(declared, (list, tuple)) else [declared]
    names = []
    for item in filters:
        item = resolve1(item)
        if not isinstance(item, PSLiteral) or item.name not in {
            "FlateDecode",
            "Fl",
            "LZWDecode",
            "LZW",
            "ASCII85Decode",
            "A85",
            "ASCIIHexDecode",
            "AHx",
            "RunLengthDecode",
            "RL",
            "DCTDecode",
            "DCT",
        }:
            raise UnsupportedAlphaPaint("native image filter requires independent decoder")
        names.append(item.name)
    jpeg = any(name in {"DCTDecode", "DCT"} for name in names)
    if jpeg and (names[-1] not in {"DCTDecode", "DCT"} or sum(name in {"DCTDecode", "DCT"} for name in names) != 1):
        raise UnsupportedAlphaPaint("native JPEG filter chain requires independent decoder")
    raw = stream.get_data()
    channels = 3 if mode == "RGB" else 1
    if jpeg:
        with Image.open(BytesIO(raw)) as image:
            if image.size != (width, height) or image.mode not in {"RGB", "L"} or image.info.get("icc_profile"):
                raise UnsupportedAlphaPaint("native JPEG source color/dimensions require independent decoder")
            return image.convert(mode)
    if len(raw) != width * height * channels:
        raise UnsupportedAlphaPaint("native image/mask stride requires independent decoder")
    return Image.frombytes(mode, (width, height), raw)


def _identity_decode(declared: Any, channels: int) -> list[int | float] | None:
    """Admit only the literal known 8-bit DeviceRGB/Gray identity intervals."""
    from pdfminer.pdftypes import resolve1

    value = resolve1(declared)
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or len(value) != channels * 2:
        raise UnsupportedAlphaPaint("native nonidentity Decode requires independent interpretation")
    expected = (0, 1) * channels
    result = []
    for item, target in zip(value, expected, strict=True):
        item = resolve1(item)
        if type(item) not in {int, float} or not math.isfinite(item) or item != target:
            raise UnsupportedAlphaPaint("native nonidentity Decode requires independent interpretation")
        result.append(item)
    return result


def decode_native_rgba(
    stream: Any,
    *,
    deadline: float,
    remaining_decoded_pixels: int,
    background_rgb: tuple[int, int, int] | None = None,
) -> dict[str, Any]:
    """Decode real RGB/gray and literal 8-bit gray SMask with aggregate bounds.

    The caller decrements remaining_decoded_pixels by consumed_decoded_pixels
    for every retained occurrence, including separately allocated soft masks.
    Literal identity Decode is retained; nonidentity Decode/Matte, color-key
    masks, custom spaces and nested masks stay blocked.
    """
    from pdfminer.pdftypes import PDFStream, resolve1
    from pdfminer.psparser import PSLiteral

    _deadline(deadline)
    if type(remaining_decoded_pixels) is not int or not 0 <= remaining_decoded_pixels <= 120_000_000:
        raise ValueError("native alpha aggregate pixel allowance exceeds its existing bound")
    if not isinstance(stream, PDFStream):
        raise ValueError("native alpha decoder requires an actual PDF image stream")
    attrs = resolve1(stream.attrs)
    width, height = attrs.get("Width"), attrs.get("Height")
    if type(width) is not int or type(height) is not int or min(width, height) <= 0 or width * height > 60_000_000:
        raise ValueError("native alpha image dimensions exceed their finite bound")
    mask = resolve1(attrs.get("SMask"))
    consumed = width * height * (2 if mask is not None else 1)
    if consumed > remaining_decoded_pixels:
        raise ValueError("native image plus soft mask exceeds aggregate decoded-pixel allowance")
    colorspace = resolve1(attrs.get("ColorSpace"))
    if (
        attrs.get("Mask") is not None
        or attrs.get("Matte") is not None
        or attrs.get("ImageMask")
        or attrs.get("BitsPerComponent") != 8
        or not isinstance(colorspace, PSLiteral)
        or colorspace.name not in {"DeviceRGB", "DeviceGray"}
    ):
        raise UnsupportedAlphaPaint("native alpha color/mask/Decode/Matte behavior requires independent decoder")
    image_decode = _identity_decode(attrs.get("Decode"), 3 if colorspace.name == "DeviceRGB" else 1)
    mask_decode = None
    # Complete image and mask headers are admitted before either decompression.
    if mask is not None:
        if not isinstance(mask, PDFStream):
            raise UnsupportedAlphaPaint("native soft mask is not a literal image stream")
        mask_attrs = resolve1(mask.attrs)
        mask_space = resolve1(mask_attrs.get("ColorSpace"))
        if (
            mask_attrs.get("Width") != width
            or mask_attrs.get("Height") != height
            or mask_attrs.get("BitsPerComponent") != 8
            or not isinstance(mask_space, PSLiteral)
            or mask_space.name != "DeviceGray"
            or any(mask_attrs.get(key) is not None for key in ("SMask", "Mask", "Matte"))
            or mask_attrs.get("ImageMask")
        ):
            raise UnsupportedAlphaPaint("native soft-mask dimensions/color/transform require independent decoder")
        mask_decode = _identity_decode(mask_attrs.get("Decode"), 1)
    rgba = _stream_pixels(stream, "RGB" if colorspace.name == "DeviceRGB" else "L", width, height).convert("RGBA")
    if mask is not None:
        rgba.putalpha(_stream_pixels(mask, "L", width, height))
    rgb = composite_source_rgba(rgba, background_rgb)
    _deadline(deadline)
    return {
        "rgba": rgba,
        "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
        "paint_rgb": rgb,
        "paint_rgb_sha256": hashlib.sha256(rgb.tobytes()).hexdigest(),
        "consumed_decoded_pixels": consumed,
        "alpha_extrema": list(rgba.getchannel("A").getextrema()),
        "background_rgb": list(background_rgb) if background_rgb is not None else None,
        "image_decode": image_decode,
        "soft_mask_decode": mask_decode,
    }

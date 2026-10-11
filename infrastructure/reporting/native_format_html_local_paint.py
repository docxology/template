"""Localized native character, math-leaf and complete unit-image paint checks.

These checks narrow the scientific-mark visibility obligation. They do not
claim to reconstruct every font outline or every scaled image sample.
"""

from __future__ import annotations

import hashlib
import math
import unicodedata
from io import BytesIO
from collections.abc import Iterable
from typing import Any, cast

LOCAL_PAINT_SCRIPT = r"""
 let characterCount=0;
 for(const [i,n] of textNodes.entries()){
  const chars=[];let offset=0;
  if(!n.parentElement.closest('.math'))for(const character of n.textContent){
   if(++characterCount>200000)throw new Error('source character paint budget exceeded');
   const r=document.createRange();r.setStart(n,offset);r.setEnd(n,offset+character.length);
   chars.push({character,offset_utf16:offset,boxes:[...r.getClientRects()].map(b=>[b.x,b.y,b.width,b.height])});
   offset+=character.length;
  }
  rows[i].characters=chars;rows[i].math_owner=!!n.parentElement.closest('.math');
 }
 const math_leaf_census=[...document.querySelectorAll('.math')].map(e=>
  [...e.querySelectorAll('mjx-c,mjx-line,mjx-surd,svg use,svg path,svg line,svg rect,svg polygon,'+
    'math mi,math mn,math mo,math mtext')]
   .filter(n=>!n.querySelector('mjx-c,svg use,svg path,math mi,math mn,math mo,math mtext'))
   .map(n=>({...elementState(n),tag:n.tagName.toLowerCase(),text:n.textContent,
    data_c:n.getAttribute('data-c'),href:n.getAttribute('href')||n.getAttribute('xlink:href')})));
"""


def _region(box: Any, page: Any) -> tuple[int, int, int, int]:
    if (
        not isinstance(box, list)
        or len(box) != 4
        or any(type(value) not in {int, float} or not math.isfinite(value) for value in box)
    ):
        raise ValueError("localized native paint omitted finite actual geometry")
    x, y, width, height = box
    return (
        max(0, math.ceil(x)),
        max(0, math.ceil(y)),
        min(page.width, math.floor(x + width)),
        min(page.height, math.floor(y + height)),
    )


def _outside(box: list[float], page: Any) -> bool:
    """A finite box wholly beyond the captured page is unpainted, not subpixel."""
    x, y, width, height = box
    return x >= page.width or y >= page.height or x + width <= 0 or y + height <= 0


def inspect_local_paint(dom: dict[str, Any], pixels: bytes, indices: list[int]) -> dict[str, Any]:
    """Recompute every required nonspace character and rendered math leaf ROI.

    Missing/zero-width/combined geometry remains explicit. Geometry wholly
    beyond the captured page is an unpainted finding; in-page geometry too
    small for an integral pixel region remains a blocker. All character text
    is reconstructed, so a producer cannot omit the covered minus or exponent
    while leaving the whole paragraph's contrast intact.
    """
    from PIL import Image

    findings: list[dict[str, Any]] = []
    blockers = []
    regions = []
    count = 0
    with Image.open(BytesIO(pixels)) as page:
        page.load()
        gray = page.convert("L")
        for index in indices:
            row = dom["text"][index]
            chars = row.get("characters")
            if not isinstance(chars, list) or row.get("math_owner"):
                raise ValueError("source text omitted its complete native character census")
            if "".join(item.get("character", "") for item in chars) != row["text"]:
                raise ValueError("native character census does not reconstruct source-bound DOM text")
            offset = 0
            previous_boxes = None
            for character_index, item in enumerate(chars):
                character = item["character"]
                if len(character) != 1 or item.get("offset_utf16") != offset:
                    raise ValueError("native character occurrence offset or cardinality changed")
                offset += len(character.encode("utf-16-le")) // 2
                count += 1
                if count > 200000:
                    raise ValueError("localized source character finite budget exceeded")
                if character.isspace():
                    continue
                boxes = item.get("boxes")
                if not isinstance(boxes, list):
                    raise ValueError("native source character omitted range geometry")
                owner = {"text_index": index, "character_index": character_index, "character": character}
                if unicodedata.combining(character) or boxes == previous_boxes:
                    blockers.append(
                        f"text:{index}:{character_index}: combined/ligature glyph needs a source outline witness"
                    )
                previous_boxes = boxes
                if not boxes:
                    findings.append({"code": "html.text.character-missing", **owner})
                for box in boxes:
                    roi = _region(box, page)
                    if roi[0] >= roi[2] or roi[1] >= roi[3]:
                        if _outside(box, page):
                            findings.append({"code": "html.text.character-outside", **owner})
                        else:
                            blockers.append(
                                f"text:{index}:{character_index}: subpixel glyph needs a source outline witness"
                            )
                        continue
                    low, high = cast(tuple[int, int], gray.crop(roi).getextrema())
                    regions.append({**owner, "box_px": list(roi), "luminance_range": high - low})
                    if high - low < 32:
                        findings.append({"code": "html.text.character-invisible", **owner})
        math_leaves = dom.get("math_leaf_census")
        if not isinstance(math_leaves, list) or len(math_leaves) != len(dom["math"]):
            raise ValueError("native math omitted its complete localized leaf census")
        for math_index, leaves in enumerate(math_leaves):
            if not isinstance(leaves, list) or len(leaves) > 10000:
                raise ValueError("native math leaf census exceeds finite bounds")
            if not leaves:
                blockers.append(f"math:{math_index}: unknown native math layout requires localized source witness")
            for leaf_index, leaf in enumerate(leaves):
                owner = {
                    "math_index": math_index,
                    "leaf_index": leaf_index,
                    "native_tag": leaf["tag"],
                    "native_code": leaf.get("data_c"),
                }
                if leaf.get("hidden") or leaf.get("clipped"):
                    findings.append({"code": "html.math.leaf-hidden", **owner})
                roi = _region(leaf.get("box"), page)
                if roi[0] >= roi[2] or roi[1] >= roi[3]:
                    if _outside(leaf["box"], page):
                        findings.append({"code": "html.math.leaf-outside", **owner})
                    else:
                        blockers.append(
                            f"math:{math_index}:{leaf_index}: subpixel math leaf needs a source outline witness"
                        )
                    continue
                low, high = cast(tuple[int, int], gray.crop(roi).getextrema())
                regions.append({**owner, "box_px": list(roi), "luminance_range": high - low})
                if high - low < 32:
                    findings.append({"code": "html.math.leaf-invisible", **owner})
    return {"regions": regions, "findings": findings, "blockers": blockers}


def inspect_unit_image_paint(
    page: Any, expected_rgba: Any, box: list[float], background: Any, identity: str
) -> dict[str, Any]:
    """Compare every source pixel at exact unscaled integral native placement.

    Every unit pixel, including a one-pixel scientific mark, has a maximum
    error obligation. Mean image error cannot hide a localized opaque cover.
    The native browser paints an unscaled replaced image at its device-pixel
    snapped rectangle (origin rounded half up at the 1:1 screenshot scale), so
    a fractional layout origin is compared at that exact integral placement;
    shifted or resampled paint remains a localized-paint finding. Resized
    figures retain a separate native capability gap.
    """
    from PIL import Image, ImageChops

    if len(box) != 4 or any(type(value) not in {int, float} or not math.isfinite(value) for value in box):
        raise ValueError("unit source image omitted finite actual geometry")
    x, y, width, height = box
    blockers = []
    findings: list[dict[str, Any]] = []
    if (width, height) != expected_rgba.size:
        blockers.append(f"{identity}: resized figure requires calibrated localized source paint proof")
        return {"source_id": identity, "findings": findings, "blockers": blockers, "pixels": None}
    left, top = math.floor(x + 0.5), math.floor(y + 0.5)
    roi = (left, top, left + int(width), top + int(height))
    if x < 0 or y < 0 or roi[2] > page.width or roi[3] > page.height:
        findings.append({"code": "html.figure.localized-crop", "source_id": identity})
        return {"source_id": identity, "findings": findings, "blockers": blockers, "pixels": None}
    expected = (
        Image.alpha_composite(Image.new("RGBA", expected_rgba.size, background), expected_rgba)
        if background is not None
        else expected_rgba
    ).convert("RGB")
    actual = page.convert("RGB").crop(roi)
    difference = ImageChops.difference(expected, actual)
    maximum = max(high for low, high in cast(tuple[tuple[int, int], ...], difference.getextrema()))
    changed = sum(
        any(channel > 2 for channel in pixel) for pixel in cast(Iterable[tuple[int, int, int]], difference.getdata())
    )
    if changed:
        findings.append({"code": "html.figure.localized-paint", "source_id": identity})
    return {
        "source_id": identity,
        "findings": findings,
        "blockers": blockers,
        "pixels": {
            "box_px": list(roi),
            "max_channel_error": maximum,
            "pixels_over_error_2": changed,
            "expected_rgb_sha256": hashlib.sha256(expected.tobytes()).hexdigest(),
            "native_rgb_sha256": hashlib.sha256(actual.tobytes()).hexdigest(),
        },
    }

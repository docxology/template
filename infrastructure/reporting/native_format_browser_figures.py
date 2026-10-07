"""Independent decoded source image and rendered image-region observations."""

from __future__ import annotations

import base64
import hashlib
import math
import os
from io import BytesIO
from pathlib import Path
from typing import Any, cast
from urllib.parse import unquote, urlsplit

from infrastructure.reporting.native_format_content_contracts import NativeContentContract, SemanticContentContract
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


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
        for identity, target, _ in contract.image_sources:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
                blockers.append(f"{identity}: independent external figure source bytes unavailable")
                continue
            path = Path(os.path.normpath(str(artifact.path.parent / unquote(parsed.path))))
            source = reader.read(path.relative_to(reader.root).as_posix())
            if source.path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                blockers.append(f"{identity}: independent decoded vector/animated figure semantics unsupported")
                continue
            images = [image for image in dom["images"] if image["src"] == target]
            if len(images) != 1:
                findings.append({"code": "html.figure.source", "source_id": identity})
                continue
            image = images[0]
            with Image.open(BytesIO(source.content)) as source_image:
                if getattr(source_image, "n_frames", 1) != 1:
                    blockers.append(f"{identity}: animated source image semantics unsupported")
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
            if actual.size != expected.size or actual_hash != expected_hash:
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
            if expected.getchannel("A").getextrema() != (255, 255):
                blockers.append(f"{identity}: source alpha compositing requires independent background projection")
                continue
            projected = expected.convert("RGB").resize(roi.size, Image.Resampling.LANCZOS)
            error = sum(ImageStat.Stat(ImageChops.difference(projected, roi)).mean) / 3
            if error > 24:
                findings.append({"code": "html.figure.visual", "source_id": identity})
            observations.append(
                {
                    "source_id": identity,
                    "source": {"path": source.relative, "sha256": source.sha256},
                    "decoded_source_sha256": expected_hash,
                    "decoded_native_sha256": actual_hash,
                    "box_px": box,
                    "rendered_region_mean_error": error,
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

"""Source-driven Pitch OOXML package and all-three native PDF/PPTX pair closure."""

from __future__ import annotations

import hashlib
import math
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_content_contracts import text_tokens
from infrastructure.reporting.native_projection_contracts import ProjectionPage, projection_contract_record

PITCH_VARIANTS = ("short", "medium", "long")


def _pixels(content: bytes) -> tuple[tuple[int, int], str]:
    from PIL import Image

    with Image.open(BytesIO(content)) as image:
        if image.width * image.height > 20_000_000:
            raise ValueError("native/source Pitch picture exceeds original pixel bound")
        pixels = image.convert("RGBA")
        return pixels.size, hashlib.sha256(pixels.tobytes()).hexdigest()


def inspect_pitch_package(
    content: bytes,
    pages: tuple[ProjectionPage, ...],
    *,
    deadline: float,
    native_context: tuple[Path, Path, dict[str, str], str] | None = None,
    source_model: Any | None = None,
) -> dict[str, Any]:
    """Inspect exact text, inherited fonts, source images, QR pixels/targets/layout.

    This is additional source evidence. The complete native Office conversion,
    every actual page raster and existing projection oracle remain required.
    """
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes
    from infrastructure.reporting.native_projection_checks import decode_projection_qr
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory

    parsed = parse_native_bytes("pptx", content)
    native = Presentation(BytesIO(content))
    if len(native.slides) != len(pages) or not pages:
        raise ValueError("Pitch package requires complete exact source/native slide parity")
    findings = []
    blockers = []
    observed = []
    source_notes = None
    if source_model is not None:
        source_notes = [slide.notes for slide in source_model.slides]
        if not source_model.slides or source_model.slides[0].kind != "title":
            source_notes.insert(0, "")
        if len(source_notes) != len(pages):
            raise ValueError("Pitch complete source model notes differ from its exact source page plan")
    for ordinal, (slide, page) in enumerate(zip(native.slides, pages, strict=True), 1):
        if time.monotonic() >= deadline:
            raise TimeoutError("Pitch source package exhausted original deadline")
        native_width, native_height = native.slide_width, native.slide_height
        if native_width is None or native_height is None:
            raise ValueError("Pitch native package is missing its original slide dimensions")
        width, height = float(native_width) / 12700, float(native_height) / 12700
        if abs(width - page.size_pt[0]) > 0.001 or abs(height - page.size_pt[1]) > 0.001:
            findings.append({"code": "pitch.package.page.geometry", "page": ordinal})
        texts: list[str] = []
        targets = []
        pictures = []
        floors = []
        for shape in slide.shapes:
            box = tuple(
                float(x) / 12700 for x in (shape.left, shape.top, shape.left + shape.width, shape.top + shape.height)
            )
            if (
                not all(math.isfinite(v) for v in box)
                or box[0] < -0.001
                or box[1] < -0.001
                or box[2] > width + 0.001
                or box[3] > height + 0.001
            ):
                findings.append({"code": "pitch.package.layout.crop", "page": ordinal, "shape_id": shape.shape_id})
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    text = "".join(run.text for run in paragraph.runs)
                    if text_tokens(text):
                        texts.extend(text_tokens(text))
                        run_floor: list[tuple[str, float]] = []
                        for run in paragraph.runs:
                            if not text_tokens(run.text):
                                continue
                            font = run.font.size or paragraph.font.size
                            if font is None:
                                blockers.append(
                                    f"page {ordinal}: inherited native font needs explicit source/theme resolution"
                                )
                            else:
                                run_floor.extend((token, float(font) / 12700) for token in text_tokens(run.text))
                            if run.hyperlink.address:
                                targets.append(run.hyperlink.address)
                        floors.extend(run_floor)
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                target = shape.click_action.hyperlink.address or ""
                if target:
                    targets.append(target)
                pictures.append(
                    {
                        "shape_id": shape.shape_id,
                        "box_pt": list(box),
                        "target": target,
                        "pixels": _pixels(shape.image.blob),
                        "content": shape.image.blob,
                    }
                )
        expected: list[tuple[str, float]] = []
        for role, text, floor in page.texts:
            visible = "“" + text + "”" if role == "quote" else "— " + text if role == "attribution" else text
            expected.extend((token, floor) for token in text_tokens(visible))
        if texts != [token for token, _ in expected]:
            findings.append({"code": "pitch.package.source.text", "page": ordinal})
        elif len(floors) == len(expected):
            for (token, actual), (_, floor) in zip(floors, expected, strict=True):
                if actual + 0.05 < floor:
                    findings.append(
                        {
                            "code": "pitch.package.typography.font",
                            "page": ordinal,
                            "token": token,
                            "actual_pt": actual,
                            "minimum_pt": floor,
                        }
                    )
        wanted_targets = sorted(target for target in (page.citation, page.qr_target) if target)
        if sorted(targets) != wanted_targets:
            findings.append({"code": "pitch.package.source.targets", "page": ordinal})
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        if source_notes is not None and notes != source_notes[ordinal - 1]:
            findings.append({"code": "pitch.package.source.notes", "page": ordinal})
        figure_pictures = []
        qr_pictures = []
        source_width, source_height = page.size_pt
        qr_box = (
            source_width - 39.6 - 44.64,
            source_height - 53.28,
            source_width - 39.6,
            source_height - 53.28 + 44.64,
        )
        for picture in pictures:
            # The role comes from the Source-owned QR position, not a mutable
            # candidate hyperlink. A wrong link still fails source.targets.
            # An unplaced/extra picture remains an explicit figure blocker.
            in_qr_box = all(abs(a - b) <= 0.05 for a, b in zip(picture["box_pt"], qr_box, strict=True))
            if page.qr_target and (picture["target"] == page.qr_target or in_qr_box):
                qr_pictures.append(picture)
            else:
                figure_pictures.append(picture)
        if page.figure_projection:
            wanted_pixels = _pixels(page.figure_projection.content)
            if len(figure_pictures) != 1 or figure_pictures[0]["pixels"] != wanted_pixels:
                findings.append({"code": "pitch.package.figure.source-pixels", "page": ordinal})
            elif any(
                abs(a - b) > 0.5
                for a, b in zip(figure_pictures[0]["box_pt"], page.figure_projection.box_pt, strict=True)
            ):
                findings.append({"code": "pitch.package.figure.geometry", "page": ordinal})
        elif page.figure or figure_pictures:
            blockers.append(f"page {ordinal}: complete source-owned figure projection is required")
        qr = None
        if page.qr_target:
            wanted_box = qr_box
            if len(qr_pictures) != 1:
                findings.append({"code": "pitch.package.qr.draw", "page": ordinal})
            else:
                picture = qr_pictures[0]
                if any(abs(a - b) > 0.05 for a, b in zip(picture["box_pt"], wanted_box, strict=True)):
                    findings.append({"code": "pitch.package.qr.geometry", "page": ordinal})
                if native_context is None:
                    blockers.append(f"page {ordinal}: actual package QR pixel decoder is required")
                else:
                    root, parent, env, run_id = native_context
                    private = parent / f"package-qr-{ordinal}"
                    create_private_native_directory(root, private)
                    qr = decode_projection_qr(
                        root,
                        private,
                        picture["content"],
                        page.qr_target,
                        env=env,
                        deadline=deadline,
                        run_id=run_id,
                        ordinal=ordinal,
                    )
                    findings.extend({**item, "page": ordinal} for item in qr["findings"])
        observed.append(
            {
                "page": ordinal,
                "text_tokens": texts,
                "fonts_pt": [size for _, size in floors],
                "targets": sorted(targets),
                "notes": notes,
                "pictures": [{k: v for k, v in p.items() if k != "content"} for p in pictures],
                "qr": qr,
            }
        )
    return {
        "schema_version": "template-native-pitch-package-source-v1",
        "input_sha256": hashlib.sha256(content).hexdigest(),
        "parser": parsed,
        "contract": projection_contract_record(pages),
        "source_notes_checked": source_model is not None,
        "pages": observed,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def inspect_pitch_native_pairs(
    artifacts: dict[str, dict[str, Any]], contracts: dict[str, tuple[ProjectionPage, ...]]
) -> dict[str, Any]:
    """All six exact artifact IDs, original native observations and source models.

    No variant or format can be substituted for another; equal titles, page
    counts or content summaries do not authorize a missing native observation.
    """
    from infrastructure.reporting.native_pitch_source_layout import LAYOUT_CANONICALIZATION, LAYOUT_SCHEMA

    expected_ids = {f"pitch:{length}:{kind}" for length in PITCH_VARIANTS for kind in ("pdf", "pptx")}
    if set(artifacts) != expected_ids or set(contracts) != expected_ids:
        raise ValueError("Pitch native parity requires exactly all three PDF/PPTX source-owned pairs")
    findings = []
    blockers = []
    pairs = []
    for length in PITCH_VARIANTS:
        ids = (f"pitch:{length}:pdf", f"pitch:{length}:pptx")
        records = [projection_contract_record(contracts[identity]) for identity in ids]
        if records[0] != records[1]:
            findings.append({"code": "pitch.pair.source.contract", "variant": length})
        for identity in ids:
            value = artifacts[identity]
            observation = value.get("observation", {})
            kind = identity.rsplit(":", 1)[1]
            if (
                value.get("id") != identity
                or value.get("format") != kind
                or value.get("projection_contract") != records[0]
                or not re_sha256(value.get("input", {}).get("sha256"))
            ):
                findings.append({"code": "pitch.pair.artifact.identity", "id": identity})
            if kind == "pptx":
                observation = observation.get("observation", {})
                package = value.get("source_package", {})
                if (
                    package.get("status") != "pass"
                    or package.get("contract") != records[0]
                    or package.get("blockers")
                    or package.get("findings")
                    or package.get("input_sha256") != value.get("input", {}).get("sha256")
                    or package.get("source_notes_checked") is not True
                    or package.get("source_layout", {}).get("schema_version") != LAYOUT_SCHEMA
                    or package.get("source_layout", {}).get("canonicalization") != LAYOUT_CANONICALIZATION
                    or package.get("source_layout", {}).get("status") != "pass"
                    or package.get("source_layout", {}).get("findings")
                    or package.get("source_layout", {}).get("source_layout_digest")
                    != package.get("source_layout", {}).get("candidate_layout_digest")
                ):
                    blockers.append(f"{identity}: actual complete source/package/QR parity is required")
            else:
                reference = value.get("source_native_reference", {})
                if (
                    reference.get("status") != "pass"
                    or reference.get("findings")
                    or reference.get("blockers")
                    or reference.get("projection_contract") != records[0]
                    or reference.get("input_sha256") != value.get("input", {}).get("sha256")
                ):
                    blockers.append(f"{identity}: complete source-only native PDF layout/theme parity is required")
            if observation.get("status") != "pass" or observation.get("blockers") or observation.get("findings"):
                blockers.append(f"{identity}: actual complete native source projection must pass")
            if len(observation.get("pages", [])) != len(contracts[identity]):
                findings.append({"code": "pitch.pair.native.pages", "id": identity})
        pairs.append(
            {
                "variant": length,
                "ids": list(ids),
                "source_contract_digest": records[0]["digest"],
                "pages": len(contracts[ids[0]]),
            }
        )
    return {
        "schema_version": "template-native-pitch-all-pairs-v1",
        "pairs": pairs,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def re_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)

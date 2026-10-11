"""Current-reader font bytes and full contours from a genuine local probe."""

from __future__ import annotations

import hashlib
import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_acceptance_contracts import (
    native_deadline_guard,
)
from infrastructure.reporting.native_format_html_glyph_contours import (
    admitted_font_contours,
    admitted_shaped_glyph_contours,
)
from infrastructure.reporting.native_format_html_platform_font_probe import PROBE_SCHEMA
from infrastructure.reporting.native_format_html_source_metadata import (
    remaining_seconds,
)


def derive_probed_font_contours(request: dict[str, Any], probe: dict[str, Any], *, deadline: float) -> dict[str, Any]:
    """Decode local exact font files resolved by a freshly admitted actual probe.

    The enclosing producer/reader authenticates this probe's original successful
    NativeToolRecord, exact request/SDK bytes and current source provenance. A
    portable reader resolves its own local font URLs with its own genuine tool;
    it must never pass producer JSON/path labels directly into this function.
    Neither resolver names nor this result approve OS/font pipeline custody.
    """
    from fontTools.ttLib import TTCollection, TTFont

    remaining_seconds(deadline)
    request_hash = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if (
        probe.get("schema_version") != PROBE_SCHEMA
        or probe.get("request_sha256") != request_hash
        or probe.get("framework_before") != probe.get("framework_after")
    ):
        raise ValueError("genuine current platform font probe/request custody changed")
    requested = request["fonts"]
    observed = probe.get("fonts")
    if not isinstance(observed, list) or len(observed) != len(requested):
        raise ValueError("genuine local platform font probe omitted source faces")
    contours = []
    blockers = list(probe["blockers"])
    for source, native in zip(requested, observed, strict=True):
        remaining_seconds(deadline)
        if (
            native["postscript_name"] != source["postscript_name"]
            or native["characters"] != source["characters"]
            or native["font_file_before"] != native["font_file_after"]
        ):
            raise ValueError("genuine local platform font probe substituted source font/codepoints")
        path = Path(native["font_file_after"]["path"]).resolve(strict=True)
        stat = path.stat()
        content = read_bytes_confined(path.parent, path, max_bytes=32 * 1024 * 1024)
        after = path.stat()
        expected = native["font_file_after"]
        if (
            any(
                getattr(stat, key) != value or getattr(after, key) != value
                for key, value in expected["metadata"].items()
            )
            or len(content) != expected["bytes"]
            or hashlib.sha256(content).hexdigest() != expected["sha256"]
            or expected["sha256"] != native["font_sha256"]
        ):
            raise ValueError("source platform font bytes changed before independent outline decode")
        face_indices = []
        with native_deadline_guard(deadline):
            if content.startswith(b"ttcf"):
                collection = TTCollection(BytesIO(content), lazy=False)
                try:
                    if len(collection.fonts) > 256:
                        raise ValueError("source font collection exceeds its finite face bound")
                    face_indices = [
                        index
                        for index, font in enumerate(collection.fonts)
                        if font["name"].getDebugName(6) == source["postscript_name"]
                    ]
                finally:
                    collection.close()
            else:
                font = TTFont(BytesIO(content), lazy=False)
                try:
                    if font["name"].getDebugName(6) == source["postscript_name"]:
                        face_indices = [0]
                finally:
                    font.close()
        if len(face_indices) != 1:
            blockers.append(source["postscript_name"] + ": physical collection face is missing/ambiguous")
            continue
        if native.get("provider") == "Fontconfig/FreeType" and native.get("face_index") != face_indices[0]:
            raise ValueError("Linux native/source decoder physical collection face index differs")
        outline = admitted_font_contours(
            content,
            face_indices[0],
            source["postscript_name"],
            source["characters"],
            deadline=deadline,
        )
        contextual = source.get("contextual_runs", [])
        if contextual:
            context_observation = native.get("contextual_runs")
            if (
                not isinstance(context_observation, dict)
                or context_observation["physical_provider_before"] != context_observation["physical_provider_after"]
                or context_observation["actual_provider_symbols_before"]
                != context_observation["actual_provider_symbols_after"]
            ):
                raise ValueError("actual contextual Source shaper physical/callable custody did not close")
            actual_contextual = context_observation["runs"]
            if not isinstance(actual_contextual, list) or len(contextual) != len(actual_contextual):
                raise ValueError("genuine physical Source probe omitted original contextual shaping")
            shaped_runs = []
            all_shaped_ids = [
                glyph["glyph_id"] for actual in actual_contextual for glyph in actual["shaping"]["glyphs"]
            ]
            shaped_contours = admitted_shaped_glyph_contours(
                content,
                face_indices[0],
                source["postscript_name"],
                all_shaped_ids,
                deadline=deadline,
            )
            for expected, actual in zip(contextual, actual_contextual, strict=True):
                shaped = actual["shaping"]
                if (
                    any(
                        actual[key] != expected[key]
                        for key in (
                            "source_id",
                            "source_run_id",
                            "source_start",
                            "source_end",
                        )
                    )
                    or shaped["original_text"] != expected["text"]
                    or shaped["font_sha256"] != hashlib.sha256(content).hexdigest()
                    or shaped["face_index"] != face_indices[0]
                    or shaped["digest"]
                    != canonical_digest({key: value for key, value in shaped.items() if key != "digest"})
                ):
                    raise ValueError("actual contextual Source shaping changed font/original text/occurrence")
                shaped_runs.append(
                    {
                        **expected,
                        "glyphs": shaped["glyphs"],
                        "provider_sha256": context_observation["physical_provider_after"]["sha256"],
                        "provider_version": shaped["provider_version"],
                        "units_per_em": shaped["units_per_em"],
                    }
                )
                blockers.extend(shaped["blockers"])
            # These are the exact re-read physical font bytes, not a local-name
            # substitution. Only the source-only reference receives this body.
            outline.pop("digest")
            outline["shaped_runs"] = shaped_runs
            outline["shaped_outlines"] = shaped_contours
            outline["font_data_base64"] = base64.b64encode(content).decode("ascii")
            outline["digest"] = canonical_digest(outline)
        glyphs = {glyph["character"]: glyph["glyph_id"] for glyph in outline["glyphs"]}
        if len(native["glyph_ids"]) != len(source["characters"]):
            raise ValueError("genuine platform source glyph cardinality changed")
        for character, glyph_id in zip(source["characters"], native["glyph_ids"], strict=True):
            if not character.isspace() and glyphs.get(character) != glyph_id:
                blockers.append(
                    source["postscript_name"]
                    + f": U+{ord(character):04X} platform/source-cmap glyph differs or is unsupported"
                )
        blockers.extend(outline["blockers"])
        contours.append(outline)
    remaining_seconds(deadline)
    return {"request_sha256": request_hash, "contours": contours, "blockers": blockers}

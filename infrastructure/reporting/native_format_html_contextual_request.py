"""Source-derived styled text segments for genuine physical font/shaper probes."""

from __future__ import annotations

from typing import Any

from infrastructure.reporting.native_format_html_source_metadata import (
    remaining_seconds,
)


def compile_contextual_font_request(
    source: dict[str, Any],
    dom: dict[str, Any],
    mapping: dict[str, Any],
    *,
    deadline: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Use original ancestry for expected faces; native rows supply placement only.

    Whole original text is shaped within native line segments. The text and its
    style come from current Source. Choosing line placement does not admit the
    document's independently required layout/wrapping/UA calibration gates.
    """
    fonts: dict[str, dict[str, Any]] = {}
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    mapped_by_run: dict[str, list[dict[str, Any]]] = {}
    for row in mapping["characters"]:
        mapped_by_run.setdefault(row["source_run_id"], []).append(row)
    for run in source["runs"]:
        remaining_seconds(deadline)
        rows = mapped_by_run.get(run["source_id"], [])
        if not rows:
            continue
        style = run["source_style"]
        expected = style["expected_postscript_name"]
        if expected is None:
            blockers.extend(style["blockers"])
            continue
        segments: list[list[dict[str, Any]]] = []
        for row in rows:
            native = dom["text"][row["text_index"]]
            actual_style = native.get("glyph_style", {})
            expected_px = style.get("independent_font_px")
            if type(expected_px) not in (float, int):
                blockers.append(
                    row["source_id"] + ": actual independent Source writer/UA font-size calibration is missing"
                )
            elif abs(native["font_px"] - expected_px) > 1 / 64:
                findings.append({"code": "html.glyph.source-authored-font-size", "source_id": row["source_id"]})
            if any(actual_style.get(key) != style[key] for key in ("font_weight", "font_style")):
                findings.append(
                    {
                        "code": "html.glyph.source-authored-style",
                        "source_id": row["source_id"],
                    }
                )
            actual_fonts = native.get("platform_fonts")
            if not isinstance(actual_fonts, list) or not any(
                face.get("postScriptName") == expected for face in actual_fonts
            ):
                findings.append(
                    {
                        "code": "html.glyph.source-authored-font",
                        "source_id": row["source_id"],
                    }
                )
            elif len(actual_fonts) != 1:
                blockers.append(
                    row["source_id"] + ": aggregate CDP font usage does not attribute each physical text run"
                )
            if len(row["boxes"]) != 1:
                blockers.append(row["source_id"] + ": contextual source placement lacks a unique native line box")
                continue
            if (
                not segments
                or abs(segments[-1][-1]["boxes"][0][1] - row["boxes"][0][1]) > 1 / 64
                or segments[-1][-1]["text_index"] != row["text_index"]
            ):
                segments.append([])
            segments[-1].append(row)
        item = fonts.setdefault(
            expected,
            {
                "postscript_name": expected,
                "characters": "",
                "source_ids": [],
                "contextual_runs": [],
            },
        )
        for index, segment in enumerate(segments):
            start = segment[0]["source_character_offset"]
            end = segment[-1]["source_character_offset"] + 1
            text = run["text"][start:end]
            if "\n" in text or "\r" in text:
                blockers.append(run["source_id"] + ": a contextual line segment crossed an original hard line break")
                continue
            for character in text:
                if character not in item["characters"]:
                    item["characters"] += character
            identity = run["source_id"] + ":line:" + str(index)
            item["source_ids"].append(identity)
            item["contextual_runs"].append(
                {
                    "source_id": identity,
                    "source_run_id": run["source_id"],
                    "source_start": start,
                    "source_end": end,
                    "text": text,
                }
            )
    return list(fonts.values()), findings, blockers

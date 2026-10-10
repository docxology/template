"""Current-reader citation regeneration and exact native glyph/ink observations.

Only original source bindings and actual native tool outcomes establish the
reference. Original installed paths are retained observations, never reader
access requests. A transported local receipt is not an authenticated attestation.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from bisect import bisect_left
from importlib.metadata import version
from io import BytesIO
from pathlib import Path
from typing import Any, cast

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_acceptance_contracts import TOOL_SCHEMA
from infrastructure.reporting.native_format_content_contracts import text_tokens
from infrastructure.reporting.native_format_pdf_oracles import PDF_POLICY
from infrastructure.reporting.native_pdf_citation_runtime import budget, dependency_identity
from infrastructure.reporting.native_pdf_citations import CITATION_POLICY, CITATION_SCHEMA, observe_natbib_reference
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

CITATION_OBSERVATION_SCHEMA = "template-native-natbib-glyph-observation-v1"


def _compact(text: str) -> str:
    return "".join(text_tokens(text))


def _validate_original_tools(
    raw: dict[str, Any], reader: SnapshotReader, fresh: dict[str, Any], fresh_reader: SnapshotReader
) -> None:
    bindings = raw.get("tool_artifacts")
    if not isinstance(bindings, list) or len(bindings) != 14:
        raise ValueError("original citation reference omitted its complete actual process cohort")
    expected = [("pandoc", "citation-pandoc-natbib")]
    expected += [
        (name, f"discovery-{index:02d}-{name}")
        for index, name in enumerate(("xelatex", "bibtex", "xelatex", "xelatex"), 1)
    ]
    expected += [("xdvipdfmx", "discovery-native-backend"), ("kpsewhich", "style-resolution")]
    expected += [
        (name, f"reference-{index:02d}-{name}")
        for index, name in enumerate(("xelatex", "bibtex", "xelatex", "xelatex"), 1)
    ]
    expected += [
        ("xdvipdfmx", "reference-native-backend"),
        ("pdffonts", "citation-reference-fonts"),
        ("pdftotext", "citation-reference-text"),
    ]
    cwd = None
    for binding, fresh_binding, (name, purpose) in zip(bindings, fresh["tool_artifacts"], expected, strict=True):
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
            raise ValueError("original citation tool artifact binding is malformed")
        snapshot = reader.read(binding["path"])
        if snapshot.sha256 != binding["sha256"]:
            raise ValueError("original citation tool receipt bytes changed")
        process = snapshot.json_object()
        new_process = fresh_reader.read(fresh_binding["path"]).json_object()
        executable, digest, command = (
            process.get("executable"),
            process.get("executable_sha256"),
            process.get("command"),
        )
        if (
            process.get("schema_version") != TOOL_SCHEMA
            or process.get("tool") != name
            or process.get("purpose") != purpose
            or process.get("run_id") != raw.get("run_id")
            or type(process.get("exit_code")) is not int
            or process["exit_code"] != 0
            or type(process.get("original_exit_code")) is not int
            or process["original_exit_code"] != 0
            or process.get("timed_out") is not False
            or process.get("custody_refused") is not False
            or process.get("diagnostic") != ""
            or not isinstance(command, list)
            or not command
            or not isinstance(executable, str)
            or not Path(executable).is_absolute()
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ValueError("original citation tool did not actually execute the required successful process")
        native_binding = process.get("native_process_artifact")
        if not isinstance(native_binding, dict) or set(native_binding) != {"path", "sha256"}:
            raise ValueError("original citation lacks its bound actual native process nomination")
        native_snapshot = reader.read(native_binding["path"])
        if native_snapshot.sha256 != native_binding["sha256"]:
            raise ValueError("original citation actual native process nomination bytes changed")
        native = native_snapshot.json_object()
        nomination = native.get("nomination")
        preserve = name == "xelatex"
        if (
            not isinstance(nomination, dict)
            or set(nomination) != {"tool", "path", "resolved_path"}
            or nomination["tool"] != name
            or nomination["resolved_path"] != executable
            or not isinstance(nomination["path"], str)
            or not Path(nomination["path"]).is_absolute()
            or native.get("launcher_preserved") is not preserve
            or native.get("command") != command
            or command[0] != (nomination["path"] if preserve else executable)
        ):
            raise ValueError("original citation argv differs from its Source-selected actual native launcher")
        for key in ("executable_observation_before", "executable_observation_after"):
            if process.get(key) != {
                "schema_version": "template-native-executable-observation-v1",
                "path": executable,
                "sha256": digest,
            }:
                raise ValueError("original citation executable before/after observation changed")
        if process.get("input_observations_before") != process.get("input_observations_after"):
            raise ValueError("original citation consumed input before/after observations changed")
        if not isinstance(process.get("input_observations_before"), list) or not process["input_observations_before"]:
            raise ValueError("original citation process omitted consumed source observations")
        if not isinstance(process.get("cwd"), str) or not Path(process["cwd"]).is_absolute():
            raise ValueError("original citation process working directory is absent")
        if cwd is None:
            cwd = process["cwd"]
        if process["cwd"] != cwd:
            raise ValueError("original citation process cohort mixes producer working directories")
        expected_sources = [raw["inputs"][role] for role in ("sources", "bibliographies", "config", "preamble")]
        expected_inputs = {"original-ast.json": raw["inputs"]["ast_sha256"]}
        for index, row in enumerate(item for group in expected_sources for item in group):
            expected_inputs[f"source-{index:06d}.input"] = row["sha256"]
        for index, row in enumerate(raw["inputs"]["bibliographies"]):
            expected_inputs[f"database-{index:06d}.bib"] = row["sha256"]
        observed_inputs = {}
        for row in process["input_observations_before"]:
            if (
                not isinstance(row, dict)
                or set(row) != {"path", "name", "sha256", "bytes"}
                or not isinstance(row["path"], str)
                or not isinstance(row["name"], str)
                or type(row["bytes"]) is not int
                or row["bytes"] < 0
                or not isinstance(row["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
            ):
                raise ValueError("original citation consumed-input observation is malformed")
            path = Path(row["path"])
            if (
                not path.is_absolute()
                or path.parent != Path(cwd)
                or path.name != row["name"]
                or path.name in observed_inputs
            ):
                raise ValueError("original citation consumed-input path/census is invalid")
            consumption = [
                item for item in process.get("consumed_input_artifacts", []) if item.get("observation") == row
            ]
            if len(consumption) > 1:
                raise ValueError("original generated citation input consumption is ambiguous")
            copied = reader.read(
                consumption[0]["artifact"]["path"]
                if consumption
                else (Path(binding["path"]).parent / path.name).as_posix()
            )
            if consumption and copied.sha256 != consumption[0]["artifact"]["sha256"]:
                raise ValueError("original generated citation input consumed bytes changed")
            if copied.sha256 != row["sha256"] or len(copied.content) != row["bytes"]:
                raise ValueError("original citation consumed bytes differ from before/after observations")
            observed_inputs[path.name] = row["sha256"]
        if any(observed_inputs.get(name) != digest for name, digest in expected_inputs.items()):
            raise ValueError("original citation process omitted its complete frozen source/bibliography inputs")
        if (
            name != "pandoc"
            and observed_inputs.get("oracle.tex") != raw["dependency_custody"]["diagnostic_outputs"]["tex"]["sha256"]
        ):
            raise ValueError("original citation process consumed different generated reference TeX")
        if name == "xelatex" and command[1:] != [
            "-fmt=xelatex",
            "-progname=xelatex",
            "-no-pdf",
            "-recorder",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-no-shell-escape",
            "oracle.tex",
        ]:
            raise ValueError("original citation compiler command differs from the source-owned finite reference")
        exact = {
            "bibtex": ["oracle"],
            "xdvipdfmx": ["--kpathsea-debug=4", "-vv", "-o", "oracle.pdf", "oracle.xdv"],
            "kpsewhich": ["plainnat.bst"],
            "pdffonts": ["oracle.pdf"],
            "pdftotext": ["-layout", "oracle.pdf", "-"],
        }
        if name in exact and command[1:] != exact[name]:
            raise ValueError("original citation native command differs from its required reference")
        if name == "pandoc" and command[1:6] != [
            str(Path(cwd) / "citation-projection.json"),
            "--from=json",
            "--to=latex",
            "--standalone",
            "--natbib",
        ]:
            raise ValueError("original citation Pandoc did not consume the source-only natbib projection")
        if name == "pandoc" and command[2:] != new_process["command"][2:]:
            raise ValueError("original citation Pandoc options differ from current source configuration")


def replay_natbib_reference(
    root: Path, directory: Path, original: dict[str, Any], reader: SnapshotReader, **source_arguments: Any
) -> dict[str, Any]:
    """Recreate labels on the current reader and validate original source custody.

    ``source_arguments`` are the exact keyword inputs to observe_natbib_reference,
    independently reconstructed by the PDF source worker. No producer path opens.
    Complete root/native gates and full prose anchors remain mandatory upstream.
    """
    if original.get("schema_version") != CITATION_SCHEMA or original.get("policy_digest") != canonical_digest(
        CITATION_POLICY
    ):
        raise ValueError("original citation reference policy/schema changed")
    if not isinstance(original.get("run_id"), str) or not original["run_id"]:
        raise ValueError("original citation reference lacks original run identity")
    fresh = observe_natbib_reference(root, directory, **source_arguments)
    return validate_natbib_reference_reproduction(original, reader, fresh)


def validate_natbib_reference_reproduction(
    original: dict[str, Any],
    reader: SnapshotReader,
    fresh: dict[str, Any],
    *,
    fresh_reader: SnapshotReader | None = None,
) -> dict[str, Any]:
    """Validate an already genuine fresh reference; DATA grants no ownership.

    The enclosing caller authenticates both actual Source execution cohorts.
    Sharing this predicate avoids a second identical native citation compile.
    """
    if original.get("schema_version") != CITATION_SCHEMA or original.get("policy_digest") != canonical_digest(
        CITATION_POLICY
    ):
        raise ValueError("original citation reference policy/schema changed")
    if not isinstance(original.get("run_id"), str) or not original["run_id"]:
        raise ValueError("original citation reference lacks original run identity")
    for key in ("artifact_id", "policy_digest", "inputs", "occurrences", "nonvisible", "blockers"):
        if original.get(key) != fresh[key]:
            raise ValueError(f"current source-only citation reference differs from original {key}")
    if not fresh["occurrences"]:
        if original.get("tool_artifacts") != [] or original.get("dependency_custody") is not None:
            raise ValueError("citation-free original source claims unexecuted process/dependency evidence")
        return fresh
    _validate_original_tools(original, reader, fresh, fresh_reader if fresh_reader is not None else reader)
    old = original.get("dependency_custody")
    current = fresh["dependency_custody"]
    if (
        not isinstance(old, dict)
        or old.get("schema_version") != current["schema_version"]
        or old.get("before") != old.get("after")
    ):
        raise ValueError("original citation dependency before/after custody changed")
    if (
        old.get("dependency_identity") != dependency_identity(old["before"])
        or old["dependency_identity"] != current["dependency_identity"]
        or old.get("style_before") != old.get("style_after")
        or dependency_identity([old["style_before"]]) != dependency_identity([current["style_before"]])
    ):
        raise ValueError("reader citation dependency/font/style bytes differ from original reference")
    retained = old.get("retained")
    if not isinstance(retained, list) or len(retained) != len(old["before"]) + 1:
        raise ValueError("original citation retained dependency byte census is incomplete")
    for row, observation in zip(retained, [*old["before"], old["style_before"]], strict=True):
        if {key: row.get(key) for key in ("path", "name", "sha256", "bytes")} != observation:
            raise ValueError("original retained citation dependency observation differs")
        binding = row.get("artifact")
        if not isinstance(binding, dict):
            raise ValueError("original citation dependency bytes are absent")
        snapshot = reader.read(binding["path"])
        if (
            snapshot.sha256 != row["sha256"]
            or snapshot.sha256 != binding["sha256"]
            or len(snapshot.content) != row["bytes"]
        ):
            raise ValueError("original citation dependency/font/style artifact bytes changed")
    return fresh


def inspect_natbib_citations(
    pdf: bytes, rasters: tuple[bytes, ...], reference: dict[str, Any], *, deadline: float
) -> dict[str, Any]:
    """Observe exact ordered citation glyphs, original glyph bounds and 150dpi ink.

    Presentation whitespace is excluded from citation glyph identities. Full
    prose placement and whitespace semantics are separate source obligations.
    Source omissions/changes/order and invisible native glyphs are findings;
    parser/tool/resource failures never count as successful negative controls.
    """
    import pdfplumber
    from PIL import Image

    budget(deadline)
    if reference.get("schema_version") != CITATION_SCHEMA or reference.get("policy_digest") != canonical_digest(
        CITATION_POLICY
    ):
        raise ValueError("citation glyph observer requires an admitted source-only reference")
    if sum(len(content) for content in rasters) > PDF_POLICY["max_raster_bytes"]:
        raise ValueError("citation pixels exceed existing native PDF raster bounds")
    glyphs: list[dict[str, Any]] = []
    chars: list[str] = []
    owners: list[int] = []
    pages = []
    blockers = list(reference["blockers"])
    with pdfplumber.open(BytesIO(pdf)) as document:
        if not document.pages or len(document.pages) > PDF_POLICY["max_pages"] or len(document.pages) != len(rasters):
            raise ValueError("citation observer requires the bounded complete actual page/raster set")
        word_count = chars_total = 0
        for number, page in enumerate(document.pages, 1):
            budget(deadline)
            chars_total += len(page.chars)
            if chars_total > PDF_POLICY["max_chars"]:
                raise ValueError("citation observer exceeds existing native PDF glyph bounds")
            word_count += len(page.extract_words(use_text_flow=True, expand_ligatures=False))
            if word_count > PDF_POLICY["max_words"]:
                raise ValueError("citation observer exceeds existing native PDF word bounds")
            media, crop = list(map(float, page.mediabox)), list(map(float, page.cropbox))
            if not all(math.isfinite(n) for n in (*media, *crop)):
                raise ValueError("citation page/crop geometry is not finite")
            supported = page.rotation == 0 and media[:2] == [0.0, 0.0]
            if not supported:
                blockers.append(f"page {number}: citation glyph geometry needs a rotation/origin projection")
            pages.append({"page": number, "media_box_pt": media, "crop_box_pt": crop, "rotation": page.rotation})
            for char in page.chars:
                if len(glyphs) % 1024 == 0:
                    budget(deadline)
                if len(glyphs) >= PDF_POLICY["max_chars"]:
                    raise ValueError("citation observer exceeds existing native PDF glyph bounds")
                text = _compact(char["text"])
                if not text:
                    continue
                box = [float(char[key]) for key in ("x0", "top", "x1", "bottom")]
                size = float(char["size"])
                if not all(math.isfinite(n) for n in (*box, size)) or box[0] >= box[2] or box[1] >= box[3] or size <= 0:
                    raise ValueError("actual citation glyph has invalid geometry/font metrics")
                owners.extend([len(glyphs)] * len(text))
                chars.extend(text)
                glyphs.append(
                    {
                        "page": number,
                        "box_pt": box,
                        "font_pt": size,
                        "font": str(char["fontname"]),
                        "text": text,
                        "geometry_supported": supported,
                    }
                )
    stream = "".join(chars)
    wrap_hyphens: set[int] = set()
    for index in range(1, len(glyphs) - 1):
        previous, glyph, following = glyphs[index - 1 : index + 2]
        if (
            glyph["text"] == "-"
            and previous["text"][-1:].isalpha()
            and following["text"][:1].isalpha()
            and following["box_pt"][0] < glyph["box_pt"][0]
            and (
                following["page"] == glyph["page"] + 1
                or (
                    following["page"] == glyph["page"]
                    and following["box_pt"][1] > glyph["box_pt"][1] + glyph["font_pt"] * 0.5
                )
            )
        ):
            wrap_hyphens.add(index)
    joined_chars, joined_owners = [], []
    for text_character, owner in zip(chars, owners, strict=True):
        if owner not in wrap_hyphens:
            joined_chars.append(text_character)
            joined_owners.append(owner)
    joined = "".join(joined_chars)
    if unicodedata.normalize("NFC", stream) != stream:
        blockers.append("decomposed citation glyph identities need a composed glyph-owner projection")
    findings, matches, required = [], [], set()
    cursor = 0
    for occurrence in reference["occurrences"]:
        budget(deadline)
        expected = _compact(occurrence["native_text"])
        if not expected or occurrence["tokens"] != list(text_tokens(occurrence["native_text"])):
            raise ValueError("citation occurrence expected native glyph identity is malformed")
        start = bisect_left(owners, cursor)
        index = stream.find(expected, start)
        matched_owners = owners
        used_joined = False
        if index < 0:
            start = bisect_left(joined_owners, cursor)
            index = joined.find(expected, start)
            matched_owners = joined_owners
            used_joined = True
        if index < 0:
            findings.append(
                {
                    "code": "citation.glyph.order"
                    if expected in stream or expected in joined
                    else "citation.glyph.missing",
                    "occurrence_id": occurrence["id"],
                }
            )
            continue
        end = index + len(expected)
        selected = sorted(set(matched_owners[index:end]))
        if used_joined:
            selected += [owner for owner in wrap_hyphens if selected[0] < owner < selected[-1]]
            selected.sort()
        required.update(selected)
        matches.append({"occurrence_id": occurrence["id"], "glyph_span": [index, end], "glyph_indices": selected})
        cursor = selected[-1] + 1
    observed = []
    for number, data in enumerate(rasters, 1):
        budget(deadline)
        page_row = pages[number - 1]
        with Image.open(BytesIO(data)) as image:
            if image.format != "PNG" or image.width * image.height > PDF_POLICY["max_page_pixels"]:
                raise ValueError("citation pixels require bounded actual native PNG pages")
            image.load()
            gray = image.convert("L")
            media = page_row["media_box_pt"]
            if (
                abs(image.width - (media[2] - media[0]) * 150 / 72) > 2
                or abs(image.height - (media[3] - media[1]) * 150 / 72) > 2
            ):
                raise ValueError("citation pixels differ from admitted 150dpi native geometry")
            for index in sorted(required):
                glyph = glyphs[index]
                if glyph["page"] != number:
                    continue
                budget(deadline)
                row = {"glyph_index": index, **glyph}
                if glyph["font_pt"] < PDF_POLICY["min_supported_font_pt"]:
                    findings.append({"code": "citation.layout.font", "glyph_index": index})
                if glyph["geometry_supported"]:
                    x0, top, x1, bottom = glyph["box_pt"]
                    crop, tolerance = page_row["crop_box_pt"], PDF_POLICY["crop_tolerance_pt"]
                    if (
                        x0 < crop[0] - tolerance
                        or top < crop[1] - tolerance
                        or x1 > crop[2] + tolerance
                        or bottom > crop[3] + tolerance
                    ):
                        findings.append({"code": "citation.layout.crop", "glyph_index": index})
                    else:
                        pixels = [
                            max(0, math.floor(x0 * 150 / 72)),
                            max(0, math.floor(top * 150 / 72)),
                            min(image.width, math.ceil(x1 * 150 / 72)),
                            min(image.height, math.ceil(bottom * 150 / 72)),
                        ]
                        if pixels[0] >= pixels[2] or pixels[1] >= pixels[3]:
                            raise ValueError("actual citation glyph has no localized pixel region")
                        region = gray.crop(tuple(pixels))
                        low, high = cast(tuple[int, int], region.getextrema())
                        ink = sum(region.histogram()[: max(0, high - PDF_POLICY["min_word_luminance_range"] + 1)]) / (
                            region.width * region.height
                        )
                        row.update({"roi_px": pixels, "luminance_range": high - low, "ink_fraction": round(ink, 8)})
                        if (
                            high - low < PDF_POLICY["min_word_luminance_range"]
                            or ink < PDF_POLICY["min_word_ink_fraction"]
                        ):
                            findings.append({"code": "citation.visual.invisible", "glyph_index": index})
                observed.append(row)
    budget(deadline)
    return {
        "schema_version": CITATION_OBSERVATION_SCHEMA,
        "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "raster_sha256": [hashlib.sha256(data).hexdigest() for data in rasters],
        "reference_digest": canonical_digest(reference),
        "policy_digest": canonical_digest(PDF_POLICY),
        "observer_versions": {name: version(name) for name in ("pdfplumber", "pdfminer.six", "Pillow")},
        "pages": pages,
        "matches": matches,
        "geometry_wrap_hyphens": sorted(wrap_hyphens),
        "observed_glyphs": observed,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def _main() -> int:
    """Execute a bounded independent reader from an upstream source input bundle."""
    import argparse
    import base64
    import sys

    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.native_format_acceptance_contracts import native_environment

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    args = parser.parse_args()
    budget(args.deadline)
    reader = SnapshotReader(args.root)
    request = reader.read(args.request.relative_to(args.root).as_posix()).json_object()
    original = reader.read(request["reference"]).json_object()
    source = request["inputs"]

    def bindings(name: str) -> tuple[tuple[str, bytes], ...]:
        return tuple((path, base64.b64decode(content, validate=True)) for path, content in source.get(name, []))

    preamble = source.get("preamble")
    kwargs = {
        "ast_bytes": base64.b64decode(source["ast"], validate=True),
        "sources": bindings("sources"),
        "bibliographies": bindings("bibliographies"),
        "config": bindings("config"),
        "preamble": (preamble[0], base64.b64decode(preamble[1], validate=True)) if preamble else None,
        "crossref_keys": tuple(source.get("crossref_keys", [])),
        "run_id": source["run_id"],
        "artifact_id": source["artifact_id"],
        "deadline": args.deadline,
        "env": native_environment(Path(__file__).resolve().parents[2], Path(sys.executable), args.directory),
    }
    fresh = replay_natbib_reference(args.root, args.directory, original, reader, **kwargs)
    if not reader.unchanged():
        raise ValueError("independent reader source/receipt inputs changed during replay")
    write_json(args.root, args.directory / "reader-reference.json", fresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

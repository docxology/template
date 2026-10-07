"""Source-engine mathematical references and native glyph/shape comparisons."""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, cast

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_tex_reference import observe_tex_reference
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-source-scientific-math-v1"


@dataclass(frozen=True)
class ScientificMath:
    identity: str
    source: str
    mode: str
    context: str
    before: str
    after: str


def scientific_math_from_ast(ast_bytes: bytes) -> tuple[ScientificMath, ...]:
    """Account for every original Math node, including notes, headings and cells."""
    if len(ast_bytes) > 4 * 1024 * 1024:
        raise ValueError("source mathematical AST exceeds its byte budget")
    document = json.loads(ast_bytes)
    if not isinstance(document.get("blocks"), list) or not document.get("pandoc-api-version"):
        raise ValueError("scientific math requires actual original Pandoc AST")
    nodes: list[ScientificMath] = []
    count = 0

    def prose(value: Any) -> str:
        if isinstance(value, dict):
            tag = value.get("t")
            content: Any = value.get("c")
            if tag == "Str":
                return str(content)
            if tag in {"Space", "SoftBreak", "LineBreak"}:
                return " "
            if tag in {"Strong", "Emph", "Underline", "SmallCaps"}:
                return "".join(prose(child) for child in content)
            if tag in {"Span", "Link"}:
                return "".join(prose(child) for child in content[1])
        return ""

    def visit(value: Any, path: str, context: str, before: str = "", after: str = "") -> None:
        nonlocal count
        count += 1
        if count > 100_000:
            raise ValueError("source math node budget exceeded")
        if isinstance(value, dict):
            tag = value.get("t")
            if tag == "Math":
                mode = value["c"][0]["t"]
                source = value["c"][1]
                if mode not in {"InlineMath", "DisplayMath"} or not isinstance(source, str) or not source:
                    raise ValueError("invalid source mathematical occurrence")
                nodes.append(ScientificMath(path, source, mode, context, before[-100:], after[:100]))
                return
            if tag == "Header":
                context = f"heading:{value['c'][0]}"
            elif tag == "Note":
                context = "footnote"
            elif tag == "Table":
                context = "table"
            for key, child in value.items():
                visit(child, f"{path}/{key}", context, before, after)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                left = "".join(prose(item) for item in value[:index])
                right = "".join(prose(item) for item in value[index + 1 :])
                visit(child, f"{path}/{index}", context, left or before, right or after)

    visit(document["blocks"], "blocks", "body")
    if len(nodes) > 10_000:
        raise ValueError("source mathematical occurrence budget exceeded")
    return tuple(nodes)


def _math_body(nodes: tuple[ScientificMath, ...]) -> str:
    pieces = []
    for ordinal, node in enumerate(nodes):
        if re.search(r"\\(?:input|include|openin|openout|read|write|catcode|special)\b", node.source):
            raise ValueError("mathematical source expands outside its admitted reference scope")
        begin, end = f"NATIVEBEGIN{ordinal:06d}", f"NATIVEEND{ordinal:06d}"
        equation = (r"\[" + node.source + r"\]") if node.mode == "DisplayMath" else (r"\(" + node.source + r"\)")
        if node.context == "footnote":
            equation = r"{\footnotesize " + equation + "}"
        elif node.context.startswith("heading:"):
            level = int(node.context.split(":")[1])
            command = {1: "section", 2: "subsection", 3: "subsubsection", 4: "paragraph", 5: "subparagraph"}.get(level)
            if command is None:
                raise ValueError("source heading mathematical typography is unsupported")
            equation = "\\" + command + "*{" + equation + "}"
        pieces.append(
            r"\par\noindent " + begin + "\\par\n{" + equation + "}\\par\n\\noindent " + end + "\\par\n\\medskip\n"
        )
    return "".join(pieces)


def observe_scientific_math_reference(
    root: Path,
    directory: Path,
    ast_bytes: bytes,
    inputs: PDFSourceInputs,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Interpret exact source mathematics and declared preamble independently."""
    from infrastructure.rendering._pdf_combined_latex import postprocess_latex
    from infrastructure.rendering._pdf_latex_helpers import extract_preamble
    import yaml

    original_ast = directory / "original-source.ast.json"
    atomic_write_bytes_confined(root, original_ast, ast_bytes, mode=0o600)
    implementation: list[dict[str, Any]] = []
    for ordinal, source_path in enumerate(
        (Path(__file__), Path(cast(str, __import__(observe_tex_reference.__module__, fromlist=["__file__"]).__file__)))
    ):
        source_path = source_path.resolve(strict=True)
        content = source_path.read_bytes()
        retained = directory / "implementation" / f"{ordinal:02d}-{source_path.name}.bin"
        atomic_write_bytes_confined(root, retained, content, mode=0o600)
        implementation.append(
            {
                "original_path": str(source_path),
                "sha256": hashlib.sha256(content).hexdigest(),
                "artifact": {
                    "path": retained.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                },
            }
        )
    nodes = scientific_math_from_ast(ast_bytes)
    if not nodes:
        raise ValueError("scientific math reference contains no source equations")
    blank = json.loads(ast_bytes)
    blank["blocks"], blank["meta"] = [], {}
    template_ast = directory / "template.ast.json"
    atomic_write_bytes_confined(root, template_ast, json.dumps(blank).encode(), mode=0o600)
    arguments = [str(template_ast), "--from=json", "--to=latex", "--standalone"]
    config = yaml.safe_load(inputs.config[1])
    metadata = config.get("metadata", {}) if isinstance(config, dict) else {}
    for name in ("fontsize", "documentclass", "geometry"):
        if metadata.get(name):
            arguments.extend(["-V", f"{name}:{metadata[name]}"])
    tool = native_tool_record(
        root,
        directory,
        "pandoc",
        arguments,
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="math-reference-template",
    )
    process = json.loads(SnapshotReader(root).read(tool["artifact"]["path"]).content)
    if process["exit_code"] != 0 or process["original_exit_code"] != 0:
        raise ValueError("actual declared source math template failed")
    template = process["stdout"]
    if template.count(r"\begin{document}") != 1:
        raise ValueError("actual reference template has no unique document boundary")
    header = template.split(r"\begin{document}", 1)[0]
    declared = ""
    if inputs.preamble:
        copied = directory / "declared-preamble.md"
        atomic_write_bytes_confined(root, copied, inputs.preamble[1], mode=0o600)
        declared = extract_preamble(copied)
    tex = postprocess_latex(
        header + declared + "\n\\begin{document}\n\\pagestyle{empty}\n" + _math_body(nodes) + "\n\\end{document}\n"
    ).encode()
    reference = observe_tex_reference(root, directory, tex, env=env, deadline=deadline, run_id=run_id)
    for row in implementation:
        if hashlib.sha256(Path(row["original_path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("loaded scientific reference implementation changed during execution")
    reference.update(
        {
            "schema_version": SCHEMA,
            "implementation": implementation,
            "source_ast_sha256": hashlib.sha256(ast_bytes).hexdigest(),
            "source_ast": {
                "path": original_ast.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(ast_bytes).hexdigest(),
            },
            "nodes": [asdict(node) for node in nodes],
            "template_tool_artifact": tool["artifact"],
            "source_inputs": [
                {"path": path, "sha256": hashlib.sha256(content).hexdigest()}
                for path, content in (*inputs.sources, inputs.config, *((inputs.preamble,) if inputs.preamble else ()))
            ],
            "blockers": list(inputs.blockers),
        }
    )
    return reference


def _font(glyph: dict[str, Any]) -> str:
    return re.sub(r"^[A-Z]{6}\+", "", str(glyph["fontname"]))


def reference_math_glyphs(pdf_bytes: bytes, nodes: tuple[ScientificMath, ...]) -> tuple[dict[str, Any], ...]:
    """Read exact interpreted math glyphs between source-owned native markers."""
    import pdfplumber

    rows = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as document:
        if not document.pages or len(document.pages) > 500:
            raise ValueError("mathematical reference exceeds its native page budget")
        for ordinal, node in enumerate(nodes):
            begin, end = f"NATIVEBEGIN{ordinal:06d}", f"NATIVEEND{ordinal:06d}"
            candidates = []
            for number, page in enumerate(document.pages, 1):
                words = page.extract_words(use_text_flow=True)
                starts = [word for word in words if word["text"] == begin]
                stops = [word for word in words if word["text"] == end]
                if len(starts) == len(stops) == 1 and starts[0]["bottom"] < stops[0]["top"]:
                    glyphs = [
                        glyph
                        for glyph in page.chars
                        if glyph["top"] >= starts[0]["bottom"] - 0.5
                        and glyph["bottom"] <= stops[0]["top"] + 0.5
                        and glyph["text"].strip()
                    ]
                    candidates.append((number, glyphs))
            if len(candidates) != 1 or not candidates[0][1]:
                raise ValueError("source math reference lost an occurrence or crossed marker page boundaries")
            page_number, glyphs = candidates[0]
            if any(str(glyph["text"]).startswith("(cid:") for glyph in glyphs):
                raise ValueError("source mathematical glyph identity is unresolved")
            box = [
                min(g["x0"] for g in glyphs),
                min(g["top"] for g in glyphs),
                max(g["x1"] for g in glyphs),
                max(g["bottom"] for g in glyphs),
            ]
            rows.append(
                {
                    "identity": node.identity,
                    "page": page_number,
                    "box": box,
                    "glyphs": [
                        {key: glyph[key] for key in ("text", "fontname", "x0", "x1", "top", "bottom", "size")}
                        for glyph in glyphs
                    ],
                }
            )
    return tuple(rows)


def inspect_scientific_pdf_math(
    pdf_bytes: bytes,
    raster_bytes: tuple[bytes, ...],
    nodes: tuple[ScientificMath, ...],
    reference_rows: tuple[dict[str, Any], ...],
    reference_rasters: tuple[bytes, ...],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Compare independently interpreted source glyphs, geometry and actual ink."""
    import pdfplumber
    from PIL import Image, ImageChops, ImageStat

    if (
        len(nodes) != len(reference_rows)
        or not nodes
        or sum(map(len, (*raster_bytes, *reference_rasters))) > 256 * 1024 * 1024
    ):
        raise ValueError("scientific native comparison has incomplete or excessive inputs")
    findings = []
    blockers = [
        f"{node.identity}: source prose anchor placement requires independent full-source replay" for node in nodes
    ]
    blockers.extend(
        f"{node.identity}: table mathematical typography requires native cell geometry"
        for node in nodes
        if node.context == "table"
    )
    observations = []
    cursor = (0, 0)
    with pdfplumber.open(BytesIO(pdf_bytes)) as document:
        if not document.pages or len(document.pages) != len(raster_bytes) or len(document.pages) > 500:
            raise ValueError("scientific comparison requires every original native page")
        pages = []
        total = 0
        for page in document.pages:
            glyphs = [glyph for glyph in page.chars if glyph["text"].strip()]
            total += len(glyphs)
            if total > 2_000_000:
                raise ValueError("scientific comparison exceeds native glyph budget")
            pages.append((page, glyphs))
        for node, reference in zip(nodes, reference_rows, strict=True):
            if time.monotonic() >= deadline:
                raise TimeoutError("scientific math exhausted its original deadline")
            if reference["identity"] != node.identity:
                raise ValueError("mathematical reference occurrence identity differs")
            expected = reference["glyphs"]
            keys = [(str(glyph["text"]), _font(glyph)) for glyph in expected]
            candidates = []
            for page_number, (page, glyphs) in enumerate(pages):
                actual_keys = [(str(glyph["text"]), _font(glyph)) for glyph in glyphs]
                for start in range(len(glyphs) - len(keys) + 1):
                    if actual_keys[start : start + len(keys)] == keys:
                        if node.context != "footnote" and (page_number, start) < cursor:
                            continue
                        candidates.append((page_number, start, glyphs[start : start + len(keys)]))
            if len(candidates) != 1:
                findings.append({"code": "pdf.math.source", "identity": node.identity, "candidates": len(candidates)})
                continue
            page_number, start, glyphs = candidates[0]
            if node.context != "footnote":
                cursor = (page_number, start + len(glyphs))
            page = pages[page_number][0]
            box = [
                min(g["x0"] for g in glyphs),
                min(g["top"] for g in glyphs),
                max(g["x1"] for g in glyphs),
                max(g["bottom"] for g in glyphs),
            ]
            if page.rotation != 0 or page.mediabox[:2] != (0, 0):
                blockers.append(f"{node.identity}: unsupported native rotated/origin equation geometry")
                continue
            if any(
                not math.isfinite(float(value))
                for glyph in glyphs
                for value in (glyph["x0"], glyph["x1"], glyph["top"], glyph["bottom"], glyph["size"])
            ):
                raise ValueError("actual mathematical glyph geometry is not finite")
            scale = max(g["size"] for g in glyphs) / max(g["size"] for g in expected)
            if abs(scale - 1) > 0.02:
                findings.append({"code": "pdf.math.font", "identity": node.identity})
            geometry_error = max(
                abs((actual[key] - box[axis]) - (wanted[key] - reference["box"][axis]) * scale)
                for actual, wanted in zip(glyphs, expected, strict=True)
                for key, axis in (("x0", 0), ("x1", 0), ("top", 1), ("bottom", 1))
            )
            if geometry_error > 0.6:
                findings.append({"code": "pdf.math.geometry", "identity": node.identity})
            with (
                Image.open(BytesIO(raster_bytes[page_number])) as native,
                Image.open(BytesIO(reference_rasters[reference["page"] - 1])) as original,
            ):
                if (
                    native.format != "PNG"
                    or original.format != "PNG"
                    or max(native.width * native.height, original.width * original.height) > 60_000_000
                ):
                    raise ValueError("scientific comparison requires bounded actual PNG pixels")
                if abs(native.width - page.width * 150 / 72) > 2 or abs(native.height - page.height * 150 / 72) > 2:
                    raise ValueError("scientific native pixels lack exact 150dpi page geometry")
                native_box = tuple(int(value * 150 / 72) for value in box)
                reference_box = tuple(int(value * 150 / 72) for value in reference["box"])
                if (
                    min(native_box) < 0
                    or native_box[2] > native.width
                    or native_box[3] > native.height
                    or native_box[0] >= native_box[2]
                    or native_box[1] >= native_box[3]
                ):
                    findings.append({"code": "pdf.math.crop", "identity": node.identity})
                    continue
                native_region = native.crop(cast(tuple[int, int, int, int], native_box)).convert("L")
                source_region = (
                    original.crop(cast(tuple[int, int, int, int], reference_box))
                    .convert("L")
                    .resize(native_region.size)
                )
                low, high = cast(tuple[int, int], native_region.getextrema())
                if high - low < 32:
                    findings.append({"code": "pdf.math.invisible", "identity": node.identity})
                errors = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        shifted = Image.new("L", source_region.size, 255)
                        shifted.paste(source_region, (dx, dy))
                        errors.append(ImageStat.Stat(ImageChops.difference(native_region, shifted)).mean[0])
                pixel_error = min(errors)
                if pixel_error > 12:
                    findings.append({"code": "pdf.math.pixels", "identity": node.identity})
            observations.append(
                {
                    "identity": node.identity,
                    "source": node.source,
                    "page": page_number + 1,
                    "glyph_start": start,
                    "glyph_count": len(glyphs),
                    "geometry_error_pt": geometry_error,
                    "scale": scale,
                    "pixel_error": pixel_error,
                }
            )
    return {
        "schema_version": SCHEMA,
        "source_nodes": [asdict(node) for node in nodes],
        "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "raster_sha256": [hashlib.sha256(item).hexdigest() for item in raster_bytes],
        "observations": observations,
        "findings": findings,
        "blockers": blockers,
        "status": "blocked" if blockers else "fail" if findings else "pass",
    }

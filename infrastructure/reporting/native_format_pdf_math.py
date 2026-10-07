"""Independent source algebra and anchored native PDF equation observations.

This finite grammar admits inline atoms, signs, digits and single scripts. It
never drops unknown TeX, display equations, references or unanchored occurrences.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Any, cast

from infrastructure.reporting.native_format_content_contracts import MAX_SOURCE_BYTES

SCHEMA = "template-native-pdf-anchored-math-v1"
_SYMBOLS = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "lambda": "λ",
    "mu": "μ",
    "pi": "π",
    "sigma": "σ",
    "rho": "ρ",
    "times": "×",
    "cdot": "·",
    "pm": "±",
    "geq": "≥",
    "leq": "≤",
    "approx": "≈",
    "to": "→",
    "rightarrow": "→",
    "in": "∈",
    "infty": "∞",
    "ast": "∗",
    "star": "⋆",
}


@dataclass(frozen=True)
class MathAtom:
    value: str
    role: str = "baseline"
    group: int | None = None


@dataclass(frozen=True)
class AnchoredEquation:
    identity: str
    source: str
    before: str
    after: str
    atoms: tuple[MathAtom, ...]
    blockers: tuple[str, ...]


def _compact(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace("−", "-")
    return "".join(text.split())


def parse_inline_algebra(source: str) -> tuple[MathAtom, ...]:
    """Parse every source byte into a finite independent algebra obligation."""
    if len(source) > 4096:
        raise ValueError("inline algebra exceeds its source budget")
    atoms: list[MathAtom] = []
    position = 0
    fraction_group = 0

    def atom(role: str, group: int | None = None) -> None:
        nonlocal position
        if position >= len(source):
            raise ValueError("incomplete mathematical atom")
        character = source[position]
        if character == "\\":
            match = re.match(r"\\([A-Za-z]+)", source[position:])
            if match is None or match[1] not in _SYMBOLS:
                raise ValueError("unsupported mathematical command")
            position += len(match[0])
            value = _SYMBOLS[match[1]]
        elif character.isascii() and (character.isalnum() or character in "+-=().,[]<>|/:!"):
            position += 1
            value = character
        else:
            raise ValueError("unsupported mathematical atom")
        atoms.append(MathAtom(value, role, group))

    while position < len(source):
        if source[position].isspace():
            position += 1
            continue
        fraction = re.match(r"\\(?:tfrac|frac)(?![A-Za-z])", source[position:])
        if fraction:
            position += len(fraction[0])
            for role in ("numerator", "denominator"):
                while position < len(source) and source[position].isspace():
                    position += 1
                grouped = position < len(source) and source[position] == "{"
                if grouped:
                    position += 1
                atom(role, fraction_group)
                if grouped:
                    if position >= len(source) or source[position] != "}":
                        raise ValueError("only one-atom fraction terms are admitted")
                    position += 1
            fraction_group += 1
        elif source[position] in "^_":
            if not atoms or atoms[-1].role != "baseline":
                raise ValueError("unsupported nested or repeated script")
            role = "superscript" if source[position] == "^" else "subscript"
            position += 1
            grouped = position < len(source) and source[position] == "{"
            if grouped:
                position += 1
            start = len(atoms)
            atom(role)
            if grouped:
                if position >= len(source) or source[position] != "}":
                    raise ValueError("only one-atom scripts are admitted")
                position += 1
            if len(atoms) != start + 1:
                raise ValueError("script obligation is not atomic")
        else:
            atom("baseline")
    if not atoms:
        raise ValueError("equation has no mathematical atoms")
    return tuple(atoms)


def anchored_equations_from_ast(ast_bytes: bytes) -> tuple[AnchoredEquation, ...]:
    """Compile occurrence identities and adjacent text from actual Pandoc AST."""
    if len(ast_bytes) > MAX_SOURCE_BYTES:
        raise ValueError("mathematical AST exceeds its byte budget")
    document = json.loads(ast_bytes)
    if (
        not isinstance(document, dict)
        or not isinstance(document.get("blocks"), list)
        or not document.get("pandoc-api-version")
    ):
        raise ValueError("equations require a genuine Pandoc document")
    equations: list[AnchoredEquation] = []
    anchored_nodes: set[int] = set()
    count = 0

    def paragraph(nodes: list[dict[str, Any]]) -> None:
        pieces: list[str | dict[str, Any]] = []

        def inline(node: dict[str, Any]) -> None:
            tag = node.get("t")
            content: Any = node.get("c")
            if tag == "Str":
                pieces.append(content)
            elif tag in {"Space", "SoftBreak", "LineBreak"}:
                pieces.append(" ")
            elif tag in {"Emph", "Strong", "Underline", "SmallCaps"}:
                for child in content:
                    inline(child)
            elif tag in {"Span", "Link", "Cite"}:
                for child in content[1]:
                    inline(child)
            elif tag == "Math":
                pieces.append(node)
            else:
                # Unknown nodes interrupt anchors rather than silently vanishing.
                pieces.append({"t": "Unsupported"})

        for node in nodes:
            inline(node)
        for index, piece in enumerate(pieces):
            if not isinstance(piece, dict) or piece.get("t") != "Math":
                continue
            before: list[str] = []
            after: list[str] = []
            for previous in reversed(pieces[:index]):
                if not isinstance(previous, str):
                    break
                before.insert(0, previous)
            for following in pieces[index + 1 :]:
                if not isinstance(following, str):
                    break
                after.append(following)
            anchored_nodes.add(id(piece))
            source = piece["c"][1]
            blockers = []
            try:
                atoms = parse_inline_algebra(source)
            except ValueError as error:
                atoms = ()
                blockers.append(str(error))
            left, right = _compact("".join(before))[-80:], _compact("".join(after))[:80]
            if piece["c"][0].get("t") != "InlineMath":
                blockers.append("display equation geometry requires separate observation")
            if len(left) < 3 or not right:
                blockers.append("equation lacks independent adjacent text anchors")
            equations.append(AnchoredEquation(f"math:{len(equations)}", source, left, right, atoms, tuple(blockers)))

    def visit(value: Any) -> None:
        nonlocal count
        count += 1
        if count > 100_000:
            raise ValueError("mathematical AST exceeds its node budget")
        if isinstance(value, dict):
            if value.get("t") in {"Para", "Plain"}:
                paragraph(value["c"])
            else:
                for child in value.values():
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(document["blocks"])

    def account(value: Any) -> None:
        nonlocal count
        count += 1
        if count > 200_000:
            raise ValueError("complete mathematical accounting exceeds node budget")
        if isinstance(value, dict):
            if value.get("t") == "Math" and id(value) not in anchored_nodes:
                equations.append(
                    AnchoredEquation(
                        f"math:{len(equations)}",
                        value["c"][1],
                        "",
                        "",
                        (),
                        ("math outside independently anchorable paragraph",),
                    )
                )
            for child in value.values():
                account(child)
        elif isinstance(value, list):
            for child in value:
                account(child)

    account(document["blocks"])
    return tuple(equations)


def inspect_anchored_pdf_math(
    pdf_bytes: bytes, rasters: tuple[bytes, ...], equations: tuple[AnchoredEquation, ...], *, deadline: float
) -> dict[str, Any]:
    """Check source atoms, native glyph positions and localized actual ink.

    Anchors must uniquely identify a same-line equation occurrence. Baseline and
    script relations come from the independent grammar, never renderer output.
    """
    import pdfplumber
    from PIL import Image

    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("mathematical observation deadline expired")
    if sum(len(item) for item in rasters) > 256 * 1024 * 1024:
        raise ValueError("mathematical raster-byte budget exceeded")
    rows = []
    blockers: list[str] = []
    if not equations:
        blockers.append("no independently anchored mathematical obligations")
    findings: list[dict[str, Any]] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as document:
        if not document.pages or len(document.pages) > 500 or len(rasters) != len(document.pages):
            raise ValueError("math observation requires every actual PDF page raster")
        pages = []
        total = 0
        for page in document.pages:
            total += len(page.chars)
            if total > 2_000_000:
                raise ValueError("math observation exceeds glyph budget")
            characters = []
            owners = []
            for index, glyph in enumerate(page.chars):
                for character in _compact(glyph["text"]):
                    characters.append(character)
                    owners.append(index)
            pages.append(("".join(characters), owners, page))
        for equation in equations:
            if time.monotonic() >= deadline:
                raise TimeoutError("mathematical observation deadline expired")
            blockers.extend(f"{equation.identity}: {item}" for item in equation.blockers)
            if equation.blockers:
                continue
            candidates = []
            for number, (text, owners, page) in enumerate(pages):
                start = text.find(equation.before)
                while start >= 0:
                    end_before = start + len(equation.before)
                    end = text.find(equation.after, end_before)
                    if end >= 0 and end - end_before <= 4096:
                        candidates.append((number, end_before, end, owners, page, text[end_before:end]))
                    start = text.find(equation.before, start + 1)
            if len(candidates) != 1:
                findings.append(
                    {"code": "pdf.math.anchor", "identity": equation.identity, "candidates": len(candidates)}
                )
                continue
            number, start, end, owners, page, actual = candidates[0]
            expected = _compact("".join(atom.value for atom in equation.atoms))
            row: dict[str, Any] = {
                "identity": equation.identity,
                "source": equation.source,
                "page": number + 1,
                "expected": expected,
                "actual": actual,
            }
            rows.append(row)
            normalized_actual = "".join(
                unicodedata.normalize("NFKC", character) if 0x1D400 <= ord(character) <= 0x1D7FF else character
                for character in actual
            )
            row["normalized_actual"] = normalized_actual
            if normalized_actual != expected:
                findings.append({"code": "pdf.math.content", "identity": equation.identity})
                continue
            glyphs = [page.chars[index] for index in owners[start:end]]
            baseline = [glyph for atom, glyph in zip(equation.atoms, glyphs, strict=True) if atom.role == "baseline"]
            if any(
                not math.isfinite(float(glyph[key]))
                for glyph in glyphs
                for key in ("x0", "x1", "top", "bottom", "size")
            ):
                raise ValueError("mathematical native glyph geometry is not finite")
            if not baseline:
                baseline = [page.chars[owners[start - 1]]]
            centers = [(float(glyph["top"]) + float(glyph["bottom"])) / 2 for glyph in baseline]
            if not centers or max(centers) - min(centers) > max(float(glyph["size"]) for glyph in baseline) * 0.6:
                blockers.append(f"{equation.identity}: multiline/native equation geometry unsupported")
                continue
            center = sum(centers) / len(centers)
            size = max(float(glyph["size"]) for glyph in baseline)
            if min(float(glyph["size"]) for glyph in baseline) < 9:
                findings.append({"code": "pdf.math.font", "identity": equation.identity})
            fractions: dict[int, dict[str, dict[str, Any]]] = {}
            for atom, glyph in zip(equation.atoms, glyphs, strict=True):
                if atom.group is not None:
                    fractions.setdefault(atom.group, {})[atom.role] = glyph
            for terms in fractions.values():
                numerator, denominator = terms["numerator"], terms["denominator"]
                if float(numerator["bottom"]) >= float(denominator["top"]) or min(
                    float(numerator["x1"]), float(denominator["x1"])
                ) <= max(float(numerator["x0"]), float(denominator["x0"])):
                    findings.append({"code": "pdf.math.fraction", "identity": equation.identity})
            previous = None
            previous_group = None
            for atom, glyph in zip(equation.atoms, glyphs, strict=True):
                glyph_center = (float(glyph["top"]) + float(glyph["bottom"])) / 2
                if atom.role == "superscript" and (
                    glyph_center >= center - size * 0.12 or float(glyph["size"]) >= size * 0.95
                ):
                    findings.append({"code": "pdf.math.script", "identity": equation.identity})
                if atom.role == "subscript" and (
                    glyph_center <= center + size * 0.05 or float(glyph["size"]) >= size * 0.95
                ):
                    findings.append({"code": "pdf.math.script", "identity": equation.identity})
                if (
                    previous is not None
                    and not (atom.group is not None and atom.group == previous_group)
                    and float(glyph["x0"]) < previous - 0.5
                ):
                    findings.append({"code": "pdf.math.order", "identity": equation.identity})
                previous = float(glyph["x0"])
                previous_group = atom.group
            with Image.open(BytesIO(rasters[number])) as image:
                if image.format != "PNG" or image.width * image.height > 60_000_000 or page.rotation != 0:
                    raise ValueError("mathematical pixel input lacks bounded native PNG geometry")
                if abs(image.width - page.width * 150 / 72) > 2 or abs(image.height - page.height * 150 / 72) > 2:
                    raise ValueError("mathematical pixels must have actual 150dpi page geometry")
                image.load()
                bars = []
                for terms in fractions.values():
                    numerator, denominator = terms["numerator"], terms["denominator"]
                    left = min(float(numerator["x0"]), float(denominator["x0"]))
                    right = max(float(numerator["x1"]), float(denominator["x1"]))
                    top, bottom = float(numerator["bottom"]), float(denominator["top"])
                    if top >= bottom:
                        continue
                    box = (
                        max(0, int(left * 150 / 72)),
                        max(0, int(top * 150 / 72)),
                        min(image.width, int(right * 150 / 72)),
                        min(image.height, int(bottom * 150 / 72)),
                    )
                    if box[0] >= box[2] or box[1] >= box[3]:
                        findings.append({"code": "pdf.math.fraction", "identity": equation.identity})
                        continue
                    region = image.crop(box).convert("L")
                    rows_ink = [
                        sum(cast(int, region.getpixel((x, y))) < 128 for x in range(region.width)) / region.width
                        for y in range(region.height)
                    ]
                    longest = max(rows_ink, default=0)
                    bars.append(longest)
                    if longest < 0.8:
                        findings.append({"code": "pdf.math.fraction_bar", "identity": equation.identity})
                row["fraction_bar_coverage"] = bars
                ink = []
                for glyph in glyphs:
                    glyph_box = tuple(int(float(glyph[key]) * 150 / 72) for key in ("x0", "top", "x1", "bottom"))
                    if (
                        glyph_box[0] < 0
                        or glyph_box[1] < 0
                        or glyph_box[2] > image.width
                        or glyph_box[3] > image.height
                        or glyph_box[0] >= glyph_box[2]
                        or glyph_box[1] >= glyph_box[3]
                    ):
                        findings.append({"code": "pdf.math.crop", "identity": equation.identity})
                        continue
                    region = image.crop(cast(tuple[int, int, int, int], glyph_box)).convert("L")
                    low, high = cast(tuple[int, int], region.getextrema())
                    ink.append(high - low)
                    if high - low < 32:
                        findings.append({"code": "pdf.math.invisible", "identity": equation.identity})
                row["ink_ranges"] = ink
                row["glyphs"] = [
                    {key: glyph[key] for key in ("text", "x0", "top", "x1", "bottom", "size")} for glyph in glyphs
                ]
    return {
        "schema_version": SCHEMA,
        "input_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "raster_sha256": [hashlib.sha256(item).hexdigest() for item in rasters],
        "normalization": "NFC and mathematical-alphanumeric U+1D400..U+1D7FF logical characters; U+2212 minus",
        "source_equations": [asdict(item) for item in equations],
        "observations": rows,
        "blockers": blockers,
        "findings": findings,
        "status": "blocked" if blockers else "fail" if findings else "pass",
    }

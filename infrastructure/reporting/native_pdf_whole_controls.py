"""Complete Source/page control requirements and actual native PDF mutations.

Requirements and mutated bytes are DATA. Original SDK child execution, signed
OS result and independently current predicate replay are required separately.
"""

from __future__ import annotations

import hashlib
import math
from io import BytesIO
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_pdf_semantic_plan import PDFSemanticPlan
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams

SCHEMA = "template-native-whole-pdf-control-requirements-v2"


def _box(value: Any) -> list[float]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 4
        or any(type(number) not in (int, float) or not math.isfinite(number) for number in value)
        or value[0] >= value[2]
        or value[1] >= value[3]
    ):
        raise ValueError("whole PDF control requires a complete finite positive actual box")
    return list(map(float, value))


def compile_whole_pdf_control_requirements(
    plan: PDFSemanticPlan,
    witness: dict[str, Any],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Select every original page, literal block and scientific occurrence.

    A missing supported native position stays an explicit required row. The
    caller cannot pass a selected subset or a claimed fulfilled control list.
    """
    remaining(deadline)
    if witness.get("source_plan_digest") != plan.digest:
        raise ValueError("whole PDF controls require the exact complete Source occurrence witness")
    literal = witness["literal"]
    pages = literal["pages"]
    if not 1 <= len(pages) <= 500 or [row["page"] for row in pages] != list(range(1, len(pages) + 1)):
        raise ValueError("whole PDF controls omitted original page identities")
    rows: list[dict[str, Any]] = [
        {
            "identity": "baseline",
            "mutation": "baseline",
            "target": None,
            "intended_diagnostic": None,
            "unsupported": None,
            "source_category": None,
            "source_identity": None,
        }
    ]
    for page in pages:
        remaining(deadline)
        rows.append(
            {
                "identity": f"page:{page['page']}:rotation",
                "mutation": "page-rotation",
                "target": {"page": page["page"]},
                "intended_diagnostic": "pdf.reference.layout",
                "unsupported": None,
                "source_category": None,
                "source_identity": None,
            }
        )
    positions: dict[str, list[dict[str, Any]]] = {}
    for category, component, blocks in (("text", literal, plan.text), ("note", witness.get("notes"), plan.notes)):
        if component is None:
            continue
        words = {row["word_index"]: row for row in component["supported_words"]}
        matches = {row["block_id"]: row for row in component["matches"]}
        for block in blocks:
            match = matches.get(block.id)
            if match is not None:
                positions[category + ":" + block.id] = [
                    {"page": words[index]["page"], "box_pt": _box(words[index]["box_pt"])}
                    for index in match["word_indices"]
                ]
    for component, key in ((witness["figures"], "figures"), (witness.get("equations"), "observations")):
        if component is not None:
            for row in component[key]:
                if row.get("covered", True) and "page" in row and "box_pt" in row:
                    positions["occurrence:" + row["identity"]] = [{"page": row["page"], "box_pt": _box(row["box_pt"])}]
    from infrastructure.reporting.native_pdf_whole_semantic_references import citation_occurrence_positions

    positions.update(
        {
            identity: [{"page": row["page"], "box_pt": _box(row["box_pt"])} for row in rows]
            for identity, rows in citation_occurrence_positions(
                plan, witness.get("citations"), deadline=deadline
            ).items()
        }
    )
    for role in witness.get("literal_roles", {}).get("observations", []):
        positions["occurrence:" + role["identity"]] = [
            {"page": word["page"], "box_pt": _box(word["box_pt"])} for word in role["words"]
        ]
    selected_source = [("text", block.id) for block in plan.text]
    selected_source.extend(("note", block.id) for block in plan.notes)
    selected_source.extend(("occurrence", row["identity"]) for row in plan.occurrences)
    # CodeBlock deliberately has both a literal ContentBlock and scientific
    # Source occurrence at the same path. Retain both roles, using the exact
    # literal position only for this explicitly compiled same-Source alias.
    literal_ids = {"text": {block.id for block in plan.text}, "note": {block.id for block in plan.notes}}
    for occurrence in plan.occurrences:
        remaining(deadline)
        if occurrence["kind"] == "CodeBlock":
            categories = [
                category for category, identities in literal_ids.items() if occurrence["identity"] in identities
            ]
            if len(categories) > 1:
                raise ValueError("whole PDF CodeBlock has ambiguous complete literal/note Source membership")
            if categories:
                position = positions.get(categories[0] + ":" + occurrence["identity"])
                if position:
                    positions["occurrence:" + occurrence["identity"]] = position
    for table in plan.tables:
        for row in table["rows"]:
            selected_source.extend(("table-cell", cell["identity"]) for cell in row["cells"])
    for row in witness["tables"]["rows"]:
        for cell in row["cells"]:
            positions["table-cell:" + cell["identity"]] = [{"page": cell["page"], "box_pt": _box(cell["box_pt"])}]
    identities = [category + ":" + identity for category, identity in selected_source]
    if len(set(identities)) != len(identities) or len(identities) > 100_000:
        raise ValueError("whole PDF control Source occurrence roster is ambiguous or excessive")
    for category, source_identity in selected_source:
        remaining(deadline)
        identity = category + ":" + source_identity
        target = positions.get(identity)
        rows.append(
            {
                "identity": identity + ":paint",
                "mutation": "occurrence-white-paint",
                "target": target,
                "intended_diagnostic": "pdf.reference.pixels",
                "unsupported": None if target else "exact independently admitted native occurrence box is absent",
                "source_category": category,
                "source_identity": source_identity,
            }
        )
    body = {
        "schema_version": SCHEMA,
        "source_plan_digest": plan.digest,
        "pdf_sha256": witness["pdf_sha256"],
        "ordered_pages": [row["page"] for row in pages],
        "ordered_source_occurrences": identities,
        "controls": rows,
        "remaining": [
            "fixed SDK original whole-PDF child supervisor and actual signed OS results",
            "independently current complete Source/native control predicate replay",
        ],
    }
    return {**body, "content_digest": canonical_digest(body)}


def mutate_whole_pdf_native(original: bytes, requirements: dict[str, Any], identity: str, *, deadline: float) -> bytes:
    """Alter actual selected original PDF bytes; never synthesize a receipt.

    The complete original supervisor must establish the intended actual pixel
    or geometry change. A no-op, parser/setup/custody failure or missing native
    position cannot be counted as detection of a semantic/native control.
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, ContentStream, DecodedStreamObject, NameObject

    remaining(deadline)
    if (
        requirements.get("schema_version") != SCHEMA
        or hashlib.sha256(original).hexdigest() != requirements["pdf_sha256"]
    ):
        raise ValueError("whole PDF mutation differs from its exact original Source/native declaration")
    selected = [row for row in requirements["controls"] if row["identity"] == identity]
    if len(selected) != 1 or selected[0]["unsupported"] is not None:
        raise ValueError("whole PDF original control is missing, ambiguous or explicitly unsupported")
    control = selected[0]
    if control["mutation"] == "baseline":
        return original
    preflight_pdf_streams(original, deadline=deadline, max_objects=4_000_000)
    reader = PdfReader(BytesIO(original), strict=True)
    if list(range(1, len(reader.pages) + 1)) != requirements["ordered_pages"]:
        raise ValueError("whole PDF original control omitted actual pages")
    writer = PdfWriter()
    writer.append(reader)
    if control["mutation"] == "page-rotation":
        page = writer.pages[control["target"]["page"] - 1]
        # 180 degrees preserves encoded raster dimensions, so the original
        # supervisor can reach the native parity predicate without a rotated
        # width/height setup refusal replacing the intended layout diagnostic.
        page.rotate(180)
    elif control["mutation"] == "occurrence-white-paint":
        isolated_pages: set[int] = set()
        for target in control["target"]:
            remaining(deadline)
            page = writer.pages[target["page"] - 1]
            if (
                int(page.get("/Rotate", 0)) != 0
                or list(page.mediabox)[:2] != [0, 0]
                or page.get("/UserUnit", 1) != 1
                or list(page.cropbox) != list(page.mediabox)
            ):
                raise ValueError("whole PDF occurrence mutation requires admitted zero-origin unrotated geometry")
            if target["page"] not in isolated_pages:
                existing = page.raw_get("/Contents")
                operations = ContentStream(existing, writer).operations
                if len(operations) > 4_000_000:
                    raise ValueError("whole PDF original graphics stream exceeds its finite operation budget")
                depth = 0
                for _, operator in operations:
                    remaining(deadline)
                    if operator == b"q":
                        depth += 1
                        if depth > 4096:
                            raise ValueError("whole PDF original graphics state exceeds its finite stack budget")
                    elif operator == b"Q":
                        depth -= 1
                        if depth < 0:
                            raise ValueError("whole PDF original graphics state underflows")
                if depth:
                    raise ValueError("whole PDF original graphics state is unbalanced")
                before, after = DecodedStreamObject(), DecodedStreamObject()
                before.set_data(b"q\n")
                after.set_data(b"Q\n")
                resolved = existing.get_object()
                elements = list(resolved) if isinstance(resolved, ArrayObject) else [existing]
                page[NameObject("/Contents")] = ArrayObject(
                    [writer._add_object(before), *elements, writer._add_object(after)]
                )
                isolated_pages.add(target["page"])
            x0, top, x1, bottom = _box(target["box_pt"])
            height = float(page.mediabox.height)
            stream = DecodedStreamObject()
            stream.set_data(f"q 1 1 1 rg {x0} {height - bottom} {x1 - x0} {bottom - top} re f Q\n".encode())
            existing = page.raw_get("/Contents")
            resolved = existing.get_object()
            elements = list(resolved) if isinstance(resolved, ArrayObject) else [existing]
            page[NameObject("/Contents")] = ArrayObject([*elements, writer._add_object(stream)])
    else:
        raise ValueError("unknown Source whole PDF mutation")
    output = BytesIO()
    writer.write(output)
    remaining(deadline)
    changed = output.getvalue()
    if changed == original:
        raise ValueError("whole PDF native mutation changed no actual bytes")
    return changed

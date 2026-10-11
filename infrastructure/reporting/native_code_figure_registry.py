"""Independent complete Code exemplar registry reconstruction from held Source.

Only this fixed Source adapter is implemented. Other scopes, scientific figure
truth and original per-leaf native/process consumption remain obligations.
Neither registry JSON nor a caller callback may choose the figure declaration.
"""

from __future__ import annotations

import ast
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.documentation.figure_manager import FigureMetadata
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCOPE = "templates/template_code_project"
SOURCE = f"projects/{SCOPE}/src/template_code_project/analysis/scientific_reports.py"
REGISTRY = f"projects/{SCOPE}/output/figures/figure_registry.json"


def declared_code_figure_registry(source_bytes: bytes) -> dict[str, dict[str, Any]]:
    """Derive all labels/filenames/captions/alt text from the fixed Source role."""
    if not isinstance(source_bytes, bytes) or len(source_bytes) > 1024 * 1024:
        raise ValueError("Code figure declarations need bounded exact Source bytes")
    tree = ast.parse(source_bytes)
    functions = [row for row in tree.body if isinstance(row, ast.FunctionDef) and row.name == "register_figure"]
    if len(functions) != 1:
        raise ValueError("Code Source omitted/repeated its complete figure registry producer")
    function = functions[0]
    declarations = [
        row.value
        for row in ast.walk(function)
        if isinstance(row, ast.Assign)
        and len(row.targets) == 1
        and isinstance(row.targets[0], ast.Name)
        and row.targets[0].id == "figures"
    ]
    if len(declarations) != 1 or not isinstance(declarations[0], ast.List):
        raise ValueError("Code Source figure roster is not its complete unique literal declaration")
    items = ast.literal_eval(declarations[0])
    if not isinstance(items, list) or not items or len(items) > 1000:
        raise ValueError("Code Source figure roster is absent or exceeds its held declaration ceiling")
    registrations = [
        row
        for row in ast.walk(function)
        if isinstance(row, ast.Call) and isinstance(row.func, ast.Attribute) and row.func.attr == "register_figure"
    ]
    if len(registrations) != 1 or registrations[0].args:
        raise ValueError("Code Source figure producer changed its exact real registration role")
    loops = [row for row in ast.walk(function) if isinstance(row, (ast.For, ast.AsyncFor))]
    if (
        len(loops) != 1
        or not isinstance(loops[0], ast.For)
        or not isinstance(loops[0].iter, ast.Name)
        or loops[0].iter.id != "figures"
        or not isinstance(loops[0].target, ast.Tuple)
        or [row.id if isinstance(row, ast.Name) else None for row in loops[0].target.elts]
        != ["filename", "caption", "label", "alt_text"]
        or loops[0].orelse
        or len(loops[0].body) != 2
        or not isinstance(loops[0].body[0], ast.Expr)
        or loops[0].body[0].value is not registrations[0]
        or not isinstance(registrations[0].func, ast.Attribute)
        or not isinstance(registrations[0].func.value, ast.Name)
        or registrations[0].func.value.id != "fm"
    ):
        raise ValueError("Code Source registry must consume every declared figure once in actual Source order")
    resets = {
        row.targets[0].attr: row.value
        for row in ast.walk(function)
        if isinstance(row, ast.Assign)
        and len(row.targets) == 1
        and isinstance(row.targets[0], ast.Attribute)
        and isinstance(row.targets[0].value, ast.Name)
        and row.targets[0].value.id == "fm"
    }
    if set(resets) != {"figures", "counter"} or any(
        ast.literal_eval(resets[key]) != value for key, value in (("figures", {}), ("counter", 0))
    ):
        raise ValueError("Code Source registry must reset its complete owned label and ID namespace")
    actual = {keyword.arg: keyword.value for keyword in registrations[0].keywords}
    expected_names = {"filename": "filename", "caption": "caption", "label": "label"}
    if (
        set(actual) != {"filename", "caption", "label", "section", "generated_by", "metadata"}
        or any(
            not isinstance(node, ast.Name) or node.id != name
            for key, name in expected_names.items()
            for node in (actual[key],)
        )
        or ast.literal_eval(actual["section"]) != "Results"
        or ast.literal_eval(actual["generated_by"]) != "optimization_analysis.py"
    ):
        raise ValueError("Code Source figure registration changed its complete field/role mapping")
    metadata = actual["metadata"]
    if (
        not isinstance(metadata, ast.Dict)
        or [ast.literal_eval(key) if key is not None else None for key in metadata.keys] != ["alt_text", "source"]
        or not isinstance(metadata.values[0], ast.Name)
        or metadata.values[0].id != "alt_text"
        or ast.literal_eval(metadata.values[1]) != "template_code_project analysis pipeline"
    ):
        raise ValueError("Code Source figure registration changed its exact alt/source mapping")
    result = {}
    filenames = set()
    for ordinal, row in enumerate(items):
        if (
            not isinstance(row, tuple)
            or len(row) != 4
            or any(not isinstance(value, str) or not value for value in row)
            or row[2] in result
            or row[0] in filenames
        ):
            raise ValueError("Code Source figure declaration omitted/repeated a complete typed figure")
        filename, caption, label, alt = row
        result[label] = FigureMetadata(
            figure_id=f"figure_{ordinal:03d}",
            filename=filename,
            caption=caption,
            label=label,
            section="Results",
            generated_by="optimization_analysis.py",
            metadata={"alt_text": alt, "source": "template_code_project analysis pipeline"},
        ).to_dict()
        filenames.add(filename)
    return result


def reconstruct_code_figure_registry(
    source: NativeSourceContext,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Compare the entire actual registry and every figure with genuine Source.

    This returns a deterministic graph node only; it does not grant native,
    domain, original-process or registry-to-page consumption admission.
    """
    if not isinstance(source, NativeSourceContext) or reader.root != source.bindings.current_root:
        raise ValueError("Code registry reconstruction needs the genuine admitted Source/current-root context")
    remaining(deadline)
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    authored = reader.read(SOURCE, max_bytes=1024 * 1024)
    if source.reference.read(SOURCE) != authored.content:
        raise ValueError("Code registry producer differs from independently held original Source")
    expected = declared_code_figure_registry(authored.content)
    registry = reader.read(REGISTRY, max_bytes=8 * 1024 * 1024)
    if registry.json_object() != expected:
        raise ValueError("Code registry differs from its complete independent Source-derived declaration")
    bodies = []
    for ordinal, (label, row) in enumerate(expected.items(), 1):
        remaining(deadline)
        figure = reader.read(f"projects/{SCOPE}/output/figures/{row['filename']}")
        bodies.append(
            {
                "ordinal": ordinal,
                "label": label,
                "path": figure.relative,
                "sha256": figure.sha256,
                "bytes": len(figure.content),
            }
        )
    body = {
        "schema": "template-native-code-figure-registry-v1",
        "scope": SCOPE,
        "source": {"path": SOURCE, "sha256": authored.sha256},
        "registry": {"path": REGISTRY, "sha256": registry.sha256},
        "complete_declared_records": expected,
        "ordered_figure_bodies": bodies,
        "claim_boundary": "Source-registry-fields-and-bytes-only; scientific/native-consumption-not-qualified",
    }
    if not reader.unchanged():
        raise ValueError("Code registry Source or exact registered figures changed during reconstruction")
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    remaining(deadline)
    return {**body, "content_digest": canonical_digest(body)}

"""Observer/portable-reader adapters for original HTML fidelity components.

The release owner's source adapters supply genuinely reparsed original and
projected ASTs, outside config witnesses and bound source asset bytes. These
functions do not reconstruct source from candidate HTML and do not grant whole
HTML approval or delete existing source/unsupported obligations.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_html_column_allocation import (
    compile_column_allocation,
    inspect_column_allocation,
)
from infrastructure.reporting.native_format_html_glyph_contours import (
    compile_source_character_runs,
)
from infrastructure.reporting.native_format_html_glyph_reference import (
    build_source_glyph_scene,
    platform_font_request,
)
from infrastructure.reporting.native_format_html_image_alt import (
    compile_original_image_alt,
    inspect_original_image_alt,
)
from infrastructure.reporting.native_format_html_source_metadata import (
    remaining_seconds,
)
from infrastructure.reporting.native_format_semantic_ast import compile_semantic_ast

FIDELITY_SCHEMA = "template-native-html-original-fidelity-components-v1"


def compile_html_fidelity_source(
    sources: tuple[tuple[str, bytes], ...],
    original_ast: bytes,
    projected_ast: bytes,
    *,
    metadata_source: dict[str, Any] | None,
    source_styles: dict[str, Any] | None = None,
    deadline: float,
) -> dict[str, Any]:
    """Build retained source witnesses before any candidate-native inspection."""
    remaining_seconds(deadline)
    original = compile_semantic_ast(sources, original_ast)
    projected = compile_semantic_ast(sources, projected_ast)
    tables = []
    findings = []
    blockers = [*original["blockers"], *projected["blockers"]]
    if len(original["tables"]) != len(projected["tables"]):
        findings.append({"code": "html.table.original-allocation-count"})
    for index, table in enumerate(original["tables"]):
        if index >= len(projected["tables"]):
            blockers.append(table["source_id"] + ": original table has no projected occurrence")
            continue
        tables.append(compile_column_allocation(table, projected["tables"][index], deadline=deadline))
    result = {
        "schema_version": FIDELITY_SCHEMA,
        "original_ast_sha256": hashlib.sha256(original_ast).hexdigest(),
        "projected_ast_sha256": hashlib.sha256(projected_ast).hexdigest(),
        "source_bytes": [{"path": path, "sha256": hashlib.sha256(data).hexdigest()} for path, data in sources],
        "image_alt": compile_original_image_alt(original_ast, projected_ast),
        "column_allocation": tables,
        "characters": compile_source_character_runs(original_ast, metadata_source, source_styles=source_styles),
        "findings": findings,
        "blockers": blockers,
    }
    result = {**result, "digest": canonical_digest(result)}
    remaining_seconds(deadline)
    return result


def inspect_html_fidelity_components(
    source: dict[str, Any],
    dom: dict[str, Any],
    *,
    font_witness: dict[str, Any] | None,
    deadline: float,
) -> tuple[dict[str, Any], bytes | None]:
    """Consumer API returning diagnostics and an exact source-only glyph scene.

    The caller retains the returned scene and runs it through the SAME actual
    original bounded browser, authenticates NativeToolRecord/font consumption,
    and invokes the glyph ink inspector. A missing font/reference witness is
    blocked, not a pass. Baseline metadata/body-source witnesses stay separate.
    """
    remaining_seconds(deadline)
    if source.get("schema_version") != FIDELITY_SCHEMA or source.get("digest") != canonical_digest(
        {key: value for key, value in source.items() if key != "digest"}
    ):
        raise ValueError("original HTML fidelity source witness changed")
    alt = inspect_original_image_alt(source["image_alt"], dom)
    tables = []
    findings = [*source["findings"], *alt["findings"]]
    blockers = [*source["blockers"], *alt["blockers"]]
    if len(dom["tables"]) != len(source["column_allocation"]):
        findings.append({"code": "html.table.original-allocation-count"})
    for index, allocation in enumerate(source["column_allocation"]):
        remaining_seconds(deadline)
        if index >= len(dom["tables"]):
            continue
        observed = inspect_column_allocation(allocation, dom["tables"][index], deadline=deadline)
        findings.extend(observed["findings"])
        blockers.extend(observed["blockers"])
        tables.append(observed)
    request = platform_font_request(source["characters"], dom, deadline=deadline)
    findings.extend(request["findings"])
    blockers.extend(request["blockers"])
    scene = None
    page = None
    if font_witness is None:
        blockers.append(
            "actual physical font bytes/full source glyph contours and fresh source-only native reference are missing"
        )
    else:
        expected_request = hashlib.sha256(
            json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if font_witness["request_sha256"] != expected_request:
            raise ValueError("genuine local font witness/source request changed")
        scene, page = build_source_glyph_scene(source["characters"], dom, font_witness["contours"], deadline=deadline)
        blockers.extend(font_witness["blockers"])
        findings.extend(scene["findings"])
        blockers.extend(scene["blockers"])
    result = {
        "source_digest": source["digest"],
        "image_alt": alt,
        "column_allocation": tables,
        "font_request": request,
        "glyph_scene": scene,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }
    result = {**result, "digest": canonical_digest(result)}
    remaining_seconds(deadline)
    return result, page


def replay_html_fidelity_components(
    sources: tuple[tuple[str, bytes], ...],
    original_ast: bytes,
    projected_ast: bytes,
    dom: dict[str, Any],
    raw: dict[str, Any],
    *,
    metadata_source: dict[str, Any] | None,
    independent_font_witness: dict[str, Any] | None,
    deadline: float,
) -> tuple[dict[str, Any], bytes | None]:
    """Rebuild from current actual Source AST/config/local fonts, never booleans."""
    source = compile_html_fidelity_source(
        sources,
        original_ast,
        projected_ast,
        metadata_source=metadata_source,
        deadline=deadline,
    )
    result, scene = inspect_html_fidelity_components(
        source, dom, font_witness=independent_font_witness, deadline=deadline
    )
    if raw != result:
        raise ValueError("independent original-source HTML fidelity component replay differs")
    remaining_seconds(deadline)
    return result, scene

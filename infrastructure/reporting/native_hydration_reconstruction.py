"""Actual Source/SDK-bound hydration and combined-byte reconstruction.

No generated variable is promoted to a scientific fact by this module. It
proves the deterministic hydration/composition edge and retains all original
analysis, domain, registry, custom-writer and native-consumption requirements.
"""

from __future__ import annotations

import hashlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rendering._combined_exports import combined_source_files
from infrastructure.rendering._pdf_combined_markdown import preprocess_combined_markdown
from infrastructure.rendering._pdf_mermaid import _MERMAID_BLOCK_RE
from infrastructure.rendering._pdf_title_page_config import _rendering_options
from infrastructure.rendering.manuscript_composition import COMPOSITION_RELATIVE_PATH, read_manuscript_composition
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.rendering.manuscript_hydration_replay import combine_held_manuscripts, require_shared_hydration
from infrastructure.rendering._web_markdown_preprocess import html_safe_markdown
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_selected_manuscript_transforms import (
    PROJECT_WRITERS,
    reconstruct_inline_mermaid_source,
    reconstruct_project_authored_hydration,
    reconstruct_transmission_bookend,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.transmission.transmission_bookends import is_transmission_bookend
from infrastructure.validation.output.render_formats import render_config_manuscript_dir

SCHEMA = "template-native-hydration-reconstruction-v3"
REMAINING = (
    "same-original-analysis-request-completion-produced-and-consumed-byte-graph",
    "independent-project-domain-mapping-for-every-generated-value-unit-sign-and-figure",
    "source-owned-complete-registry-reconstruction-and-original-stage-custody",
    "complete-native-semantic-and-visual-consumption-of-reconstructed-source-occurrences",
)


def _binding(item: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": item.relative, "sha256": item.sha256, "bytes": len(item.content)}


@dataclass(frozen=True)
class _Reconstruction:
    graph: dict[str, Any]
    pdf_body: bytes | None


def _pdf_body(
    bodies: tuple[bytes, ...],
    settings: dict[str, Any] | None,
    dotted_vars: ArtifactSnapshot | None,
    reader: SnapshotReader,
    scope: str,
    *,
    deadline: float,
) -> tuple[bytes | None, list[dict[str, Any]], list[str]]:
    """Apply actual PDF composition to held bytes without launching Mermaid.

    A final web composition receipt does not choose the PDF writer algorithm.
    This body stays transient and is exposed only by a genuine observation or
    externally authenticated replay, never by deserializing its graph hash.
    """
    separator = "\n```{=latex}\n\\newpage\n```\n" if _rendering_options(settings)["section_breaks"] else ""
    joined = combine_held_manuscripts(bodies, separator=separator)
    rewritten, mermaid_rows, mermaid_gaps = reconstruct_inline_mermaid_source(joined, scope, reader, deadline=deadline)
    if rewritten is None:
        return None, mermaid_rows, mermaid_gaps
    if _MERMAID_BLOCK_RE.search(rewritten.decode()) or re.search(r"(?m)^\s*```\s*mermaid\b", rewritten.decode()):
        return None, mermaid_rows, [*mermaid_gaps, "unsupported-selected-mermaid-fence-transformation"]
    with tempfile.TemporaryDirectory(prefix="native-hydration-reconstruction-") as temporary:
        work = Path(temporary).resolve(strict=True)
        if dotted_vars is not None:
            atomic_write_bytes_confined(work, work / "manuscript_vars.yaml", dotted_vars.content, mode=0o600)
        body = preprocess_combined_markdown(rewritten.decode(), manuscript_dir=work).content.encode()
    remaining(deadline)
    return body, mermaid_rows, mermaid_gaps


def _reconstruct(
    source: NativeSourceContext,
    scope: str,
    pipeline_run_id: str,
    plan_digest: str,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> _Reconstruction:
    if (
        not isinstance(source, NativeSourceContext)
        or scope not in PUBLIC_PROJECT_NAMES
        or reader.root != source.bindings.current_root
        or not isinstance(pipeline_run_id, str)
        or not pipeline_run_id
        or not isinstance(plan_digest, str)
        or len(plan_digest) != 64
        or any(char not in "0123456789abcdef" for char in plan_digest)
    ):
        raise ValueError("hydration reconstruction needs genuine Source and exact native pipeline identity")
    remaining(deadline)
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    project = reader.root / "projects" / scope
    authored_root = resolve_source_manuscript_dir(project)
    consumed_root = render_config_manuscript_dir(project)
    paths = combined_source_files(discover_manuscript_files(consumed_root))
    if not paths or len(paths) > 1000:
        raise ValueError("hydration requires the complete bounded Source-selected manuscript roster")
    config = reader.read((consumed_root / "config.yaml").relative_to(reader.root).as_posix())
    composition = reader.read((project / COMPOSITION_RELATIVE_PATH).relative_to(reader.root).as_posix())
    # The actual Source parser validates its closed shape and digest; held
    # snapshot identity is checked after its independent file read.
    parsed = read_manuscript_composition(composition.path)
    ordered_paths = tuple(path.relative_to(project).as_posix() for path in paths)
    if (
        parsed.project != scope
        or tuple(row.path for row in parsed.ordered_inputs) != ordered_paths
        or any(row.ordinal != index for index, row in enumerate(parsed.ordered_inputs, 1))
    ):
        raise ValueError("native composition omits/reorders a complete current Source-selected input")
    variables = None
    values: dict[str, Any] = {}
    project_writer = None
    if consumed_root == project / "output/manuscript":
        variable_name = "metrics.json" if scope == "templates/template_template" else "manuscript_variables.json"
        variable_path = project / "output/data" / variable_name
        if variable_path.is_file():
            variables = reader.read(variable_path.relative_to(reader.root).as_posix(), max_bytes=8 * 1024 * 1024)
            values = variables.json_object()
            if scope in PROJECT_WRITERS:
                project_writer = reader.read(f"projects/{scope}/{PROJECT_WRITERS[scope]}")
                if source.reference.read(project_writer.relative) != project_writer.content:
                    raise ValueError("custom hydration writer differs from independently admitted complete Source")
            elif any(not isinstance(key, str) or not isinstance(value, str) for key, value in values.items()):
                raise ValueError("standard shared hydration needs the exact flat string-valued original variables")
    bookend_absences: list[Path] = []
    rows = []
    bodies = []
    gaps = list(REMAINING)
    for index, path in enumerate(paths, 1):
        remaining(deadline)
        item = reader.read(path.relative_to(reader.root).as_posix())
        recorded = parsed.ordered_inputs[index - 1]
        if recorded.sha256 != item.sha256 or recorded.size_bytes != len(item.content):
            raise ValueError("native composition input differs from its held consumed body")
        bodies.append(item.content)
        row: dict[str, Any] = {"ordinal": index, "consumed": _binding(item)}
        authored = authored_root / path.relative_to(consumed_root)
        if is_transmission_bookend(path):
            candidates = (
                project / "manuscript/config.yaml",
                project / "output/manuscript/config.yaml",
                project / "docs/manuscript/config.yaml",
            )
            config_path = next((candidate for candidate in candidates if candidate.is_file()), None)
            if config_path is None:
                raise ValueError("selected transmission bookend lacks the actual writer-selected config")
            selected_config = reader.read(config_path.relative_to(reader.root).as_posix())
            if (
                config_path != project / "output/manuscript/config.yaml"
                and source.reference.read(selected_config.relative) != selected_config.content
            ):
                raise ValueError("transmission authored config differs from independently admitted Source")
            ledger_path = project / "output/data/publication_ledger.json"
            ledger = (
                reader.read(ledger_path.relative_to(reader.root).as_posix(), max_bytes=8 * 1024 * 1024)
                if ledger_path.is_file()
                else None
            )
            receipts = (
                reader.root / "output" / scope / "release_bundle/RELEASE_RECEIPT.json",
                project / "output/release_bundle/RELEASE_RECEIPT.json",
            )
            if (ledger is None or not ledger.json_object().get("releases")) and any(
                candidate.exists() or candidate.is_symlink() for candidate in receipts
            ):
                gaps.append("selected-transmission-receipt-backfill-history-adapter:" + item.relative)
            else:
                rebuilt_bookend, details = reconstruct_transmission_bookend(selected_config, ledger, path.name)
                if rebuilt_bookend != item.content:
                    raise ValueError("generated transmission boundary differs from actual Source config/ledger text")
                row["transformation"] = "Source-generated-transmission-boundary"
                row["bookend"] = details
                if ledger is None or not ledger.json_object().get("releases"):
                    absent = ([ledger_path] if ledger is None else []) + list(receipts)
                    bookend_absences.extend(absent)
                    row["absence_inputs"] = [candidate.relative_to(reader.root).as_posix() for candidate in absent]
                gaps.append(
                    "generated-transmission-figure-integrity-strip-and-publication-history-authority:" + item.relative
                )
        elif not authored.is_file():
            gaps.append("custom-generated-manuscript-source-adapter:" + item.relative)
        else:
            original = reader.read(authored.relative_to(reader.root).as_posix())
            if source.reference.read(original.relative) != original.content:
                raise ValueError("hydration authored manuscript differs from independently admitted Source")
            row["source"] = _binding(original)
            if variables is None:
                if original.content != item.content:
                    raise ValueError("direct Source manuscript body differs from actual consumed source")
                row["transformation"] = "exact-authored-source-body"
            elif project_writer is not None:
                # Template's numbered chapters are substituted; ancillary
                # manuscript text is copied verbatim by the same Source writer.
                custom = (
                    reconstruct_project_authored_hydration(scope, original.content, values)
                    if scope != "templates/template_template" or path.name[0].isdigit()
                    else (original.content, {"algorithm": "Source-template-ancillary-verbatim-v1"})
                )
                if custom is None or custom[0] != item.content:
                    raise ValueError(
                        "custom authored manuscript differs from its complete Source writer reconstruction"
                    )
                row["transformation"] = "Source-selected-project-authored-hydration"
                row["project_hydration"] = {**custom[1], "writer": _binding(project_writer)}
            else:
                rebuilt = require_shared_hydration(original.content, values, item.content)
                row["transformation"] = "shared-uppercase-token-hydration"
                row["hydration"] = rebuilt.data()
        rows.append(row)
    combined = reader.read(f"projects/{scope}/{parsed.combined_path}")
    if combined.sha256 != parsed.combined_sha256 or len(combined.content) != parsed.combined_size_bytes:
        raise ValueError("native combined manuscript differs from its original composition binding")
    settings = yaml.safe_load(config.content)
    if settings is not None and not isinstance(settings, dict):
        raise ValueError("native consumed manuscript config is not a mapping")
    vars_path = consumed_root / "manuscript_vars.yaml"
    dotted_vars = (
        reader.read(vars_path.relative_to(reader.root).as_posix(), max_bytes=8 * 1024 * 1024)
        if vars_path.is_file()
        else None
    )
    pdf_body, mermaid_rows, mermaid_gaps = _pdf_body(
        tuple(bodies), settings, dotted_vars, reader, scope, deadline=deadline
    )
    gaps.extend(mermaid_gaps)
    if pdf_body is None:
        gaps.append("authenticated-generated-mermaid-assets-to-combined-source-transformation")
    reconstructed: bytes | None
    if parsed.algorithm == "web-renderer-combine-v1":
        joined = combine_held_manuscripts(tuple(bodies), separator="\n---\n\n")
        reconstructed = html_safe_markdown(joined.decode(), render_citations=False).encode()
    else:
        reconstructed = pdf_body
    if reconstructed is not None and reconstructed != combined.content:
        raise ValueError("native combined manuscript differs from actual complete Source composition/preprocessing")
    body = {
        "schema_version": SCHEMA,
        "scope": scope,
        "pipeline_run_id": pipeline_run_id,
        "plan_digest": plan_digest,
        "source_binding": [source.reference.commit, source.reference.source_identity],
        "variables": None if variables is None else _binding(variables),
        "config": _binding(config),
        "ordered_inputs": rows,
        "composition": _binding(composition),
        "algorithm": parsed.algorithm,
        "combined": _binding(combined),
        "dotted_variables": None if dotted_vars is None else _binding(dotted_vars),
        "independent_combined_sha256": None if reconstructed is None else hashlib.sha256(reconstructed).hexdigest(),
        "pdf_recomposition": {
            "algorithm": "Source-pdf-section-break-combine-and-preprocess-v1",
            "sha256": None if pdf_body is None else hashlib.sha256(pdf_body).hexdigest(),
            "bytes": None if pdf_body is None else len(pdf_body),
            "section_breaks": _rendering_options(settings)["section_breaks"],
            "mermaid_transformations": mermaid_rows,
        },
        "unresolved_edges": gaps,
    }
    if any(candidate.exists() or candidate.is_symlink() for candidate in bookend_absences):
        raise ValueError("transmission absent ledger/receipt inputs appeared during reconstruction")
    if not reader.unchanged():
        raise ValueError("hydration inputs/variables/composition changed across independent reconstruction")
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    remaining(deadline)
    return _Reconstruction({**body, "content_digest": canonical_digest(body)}, pdf_body)


def observe_native_hydration_reconstruction(
    source: NativeSourceContext,
    scope: str,
    pipeline_run_id: str,
    plan_digest: str,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Observe actual current bytes inside the genuine original Source owner."""
    return observe_native_pdf_recomposition(source, scope, pipeline_run_id, plan_digest, reader, deadline=deadline)[0]


def observe_native_pdf_recomposition(
    source: NativeSourceContext,
    scope: str,
    pipeline_run_id: str,
    plan_digest: str,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> tuple[dict[str, Any], bytes | None]:
    """Return the independently recomposed PDF bytes inside the genuine owner.

    The graph still contains all unresolved domain, custom-writer, bookend and
    native-consumption edges. A body alone never admits any native obligation.
    """
    owner = current_native_producer_operation()
    if owner is None or owner.source is not source or deadline != owner.deadline:
        raise ValueError("native original hydration needs its actual live Source owner and existing clock")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    result = _reconstruct(source, scope, pipeline_run_id, plan_digest, reader, deadline=deadline)
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    return result.graph, result.pdf_body


def replay_native_hydration_reconstruction(
    scope: str,
    native_execution: ArtifactSnapshot,
    reader: SnapshotReader,
) -> dict[str, Any]:
    """Rebuild the edge only under externally held genuine original custody.

    No JSON may construct an operation, original launch, clock or fulfilled set.
    An exact match still carries all unchanged unresolved analysis/domain edges.
    """
    return replay_native_pdf_recomposition(scope, native_execution, reader)[0]


def replay_native_pdf_recomposition(
    scope: str,
    native_execution: ArtifactSnapshot,
    reader: SnapshotReader,
) -> tuple[dict[str, Any], bytes | None]:
    """Return fresh PDF bytes under externally held actual original custody.

    This replays the complete graph, not a serialized expected PDF digest. A
    final web combined body remains independently matched to its own algorithm.
    """
    operation = require_native_operation(reader)
    original = operation.originals.get(scope)
    if (
        original is None
        or native_execution.relative != original.native_execution_relative
        or native_execution.sha256 != original.native_execution_sha256
        or reader.read(native_execution.relative) != native_execution
    ):
        raise ValueError("hydration evidence is not the actual externally authenticated original native artifact")
    raw = native_execution.json_object()
    pipeline = raw.get("pipeline")
    if (
        raw.get("scope") != scope
        or raw.get("run_id") != original.run_id
        or not isinstance(pipeline, dict)
        or pipeline.get("mode") != "core"
        or not isinstance(pipeline.get("plan"), dict)
        or pipeline["plan"].get("project") != scope
    ):
        raise ValueError("hydration evidence omitted the genuine full original native pipeline")
    expected = _reconstruct(
        operation.source,
        scope,
        pipeline.get("run_id", ""),
        pipeline.get("plan_digest", ""),
        reader,
        deadline=operation.deadline,
    )
    if raw.get("hydration_reconstruction") != expected.graph:
        raise ValueError("retained hydration differs from fresh complete Source/occurrence/body reconstruction")
    operation.verify(reader)
    return expected.graph, expected.pdf_body

"""Actual complete Source fence observation and explicitly nominated fresh reader.

One already-live original producer retains both phases. Independent reader roots
are supplied by the caller; no original receipt path selects the fresh runtime.
The operation grants component observations, never full native/release approval.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_citation_process_custody import CitationOriginalProcessCustodian
from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidSelection,
    admit_source_mermaid_selection,
    source_mermaid_runtime_operation,
)
from infrastructure.reporting.native_mermaid_source_census import collect_current_source_mermaid_fences
from infrastructure.reporting.native_mermaid_source_reference import (
    observe_original_mermaid_sources,
    replay_original_mermaid_sources,
)
from infrastructure.reporting.native_mermaid_svg_topology import inspect_original_mermaid_svg
from infrastructure.reporting.native_mermaid_svg_ink_enclosures import inspect_original_svg_ink_enclosures
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-all-current-mermaid-original-and-reader-component-v1"
SOURCE_PHASE_SECONDS = 60
SOURCE_PHASE_BYTES = 128 * 1024 * 1024
REQUIRED_FREE_RESERVE_BYTES = 2 * 1024 * 1024 * 1024
REQUIRED_CURRENT_FENCES = 28
REMAINING_ADMISSION = (
    "original selected SDK/preimport/guardian terminal custody and exact Source whole-revision release gates",
    "Source-required Node/Chrome loaded provider/shared-cache/kernel and complete font/shaping custody",
    "independent complete unclipped source glyph/stroke/marker/clip/mask/filter ink admission",
    "genuine complete native PDF/HTML/Office document page position and visibility admission",
    "all25 native/installed/export/transfer and exact-revision hosted/publication acceptance",
)


def _storage(directory: Path, deadline: float) -> dict[str, int]:
    remaining(deadline)
    statistics = os.statvfs(directory)
    available = statistics.f_bavail * statistics.f_frsize
    if available < REQUIRED_FREE_RESERVE_BYTES:
        raise ValueError("all-source original component lacks its required 2GiB actual free reserve")
    total = 0
    count = 0
    for path in directory.rglob("*"):
        remaining(deadline)
        if path.is_file():
            total += path.stat().st_size
            count += 1
            if total > SOURCE_PHASE_BYTES:
                raise ValueError("all-source actual original component exceeds its unchanged128MiB storage cap")
    return {"retained_files": count, "retained_bytes": total, "available_bytes": available}


def _environment(env: dict[str, str], node: Path) -> dict[str, str]:
    selected = dict(env)
    # This is the explicit command nominee, not an inferred global tool. The
    # Source observer still checks actual executable selection and byte custody.
    selected["PATH"] = str(node.parent) + os.pathsep + selected.get("PATH", "")
    return selected


def observe_all_current_mermaid_sources(
    source: NativeSourceContext,
    directory: Path,
    *,
    original_selection: NativeMermaidSelection,
    reader_selection: NativeMermaidSelection,
    font_files: tuple[Path, ...],
    reader_font_files: tuple[Path, ...],
    env: dict[str, str],
    deadline: float,
    expected_census_digest: str | None = None,
) -> dict[str, Any]:
    """Execute every ordered fence once and genuinely reproduce all in fresh tools.

    A live Source owner stays active until both phases complete, so original
    process facts remain genuine. This cannot be resumed from JSON after that
    owner closes. Separately scheduled/portable readers need the original
    external completed-process custodian; this API never invents one.
    """
    remaining(deadline)
    producer = current_native_producer_operation()
    if not isinstance(source, NativeSourceContext) or producer is None or producer.source is not source:
        raise ValueError("all-source component requires its genuine active original Source producer")
    if directory.exists() or not directory.absolute().is_relative_to(source.bindings.current_root):
        raise ValueError("all-source component requires a fresh original directory below its actual Source root")
    create_private_native_directory(source.bindings.current_root, directory)
    before_storage = _storage(directory, deadline)
    census = collect_current_source_mermaid_fences(source, deadline=deadline)
    if len(census.occurrences) != REQUIRED_CURRENT_FENCES:
        raise ValueError("current release requires every exact ordered28 source fence; source census changed")
    original_census = census.data()
    if expected_census_digest is not None and expected_census_digest != original_census["content_digest"]:
        raise ValueError("genuine current Source census differs from the independently nominated release expectation")
    sources = census.sources()
    root = source.bindings.current_root
    run_id = source.bindings.run_id
    original_env = _environment(env, original_selection.node_executable)
    original_runtime = admit_source_mermaid_selection(
        original_selection,
        source,
        deadline=deadline,
        directory=directory / "original-runtime",
        env=original_env,
    )
    original_custodian = CitationOriginalProcessCustodian(root, source, run_id=run_id, deadline=deadline)
    # Original capture reserves three decoded copies per occurrence, retained
    # validation plus fresh capture reserves five more. One live operation
    # shares the existing aggregate pixel cap across every one of these copies.
    decoded_budget = SourceImageDecodeBudget(8 * len(sources))
    with source_mermaid_runtime_operation(original_runtime, source=source, deadline=deadline):
        original = observe_original_mermaid_sources(
            root,
            directory / "original",
            sources,
            package_root=original_selection.package_root,
            node_executable=original_selection.node_executable,
            chrome_executable=original_selection.chrome_executable,
            font_files=font_files,
            decoded_pixel_budget=decoded_budget,
            inspect_svg=inspect_original_mermaid_svg,
            env=original_env,
            deadline=deadline,
            run_id=run_id,
            on_original_tool=original_custodian.observe_actual_tool,
            runtime_admission=original_runtime,
        )
    if decoded_budget.admitted_occurrences != 3 * len(sources):
        raise ValueError("original complete28 source decoder allocations differ from their declared occurrence count")
    original_decoded_pixels = decoded_budget.decoded_pixels
    between_storage = _storage(directory, deadline)

    def admit_original_process(raw: dict[str, Any]) -> None:
        if raw.get("purpose") == "source-mermaid-node-version":
            original_runtime.admit_node_version_process(raw)
        else:
            original_custodian.admit_original_process(raw)

    original_reader = SnapshotReader(root, native_producer_operation=producer)

    def artifact_reader(binding: dict[str, Any]) -> bytes:
        selected = original_reader.read(binding["path"])
        if selected.sha256 != binding["sha256"]:
            raise ValueError("all-source retained original artifact bytes changed before fresh independent reader")
        return selected.content

    reader_env = _environment(env, reader_selection.node_executable)
    reader_runtime = admit_source_mermaid_selection(
        reader_selection,
        source,
        deadline=deadline,
        directory=directory / "reader-runtime",
        env=reader_env,
    )
    reader_custodian = CitationOriginalProcessCustodian(root, source, run_id=run_id, deadline=deadline)
    with source_mermaid_runtime_operation(reader_runtime, source=source, deadline=deadline):
        reproduced = replay_original_mermaid_sources(
            original,
            sources,
            artifact_reader=artifact_reader,
            admit_original_process=admit_original_process,
            root=root,
            directory=directory / "reader",
            package_root=reader_selection.package_root,
            node_executable=reader_selection.node_executable,
            chrome_executable=reader_selection.chrome_executable,
            font_files=reader_font_files,
            decoded_pixel_budget=decoded_budget,
            inspect_svg=inspect_original_mermaid_svg,
            env=reader_env,
            deadline=deadline,
            run_id=run_id,
            on_original_tool=reader_custodian.observe_actual_tool,
            runtime_admission=reader_runtime,
        )
    if decoded_budget.admitted_occurrences != decoded_budget.expected_occurrences or not original_reader.unchanged():
        raise ValueError("complete28 fresh-reader decode allocations/original artifacts changed")
    current_census = collect_current_source_mermaid_fences(source, deadline=deadline)
    if current_census.data() != original_census or current_census.sources() != sources:
        raise ValueError("complete ordered Source fence bytes/positions/hydration changed during original/reproduction")
    for original_row, current_row in zip(original["occurrences"], reproduced["occurrences"], strict=True):
        if original_row["identity"] != current_row["identity"]:
            raise ValueError("fresh reader changed an original Source occurrence identity")
        for kind in ("svg", "png"):
            if original_row["processes"][kind]["pid"] == current_row["processes"][kind]["pid"]:
                raise ValueError("fresh reader reused an original native process instead of a genuine new invocation")
    original_enclosures: list[dict[str, Any]] = []
    reader_enclosures: list[dict[str, Any]] = []
    for collection, observed_reference in ((original_enclosures, original), (reader_enclosures, reproduced)):
        for row in observed_reference["occurrences"]:
            remaining(deadline)
            data = artifact_reader(row["artifacts"]["svg"])
            collection.append(
                {
                    "identity": row["identity"],
                    "original_source_enclosures": inspect_original_svg_ink_enclosures(
                        data, row["paint"]["original_dom"]
                    ),
                }
            )
    # Uninterpreted glyph/marker/effect gates are retained, not turned into a
    # pass because the observed original and reader happened to agree.
    if original_enclosures != reader_enclosures:
        raise ValueError("fresh independent Source primitive/effect/glyph-owner enclosure census differs")
    producer.verify(SnapshotReader(root), run_id=run_id, deadline=deadline)
    after_storage = _storage(directory, deadline)
    # This reader held every original and reproduced artifact consumed by the
    # enclosure pass. The producer check above uses a distinct reader, so it
    # cannot close these cached artifact identities on our behalf.
    remaining(deadline)
    if not original_reader.unchanged():
        raise ValueError("complete28 original/fresh-reader artifacts changed during final enclosure observation")
    remaining(deadline)
    return {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "component_status": "actual-original-and-fresh-reader-observed",
        "full_native_or_release_approval": False,
        "source_census": original_census,
        "original": original,
        "fresh_reader": reproduced,
        "independent_source_enclosures": original_enclosures,
        "original_selection": original_runtime.spec_data(),
        "reader_selection": reader_runtime.spec_data(),
        "decoded_budgets": {
            "original_declared_occurrences": 3 * len(sources),
            "original_admitted_occurrences": 3 * len(sources),
            "original_decoded_pixels": original_decoded_pixels,
            "reader_declared_occurrences": 5 * len(sources),
            "reader_admitted_occurrences": decoded_budget.admitted_occurrences - 3 * len(sources),
            "reader_decoded_pixels": decoded_budget.decoded_pixels - original_decoded_pixels,
            "operation_declared_occurrences": decoded_budget.expected_occurrences,
            "operation_admitted_occurrences": decoded_budget.admitted_occurrences,
            "operation_decoded_pixels": decoded_budget.decoded_pixels,
            "per_image_pixel_cap": 60_000_000,
            "aggregate_operation_pixel_cap": 120_000_000,
        },
        "storage_before": before_storage,
        "storage_between": between_storage,
        "storage_after": after_storage,
        "original_deadline_monotonic": deadline,
        "remaining_admission": list(REMAINING_ADMISSION),
    }

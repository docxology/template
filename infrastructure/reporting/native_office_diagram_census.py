"""Complete Source-composed Office Mermaid applicability and native targets.

The records are DATA. Only the existing fixed child supervisor/reader grants
original process custody; an empty list does not independently prove absence.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, create_private_native_directory
from infrastructure.reporting.native_office_diagram_geometry import DiagramSource
from infrastructure.reporting.native_office_diagram_positive import build_office_diagram_native_positive
from infrastructure.reporting.native_office_mermaid_binding import (
    OfficeMermaidAdmission,
    office_original_mermaid_sources,
)
from infrastructure.reporting.native_office_semantic_source import office_semantic_source_plan
from infrastructure.reporting.native_mermaid_source_census import SourceMermaidFence
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.rendering._pdf_mermaid import _MERMAID_BLOCK_RE

SCHEMA = "template-native-office-complete-source-diagram-census-v1"
MAX_TARGETS = 100


def _ordered_source_fences(
    inputs: tuple[tuple[str, bytes], ...],
    scope: str,
    *,
    deadline: float,
) -> tuple[SourceMermaidFence, ...]:
    """Use the global Source census identities on the exact selected inputs."""
    result: list[SourceMermaidFence] = []
    for input_ordinal, (path, body) in enumerate(inputs):
        remaining(deadline)
        content = body.decode("utf-8", errors="strict")
        for file_ordinal, match in enumerate(_MERMAID_BLOCK_RE.finditer(content)):
            remaining(deadline)
            if len(result) >= MAX_TARGETS:
                raise ValueError("Office Source fence census exceeds the existing hundred-occurrence bound")
            start = len(content[: match.start("source")].encode("utf-8"))
            end = len(content[: match.end("source")].encode("utf-8"))
            raw = match.group("source").encode("utf-8")
            if not raw.strip() or len(raw) > 1024 * 1024:
                raise ValueError("Office Source fence body exceeds the existing source census bounds")
            result.append(
                SourceMermaidFence(
                    scope,
                    path,
                    hashlib.sha256(body).hexdigest(),
                    input_ordinal,
                    file_ordinal,
                    len(result),
                    content.count("\n", 0, match.start()) + 1,
                    start,
                    end,
                    raw,
                    hashlib.sha256(body[:start]).hexdigest(),
                    hashlib.sha256(body[end:]).hexdigest(),
                )
            )
    return tuple(result)


def replay_diagram_census_inputs(raw: dict[str, Any], reader: SnapshotReader, *, deadline: float) -> None:
    """Reopen all selected Source inputs and independently rebuild each fence."""
    remaining(deadline)
    inputs = raw["inputs"]
    if set(inputs) != {"ordered_manuscripts", "bibliographies", "config", "variables"}:
        raise ValueError("Office census omitted a complete Source input role")

    def reopen(binding: dict[str, str]) -> tuple[str, bytes]:
        remaining(deadline)
        if set(binding) != {"path", "sha256"}:
            raise ValueError("Office Source census input binding differs")
        value = reader.read(binding["path"])
        if value.sha256 != binding["sha256"]:
            raise ValueError("Office complete Source census input body changed")
        return value.relative, value.content

    manuscripts = tuple(reopen(binding) for binding in inputs["ordered_manuscripts"])
    if not manuscripts or len({path for path, _ in manuscripts}) != len(manuscripts):
        raise ValueError("Office Source census requires the exact nonduplicated manuscript order")
    for binding in inputs["bibliographies"]:
        reopen(binding)
    for role in ("config", "variables"):
        if inputs[role] is not None:
            reopen(inputs[role])
    _, composed = reopen(raw["original_source"])
    source_fences = _ordered_source_fences(manuscripts, raw["scope"], deadline=deadline)
    composed_fences = office_original_mermaid_sources(composed.decode("utf-8"), raw["scope"])
    if (
        raw["source_fences"] != [fence.data() for fence in source_fences]
        or tuple(fence.raw_source for fence in source_fences) != tuple(body for _, body in composed_fences)
        or raw["occurrences"] != [identity for identity, _ in composed_fences]
    ):
        raise ValueError("Office complete selected-input/composed Source fence census differs")
    remaining(deadline)


def select_diagram_control_targets(
    sources: tuple[DiagramSource, ...],
    geometry: dict[str, Any],
    *,
    deadline: float,
) -> list[dict[str, Any]]:
    """Account every actual paint and every Source occurrence, without aliases.

    Equal Source PNG pixels deliberately remain an equivalence class. The
    geometry proves the complete multiplicity; this selector does not invent
    a one-to-one source identity for indistinguishable repeated image paints.
    Shared Form instructions are retained as every applicable placement.
    """
    remaining(deadline)
    placements = geometry.get("placements")
    identities = [source.identity for source in sources]
    counts = dict(Counter(source.rgb_sha256 for source in sources))
    if (
        not sources
        or len(sources) > MAX_TARGETS
        or len(set(identities)) != len(sources)
        or not isinstance(placements, list)
        or not 1 <= len(placements) <= MAX_TARGETS
        or geometry.get("status") != "pass"
        or geometry.get("findings") != []
        or geometry.get("blockers") != []
        or geometry.get("source_counts") != counts
        or geometry.get("native_counts") != counts
        or Counter(row.get("rgb_sha256") for row in placements) != Counter(source.rgb_sha256 for source in sources)
    ):
        raise ValueError("Office diagram control roster requires the entire supported actual Source/native census")
    result = []
    for ordinal, placement in enumerate(placements):
        remaining(deadline)
        matching = [source.identity for source in sources if source.rgb_sha256 == placement["rgb_sha256"]]
        if placement.get("source_identities") != matching:
            raise ValueError("Office native placement has an incomplete original Source equivalence class")
        result.append({"ordinal": ordinal, "source_identities": matching, "placement": placement})
    remaining(deadline)
    return result


def observe_office_diagram_census(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    source: NativeSourceContext,
    mermaid: OfficeMermaidAdmission | None,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_epub_engine: Path | None = None,
) -> dict[str, Any]:
    """Execute one fixed child's full Source census, including actual absence."""
    remaining(deadline)
    if source.bindings.current_root != root or source.bindings.run_id != run_id:
        raise ValueError("Office census requires this actual Source run/root")
    reader = SnapshotReader(root)
    source.verify_correspondence(source.reference, root, reader, deadline)
    plan_directory = directory / "complete-source-census"
    create_private_native_directory(root, plan_directory)
    plan = office_semantic_source_plan(root, plan_directory, scope, artifact, reader, deadline=deadline)
    content_path = plan_directory / "original-composed-source.md"
    atomic_write_bytes_confined(root, content_path, plan.original_content, mode=0o600)
    content = reader.read(content_path.relative_to(root).as_posix())
    fences = office_original_mermaid_sources(plan.original_content.decode("utf-8"), scope)
    source_fences = _ordered_source_fences(plan.sources, scope, deadline=deadline)
    if tuple(fence.raw_source for fence in source_fences) != tuple(body for _, body in fences):
        raise ValueError("Office composed diagram fences require an unimplemented source transformation lineage")
    if bool(fences) != (mermaid is not None):
        raise ValueError("Office diagram census differs from genuine complete Source paint applicability")
    positive = None
    targets: list[dict[str, Any]] = []
    if mermaid is not None:
        actual = build_office_diagram_native_positive(
            root,
            directory / "positive-native",
            scope,
            artifact,
            source,
            mermaid,
            env=env,
            deadline=deadline,
            run_id=run_id,
            epubcheck_jar=epubcheck_jar,
            java_executable=java_executable,
            frozen_epub_engine=frozen_epub_engine,
        )
        actual.verify(deadline)
        if [item.identity for item in actual.sources] != [identity for identity, _ in fences]:
            raise ValueError("Office positive omitted a complete composed Source fence")
        targets = select_diagram_control_targets(
            actual.sources, actual.record["visibility"]["geometry"], deadline=deadline
        )
        positive = actual.record
        original = reader.read(positive["reference"]["source"]["original_source"]["path"])
        if original.content != plan.original_content:
            raise ValueError("Office actual positive consumed another complete composed Source body")

    def binding(value: tuple[str, bytes] | None) -> dict[str, str] | None:
        return None if value is None else {"path": value[0], "sha256": hashlib.sha256(value[1]).hexdigest()}

    raw = {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "scope": scope,
        "kind": artifact.format,
        "control": "diagram-census",
        "oracle_exit_code": 0,
        "source": {"commit": source.reference.commit, "source_identity": source.reference.source_identity},
        "artifact": asdict(artifact),
        "inputs": {
            "ordered_manuscripts": [binding(value) for value in plan.sources],
            "bibliographies": [binding(value) for value in plan.bibliographies],
            "config": binding(plan.config),
            "variables": binding(plan.variables),
        },
        "original_source": {"path": content.relative, "sha256": content.sha256},
        "occurrences": [identity for identity, _ in fences],
        "source_fences": [fence.data() for fence in source_fences],
        "targets": targets,
        "positive": positive,
    }
    validate_diagram_census_data(raw, scope=scope, kind=artifact.format, source=source, deadline=deadline)
    source.verify_correspondence(source.reference, root, reader, deadline)
    if not reader.unchanged():
        raise ValueError("Office census Source/retained original composed body changed")
    return raw


def validate_diagram_census_data(
    raw: dict[str, Any],
    *,
    scope: str,
    kind: str,
    source: NativeSourceContext,
    deadline: float,
) -> None:
    """Closed DATA consistency only; actual original/current custody is separate."""
    remaining(deadline)
    if (
        set(raw)
        != {
            "schema_version",
            "run_id",
            "scope",
            "kind",
            "control",
            "oracle_exit_code",
            "source",
            "artifact",
            "inputs",
            "original_source",
            "occurrences",
            "source_fences",
            "targets",
            "positive",
        }
        or raw["schema_version"] != SCHEMA
        or raw["scope"] != scope
        or raw["kind"] != kind
        or raw["control"] != "diagram-census"
        or type(raw["oracle_exit_code"]) is not int
        or raw["oracle_exit_code"] != 0
        or raw["source"] != {"commit": source.reference.commit, "source_identity": source.reference.source_identity}
        or raw["artifact"]["id"] != f"manuscript:{kind}"
        or raw["artifact"]["format"] != kind
        or not isinstance(raw["occurrences"], list)
        or len(raw["occurrences"]) > MAX_TARGETS
        or len(set(raw["occurrences"])) != len(raw["occurrences"])
        or not isinstance(raw["source_fences"], list)
        or len(raw["source_fences"]) != len(raw["occurrences"])
        or not isinstance(raw["targets"], list)
        or len(raw["targets"]) > MAX_TARGETS
        or bool(raw["occurrences"]) != bool(raw["targets"])
        or bool(raw["occurrences"]) != (raw["positive"] is not None)
    ):
        raise ValueError("Office complete Source census DATA differs from the fixed artifact role")
    if raw["positive"] is not None:
        positive = raw["positive"]
        if positive["occurrences"] != raw["occurrences"] or positive["scope"] != scope or positive["kind"] != kind:
            raise ValueError("Office full positive Source occurrence roster differs")
        if raw["targets"] != [
            {"ordinal": ordinal, "source_identities": placement["source_identities"], "placement": placement}
            for ordinal, placement in enumerate(positive["visibility"]["geometry"]["placements"])
        ]:
            raise ValueError("Office census omitted or reordered an actual native placement")
    remaining(deadline)

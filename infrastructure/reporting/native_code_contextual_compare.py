"""Equality-only Code projection after both genuine complete per-run joins.

Raw graphs, native ownership and retained Original comparison digests remain
unchanged. This predicate never admits an execution or native artifact. It
reuses actual Source hydration/composition rules for eight contextual roles.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.rendering.manuscript_composition import (
    CompositionInput,
    ManuscriptComposition,
    _binding_digest,
    _digest_rows,
)
from infrastructure.rendering.manuscript_hydration_replay import (
    reconstruct_shared_hydration,
    require_shared_hydration,
)
from infrastructure.reporting.native_analysis_semantic_compare import (
    native_analysis_semantics,
    native_hydration_semantics,
)
from infrastructure.reporting.native_code_metadata_domains import (
    METADATA_KEYS,
    OBSERVATION,
    PROJECT,
    HYDRATION,
    SOURCE,
    _registered_metadata_origin,
    validate_metadata_observation,
)
from infrastructure.reporting.native_hydration_reconstruction import _pdf_body, _combined_body
from infrastructure.reporting.native_selected_manuscript_transforms import reconstruct_transmission_bookend
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def _binding(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256, "bytes": len(snapshot.content)}


def _held(binding: dict[str, Any], reader: SnapshotReader) -> ArtifactSnapshot:
    snapshot = reader.read(binding["path"], max_bytes=64 * 1024 * 1024)
    if _binding(snapshot) != binding:
        raise ValueError("Code contextual projection changed an exact held body binding")
    return snapshot


def _body(path: str, content: bytes) -> dict[str, Any]:
    return {"path": path, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}


def _json(content: dict[str, Any]) -> bytes:
    return json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _remap(value: Any, replacements: dict[tuple[str, str, int], dict[str, Any]], *, deadline: float) -> Any:
    """Keep all fields; replace only complete, proven body triples and totals.

    Every replacement comes from the fixed per-run Source projection below,
    never an argument selecting excluded paths/keys. Prior bodies with a
    different digest stay exact, including unknown earlier metadata outputs.
    """
    remaining(deadline)
    if isinstance(value, list):
        return [_remap(item, replacements, deadline=deadline) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: _remap(item, replacements, deadline=deadline) for key, item in value.items()}
    if {"path", "sha256", "bytes"} <= set(value):
        path = value["path"]
        full_path = path if path.startswith(PROJECT + "/") else PROJECT + "/" + path
        replacement = replacements.get((full_path, value["sha256"], value["bytes"]))
        if replacement is not None:
            result.update(sha256=replacement["sha256"], bytes=replacement["bytes"])
        prior = value.get("prior_observed")
        if prior is not None:
            replacement = replacements.get((full_path, prior["sha256"], prior["bytes"]))
            if replacement is not None:
                result["prior_observed"] = {**prior, "sha256": replacement["sha256"], "bytes": replacement["bytes"]}
    if "records" in value:
        for key in ("total_bytes", "total_returned_bytes", "total_written_bytes"):
            if key in value:
                result[key] = sum(row["bytes"] for row in result["records"])
    return result


def code_contextual_semantics(
    source: NativeSourceContext,
    reader: SnapshotReader,
    analysis: dict[str, Any],
    hydration: dict[str, Any],
    joined: dict[str, Any],
    *,
    deadline: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project exact per-run DATA only after the existing direct genuine join.

    Both roles use this same fixed function. All raw digest/binding checks and
    complete per-run bytes stay mandatory. Unknown transforms/Mermaid refuse
    this bounded contextual normalization instead of dropping their behavior.
    """
    analysis_semantics = native_analysis_semantics(analysis, reader, deadline=deadline)
    hydration_semantics = native_hydration_semantics(hydration)
    if (
        reader.root != source.bindings.current_root
        or analysis["scope"] != "templates/template_code_project"
        or joined["scope"] != analysis["scope"]
        or hydration["scope"] != analysis["scope"]
        or joined["analysis_digest"] != analysis["content_digest"]
        or joined["hydration_digest"] != hydration["content_digest"]
        or joined["pipeline_run_id"] != analysis["pipeline_run_id"]
        or hydration["pipeline_run_id"] != analysis["pipeline_run_id"]
        or any(
            row["source_binding"] != [source.reference.commit, source.reference.source_identity]
            for row in (analysis, hydration, joined)
        )
        or joined["content_digest"]
        != canonical_digest({key: value for key, value in joined.items() if key != "content_digest"})
    ):
        raise ValueError("Code contextual comparison lost its exact direct per-run Source/graph join")
    selected = [row for row in joined["values"] if row["key"] in METADATA_KEYS]
    if not selected:
        return analysis_semantics, hydration_semantics
    variables = _held(hydration["variables"], reader)
    decoded = variables.json_object()
    stages = [row for row in analysis["ordered_stages"] if row["stage_key"] == HYDRATION]
    if len(stages) != 1:
        raise ValueError("Code contextual comparison lacks its actual complete hydration stage")
    stage = stages[0]
    observation = reader.read(PROJECT + "/" + OBSERVATION, max_bytes=1024 * 1024)
    origin, missing = _registered_metadata_origin(
        stage,
        observation,
        variables,
        source_sha256=hashlib.sha256(source.reference.read(SOURCE)).hexdigest(),
        deadline=deadline,
    )
    leaf = _held(stage["leaf"], reader)
    actual_runtime = leaf.json_object()["worker"]["completion"]["actual_runtime"]["python_version"]
    captured = observation.json_object()
    expected = validate_metadata_observation(captured, decoded, actual_python_runtime=actual_runtime, deadline=deadline)
    if (
        missing is not None
        or origin is None
        or any(
            row["metadata_origin"] != origin
            or row["observation"] != _binding(observation)
            or row["variables"] != _binding(variables)
            or row["payload"] != expected[row["key"]]
            for row in selected
        )
    ):
        raise ValueError("Code contextual comparison lacks its actual per-run metadata integrity/origin")
    canonical_variables = {**decoded, **{key: "{{" + key + "}}" for key in METADATA_KEYS}}
    canonical_capture = {
        **captured,
        "timestamp": {key: "Source-observed-contextual-timestamp" for key in captured["timestamp"]},
        "runtime": {key: "Source-observed-contextual-runtime:" + key for key in captured["runtime"]},
    }
    replacements: dict[tuple[str, str, int], dict[str, Any]] = {}

    def retain(snapshot: ArtifactSnapshot, content: bytes) -> dict[str, Any]:
        canonical = _body(snapshot.relative, content)
        replacements[(snapshot.relative, snapshot.sha256, len(snapshot.content))] = canonical
        return canonical

    variable_binding = retain(variables, _json(canonical_variables))
    retain(observation, _json(canonical_capture))
    projected_rows, bodies = [], []
    for row in hydration["ordered_inputs"]:
        remaining(deadline)
        consumed = _held(row["consumed"], reader)
        if row.get("transformation") == "Source-generated-transmission-boundary":
            details = row["bookend"]
            selected_config = _held(details["config"], reader)
            ledger = None if details["ledger"] is None else _held(details["ledger"], reader)
            rebuilt, reconstructed = reconstruct_transmission_bookend(selected_config, ledger, consumed.path.name)
            if rebuilt != consumed.content or reconstructed != details:
                raise ValueError("Code contextual projection lost complete Source transmission reconstruction")
            projected_rows.append(dict(row))
            bodies.append(consumed.content)
            continue
        if "source" not in row:
            raise ValueError("Code contextual projection retains an unsupported selected generated fragment")
        original = _held(row["source"], reader)
        if original.content != source.reference.read(original.relative):
            raise ValueError("Code contextual projection differs from complete authored Source bytes")
        if row["transformation"] == "shared-uppercase-token-hydration":
            actual = require_shared_hydration(original.content, decoded, consumed.content)
            if actual.data() != row["hydration"]:
                raise ValueError("Code contextual projection lost its complete real per-run occurrence ledger")
            canonical_hydration = reconstruct_shared_hydration(original.content, canonical_variables)
            projected_rows.append(
                {
                    **row,
                    "consumed": retain(consumed, canonical_hydration.output),
                    "hydration": canonical_hydration.data(),
                }
            )
            bodies.append(canonical_hydration.output)
        elif row["transformation"] == "exact-authored-source-body" and original.content == consumed.content:
            projected_rows.append(dict(row))
            bodies.append(consumed.content)
        else:
            raise ValueError(
                "Code contextual projection requires an implemented complete selected Source transformation"
            )
    pdf = hydration["pdf_recomposition"]
    if pdf["mermaid_transformations"] or pdf["sha256"] is None or hydration["independent_combined_sha256"] is None:
        raise ValueError("Code contextual projection retains unsupported Source Mermaid/composition requirements")
    config = _held(hydration["config"], reader)
    dotted = None if hydration["dotted_variables"] is None else _held(hydration["dotted_variables"], reader)
    settings = yaml.safe_load(config.content)
    canonical_pdf, mermaid, gaps = _pdf_body(
        tuple(bodies), settings, dotted, reader, analysis["scope"], deadline=deadline
    )
    if canonical_pdf is None or mermaid or gaps:
        raise ValueError("Code contextual Source recomposition cannot normalize unsupported generated assets")
    combined = _held(hydration["combined"], reader)
    algorithm = hydration["algorithm"]
    canonical_combined = _combined_body(algorithm, tuple(bodies), settings, canonical_pdf)
    if canonical_combined is None:
        raise ValueError("Code contextual projection lacks complete actual Source composition bytes")
    combined_binding = retain(combined, canonical_combined)
    composition = _held(hydration["composition"], reader)
    raw_composition = composition.json_object()
    input_rows = tuple(
        CompositionInput(
            row["ordinal"],
            Path(row["consumed"]["path"]).relative_to(PROJECT).as_posix(),
            row["consumed"]["bytes"],
            row["consumed"]["sha256"],
        )
        for row in projected_rows
    )
    input_digest = _digest_rows(input_rows)
    canonical_composition = ManuscriptComposition(
        project=raw_composition["project"],
        input_root_kind=raw_composition["input_root_kind"],
        ordered_inputs=input_rows,
        ordered_inputs_sha256=input_digest,
        combined_path=raw_composition["combined_path"],
        combined_size_bytes=len(canonical_combined),
        combined_sha256=combined_binding["sha256"],
        binding_sha256=_binding_digest(input_digest, raw_composition["combined_path"], combined_binding["sha256"]),
        schema_version=raw_composition["schema_version"],
        algorithm=algorithm,
    )
    composition_binding = retain(composition, _json(canonical_composition.to_dict()))
    projected_hydration = {
        **hydration_semantics,
        "variables": variable_binding,
        "ordered_inputs": projected_rows,
        "composition": composition_binding,
        "combined": combined_binding,
        "independent_combined_sha256": combined_binding["sha256"],
        "pdf_recomposition": {**pdf, "sha256": hashlib.sha256(canonical_pdf).hexdigest(), "bytes": len(canonical_pdf)},
    }
    projected_analysis = _remap(analysis_semantics, replacements, deadline=deadline)
    if not isinstance(projected_analysis, dict):
        raise ValueError("Code contextual projection changed the complete analysis object")
    for body in (projected_analysis, projected_hydration):
        body["content_digest"] = canonical_digest(
            {key: value for key, value in body.items() if key != "content_digest"}
        )
    if not reader.unchanged():
        raise ValueError("Code contextual projection changed held Source/output/evidence bytes")
    remaining(deadline)
    return projected_analysis, projected_hydration

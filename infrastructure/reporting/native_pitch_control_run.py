"""Real configured Pitch controls under an existing Source/SDK native owner."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.installed_acceptance_artifacts import write_binary
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_office_observer import convert_office
from infrastructure.reporting.native_office_reference_visual import inspect_office_reference_projection
from infrastructure.reporting.native_pitch_control_mutations import mutate_pitch
from infrastructure.reporting.native_pitch_control_plan import SCOPE, PitchTarget, compile_pitch_control_plan
from infrastructure.reporting.native_pitch_source_layout import (
    LAYOUT_CANONICALIZATION,
    LAYOUT_SCHEMA,
    pitch_package_layout,
)
from infrastructure.reporting.native_pitch_source_parity import inspect_pitch_package
from infrastructure.reporting.native_projection_checks import inspect_projection
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCHEMA = "template-native-pitch-configured-control-v1"


def _native(
    root: Path,
    directory: Path,
    snapshot: ArtifactSnapshot,
    kind: str,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> tuple[dict[str, Any], ArtifactSnapshot, tuple[bytes, ...]]:
    create_private_native_directory(root, directory)
    conversion = None
    if kind == "pptx":
        conversion = convert_office(root, directory, snapshot, kind, env=env, deadline=deadline, run_id=run_id)
        native = reader.read(conversion["pdf"]["path"])
        if native.sha256 != conversion["pdf"]["sha256"]:
            raise ValueError("Pitch converted native input changed")
    elif kind == "pdf":
        native = snapshot
    else:
        raise ValueError("Pitch controls cannot substitute an undeclared native format")
    raster = audit_pdf_raster(
        root,
        directory,
        native,
        parse_native_bytes("pdf", native.content),
        env=env,
        deadline=deadline,
        run_id=run_id,
        ordinal=0,
    )
    pixels = tuple(reader.read(row["path"]).content for row in raster["rasters"])
    return (
        {"conversion": conversion, "pdf": {"path": native.relative, "sha256": native.sha256}, "raster": raster},
        native,
        pixels,
    )


def _source(
    root: Path,
    directory: Path,
    artifact: Any,
    model: Any,
    pages: tuple[Any, ...],
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> tuple[dict[str, Any], bytes, tuple[bytes, ...]]:
    import yaml
    from infrastructure.rendering.pptx_deck import render_pptx
    from infrastructure.rendering.slide_deck import DeckTheme, render_pdf

    create_private_native_directory(root, directory)
    config = yaml.safe_load(reader.read(f"projects/{SCOPE}/manuscript/config.yaml").content)
    deck = config["project_config"]["deck"]
    theme = DeckTheme(**deck.get("theme", {}))
    path = directory / f"source.{artifact.format}"
    renderer = render_pdf if artifact.format == "pdf" else render_pptx
    renderer(model, path, theme=theme, source_base_url=str(deck.get("source_base_url", "")))
    snapshot = reader.read(path.relative_to(root).as_posix())
    binding = {"path": snapshot.relative, "sha256": snapshot.sha256}
    if artifact.format == "pptx":
        return (
            {
                "schema_version": LAYOUT_SCHEMA,
                "canonicalization": LAYOUT_CANONICALIZATION,
                "input": binding,
                "layout_digest": canonical_digest(pitch_package_layout(snapshot.content)),
            },
            snapshot.content,
            (),
        )
    native, _, pixels = _native(
        root, directory / "native", snapshot, "pdf", reader, env=env, deadline=deadline, run_id=run_id
    )
    return {"input": binding, "native": native}, snapshot.content, pixels


def _inspect(
    root: Path,
    directory: Path,
    artifact: Any,
    candidate: ArtifactSnapshot,
    model: Any,
    pages: tuple[Any, ...],
    source_bytes: bytes,
    source_pixels: tuple[bytes, ...],
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    native, pdf, pixels = _native(
        root, directory / "native", candidate, artifact.format, reader, env=env, deadline=deadline, run_id=run_id
    )
    observation = inspect_projection(
        pdf.content, pixels, pages, deadline=deadline, native_context=(root, directory / "native", env, run_id)
    )
    package = None
    reference = None
    if artifact.format == "pptx":
        package = inspect_pitch_package(
            candidate.content,
            pages,
            deadline=deadline,
            native_context=(root, directory, env, run_id),
            source_model=model,
        )
        actual, expected = pitch_package_layout(candidate.content), pitch_package_layout(source_bytes)
        findings = [
            {"code": "pitch.package.source.layout", "part": name}
            for name in sorted(actual.keys() | expected.keys())
            if actual.get(name) != expected.get(name)
        ]
        package["findings"].extend(findings)
        package["source_layout"] = {
            "schema_version": LAYOUT_SCHEMA,
            "canonicalization": LAYOUT_CANONICALIZATION,
            "source_layout_digest": canonical_digest(expected),
            "candidate_layout_digest": canonical_digest(actual),
            "parts": len(expected),
            "findings": findings,
            "status": "fail" if findings else "pass",
        }
        package["status"] = "fail" if package["findings"] else "blocked" if package["blockers"] else "pass"
    else:
        reference = inspect_office_reference_projection(
            source_bytes, source_pixels, pdf.content, pixels, deadline=deadline
        )
    findings = [
        *observation["findings"],
        *(package["findings"] if package else []),
        *(reference["findings"] if reference else []),
    ]
    blockers = [*observation["blockers"], *(package["blockers"] if package else [])]
    return {
        "native": native,
        "projection": observation,
        "package": package,
        "reference": reference,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def run_pitch_control(
    root: Path,
    directory: Path,
    name: str,
    *,
    formats: tuple[str, ...],
    reader: SnapshotReader,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, str]:
    """Each single-page mutant retains all other actual pages and native reads.

    The baseline inspects all six actual files once. Each named negative child
    must reject *every* independently selected target with the intended code;
    one successful target, unsupported observation or unexpected failure refuses
    the suite. Real parent signed OS outcomes are separately authenticated.
    """
    owner = current_native_producer_operation()
    if owner is None or owner.run_id != run_id or not directory.is_relative_to(owner.stage_scope_directory(SCOPE)):
        raise ValueError("Pitch controls need the actual paired Source owner/private scope")
    plan, models = compile_pitch_control_plan(root, reader, formats=formats, deadline=deadline)
    if name not in plan["active_controls"]:
        raise ValueError("Pitch control is absent from the complete Source-derived applicability plan")
    create_private_native_directory(root, directory)
    references: dict[str, tuple[dict[str, Any], bytes, tuple[bytes, ...]]] = {}
    inputs: dict[str, ArtifactSnapshot] = {}
    rows = []
    start = len(owner.retained_tool_bindings)
    for ordinal, declaration in enumerate(plan["targets"][name]):
        remaining(deadline)
        target = PitchTarget(**declaration)
        artifact, model, pages = models[target.artifact_id]
        if artifact.id not in inputs:
            inputs[artifact.id] = reader.read(artifact.path)
        original = inputs[artifact.id]
        if artifact.id not in references:
            references[artifact.id] = _source(
                root,
                directory / f"source-{len(references):04d}",
                artifact,
                model,
                pages,
                reader,
                env=env,
                deadline=deadline,
                run_id=run_id,
            )
        reference, source_bytes, source_pixels = references[artifact.id]
        candidate_bytes = mutate_pitch(original.content, artifact.format, target, deadline=deadline)
        leaf = directory / f"target-{ordinal:04d}"
        create_private_native_directory(root, leaf)
        binding = write_binary(root, leaf / f"candidate.{artifact.format}", candidate_bytes)
        candidate = reader.read(binding["path"])
        if candidate.sha256 != binding["sha256"]:
            raise ValueError("Pitch actual control candidate changed before native consumption")
        observed = _inspect(
            root,
            leaf,
            artifact,
            candidate,
            model,
            pages,
            source_bytes,
            source_pixels,
            reader,
            env=env,
            deadline=deadline,
            run_id=run_id,
        )
        code = target.intended_diagnostic
        if observed["blockers"] or (code is None and observed["status"] != "pass"):
            raise ValueError("Pitch full configured control has a failing baseline or unsupported native target")
        if code is not None and (
            observed["status"] != "fail"
            or not any(
                finding.get("code") == code
                and (
                    finding.get("page") == target.page
                    or artifact.format == "pptx"
                    and code == "pitch.package.source.layout"
                )
                for finding in observed["findings"]
            )
        ):
            raise ValueError("Pitch single-target native mutant lacked its intended page diagnostic")
        rows.append(
            {
                "target": asdict(target),
                "artifact": asdict(artifact),
                "input": {"path": original.relative, "sha256": original.sha256},
                "candidate": binding,
                "parser": parse_native_bytes(artifact.format, candidate.content),
                "observation": observed,
                "oracle_exit_code": 0 if code is None else 1,
            }
        )
    owner.verify(reader, run_id=run_id, deadline=deadline)
    remaining(deadline)
    if not rows or not reader.unchanged():
        raise ValueError("Pitch exact selected control roster or Source/native bodies changed")
    return write_json(
        root,
        directory.parent / "control-observation.json",
        {
            "schema_version": SCHEMA,
            "scope": SCOPE,
            "name": name,
            "run_id": run_id,
            "source": json.loads(owner.source.descriptor(SCOPE, deadline=deadline)),
            "plan": plan,
            "references": {key: value[0] for key, value in references.items()},
            "rows": rows,
            "tool_artifacts": list(owner.retained_tool_bindings)[start:],
            "oracle_exit_code": 0 if name == "baseline" else 1,
        },
    )

"""Bound artifact evidence replay for native format acceptance.

Each predicate re-reads one recorded observation from its exact bound bytes and
refuses anything that differs from the actual source: file bindings, original
process outcomes, tool custody and raster observations. Replay only; the
acceptance orchestration that consumes these observations lives in
``native_format_acceptance_validation``.
"""

from __future__ import annotations

import math
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.plan_serialization import plan_from_payload
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import (
    CITATION_TOOL_FIELDS,
    HTML_TOOL_FIELDS,
    PROCESS_SCHEMA,
    TOOL_FIELDS,
    TOOL_SCHEMA,
)
from infrastructure.reporting.native_format_portable_custody import (
    producer_path,
    validate_executable_observation,
)
from infrastructure.reporting.native_format_portable_source import native_source_content_identity
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

__all__ = ["_file", "_pipeline", "_process", "_raster", "_tool"]


def _file(binding: object, reader: SnapshotReader) -> ArtifactSnapshot:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise ValueError("native evidence requires an exact artifact binding")
    snapshot = reader.read(binding["path"])
    if binding["sha256"] != snapshot.sha256 or not snapshot.content:
        raise ValueError("native evidence bytes differ from their binding")
    return snapshot


def _process(raw: dict[str, Any], nonce: str, command: list[str], code: int) -> None:
    if (
        raw.get("schema_version") != PROCESS_SCHEMA
        or raw.get("run_id") != nonce
        or raw.get("command") != command
        or type(raw.get("exit_code")) is not int
        or raw["exit_code"] != code
        or type(raw.get("original_exit_code")) is not int
        or raw["original_exit_code"] != code
        or raw.get("timed_out") is not False
        or raw.get("custody_refused") is not False
    ):
        raise ValueError("native process did not produce its bound original outcome")


def _tool(
    binding: object,
    reader: SnapshotReader,
    nonce: str,
    name: str,
    purpose: str,
    arguments: list[str],
    code: int = 0,
) -> dict[str, Any]:
    raw = _file(binding, reader).json_object()
    executable = raw.get("executable")
    if not isinstance(executable, str) or not Path(executable).is_absolute():
        raise ValueError("native tool identity is not an actual absolute executable")
    if (
        frozenset(raw) not in {TOOL_FIELDS, CITATION_TOOL_FIELDS, HTML_TOOL_FIELDS}
        or raw.get("schema_version") != TOOL_SCHEMA
        or raw.get("run_id") != nonce
        or raw.get("tool") != name
        or raw.get("purpose") != purpose
        or not isinstance(raw.get("command"), list)
        or len(raw["command"]) != len(arguments) + 1
        or raw["command"][1:] != arguments
        or type(raw.get("exit_code")) is not int
        or raw["exit_code"] != code
        or type(raw.get("original_exit_code")) is not int
        or raw["original_exit_code"] != code
        or raw.get("timed_out") is not False
        or raw.get("custody_refused") is not False
    ):
        raise ValueError("actual native tool command/run/outcome differs from its required observation")
    if frozenset(raw) == HTML_TOOL_FIELDS and (
        not isinstance(raw["html_python_source_closure"], dict) or raw["html_python_source_closure_error"] is not None
    ):
        raise ValueError("actual HTML Python launch requires its closed Source observation")
    # The original nomination, including an admitted venv launcher, is closed
    # against actual Popen argv and physical body in validate_native_tool_data.
    # An absolute requested nomination must additionally remain argv[0].
    process = _file(raw.get("native_process_artifact"), reader).json_object()
    nomination = process.get("nomination")
    if (
        not isinstance(nomination, dict)
        or nomination.get("tool") != name
        or nomination.get("resolved_path") != executable
        or (Path(name).is_absolute() and nomination.get("path") != name)
        or raw["command"][0] != (nomination.get("path") if process.get("launcher_preserved") else executable)
    ):
        raise ValueError("actual Source-nominated launcher differs from original Popen custody")
    for key in ("executable_observation_before", "executable_observation_after"):
        validate_executable_observation(raw.get(key), executable, raw.get("executable_sha256"))
    from infrastructure.reporting.native_tool_replay import (
        validate_original_native_tool,
    )

    if reader.native_producer_operation is not None:
        from infrastructure.reporting.native_tool_producer import (
            validate_live_native_tool,
        )

        validate_live_native_tool(binding, raw, reader, run_id=nonce)
    else:
        validate_original_native_tool(binding, raw, reader, run_id=nonce)
    return raw


def _pipeline(raw: dict[str, Any], scope: str, reader: SnapshotReader, custody: dict[str, Any]) -> RunResult:
    from infrastructure.reporting.native_format_acceptance_worker import (
        require_canonical_native_stages,
    )

    if raw.get("mode") != "core" or raw.get("selection") != {
        "skip_clean": True,
        "skip_infra": True,
    }:
        raise ValueError("native conformance requires explicit whole-core selection")
    plan = plan_from_payload(raw.get("plan"), expected_digest=raw.get("plan_digest"))
    if plan.project != scope or not isinstance(raw.get("run_id"), str) or not raw["run_id"]:
        raise ValueError("native pipeline has a different project/run identity")
    reader.read(plan.provenance)
    config = PipelineConfig(
        scope,
        reader.root,
        clean=False,
        skip_infra=True,
        mode="core",
        run_timeout_seconds=plan.run_timeout_seconds,
    )
    expected = compile_execution_plan(config)
    require_canonical_native_stages(expected)
    # Runtime/environment identities belong to the admitted worker, not the
    # environment of a later reader. Compare the entire logical source plan;
    # source bytes, actual interpreter and tools have their separate bindings.
    recorded_shape, expected_shape = plan.to_dict(), expected.to_dict()
    for key in ("source_identity", "environment_identity"):
        recorded_shape.pop(key)
        expected_shape.pop(key)
    if recorded_shape != expected_shape:
        raise ValueError("native execution differs from the complete current source-owned plan")
    content = native_source_content_identity(
        reader.root,
        config.project_dir,
        custody,
        definition_path=reader.root / plan.provenance,
    )
    if raw.get("source_content_identity") != content or raw.get("expected_stage_keys") != list(
        plan.expected_stage_keys
    ):
        raise ValueError("native execution source or expected stages changed")
    rows = raw.get("outcomes")
    if not isinstance(rows, list):
        raise ValueError("native stage outcomes are absent")
    outcomes = []
    for row in rows:
        if not isinstance(row, dict) or row.get("status") != "succeeded":
            raise ValueError("native acceptance needs every fresh succeeded stage")
        codes = row.get("attempt_exit_codes")
        attempts = row.get("attempt_count")
        if (
            not isinstance(codes, list)
            or type(attempts) is not int
            or len(codes) != attempts
            or not codes
            or codes[-1] != 0
        ):
            raise ValueError("native actual child attempt history is incomplete")
        outcome = StageOutcome(
            row.get("stage_key", ""),
            StageStatus.SUCCEEDED,
            row.get("child_exit_code"),
            attempt_count=attempts,
            attempt_exit_codes=tuple(codes),
        )
        if outcome.child_exit_code != 0:
            raise ValueError("native stage did not execute an actual successful child")
        outcomes.append(outcome)
    result = RunResult(plan.expected_stage_keys, tuple(outcomes))
    if not result.complete or result.exit_code:
        raise ValueError("native execution omitted or duplicated required stages")
    return result


def _raster(
    row: dict[str, Any],
    snapshot: ArtifactSnapshot,
    ordinal: int,
    directory: Path,
    reader: SnapshotReader,
    nonce: str,
    versions: dict[str, dict[str, Any]],
    custody: dict[str, str],
) -> None:
    from PIL import Image, ImageStat

    raw = row.get("raster")
    if not isinstance(raw, dict) or raw.get("dpi") != 150:
        raise ValueError("native PDF must have an actual complete 150-dpi raster observation")
    consumed = _file(raw.get("input_artifact"), reader)
    if consumed.path != directory / f"input-{ordinal:04d}.pdf" or consumed.content != snapshot.content:
        raise ValueError("native tools consumed different input bytes from the admitted PDF")
    tools = raw.get("tool_artifacts")
    if not isinstance(tools, list) or len(tools) != 2:
        raise ValueError("native raster/font tools were not both executed")
    prefix = directory / f"raster-{ordinal:04d}"
    for index, (name, arguments, purpose) in enumerate(
        (
            (
                "pdftoppm",
                [
                    "-r",
                    "150",
                    "-png",
                    str(producer_path(custody, reader.root, consumed.path)),
                    str(producer_path(custody, reader.root, prefix)),
                ],
                f"raster-{ordinal:04d}",
            ),
            (
                "pdffonts",
                [str(producer_path(custody, reader.root, consumed.path))],
                f"fonts-{ordinal:04d}",
            ),
        )
    ):
        tool = _tool(tools[index], reader, nonce, name, purpose, arguments)
        if any(tool[key] != versions[name][key] for key in ("executable", "executable_sha256")):
            raise ValueError("native raster used a different tool from its actual version probe")
    rows = raw.get("rasters")
    # Replay every observer schema against geometry parsed from admitted PDF bytes.
    boxes = parse_native_bytes("pdf", snapshot.content)["page_boxes_pt"]
    if not isinstance(rows, list) or len(rows) != len(boxes):
        raise ValueError("native raster omitted actual PDF pages")
    for page, (raster, box) in enumerate(zip(rows, boxes, strict=True), 1):
        if not isinstance(raster, dict):
            raise ValueError("native raster observation is malformed")
        image_file = _file({"path": raster.get("path"), "sha256": raster.get("sha256")}, reader)
        if (
            image_file.path.parent != directory
            or re.fullmatch(
                re.escape(prefix.name) + r"-0*" + str(page) + r"\.png",
                image_file.path.name,
            )
            is None
        ):
            raise ValueError("native raster has the wrong run/page identity")
        with Image.open(BytesIO(image_file.content)) as image:
            image.load()
            variance = sum(ImageStat.Stat(image.convert("RGB")).var)
            if image.format != "PNG" or not math.isfinite(variance) or variance <= 0:
                raise ValueError("native raster is empty/uniform or invalid")
            if (
                raster.get("width_px"),
                raster.get("height_px"),
                raster.get("variance"),
            ) != (
                image.width,
                image.height,
                variance,
            ):
                raise ValueError("native raster observation differs from its actual pixel bytes")
            expected = ((box[2] - box[0]) * 150 / 72, (box[3] - box[1]) * 150 / 72)
            if abs(image.width - expected[0]) > 2 or abs(image.height - expected[1]) > 2:
                raise ValueError("native raster geometry differs from the actual PDF page")

"""Existing literal PDF controls, with freshly checked complete return DATA."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import WORKER_MODULE
from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes
from infrastructure.reporting.native_format_portable_custody import producer_bootstrap, producer_path
from infrastructure.reporting.native_format_pdf_oracles import (
    PDF_CONTROL_CODES,
    PDF_CONTROL_SCHEMA,
    inspect_pdf_content,
    pdf_control_contract,
    pdf_control_bytes,
    require_pdf_control_result,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def replay_pdf_controls(
    raw: dict[str, Any],
    reader: SnapshotReader,
    directory: Path,
    nonce: str,
    runtime: dict[str, Any],
    specification: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    required: bool,
    custody: dict[str, str],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Reparse valid fixtures and recompute their exact intended semantic faults."""
    from infrastructure.reporting.native_format_acceptance_validation import _file, _raster, _process

    outcomes: list[dict[str, Any]] = []
    controls = raw.get("pdf_negative_controls")
    names = list(PDF_CONTROL_CODES) if required else []
    if not isinstance(controls, list) or [item.get("name") for item in controls if isinstance(item, dict)] != names:
        raise ValueError("native actual valid-PDF baseline/negative controls are absent or duplicated")
    for control, name in zip(controls, names, strict=True):
        observed_file = _file(control.get("artifact"), reader)
        if observed_file.path != directory / f"pdf-oracle-{name}.json":
            raise ValueError("valid-PDF control belongs to a different evidence attempt")
        observed = observed_file.json_object()
        contract = pdf_control_contract()
        if (
            observed.get("schema_version") != PDF_CONTROL_SCHEMA
            or observed.get("run_id") != nonce
            or observed.get("name") != name
            or observed.get("content_contract") != contract.to_dict()
        ):
            raise ValueError("valid-PDF control contract/run/name changed")
        row = observed.get("artifact")
        if not isinstance(row, dict) or row.get("id") != "invented-control:pdf" or row.get("format") != "pdf":
            raise ValueError("valid-PDF control requires the actual invented PDF artifact")
        snapshot = _file({"path": row.get("path"), "sha256": row.get("sha256")}, reader)
        control_directory = directory / f"pdf-oracle-{name}-artifacts"
        if snapshot.path != control_directory / "invented-control.pdf" or snapshot.content != pdf_control_bytes(name):
            raise ValueError("valid-PDF control does not contain its exact current valid mutant bytes")
        if row.get("observation") != parse_native_bytes("pdf", snapshot.content):
            raise ValueError("valid-PDF control did not actually parse successfully")
        _raster(row, snapshot, 0, control_directory, reader, nonce, versions, custody)
        oracle = inspect_pdf_content(
            snapshot.content,
            tuple(reader.read(item["path"]).content for item in row["raster"]["rasters"]),
            contract,
            deadline=deadline,
        )
        if observed.get("pdf_content") != oracle:
            raise ValueError("valid-PDF control semantic/geometry/pixel observations changed")
        code = require_pdf_control_result(name, oracle)
        if (
            type(observed.get("exit_code")) is not int
            or observed["exit_code"] != code
            or control.get("expected_exit_code") != code
            or control.get("observed_exit_code") != code
        ):
            raise ValueError("valid-PDF control did not preserve its exact intended original outcome")
        args = [
            "--root",
            custody["root"],
            "--pdf-oracle-control",
            name,
            "--run-id",
            nonce,
            "--control-output",
            str(producer_path(custody, reader.root, observed_file.path)),
            "--deadline-monotonic",
            str(specification["deadline_monotonic"]),
        ]
        command = producer_bootstrap(custody, reader.root, runtime, WORKER_MODULE, *args)
        _process(
            _file(control.get("process_artifact"), reader).json_object(),
            nonce,
            command,
            code,
        )
        outcomes.append(
            {
                "name": name,
                "original_exit_code": code,
                "reconstructed_exit_code": code,
                "intended_diagnostic": PDF_CONTROL_CODES[name],
                "targets": [{"fixture": "invented-control:pdf", "name": name}],
                "observation": oracle,
                "artifact": control["artifact"],
            }
        )
    if not reader.unchanged():
        raise ValueError("PDF complete control replay changed held source evidence")
    return {"suite_id": "pdf", "original_run_id": nonce, "outcomes": outcomes} if required else {}

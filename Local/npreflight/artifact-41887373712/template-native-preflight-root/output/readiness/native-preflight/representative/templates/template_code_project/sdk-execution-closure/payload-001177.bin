"""Existing worker parser/PDF controls under the original exact worker CLI role."""

from __future__ import annotations

import math
import re
import sys
import time
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import bootstrap_command, read_json, write_json
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import (
    PROCESS_SCHEMA,
    WORKER_MODULE,
    create_private_native_directory,
    native_environment,
)
from infrastructure.reporting.native_format_pdf_oracles import (
    PDF_CONTROL_CODES,
    PDF_CONTROL_SCHEMA,
    inspect_pdf_content,
    pdf_control_bytes,
    pdf_control_contract,
    require_pdf_control_result,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _parser_control(
    root: Path,
    directory: Path,
    run_id: str,
    kind: str,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    name = f"invalid-native-{kind}"
    path = directory / f"{name}.json"
    command = bootstrap_command(
        Path(sys.executable),
        root,
        WORKER_MODULE,
        "--root",
        str(root),
        "--control",
        kind,
        "--run-id",
        run_id,
        "--control-output",
        str(path),
    )
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("native negative-control deadline expired")
    process = run_bounded_subprocess(command, cwd=root, env=env, timeout=min(remaining, 60))
    raw = read_json(root, path)
    if process.returncode != 1 or process.original_returncode != 1 or raw.get("exit_code") != 1:
        raise ValueError("actual native parser negative control did not fail as required")
    observed = write_json(
        root,
        directory / f"{name}-process.json",
        {
            "schema_version": PROCESS_SCHEMA,
            "run_id": run_id,
            "command": list(command),
            "exit_code": process.returncode,
            "original_exit_code": process.original_returncode,
            "timed_out": process.timed_out,
            "custody_refused": process.custody_refused,
        },
    )
    snapshot = SnapshotReader(root).read(path.relative_to(root).as_posix())
    return {
        "name": name,
        "expected_exit_code": 1,
        "observed_exit_code": 1,
        "artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "process_artifact": observed,
    }


def _pdf_oracle_control(
    root: Path,
    directory: Path,
    run_id: str,
    name: str,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    """Require a real valid-PDF baseline before accepting specific mutant faults."""
    path = directory / f"pdf-oracle-{name}.json"
    command = bootstrap_command(
        Path(sys.executable),
        root,
        WORKER_MODULE,
        "--root",
        str(root),
        "--pdf-oracle-control",
        name,
        "--run-id",
        run_id,
        "--control-output",
        str(path),
        "--deadline-monotonic",
        str(deadline),
    )
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("actual valid-PDF controls exhausted the original deadline")
    process = run_bounded_subprocess(command, cwd=root, env=env, timeout=min(remaining, 60))
    raw = read_json(root, path)
    code = require_pdf_control_result(name, raw["pdf_content"])
    if process.returncode != code or process.original_returncode != code or raw.get("exit_code") != code:
        raise ValueError("actual valid-PDF control process did not preserve its intended original outcome")
    observed = write_json(
        root,
        directory / f"pdf-oracle-{name}-process.json",
        {
            "schema_version": PROCESS_SCHEMA,
            "run_id": run_id,
            "command": list(command),
            "exit_code": process.returncode,
            "original_exit_code": process.original_returncode,
            "timed_out": process.timed_out,
            "custody_refused": process.custody_refused,
        },
    )
    snapshot = SnapshotReader(root).read(path.relative_to(root).as_posix())
    return {
        "name": name,
        "expected_exit_code": code,
        "observed_exit_code": code,
        "artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "process_artifact": observed,
    }


def run_pdf_oracle_control(root: Path, output: Path, name: str, nonce: str, deadline: float) -> int:
    """Internal actual child: unexpected setup errors cannot manufacture a receipt."""
    if name not in PDF_CONTROL_CODES or re.fullmatch(r"[0-9a-f]{32}", nonce) is None:
        raise ValueError("valid-PDF control requires its exact name and admitted run nonce")
    if not math.isfinite(deadline) or deadline <= time.monotonic():
        raise TimeoutError("valid-PDF control requires the remaining original finite deadline")
    directory = output.parent / f"pdf-oracle-{name}-artifacts"
    create_private_native_directory(root, directory)
    pdf = directory / "invented-control.pdf"
    atomic_write_bytes_confined(root, pdf, pdf_control_bytes(name), mode=0o600)
    reader = SnapshotReader(root)
    snapshot = reader.read(pdf.relative_to(root).as_posix())
    observation = parse_native_bytes("pdf", snapshot.content)
    env = native_environment(root, Path(sys.executable), directory)
    raster = audit_pdf_raster(
        root,
        directory,
        snapshot,
        observation,
        env=env,
        deadline=deadline,
        run_id=nonce,
        ordinal=0,
    )
    contract = pdf_control_contract()
    oracle = inspect_pdf_content(
        snapshot.content,
        tuple(reader.read(item["path"]).content for item in raster["rasters"]),
        contract,
        deadline=deadline,
    )
    code = require_pdf_control_result(name, oracle)
    if not reader.unchanged():
        raise ValueError("valid-PDF control custody changed during its observation")
    write_json(
        root,
        output,
        {
            "schema_version": PDF_CONTROL_SCHEMA,
            "run_id": nonce,
            "name": name,
            "exit_code": code,
            "content_contract": contract.to_dict(),
            "pdf_content": oracle,
            "artifact": {
                "id": "invented-control:pdf",
                "format": "pdf",
                "path": snapshot.relative,
                "sha256": snapshot.sha256,
                "observation": observation,
                "raster": raster,
            },
        },
    )
    return code

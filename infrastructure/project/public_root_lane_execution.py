"""Overlap only independent Root chunk supervision under one original deadline."""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
import math
from pathlib import Path
import time
from typing import Any

from infrastructure.core.subprocess_policy import BoundedSubprocessResult, SubprocessPolicy, run_with_policy
from infrastructure.project.public_root_case_admission import RootCaseAdmission
from infrastructure.project.public_root_case_units import RootCaseUnit
from infrastructure.project.public_root_lane_contract import (
    PROCESS_SCHEMA,
    chunk_workers,
    environment,
    groups,
    lane_command,
    write,
)
from infrastructure.project.public_root_lane_diagnostics import retain_output
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


@dataclass(frozen=True)
class ChunkObservation:
    index: int
    nodes: tuple[str, ...]
    command: tuple[str, ...]
    original: BoundedSubprocessResult
    remaining_budget_seconds: int
    launch_offset_seconds: float
    finish_offset_seconds: float


def _supervise(
    root: Path,
    command: tuple[str, ...],
    env: dict[str, str],
    spec: dict[str, Any],
    index: int,
    nodes: tuple[str, ...],
    started: float,
) -> ChunkObservation:
    # Queue/startup time consumes the same enclosing clock, never a fresh budget.
    launch = time.monotonic() - started
    remaining = math.floor(spec["timeout_seconds"] - launch)
    if remaining < 1:
        raise TimeoutError("lane deadline exhausted before actual chunk")
    observed = run_with_policy(
        command,
        cwd=root,
        env=env,
        policy=SubprocessPolicy(
            policy_id="root-v3-lane-chunk",
            source_path=__name__,
            timeout_seconds=remaining,
            credential_free=spec["mode"] == "core",
        ),
    )
    return ChunkObservation(index, nodes, command, observed, remaining, launch, time.monotonic() - started)


def _retain(
    root: Path, snapshot: ArtifactSnapshot, spec: dict[str, Any], result: ChunkObservation
) -> tuple[int, dict[str, Any]]:
    directory = root / spec["directory"] / f"chunk-{result.index:04d}"
    observed = result.original
    receipt_binding = None
    try:
        held = SnapshotReader(root).read((directory / "receipt.json").relative_to(root).as_posix())
        receipt_binding = {"path": held.relative, "sha256": held.sha256}
    except (OSError, ValueError):
        pass
    code = (
        130
        if observed.returncode in (-2, 130)
        else 124
        if observed.timed_out or observed.returncode == 124
        else 75
        if observed.returncode == 75
        else 0
        if observed.returncode == observed.original_returncode == 0
        and receipt_binding is not None
        and not observed.custody_refused
        and not observed.command_error
        else 1
    )
    process_binding = write(
        root,
        directory / "process.json",
        {
            "schema_version": PROCESS_SCHEMA,
            "command": list(result.command),
            "run_id": spec["run_id"],
            "nonce": spec["nonce"],
            "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
            "index": result.index,
            "receipt_artifact": receipt_binding,
            "returncode": observed.returncode,
            "original_returncode": observed.original_returncode,
            "timed_out": observed.timed_out,
            "custody_refused": observed.custody_refused,
            "command_error": observed.command_error,
            "remaining_budget_seconds": result.remaining_budget_seconds,
            "launch_offset_seconds": result.launch_offset_seconds,
            "finish_offset_seconds": result.finish_offset_seconds,
            "duration_seconds": result.finish_offset_seconds - result.launch_offset_seconds,
            "output_artifact": retain_output(root, directory, observed, spec["root_identity"]),
        },
        spec["root_identity"],
    )
    return code, {
        "index": result.index,
        "nodes": list(result.nodes),
        "receipt_artifact": receipt_binding,
        "process_artifact": process_binding,
    }


def execute_chunks(
    root: Path,
    snapshot: ArtifactSnapshot,
    spec: dict[str, Any],
    admitted: RootCaseAdmission,
    selected: RootCaseUnit,
    started: float,
    records: list[dict[str, Any]],
) -> int:
    """Admit/write on the controller; drain every launched guardian before returning.

    Only Source-declared external-fixture units overlap. Their cases operate on
    private physical fixtures; other units retain original serial supervision.
    A failed observation stops new launches, without discarding a running sibling.
    """
    pieces = groups(selected)
    workers = chunk_workers(selected)
    code = 0

    def prepare(index: int) -> tuple[tuple[str, ...], dict[str, str]]:
        directory = root / spec["directory"] / f"chunk-{index:04d}"
        return lane_command(root, snapshot, chunk=index), environment(
            admitted, selected.id, root, directory, spec["mode"]
        )

    def retain(result: ChunkObservation) -> None:
        nonlocal code
        actual, record = _retain(root, snapshot, spec, result)
        records.append(record)
        code = next((value for value in (130, 124, 1, 75) if value in (code, actual)), 0)

    if workers == 1:
        for index, nodes in enumerate(pieces):
            command, env = prepare(index)
            retain(_supervise(root, command, env, spec, index, nodes, started))
            if code:
                break
        return code

    pending: dict[Future[ChunkObservation], int] = {}
    next_index = 0
    failure: BaseException | None = None
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="root-chunk") as executor:
        while pending or (next_index < len(pieces) and not code and failure is None):
            while next_index < len(pieces) and len(pending) < workers and not code and failure is None:
                try:
                    command, env = prepare(next_index)
                    future = executor.submit(
                        _supervise, root, command, env, spec, next_index, pieces[next_index], started
                    )
                    pending[future] = next_index
                    next_index += 1
                except BaseException as error:
                    failure = error
                    break
            try:
                completed, _ = wait(pending, return_when=FIRST_COMPLETED)
            except KeyboardInterrupt as error:
                failure = error
                code = 130
                continue
            for future in sorted(completed, key=lambda item: pending[item]):
                pending.pop(future)
                try:
                    retain(future.result())
                except BaseException as error:
                    failure = error
        records.sort(key=lambda record: record["index"])
    if code == 130 or isinstance(failure, KeyboardInterrupt):
        return 130
    if code == 124:
        return 124
    if failure is not None:
        raise failure
    return code

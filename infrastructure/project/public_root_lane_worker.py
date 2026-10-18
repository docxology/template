"""Real exact-node Root v2 execution, guarded chunks and original case outcomes."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import math
import signal
import threading
import types
from importlib import import_module
from collections.abc import Iterator
import os
import time
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.implementation_custody import verify_implementation_custody
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.project.public_acceptance_case_observer import RootCaseObserver
from infrastructure.project.public_acceptance_case_policy import digest
from infrastructure.project.public_acceptance_evidence import runtime_identity, verify_runtime_execution
from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy, RuntimeScope
from infrastructure.project.public_root_case_admission import lane_blockers
from infrastructure.project.public_root_case_contract import _artifact, _fresh_prefix, _json
from infrastructure.project.public_root_lane_coverage import capture, measurement, merge, report
from infrastructure.project.public_root_lane_diagnostics import CaseDiagnostics, retain_output
from infrastructure.project.public_root_lane_contract import (
    CHUNK_SCHEMA,
    LANE_SCHEMA,
    PROCESS_SCHEMA,
    admission,
    arguments,
    environment,
    groups,
    lane_command,
    selection,
    write,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


class LaneObserver(RootCaseObserver):
    interrupted = False
    timed_out = False

    def __init__(self, reader: SnapshotReader, source_hashes: dict[str, str]) -> None:
        super().__init__(reader, source_hashes)
        module = import_module("pytest_timeout")
        timer, callback = getattr(module, "pytest_timeout_set_timer"), getattr(module, "timeout_sigalrm")
        if not isinstance(timer, types.FunctionType) or not isinstance(callback, types.FunctionType):
            raise ValueError("Root case deadline requires the actual selected pytest-timeout implementation")
        handlers = [
            constant
            for constant in timer.__code__.co_consts
            if isinstance(constant, types.CodeType) and constant.co_name == "handler"
        ]
        if len(handlers) != 1:
            raise ValueError("Root case deadline callback is unsupported by the selected test stack")
        self.callback_code, self.handler_code = callback.__code__, handlers[0]
        self.armed_deadlines: dict[str, float] = {}
        self.timeout_module = module
        self.thread_callback = getattr(module, "timeout_timer")
        cancellations = [
            constant
            for constant in timer.__code__.co_consts
            if isinstance(constant, types.CodeType)
            and constant.co_name == "cancel"
            and constant.co_freevars == ("timer",)
        ]
        if len(cancellations) != 1 or not isinstance(self.thread_callback, types.FunctionType):
            raise ValueError("Root case thread deadline is unsupported by the selected test stack")
        self.thread_cancel_code = cancellations[0]
        self.timer_cancel = threading.Timer.cancel
        self.timer_join = threading.Thread.join
        self.armed_thread_timers: dict[str, tuple[threading.Timer, types.FunctionType, object]] = {}

    def _thread_timer(self, item: pytest.Item, settings: object, cancel: object) -> threading.Timer:
        if (
            not isinstance(cancel, types.FunctionType)
            or cancel.__code__ is not self.thread_cancel_code
            or cancel.__globals__ is not vars(self.timeout_module)
            or cancel.__closure__ is None
            or len(cancel.__closure__) != 1
        ):
            raise ValueError("Root case thread deadline lacks its actual selected cancellation owner")
        timer = cancel.__closure__[0].cell_contents
        if (
            type(timer) is not threading.Timer
            or timer.function is not self.thread_callback
            or not isinstance(timer.args, tuple)
            or timer.args != (item, settings)
            or timer.args[0] is not item
            or timer.args[1] is not settings
            or timer.kwargs != {}
            or type(timer.interval) not in (int, float)
            or timer.interval != getattr(settings, "timeout", None)
            or not math.isfinite(timer.interval)
            or timer.interval <= 0
        ):
            raise ValueError("Root case thread deadline differs from its actual timer/callback/selection")
        return timer

    @pytest.hookimpl(hookwrapper=True)
    def pytest_timeout_cancel_timer(self, item: pytest.Item) -> Iterator[None]:
        held = self.armed_thread_timers.get(item.nodeid)
        if held is not None:
            timer, cancel, settings = held
            try:
                if (
                    getattr(item, "cancel_timeout", None) is not cancel
                    or self._thread_timer(item, settings, cancel) is not timer
                    or timer.finished.is_set()
                    or not timer.is_alive()
                ):
                    raise ValueError("Root case thread deadline changed or stopped before actual cancellation")
            except BaseException:
                # Refuse the changed item callback without leaving our genuine
                # held non-daemon timer armed in a failed chunk.
                self.timer_cancel(timer)
                remaining = self.armed_deadlines[item.nodeid] - time.monotonic()
                self.timer_join(timer, timeout=max(0.0, min(1.0, remaining)))
                raise
        yield
        if held is not None:
            timer, cancel, settings = held
            if (
                getattr(item, "cancel_timeout", None) is not cancel
                or self._thread_timer(item, settings, cancel) is not timer
                or not timer.finished.is_set()
                or timer.is_alive()
            ):
                raise ValueError("Root case thread deadline did not finish its actual cancellation and join")
            del self.armed_thread_timers[item.nodeid]

    @pytest.hookimpl(hookwrapper=True)
    def pytest_timeout_set_timer(self, item: pytest.Item, settings: object) -> Iterator[None]:
        duration, method = getattr(settings, "timeout", None), getattr(settings, "method", None)
        if (
            not isinstance(duration, (int, float))
            or type(duration) not in (int, float)
            or not math.isfinite(duration)
            or duration <= 0
            or method not in {"signal", "thread"}
        ):
            raise ValueError("Root case deadline requires a finite positive actual selected timer")
        deadline = time.monotonic() + duration
        yield
        if method == "thread":
            cancel = getattr(item, "cancel_timeout", None)
            timer = self._thread_timer(item, settings, cancel)
            assert isinstance(cancel, types.FunctionType)
            if timer.finished.is_set() or not timer.is_alive():
                raise ValueError("Root case deadline did not arm its actual selected thread timer")
            self.armed_thread_timers[item.nodeid] = (timer, cancel, settings)
            self.armed_deadlines[item.nodeid] = deadline
            return
        handler = signal.getsignal(signal.SIGALRM)
        if (
            not isinstance(handler, types.FunctionType)
            or handler.__code__ is not self.handler_code
            or signal.getitimer(signal.ITIMER_REAL)[0] <= 0
        ):
            raise ValueError("Root case deadline did not arm its actual selected signal timer")
        self.armed_deadlines[item.nodeid] = deadline

    def pytest_runtest_makereport(self, item: pytest.Item, call: pytest.CallInfo[None]) -> None:
        if call.excinfo is None:
            return
        codes = {entry.frame.code.raw for entry in call.excinfo.traceback}
        deadline = self.armed_deadlines.get(item.nodeid)
        if (
            self.callback_code in codes
            and self.handler_code in codes
            and deadline is not None
            and time.monotonic() >= deadline
        ):
            self.timed_out = True

    def pytest_keyboard_interrupt(self, excinfo: pytest.ExceptionInfo[BaseException]) -> None:
        self.interrupted = True


def chunk(root: Path, snapshot_path: Path, expected: str, index: int) -> int:
    reader = SnapshotReader(root)
    snapshot = reader.read(snapshot_path.relative_to(root).as_posix())
    if snapshot.sha256 != expected:
        raise ValueError("Root lane original specification changed before actual case execution")
    spec, admitted = admission(reader, snapshot)
    selected = selection(admitted, spec["lane"])
    pieces = groups(selected.nodeids)
    if not 0 <= index < len(pieces):
        raise ValueError("Root chunk is outside its exact resolved lane")
    directory = root / spec["directory"] / f"chunk-{index:04d}"
    original_bundle = _json(_artifact(reader, spec["census_bundle_artifact"]))
    census_receipt = _json(_artifact(reader, original_bundle["receipt_artifact"]))
    census_spec = _json(_artifact(reader, original_bundle["spec_artifact"]))
    observer = LaneObserver(reader, census_spec["source_hashes"])
    source, deliverables = admitted.plan.source_identity, RuntimeScope(root, "root").deliverables_identity()
    original: int | None = None
    diagnostic = ""
    code = 1
    coverage_binding = None
    measured = measurement(root)
    diagnostics = CaseDiagnostics()
    try:
        blockers = lane_blockers(admitted, spec["lane"], spec["mode"])
        if blockers:
            raise MissingRootCasePolicy("required lane prerequisite is unavailable")
        os.chdir(root)
        argv = arguments(root, directory, pieces[index], spec["test_timeout_seconds"])
        measured.start()
        try:
            original = int(pytest.main(argv, plugins=[observer, diagnostics]))
        finally:
            measured.stop()
        if observer.interrupted:
            code = 130
        elif original != 0:
            code = 124 if observer.timed_out else 1
        else:
            expected_metadata = {
                case["nodeid"]: case for case in census_receipt["cases"] if case["nodeid"] in pieces[index]
            }
            actual_metadata = {case["nodeid"]: case for case in observer.cases}
            if (
                actual_metadata != expected_metadata
                or set(observer.nodeids) != set(pieces[index])
                or len(observer.nodeids) != len(pieces[index])
                or observer.collection_errors
                or observer.collection_skips
                or observer.deselected
                or set(observer.reports) != set(pieces[index])
                or any(
                    observer.reports[node] != [("setup", "passed"), ("call", "passed"), ("teardown", "passed")]
                    for node in pieces[index]
                )
            ):
                raise ValueError(
                    "actual lane case metadata or complete setup/call/teardown did not match reviewed selection"
                )
            verify_runtime_execution(root, root=root, scope="root")
            verify_implementation_custody(census_spec["implementation"], fresh_pycache_prefix=_fresh_prefix())
            if (
                RuntimeScope(root, "root").source_identity() != source
                or RuntimeScope(root, "root").deliverables_identity() != deliverables
                or runtime_identity() != census_spec["runtime"]
                or not reader.unchanged()
            ):
                raise ValueError("Root source, deliverables or selected provider changed during actual lane execution")
            coverage_binding = write(
                root,
                directory / "coverage-data.json",
                capture(measured, census_spec["implementation"]),
                spec["root_identity"],
            )
            code = 0
    except MissingRootCasePolicy:
        code, diagnostic = 75, "required Root lane prerequisite is unavailable"
    except KeyboardInterrupt:
        code, diagnostic = 130, "actual Root case execution interrupted"
    except (OSError, ValueError, RuntimeError) as error:
        diagnostics.caught(error)
        code, diagnostic = 1, "actual Root lane source/outcome contract refused"
    if observer.interrupted:
        code = 130
    write(
        root,
        directory / "receipt.json",
        {
            "schema_version": CHUNK_SCHEMA,
            "role": "actual-root-lane-chunk",
            "run_id": spec["run_id"],
            "nonce": spec["nonce"],
            "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
            "index": index,
            "lane": spec["lane"],
            "policy_sha256": admitted.policy.sha256,
            "census_sha256": admitted.plan.census_sha256,
            "source_identity": source,
            "deliverables_identity": deliverables,
            "runtime": census_spec["runtime"],
            "original_pytest_exit_code": original,
            "exit_code": code,
            "interrupted": observer.interrupted,
            "timed_out": observer.timed_out,
            "coverage_data_artifact": coverage_binding,
            "bytecode_verified": code == 0,
            "nodeids": observer.nodeids,
            "cases": observer.cases,
            "reports": observer.reports,
            "collection_errors": observer.collection_errors,
            "collection_skips": observer.collection_skips,
            "deselected": observer.deselected,
            "diagnostic": diagnostic,
            "diagnostics_artifact": diagnostics.retain(root, directory, spec["root_identity"]),
        },
        spec["root_identity"],
    )
    return code


def coordinate(root: Path, snapshot_path: Path, expected: str) -> int:
    started = time.monotonic()
    reader = SnapshotReader(root)
    snapshot = reader.read(snapshot_path.relative_to(root).as_posix())
    if snapshot.sha256 != expected:
        raise ValueError("Root lane original specification changed before coordinator admission")
    spec, admitted = admission(reader, snapshot)
    directory = root / spec["directory"]
    selected = selection(admitted, spec["lane"])
    deadline = started + spec["timeout_seconds"]
    code = 1
    records: list[dict[str, Any]] = []
    blockers = lane_blockers(admitted, spec["lane"], spec["mode"])
    source, deliverables = admitted.plan.source_identity, RuntimeScope(root, "root").deliverables_identity()
    coverage_binding = None
    try:
        if blockers:
            code = 75
        else:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("lane deadline exhausted before lock acquisition")
            with project_output_lock(root, timeout=remaining):
                for index, nodes in enumerate(groups(selected.nodeids)):
                    remaining = math.floor(deadline - time.monotonic())
                    if remaining < 1:
                        raise TimeoutError("lane deadline exhausted before actual chunk")
                    chunk_dir = directory / f"chunk-{index:04d}"
                    chunk_started = time.monotonic()
                    command = lane_command(root, snapshot, chunk=index)
                    observed = run_with_policy(
                        command,
                        cwd=root,
                        env=environment(admitted, selected.id, root, chunk_dir, spec["mode"]),
                        policy=SubprocessPolicy(
                            policy_id="root-v2-lane-chunk",
                            source_path=__name__,
                            timeout_seconds=remaining,
                            credential_free=spec["mode"] == "core",
                        ),
                    )
                    receipt_binding = None
                    try:
                        held = SnapshotReader(root).read((chunk_dir / "receipt.json").relative_to(root).as_posix())
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
                        if observed.returncode == 0
                        and receipt_binding is not None
                        and not observed.custody_refused
                        and not observed.command_error
                        else 1
                    )
                    process_binding = write(
                        root,
                        chunk_dir / "process.json",
                        {
                            "schema_version": PROCESS_SCHEMA,
                            "command": list(command),
                            "run_id": spec["run_id"],
                            "nonce": spec["nonce"],
                            "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
                            "index": index,
                            "receipt_artifact": receipt_binding,
                            "returncode": observed.returncode,
                            "original_returncode": observed.original_returncode,
                            "timed_out": observed.timed_out,
                            "custody_refused": observed.custody_refused,
                            "command_error": observed.command_error,
                            "remaining_budget_seconds": remaining,
                            "duration_seconds": time.monotonic() - chunk_started,
                            "output_artifact": retain_output(root, chunk_dir, observed, spec["root_identity"]),
                        },
                        spec["root_identity"],
                    )
                    records.append(
                        {
                            "index": index,
                            "nodes": list(nodes),
                            "receipt_artifact": receipt_binding,
                            "process_artifact": process_binding,
                        }
                    )
                    if code:
                        break
                if code == 0:
                    measured = measurement(root)
                    original_bundle = _json(_artifact(reader, spec["census_bundle_artifact"]))
                    implementation = _json(_artifact(reader, original_bundle["spec_artifact"]))["implementation"]
                    for record in records:
                        receipt = _json(_artifact(reader, record["receipt_artifact"]))
                        merge(measured, _json(_artifact(reader, receipt["coverage_data_artifact"])), implementation)
                    coverage_binding = write(root, directory / "coverage.json", report(measured), spec["root_identity"])
                if (
                    RuntimeScope(root, "root").source_identity() != source
                    or not reader.unchanged()
                    or RuntimeScope(root, "root").deliverables_identity() != deliverables
                ):
                    raise ValueError("Root source or deliverables changed during actual lane")
    except KeyboardInterrupt:
        code = 130
    except TimeoutError:
        if code != 130:
            code = 124
    except (OSError, ValueError, RuntimeError):
        if code not in (130, 124):
            code = 1
    if time.monotonic() >= deadline and code != 130:
        code = 124
    write(
        root,
        directory / "lane.json",
        {
            "schema_version": LANE_SCHEMA,
            "role": "actual-root-lane",
            "run_id": spec["run_id"],
            "nonce": spec["nonce"],
            "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
            "lane": selected.id,
            "mode": spec["mode"],
            "policy_sha256": admitted.policy.sha256,
            "prerequisites_artifact": admitted.prerequisites_artifact,
            "census_sha256": admitted.plan.census_sha256,
            "source_identity": source,
            "deliverables_identity": deliverables,
            "selected_nodes": list(selected.nodeids),
            "records": records,
            "coverage_artifact": coverage_binding,
            "blockers": blockers,
            "exit_code": code,
            "duration_seconds": time.monotonic() - started,
            "plan_sha256": digest(asdict(admitted.plan)),
        },
        spec["root_identity"],
    )
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--spec-sha256", required=True)
    parser.add_argument("--chunk", type=int)
    args = parser.parse_args(argv)
    if len(args.spec_sha256) != 64 or any(char not in "0123456789abcdef" for char in args.spec_sha256):
        parser.error("Root lane requires the original exact specification SHA-256")
    if args.chunk is not None and args.chunk < 0:
        parser.error("Root lane chunk index must be nonnegative")
    try:
        root = args.root.resolve(strict=True)
        return (
            coordinate(root, args.spec.absolute(), args.spec_sha256)
            if args.chunk is None
            else chunk(root, args.spec.absolute(), args.spec_sha256, args.chunk)
        )
    except MissingRootCasePolicy:
        return 75
    except KeyboardInterrupt:
        return 130
    except TimeoutError:
        return 124
    except (OSError, ValueError, RuntimeError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

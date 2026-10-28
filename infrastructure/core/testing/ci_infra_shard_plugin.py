"""Explicit pytest plugin for complete ordinary-CI infrastructure partitioning.

It is never autoloaded by nested project/acceptance pytest invocations.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import os
import sys
import threading
import time
from collections import deque
from datetime import UTC, datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NoReturn

import pytest

from infrastructure.core.files.secure_write import (
    atomic_write_text_confined,
    read_bytes_confined,
)
from infrastructure.core.testing.ci_infra_partition import (
    INFRA_MARKERS,
    SCHEMA,
    SHARD_COUNT,
    case_module,
    partition,
    receipt_path,
    selected_runtime,
    selection_source,
)


@dataclass
class _State:
    root: Path
    identity: tuple[int, int]
    shard: int
    source: str
    plan: dict[str, Any] | None = None
    worker_plans: list[dict[str, Any]] = field(default_factory=list)
    phases: dict[str, dict[str, str]] = field(default_factory=dict)
    phase_counts: dict[tuple[str, str], int] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)
    refusal: str | None = None


# Invalid shard invocation is reported with exit code 2, distinct from pytest's
# own usage-error code 4. Pytest's interrupted session also exits 2, so the
# recorded refusal diagnostic, not the code alone, identifies a refusal; see
# infrastructure/core/testing/README.md.
_INVALID_INVOCATION = 2

_STATE = pytest.StashKey[_State]()


@dataclass
class _ObserverOnlyState:
    root: Path
    identity: tuple[int, int]
    source: str | None
    shard: str = "slow"


_OBSERVER_ONLY_STATE = pytest.StashKey[_ObserverOnlyState]()


def _refuse(message: str) -> NoReturn:
    """Refuse an invalid shard invocation with the declared invalid-invocation code 2.

    ``pytest.UsageError`` would end the session with pytest's own usage code 4.
    The shard contract reserves 2 for invalid invocation: before execution at
    configure time (no session, no receipt), and during collection the session
    still finishes so an incomplete original-2 receipt records the refusal.
    """
    pytest.exit(message, returncode=_INVALID_INVOCATION)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--infra-ci-shard",
        type=int,
        help="Select one complete declared ordinary infrastructure CI shard",
    )
    parser.addoption(
        "--infra-ci-observer-only",
        choices=("slow",),
        help="Retain partial slow-lane diagnostics without partition or selection admission",
    )


def pytest_configure(config: pytest.Config) -> None:
    shard = config.getoption("infra_ci_shard")
    observer_only = config.getoption("infra_ci_observer_only")
    if observer_only is not None:
        if shard is not None or config.getoption("collectonly") or config.getoption("markexpr") != "slow":
            _refuse("slow observer-only mode requires unchanged slow markers, behavioral execution and no partition")
        root = config.rootpath.absolute()
        metadata = root.lstat()
        observed_source = None
        # Only the controller records diagnostics; workers never read the source
        # label, so they skip the whole-tree hash.
        if not hasattr(config, "workerinput"):
            try:
                observed_source = selection_source(root)
            except (OSError, ValueError) as error:
                # This mode adds no admission. Source-observation failure remains
                # unavailable diagnostic DATA and cannot alter the slow test result.
                _diagnostic_line(f"Infrastructure CI diagnostic source unavailable ({type(error).__name__})")
        config.stash[_OBSERVER_ONLY_STATE] = _ObserverOnlyState(
            root, (metadata.st_dev, metadata.st_ino), observed_source
        )
        return
    if type(shard) is not int or not 0 <= shard < SHARD_COUNT:
        _refuse("explicit infra CI plugin requires a declared --infra-ci-shard")
    if config.getoption("collectonly") or config.getoption("markexpr") != INFRA_MARKERS:
        _refuse("infra CI shard requires behavioral execution and the unchanged ordinary marker expression")
    root = config.rootpath.absolute()
    metadata = root.lstat()
    if receipt_path(root, shard).exists() or receipt_path(root, shard).is_symlink():
        _refuse("infra CI shard receipt already exists; use a fresh owned checkout")
    try:
        source = selection_source(root)
    except (OSError, ValueError) as error:
        _refuse(str(error))
    config.stash[_STATE] = _State(root, (metadata.st_dev, metadata.st_ino), shard, source)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _OBSERVER_ONLY_STATE in config.stash:
        return
    state = config.stash[_STATE]
    ids = [item.nodeid for item in items]
    try:
        assignments = partition(ids)
        assigned = assignments[state.shard]
        if not assigned:
            raise ValueError("a declared infrastructure shard collected zero selected cases")
    except ValueError as error:
        state.refusal = str(error)
        state.diagnostics.append(f"refused infrastructure collection: {error}")
        if hasattr(config, "workerinput"):
            # An xdist worker must not exit: the controller would restart it.
            # Report the refusal through workeroutput and execute nothing.
            config.hook.pytest_deselected(items=list(items))
            items[:] = []
            return
        _refuse(str(error))
    state.plan = {"all_node_ids": sorted(ids), "assigned_node_ids": list(assigned)}
    keep = set(assigned)
    deselected = [item for item in items if item.nodeid not in keep]
    items[:] = [item for item in items if item.nodeid in keep]
    config.hook.pytest_deselected(items=deselected)


# Partial controller observations are DATA only. They cannot replace the
# final selection receipt or authorize collection, completion or coverage.
_DIAGNOSTIC_SCHEMA = "template-ordinary-infra-ci-controller-diagnostics-v1"
_DIAGNOSTIC_HISTORY_LIMIT = 16
_DIAGNOSTIC_ACTIVE_LIMIT = 64
_DIAGNOSTIC_FAILURE_LIMIT = 64
_DIAGNOSTIC_CASE_LIMIT = 20000
# Routine case events coalesce into at most one confined rewrite per interval;
# failures, worker loss and session boundaries are written immediately.
_DIAGNOSTIC_WRITE_INTERVAL_SECONDS = 1.0


def _diagnostic_line(message: str) -> None:
    try:
        sys.stderr.write(message + "\n")
        sys.stderr.flush()
    except OSError, ValueError, AttributeError:
        # Lost diagnostic IO cannot change the actual pytest outcome.
        pass


def _observed_run_number(name: str) -> str | None:
    value = os.environ.get(name, "")
    return value if value.isascii() and value.isdecimal() and len(value) <= 20 else None


def _diagnostic_case_hash(node_id: str) -> str | None:
    try:
        encoded = node_id.encode("utf-8")
    except UnicodeError:
        return None
    return hashlib.sha256(encoded).hexdigest()


def _diagnostic_worker(node: object) -> str | None:
    value = getattr(getattr(node, "gateway", None), "id", None)
    if isinstance(value, str) and len(value) <= 32 and value.isascii() and value.replace("-", "").isalnum():
        return value
    return None


class _ControllerDiagnostics:
    """Bounded original observations, independent of selection/admission state."""

    def __init__(self, state: _State | _ObserverOnlyState) -> None:
        self.state = state
        self.sequence = 0
        self.recent: deque[dict[str, Any]] = deque(maxlen=_DIAGNOSTIC_HISTORY_LIMIT)
        self.active: dict[str, dict[str, Any]] = {}
        self.known_cases: dict[str, str | None] = {}
        self.public_families: dict[str, set[str]] = {}
        self.failures: list[dict[str, Any]] = []
        self.omitted_failures = 0
        self.write_refused = False
        self._lock = threading.Lock()
        self._last_write = float("-inf")
        self._pending: threading.Timer | None = None
        self.path = state.root / "output/readiness/ordinary-infra-ci/diagnostics" / f"shard-{state.shard}.json"
        self.run_id = _observed_run_number("GITHUB_RUN_ID")
        self.run_attempt = _observed_run_number("GITHUB_RUN_ATTEMPT")
        try:
            read_bytes_confined(
                self.state.root,
                self.path,
                max_bytes=1,
                expected_root_identity=self.state.identity,
            )
        except FileNotFoundError:
            pass
        except OSError, ValueError:
            self.write_refused = True
        else:
            self.write_refused = True
        if self.write_refused:
            _diagnostic_line("Infrastructure CI existing or unavailable diagnostics preserved")
        self.observe("session_start")

    def _public_family(self, node_id: str) -> str | None:
        # Every parameter is omitted. Labels must also be actual declarations
        # in a confined public test module, not runtime-derived member values.
        family = node_id.split("[", 1)[0]
        parts = family.split("::")
        try:
            module = case_module(node_id)
        except ValueError:
            return None
        if not re.fullmatch(r"tests/infra_tests/(?:[A-Za-z0-9_]+/)*test_[A-Za-z0-9_]+\.py", module):
            return None
        if len(parts) < 2 or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", name) for name in parts[1:]):
            return None
        if module not in self.public_families:
            declared: set[str] = set()
            try:
                source = read_bytes_confined(
                    self.state.root,
                    self.state.root / module,
                    max_bytes=4 * 1024 * 1024,
                    expected_root_identity=self.state.identity,
                )
                tree = ast.parse(source)

                def declarations(nodes: list[ast.stmt], prefix: str) -> None:
                    for item in nodes:
                        if isinstance(item, ast.ClassDef):
                            declarations(item.body, prefix + "::" + item.name)
                        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            declared.add(prefix + "::" + item.name)

                declarations(tree.body, module)
            except OSError, ValueError, SyntaxError, UnicodeError:
                pass
            self.public_families[module] = declared
        return family if family in self.public_families[module] else None

    def collected(self, node_ids: list[str]) -> None:
        for node_id in node_ids:
            identity = _diagnostic_case_hash(node_id)
            if identity is not None and (
                identity in self.known_cases or len(self.known_cases) < _DIAGNOSTIC_CASE_LIMIT
            ):
                self.known_cases[identity] = self._public_family(node_id)

    def observe(
        self,
        event: str,
        *,
        node_id: str | None = None,
        phase: str | None = None,
        outcome: str | None = None,
        worker: str | None = None,
        worker_error_present: bool | None = None,
        observed_exit_code: int | None = None,
    ) -> None:
        with self._lock:
            self._observe_locked(
                event,
                node_id=node_id,
                phase=phase,
                outcome=outcome,
                worker=worker,
                worker_error_present=worker_error_present,
                observed_exit_code=observed_exit_code,
            )

    def _observe_locked(
        self,
        event: str,
        *,
        node_id: str | None,
        phase: str | None,
        outcome: str | None,
        worker: str | None,
        worker_error_present: bool | None,
        observed_exit_code: int | None,
    ) -> None:
        self.sequence += 1
        record: dict[str, Any] = {
            "sequence": self.sequence,
            "observed_at_utc": datetime.now(UTC).isoformat(),
            "event": event,
        }
        identity = _diagnostic_case_hash(node_id) if node_id is not None else None
        if identity is not None:
            record["case_identity_sha256"] = identity
            family = self.known_cases.get(identity)
            if family is not None:
                record["public_family"] = family
        if phase in {"setup", "call", "teardown", "???"}:
            record["last_observed_report_phase"] = phase
        if outcome in {"passed", "failed", "skipped"}:
            record["observed_outcome"] = outcome
        if worker is not None:
            record["worker"] = worker
        if worker_error_present is not None:
            record["worker_error_present"] = worker_error_present
        if observed_exit_code is not None:
            record["observed_pytest_exit_code"] = observed_exit_code
        self.recent.append(record)
        if identity is not None:
            if event == "case_finish":
                self.active.pop(identity, None)
            elif identity in self.active or len(self.active) < _DIAGNOSTIC_ACTIVE_LIMIT:
                self.active[identity] = record
        if outcome == "failed" or worker_error_present:
            if len(self.failures) < _DIAGNOSTIC_FAILURE_LIMIT:
                self.failures.append(record)
            else:
                self.omitted_failures += 1
            # A real failed/crashed case must also remain visible if the job
            # never reaches pytest's buffered terminal failure summary.
            _diagnostic_line("Infrastructure CI diagnostic: " + json.dumps(record, sort_keys=True))
        urgent = (
            event in {"session_start", "session_finish", "worker_down"}
            or outcome == "failed"
            or bool(worker_error_present)
        )
        self._schedule_write(urgent)

    def _schedule_write(self, urgent: bool) -> None:
        # The caller holds the lock. Each confined rewrite costs two fsyncs on
        # the xdist controller loop, so routine events coalesce.
        if self.write_refused:
            return
        elapsed = time.monotonic() - self._last_write
        if urgent or elapsed >= _DIAGNOSTIC_WRITE_INTERVAL_SECONDS:
            if self._pending is not None:
                self._pending.cancel()
                self._pending = None
            self._write()
        elif self._pending is None:
            timer = threading.Timer(_DIAGNOSTIC_WRITE_INTERVAL_SECONDS - elapsed, self._deferred_write)
            timer.daemon = True
            timer.args = (timer,)
            try:
                timer.start()
            except RuntimeError:
                # Thread exhaustion is not a test outcome; keep the record current.
                self._write()
            else:
                self._pending = timer

    def _deferred_write(self, timer: threading.Timer) -> None:
        with self._lock:
            if self._pending is timer:
                self._pending = None
            if not self.write_refused:
                self._write()

    def _write(self) -> None:
        # The caller holds the lock.
        self._last_write = time.monotonic()
        payload = {
            "schema_version": _DIAGNOSTIC_SCHEMA,
            "diagnostics_only": True,
            "source_sha256": self.state.source,
            "shard": self.state.shard,
            "python_minor": selected_runtime(),
            "observed_workflow_run_id": self.run_id,
            "observed_workflow_run_attempt": self.run_attempt,
            "sequence": self.sequence,
            "active_cases": sorted(self.active.values(), key=lambda item: item["case_identity_sha256"]),
            "active_case_limit": _DIAGNOSTIC_ACTIVE_LIMIT,
            "recent_events": list(self.recent),
            "recent_event_limit": _DIAGNOSTIC_HISTORY_LIMIT,
            "first_failure_events": self.failures,
            "first_failure_limit": _DIAGNOSTIC_FAILURE_LIMIT,
            "omitted_failure_events": self.omitted_failures,
            "collected_case_limit": _DIAGNOSTIC_CASE_LIMIT,
            "member_parameter_values_omitted": True,
        }
        try:
            atomic_write_text_confined(
                self.state.root,
                self.path,
                json.dumps(payload, sort_keys=True, indent=2) + "\n",
                mode=0o600,
                expected_root_identity=self.state.identity,
            )
        except (OSError, ValueError) as error:
            self.write_refused = True
            # No path, report body, environment or exception text is disclosed.
            _diagnostic_line(f"Infrastructure CI diagnostics unavailable ({type(error).__name__})")


class _DiagnosticObserver:
    """Observe controller hooks only; no collection or admission hooks exist."""

    def __init__(self, state: _ObserverOnlyState) -> None:
        self.controller_diagnostics = _ControllerDiagnostics(state)

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.controller_diagnostics.collected([item.nodeid for item in session.items])

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(self, ids: list[str]) -> None:
        self.controller_diagnostics.collected(ids)

    def pytest_runtest_logstart(self, nodeid: str) -> None:
        self.controller_diagnostics.observe("case_start", node_id=nodeid)

    def pytest_runtest_logfinish(self, nodeid: str) -> None:
        self.controller_diagnostics.observe("case_finish", node_id=nodeid)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        self.controller_diagnostics.observe(
            "case_report",
            node_id=report.nodeid,
            phase=report.when,
            outcome=report.outcome,
            worker=_diagnostic_worker(getattr(report, "node", None)),
        )

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodeready(self, node: object) -> None:
        self.controller_diagnostics.observe("worker_ready", worker=_diagnostic_worker(node))

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: object, error: object) -> None:
        self.controller_diagnostics.observe(
            "worker_down",
            worker=_diagnostic_worker(node),
            worker_error_present=bool(error),
        )

    def pytest_sessionfinish(self, exitstatus: int) -> None:
        self.controller_diagnostics.observe("session_finish", observed_exit_code=int(exitstatus))


class _Observer:
    def __init__(self, state: _State, *, controller: bool) -> None:
        self.state = state
        self.controller_diagnostics = _ControllerDiagnostics(state) if controller else None

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        if self.controller_diagnostics is not None:
            self.controller_diagnostics.collected([item.nodeid for item in session.items])

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(self, ids: list[str]) -> None:
        if self.controller_diagnostics is not None:
            self.controller_diagnostics.collected(ids)

    def pytest_runtest_logstart(self, nodeid: str) -> None:
        if self.controller_diagnostics is not None:
            self.controller_diagnostics.observe("case_start", node_id=nodeid)

    def pytest_runtest_logfinish(self, nodeid: str) -> None:
        if self.controller_diagnostics is not None:
            self.controller_diagnostics.observe("case_finish", node_id=nodeid)

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodeready(self, node: object) -> None:
        if self.controller_diagnostics is not None:
            self.controller_diagnostics.observe("worker_ready", worker=_diagnostic_worker(node))

    def pytest_sessionfinish(self, exitstatus: int) -> None:
        if self.controller_diagnostics is not None:
            self.controller_diagnostics.observe("session_finish", observed_exit_code=int(exitstatus))

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if self.controller_diagnostics is not None:
            self.controller_diagnostics.observe(
                "case_report",
                node_id=report.nodeid,
                phase=report.when,
                outcome=report.outcome,
                worker=_diagnostic_worker(getattr(report, "node", None)),
            )
        key = report.nodeid, report.when
        self.state.phase_counts[key] = self.state.phase_counts.get(key, 0) + 1
        if self.state.phase_counts[key] != 1:
            self.state.diagnostics.append(f"duplicate execution phase: {report.nodeid} {report.when}")
        self.state.phases.setdefault(report.nodeid, {})[report.when] = report.outcome

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: object, error: object) -> None:
        if self.controller_diagnostics is not None:
            self.controller_diagnostics.observe(
                "worker_down",
                worker=_diagnostic_worker(node),
                worker_error_present=bool(error),
            )
        if error:
            self.state.diagnostics.append(f"xdist worker failed: {error}")
        output = getattr(node, "workeroutput", {})
        plan = output.get("infra_ci_selection") if isinstance(output, dict) else None
        if not isinstance(plan, dict):
            self.state.diagnostics.append("xdist worker omitted its actual collected selection")
            return
        if plan.get("source_sha256") != self.state.source or plan.get("source_unchanged") is not True:
            self.state.diagnostics.append("xdist worker source differs or changed during execution")
        self.state.worker_plans.append(plan)


def pytest_sessionstart(session: pytest.Session) -> None:
    if _OBSERVER_ONLY_STATE in session.config.stash:
        if not hasattr(session.config, "workerinput"):
            session.config.pluginmanager.register(
                _DiagnosticObserver(session.config.stash[_OBSERVER_ONLY_STATE]),
                "infra-ci-diagnostics",
            )
        return
    session.config.pluginmanager.register(
        _Observer(
            session.config.stash[_STATE],
            controller=not hasattr(session.config, "workerinput"),
        ),
        "infra-ci-observer",
    )


def _completed(state: _State) -> list[str]:
    completed: list[str] = []
    for node_id, phases in state.phases.items():
        if (
            phases.get("teardown") == "passed"
            and phases.get("setup") in {"passed", "skipped"}
            and (phases.get("call") in {"passed", "skipped"} or phases.get("setup") == "skipped")
        ):
            completed.append(node_id)
    return sorted(completed)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    config = session.config
    if _OBSERVER_ONLY_STATE in config.stash:
        return
    state = config.stash[_STATE]
    original = int(exitstatus)
    try:
        unchanged = selection_source(state.root) == state.source
    except (OSError, ValueError) as error:
        unchanged = False
        state.diagnostics.append(str(error))
    if not unchanged:
        state.diagnostics.append("infrastructure CI selection source changed during execution")
    worker_output = getattr(config, "workeroutput", None)
    if isinstance(worker_output, dict):
        worker_output["infra_ci_selection"] = {
            **(state.plan or {}),
            "source_sha256": state.source,
            "source_unchanged": unchanged,
            "refusal": state.refusal,
        }
        if original == 0 and not unchanged:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
        return
    refusals = sorted({plan["refusal"] for plan in state.worker_plans if plan.get("refusal")})
    for refusal in refusals:
        state.diagnostics.append(f"refused infrastructure collection: {refusal}")
    if state.worker_plans and not refusals:
        first = state.worker_plans[0]
        state.plan = {name: first.get(name) for name in ("all_node_ids", "assigned_node_ids")}
        if any(any(plan.get(key) != state.plan[key] for key in state.plan) for plan in state.worker_plans):
            state.diagnostics.append("xdist workers disagree on the complete collected partition")
    if state.plan is None and state.refusal is None and not refusals:
        state.diagnostics.append("infrastructure CI omitted actual selected collection")
    expected = [] if state.plan is None else state.plan["assigned_node_ids"]
    completed = _completed(state)
    if completed != expected:
        state.diagnostics.append("infrastructure CI did not complete every assigned selected case")
    complete = original == 0 and not state.diagnostics
    result = original if original != 0 or complete else 1
    if state.refusal is not None or refusals:
        result = _INVALID_INVOCATION
    session.exitstatus = result
    payload = {
        "schema_version": SCHEMA,
        "shard_count": SHARD_COUNT,
        "shard": state.shard,
        "source_sha256": state.source,
        "python_minor": selected_runtime(),
        "marker_expression": INFRA_MARKERS,
        **(state.plan or {}),
        "completed_node_ids": completed,
        "original_pytest_exit_code": original,
        "exit_code": result,
        "complete": complete,
        "diagnostics": state.diagnostics,
    }
    try:
        atomic_write_text_confined(
            state.root,
            receipt_path(state.root, state.shard),
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            expected_root_identity=state.identity,
        )
    except (OSError, ValueError) as error:
        session.config.get_terminal_writer().line(f"Infrastructure CI receipt refused: {error}", red=True)
        if result == 0:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED


__all__: list[str] = []

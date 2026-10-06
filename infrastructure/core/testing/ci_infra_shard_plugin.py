"""Explicit pytest plugin for complete ordinary-CI infrastructure partitioning.

It is never autoloaded by nested project/acceptance pytest invocations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NoReturn

import pytest

from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.testing.ci_infra_partition import (
    INFRA_MARKERS,
    SCHEMA,
    SHARD_COUNT,
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


def _refuse(message: str) -> NoReturn:
    """Refuse an invalid shard invocation with the declared invalid-invocation code 2.

    ``pytest.UsageError`` would end the session with pytest's own usage code 4.
    The shard contract reserves 2 for invalid invocation: before execution at
    configure time (no session, no receipt), and during collection the session
    still finishes so an incomplete original-2 receipt records the refusal.
    """
    pytest.exit(message, returncode=_INVALID_INVOCATION)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--infra-ci-shard", type=int, help="Select one complete declared ordinary infrastructure CI shard")


def pytest_configure(config: pytest.Config) -> None:
    shard = config.getoption("infra_ci_shard")
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


class _Observer:
    def __init__(self, state: _State) -> None:
        self.state = state

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        key = report.nodeid, report.when
        self.state.phase_counts[key] = self.state.phase_counts.get(key, 0) + 1
        if self.state.phase_counts[key] != 1:
            self.state.diagnostics.append(f"duplicate execution phase: {report.nodeid} {report.when}")
        self.state.phases.setdefault(report.nodeid, {})[report.when] = report.outcome

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: object, error: object) -> None:
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
    session.config.pluginmanager.register(_Observer(session.config.stash[_STATE]), "infra-ci-observer")


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

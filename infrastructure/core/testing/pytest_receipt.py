"""Opt-in pytest execution observations for functional CI and benchmarks.

These receipts describe actual pytest reports; they grant no release or Source
authority. Each caller supplies a fresh directory and nonce through its env.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.testing.pytest_observations import DIRECTORY_ENV, NONCE_ENV, ROOT_ENV

_ACTIVE_ENV = "TEMPLATE_PYTEST_RECEIPT_ACTIVE"
_selected: set[str] = set()
_collected: set[str] = set()
_deselected: set[str] = set()
_reports: dict[str, dict[str, str]] = {}
_timings: dict[str, dict[str, float]] = {}
_collection_errors = 0
_enabled = False


def pytest_sessionstart(session: Any) -> None:
    global _collection_errors, _enabled
    nonce = os.environ.get(NONCE_ENV)
    _enabled = bool(nonce and os.environ.get(DIRECTORY_ENV) and os.environ.get(_ACTIVE_ENV) != nonce)
    if _enabled:
        # Child pytest invocations inside tested subprocess contracts must not
        # masquerade as another original Stage-01/project controller receipt.
        os.environ[_ACTIVE_ENV] = str(nonce)
    _selected.clear()
    _collected.clear()
    _deselected.clear()
    _reports.clear()
    _timings.clear()
    _collection_errors = 0


def pytest_collection_finish(session: Any) -> None:
    _selected.update(item.nodeid for item in session.items)


def pytest_itemcollected(item: Any) -> None:
    _collected.add(item.nodeid)


def pytest_deselected(items: list[Any]) -> None:
    _deselected.update(item.nodeid for item in items)


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node: Any, ids: list[str]) -> None:
    _selected.update(ids)


def pytest_collectreport(report: Any) -> None:
    global _collection_errors
    if report.failed:
        _collection_errors += 1


def pytest_runtest_logreport(report: Any) -> None:
    outcome = report.outcome + (":xfail" if getattr(report, "wasxfail", None) is not None else "")
    _reports.setdefault(report.nodeid, {})[report.when] = outcome
    _timings.setdefault(report.nodeid, {})[report.when] = report.duration


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    directory = os.environ.get(DIRECTORY_ENV)
    nonce = os.environ.get(NONCE_ENV)
    if not _enabled or not directory or not nonce:
        return
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    root = Path(os.environ.get(ROOT_ENV, str(session.config.rootpath))).resolve()

    def qualify(nodeid: str) -> str:
        filename, separator, suffix = nodeid.partition("::")
        relative = (Path(session.config.rootpath) / filename).resolve().relative_to(root).as_posix()
        return relative + separator + suffix

    value = {
        "schema_version": "template-pytest-execution/v1",
        "nonce": nonce,
        "worker": os.environ.get("PYTEST_XDIST_WORKER", "controller"),
        "selected": sorted(qualify(node) for node in _selected),
        "collected": sorted(qualify(node) for node in _collected),
        "deselected": sorted(qualify(node) for node in _deselected),
        "selection_profile": {
            "arguments": list(session.config.invocation_params.args),
            "marker_expression": session.config.option.markexpr,
            "keyword_expression": session.config.option.keyword,
            "workers": getattr(session.config.option, "numprocesses", None),
            "ambient_addopts": bool(os.environ.get("PYTEST_ADDOPTS", "").strip()),
        },
        "reports": {qualify(node): phases for node, phases in _reports.items()},
        "timings": {qualify(node): phases for node, phases in _timings.items()},
        "collection_errors": _collection_errors,
        "exit_code": int(exitstatus),
    }
    # Exclusive original output prevents stale observations being overwritten.
    with (path / f"execution-{os.getpid()}.json").open("x") as stream:
        json.dump(value, stream, sort_keys=True)

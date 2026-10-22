"""Opt-in pytest execution observations for functional CI and benchmarks.

These receipts describe actual pytest reports; they grant no release or Source
authority. Each caller supplies a fresh directory and nonce through its env.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, BinaryIO

import pytest

from infrastructure.core.testing.pytest_observations import DIRECTORY_ENV, NONCE_ENV, ROOT_ENV

_ACTIVE_ENV = "TEMPLATE_PYTEST_RECEIPT_ACTIVE"
_selected: set[str] = set()
_collected: set[str] = set()
_deselected: set[str] = set()
_reports: dict[str, dict[str, str]] = {}
_timings: dict[str, dict[str, float]] = {}
_collection_errors = 0
_collection_skips = 0
_enabled = False
_progress: BinaryIO | None = None
_progress_events = 0
_progress_bytes = 0
_progress_exhausted = False
_progress_error = False
_progress_nonce = ""
_progress_worker = "controller"
_PROGRESS_EVENTS = 200_000
_PROGRESS_BYTES = 64 * 1024 * 1024


def _diagnostic_warning(error: Exception) -> None:
    global _progress_error
    if not _progress_error:
        _progress_error = True
        try:
            print(f"pytest progress diagnostic disabled: {type(error).__name__}: {str(error)[:512]}", file=sys.stderr)
        except Exception:
            pass


def _close_progress() -> None:
    global _progress
    stream, _progress = _progress, None
    if stream is not None:
        try:
            stream.close()
        except Exception as error:
            _diagnostic_warning(error)


def _diagnostic_text(name: str, text: str, limit: int) -> dict[str, Any]:
    truncated = len(text) > limit
    return {
        name: text[:limit],
        name + "_characters": len(text),
        name + "_truncated": truncated,
        **({name + "_sha256": hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()} if truncated else {}),
    }


def _diagnostic_event(event: str, **fields: Any) -> None:
    """Flush bounded optional DATA; I/O failure cannot replace original outcomes."""
    global _progress_events, _progress_bytes, _progress_exhausted
    if _progress is None or _progress_exhausted:
        return
    try:
        value = {
            "schema_version": "template-pytest-progress/v1",
            "nonce": _progress_nonce,
            "emitter_pid": os.getpid(),
            "worker": _progress_worker,
            "sequence": _progress_events,
            "event": event,
            **fields,
        }
        raw = (json.dumps(value, ensure_ascii=True, allow_nan=False) + "\n").encode()
        if _progress_events >= _PROGRESS_EVENTS - 1 or _progress_bytes + len(raw) > _PROGRESS_BYTES - 2048:
            value = {key: value[key] for key in ("schema_version", "nonce", "emitter_pid", "worker", "sequence")} | {
                "event": "truncated",
                "reason": "event_limit" if _progress_events >= _PROGRESS_EVENTS - 1 else "byte_limit",
            }
            raw = (json.dumps(value, ensure_ascii=True, allow_nan=False) + "\n").encode()
            if len(raw) > 2048:
                raise ValueError("progress truncation sentinel exceeds its reserved bytes")
            _progress_exhausted = True
        _progress.write(raw)
        _progress.flush()
        _progress_events += 1
        _progress_bytes += len(raw)
    except Exception as error:
        _diagnostic_warning(error)
        _close_progress()


def pytest_sessionstart(session: Any) -> None:
    global _collection_errors, _collection_skips, _enabled, _progress, _progress_events, _progress_bytes
    global _progress_exhausted, _progress_error, _progress_nonce, _progress_worker
    _close_progress()
    _progress_events = _progress_bytes = 0
    _progress_exhausted = _progress_error = False
    nonce = os.environ.get(NONCE_ENV)
    _enabled = bool(nonce and os.environ.get(DIRECTORY_ENV) and os.environ.get(_ACTIVE_ENV) != nonce)
    _progress_nonce = str(nonce or "")
    _progress_worker = os.environ.get("PYTEST_XDIST_WORKER", "controller")
    if _enabled:
        # Child pytest invocations inside tested subprocess contracts must not
        # masquerade as another original Stage-01/project controller receipt.
        os.environ[_ACTIVE_ENV] = str(nonce)
        try:
            directory = Path(os.environ[DIRECTORY_ENV])
            directory.mkdir(parents=True, exist_ok=True)
            _progress = (directory / f"progress-{os.getpid()}.jsonl").open("xb")
            _diagnostic_event(
                "session_start",
                pytest_root=str(session.config.rootpath),
                receipt_root=os.environ.get(ROOT_ENV),
                diagnostic_only=True,
            )
        except Exception as error:
            _diagnostic_warning(error)
            _close_progress()
    _selected.clear()
    _collected.clear()
    _deselected.clear()
    _reports.clear()
    _timings.clear()
    _collection_errors = 0
    _collection_skips = 0


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
    global _collection_errors, _collection_skips
    if report.failed:
        _collection_errors += 1
    if report.skipped:
        _collection_skips += 1


def pytest_runtest_logstart(nodeid: str, location: Any) -> None:
    if _progress is None or _progress_exhausted:
        return
    try:
        _diagnostic_event("case_start", **_diagnostic_text("nodeid", nodeid, 4096))
    except Exception as error:
        _diagnostic_warning(error)
        _close_progress()


def pytest_runtest_logreport(report: Any) -> None:
    outcome = report.outcome + (":xfail" if getattr(report, "wasxfail", None) is not None else "")
    _reports.setdefault(report.nodeid, {})[report.when] = outcome
    _timings.setdefault(report.nodeid, {})[report.when] = report.duration
    if _progress is None or _progress_exhausted:
        return
    try:
        _diagnostic_event(
            "phase",
            **_diagnostic_text("nodeid", report.nodeid, 4096),
            worker=getattr(report, "worker_id", _progress_worker),
            phase=report.when,
            outcome=outcome,
            duration=report.duration,
            **(_diagnostic_text("failure", str(report.longrepr), 8192) if report.failed else {}),
        )
    except Exception as error:
        _diagnostic_warning(error)
        _close_progress()


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
        "collection_skips": _collection_skips,
        "exit_code": int(exitstatus),
    }
    # Exclusive original output prevents stale observations being overwritten.
    with (path / f"execution-{os.getpid()}.json").open("x") as stream:
        json.dump(value, stream, sort_keys=True)
    _diagnostic_event("session_finish", exit_code=int(exitstatus))


def pytest_unconfigure(config: Any) -> None:
    _close_progress()

"""Bounded original Root chunk diagnostics; never case or release authority."""

from __future__ import annotations

import hashlib
import traceback
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import BoundedSubprocessResult
from infrastructure.project.public_root_case_contract import _json
from infrastructure.project.public_root_lane_contract import write
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

STREAM_BYTES = 256 * 1024
FIELD_BYTES = 16 * 1024
REPORT_BYTES = 1024 * 1024
MAX_REPORTS = 300  # At most three original phases for the 100 selected cases.
OUTPUT_SCHEMA = "template-root-original-process-output-v1"
REPORT_SCHEMA = "template-root-original-pytest-diagnostics-v1"
ROLE = "diagnostic-only-original-captured-text"


def _capture(text: str, limit: int) -> dict[str, Any]:
    # The process boundary already decodes UTF-8 with replacement. Commit that
    # actual captured text, not imaginary pre-decode native bytes.
    raw = text.encode("utf-8", errors="replace")
    retained = raw[:limit].decode("utf-8", errors="ignore")
    size = len(retained.encode("utf-8"))
    return {
        "text": retained,
        "captured_bytes": len(raw),
        "captured_sha256": hashlib.sha256(raw).hexdigest(),
        "retained_bytes": size,
        "truncated": size < len(raw),
    }


def retain_output(
    root: Path, directory: Path, observed: BoundedSubprocessResult, identity: list[int]
) -> dict[str, str]:
    """Retain the original boundary's bounded stdout/stderr even after failure."""
    return write(
        root,
        directory / "process-output.json",
        {
            "schema_version": OUTPUT_SCHEMA,
            "role": ROLE,
            "stdout": _capture(observed.stdout, STREAM_BYTES),
            "stderr": _capture(observed.stderr, STREAM_BYTES),
        },
        identity,
    )


class CaseDiagnostics:
    """Observe real pytest failure/skip reports without replacing any outcome."""

    def __init__(self) -> None:
        self.reports: list[dict[str, Any]] = []
        self.retained_bytes = 0
        self.dropped_reports = 0
        self.exception: dict[str, Any] | None = None

    def _text(self, text: str) -> dict[str, Any]:
        value = _capture(text, min(FIELD_BYTES, REPORT_BYTES - self.retained_bytes))
        self.retained_bytes += value["retained_bytes"]
        return value

    def pytest_runtest_logreport(self, report: Any) -> None:
        if report.passed:
            return
        if len(self.reports) >= MAX_REPORTS:
            self.dropped_reports += 1
            return
        self.reports.append(
            {
                "nodeid": self._text(report.nodeid),
                "phase": report.when,
                "outcome": report.outcome,
                "longrepr": self._text(report.longreprtext),
                "stdout": self._text(report.capstdout),
                "stderr": self._text(report.capstderr),
            }
        )

    def caught(self, error: BaseException) -> None:
        self.exception = self._text("".join(traceback.format_exception(error)))

    def retain(self, root: Path, directory: Path, identity: list[int]) -> dict[str, str]:
        return write(
            root,
            directory / "case-diagnostics.json",
            {
                "schema_version": REPORT_SCHEMA,
                "role": ROLE,
                "reports": self.reports,
                "retained_text_bytes": self.retained_bytes,
                "dropped_reports": self.dropped_reports,
                "exception": self.exception,
            },
            identity,
        )


def _read(reader: SnapshotReader, directory: Path, binding: object, name: str, limit: int) -> dict[str, Any]:
    expected = (directory / name).relative_to(reader.root).as_posix()
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"} or binding["path"] != expected:
        raise ValueError("Root diagnostics are outside their original chunk")
    snapshot = reader.read(expected, max_bytes=limit)
    if snapshot.sha256 != binding["sha256"]:
        raise ValueError("Root original diagnostic artifact changed")
    return _json(snapshot)


def _text(value: object, limit: int) -> int:
    if not isinstance(value, dict) or set(value) != {
        "text",
        "captured_bytes",
        "captured_sha256",
        "retained_bytes",
        "truncated",
    }:
        raise ValueError("Root diagnostic text metadata is incomplete")
    if (
        not isinstance(value["text"], str)
        or type(value["captured_bytes"]) is not int
        or type(value["retained_bytes"]) is not int
        or not 0 <= value["retained_bytes"] <= min(limit, value["captured_bytes"])
        or type(value["truncated"]) is not bool
        or value["truncated"] != (value["retained_bytes"] < value["captured_bytes"])
        or not isinstance(value["captured_sha256"], str)
        or len(value["captured_sha256"]) != 64
        or any(char not in "0123456789abcdef" for char in value["captured_sha256"])
    ):
        raise ValueError("Root diagnostic text exceeds its original bounded representation")
    raw = value["text"].encode("utf-8")
    if len(raw) != value["retained_bytes"] or (
        not value["truncated"] and hashlib.sha256(raw).hexdigest() != value["captured_sha256"]
    ):
        raise ValueError("Root diagnostic text does not match its captured commitment")
    return len(raw)


def read_output(reader: SnapshotReader, directory: Path, binding: object) -> dict[str, Any]:
    """Verify bounded retained text and custody; do not interpret it as success."""
    value = _read(reader, directory, binding, "process-output.json", 4 * 1024 * 1024)
    if set(value) != {"schema_version", "role", "stdout", "stderr"} or (
        value["schema_version"] != OUTPUT_SCHEMA or value["role"] != ROLE
    ):
        raise ValueError("Root process diagnostic schema differs")
    for key in ("stdout", "stderr"):
        _text(value[key], STREAM_BYTES)
    return value


def read_reports(reader: SnapshotReader, directory: Path, binding: object) -> dict[str, Any]:
    """Read failure diagnostics separately from exact actual case outcome admission."""
    value = _read(reader, directory, binding, "case-diagnostics.json", 8 * 1024 * 1024)
    if (
        set(value) != {"schema_version", "role", "reports", "retained_text_bytes", "dropped_reports", "exception"}
        or value["schema_version"] != REPORT_SCHEMA
        or value["role"] != ROLE
        or not isinstance(value["reports"], list)
        or len(value["reports"]) > MAX_REPORTS
        or type(value["dropped_reports"]) is not int
        or value["dropped_reports"] < 0
        or type(value["retained_text_bytes"]) is not int
    ):
        raise ValueError("Root original pytest diagnostics are incomplete")
    retained = 0
    for row in value["reports"]:
        if not isinstance(row, dict) or set(row) != {"nodeid", "phase", "outcome", "longrepr", "stdout", "stderr"}:
            raise ValueError("Root original report diagnostic shape differs")
        if row["phase"] not in {"setup", "call", "teardown"} or row["outcome"] not in {"failed", "skipped"}:
            raise ValueError("Root original report diagnostic phase/outcome differs")
        retained += sum(_text(row[key], FIELD_BYTES) for key in ("nodeid", "longrepr", "stdout", "stderr"))
    if value["exception"] is not None:
        retained += _text(value["exception"], FIELD_BYTES)
    if retained != value["retained_text_bytes"] or retained > REPORT_BYTES:
        raise ValueError("Root report diagnostics exceed their whole-chunk text bound")
    return value


__all__ = ["CaseDiagnostics", "retain_output", "read_output", "read_reports"]

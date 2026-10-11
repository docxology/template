"""Actual portable custody and source fixture controls; no simulated native passes."""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from io import BytesIO
from pathlib import Path
import zipfile

import pytest

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record, parse_native_bytes
from infrastructure.reporting.native_format_control_replay import (
    SCHEMA,
    _closure,
    _office_members,
    validate_format_controls,
)
from infrastructure.reporting.native_projection_checks import PROJECTION_CONTROL_CODES, projection_control_fixture
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

UNADMITTED = "externally admitted source and original launch custody"
CUSTODY_GATED = (
    "requires original launch custody, which unit tests cannot construct; reachable only "
    "under the platform-required-acceptance native-original/complete jobs"
)


def test_current_source_projection_fixtures_exact_repeat_and_real_parse() -> None:
    for name in PROJECTION_CONTROL_CODES:
        first, pages = projection_control_fixture(name)
        second, repeated = projection_control_fixture(name)
        assert first == second and pages == repeated
        parsed = parse_native_bytes("pdf", first)
        assert parsed["pages"] == 1
    assert projection_control_fixture("changed-number")[0] != projection_control_fixture("baseline")[0]
    with pytest.raises(ValueError):
        projection_control_fixture("unknown")


def test_original_executable_deleted_portable_actual_tool_closure(tmp_path: Path) -> None:
    """A relocated closure walks to its nested tool but never self-authorizes it.

    Admission of the original tool receipt needs the externally held original
    launch custodian; a bare relocated reader refuses even unchanged DATA.
    """
    producer = tmp_path / "producer"
    directory = producer / "output/readiness/controls"
    directory.mkdir(parents=True)
    executable = producer / "tool/native-fixture"
    executable.parent.mkdir()
    executable.write_text(f"#!/bin/sh\nexec '{sys.executable}' -I -c 'print(42)'\n")
    executable.chmod(0o700)
    env = {**os.environ, "PATH": str(executable.parent) + os.pathsep + os.environ.get("PATH", "")}
    result = native_tool_record(
        producer,
        directory,
        "native-fixture",
        [],
        env=env,
        deadline=time.monotonic() + 20,
        run_id="actual-control-custody",
        purpose="fixture",
    )
    assert result["exit_code"] == result["original_exit_code"] == 0
    reader_root = tmp_path / "reader"
    shutil.copytree(producer, reader_root)
    shutil.rmtree(producer)
    relocated = reader_root / "output/readiness/controls"
    assert not executable.exists()
    with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
        _closure(result["artifact"], SnapshotReader(reader_root), relocated, "actual-control-custody")
    path = reader_root / result["artifact"]["path"]
    original = json.loads(path.read_text())
    # Receipt DATA checked before custody is consulted is refused for its own
    # reason, never merely by the custody refusal that also refuses genuine DATA.
    for change, run_id, reason in (
        ({"unknown": True}, "actual-control-custody", "exact shared original receipt fields"),
        (
            {"executable_observation_after": {**original["executable_observation_after"], "sha256": "e" * 64}},
            "actual-control-custody",
            "original executable observation changed",
        ),
        ({}, "different-run", "command/run/outcome differs"),
    ):
        binding = write_json(reader_root, path, {**original, **change})
        with pytest.raises(ValueError, match=reason) as refused:
            _closure(binding, SnapshotReader(reader_root), relocated, run_id)
        assert not isinstance(refused.value, ProjectionSourceUnsupported)
    # The custody diagnostic is compared only after original launch custody
    # admits the receipt. Here the changed diagnostic fails closed at that gate;
    # its own rejection is the explicit skip below, not coverage claimed here.
    binding = write_json(reader_root, path, {**original, "diagnostic": "custody lost"})
    with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
        _closure(binding, SnapshotReader(reader_root), relocated, "actual-control-custody")


def test_changed_custody_diagnostic_rejection_needs_original_launch_custody() -> None:
    """Uncovered here: _closure rejects a non-empty control tool diagnostic only
    after _tool admits the receipt against original launch custody."""
    pytest.skip(f"changed-custody-diagnostic: {CUSTODY_GATED}")


def test_source_suite_cannot_be_missing_duplicate_unknown_or_bare_pass(tmp_path: Path) -> None:
    directory = tmp_path / "output/readiness/controls"
    directory.mkdir(parents=True)
    kwargs = {
        "run_id": "actual",
        "custody": {},
        "runtime": {},
        "versions": {},
        "deadline": time.monotonic() + 20,
        "original_deadline": 100.0,
        "env": os.environ.copy(),
    }
    for raw in (
        {"schema_version": SCHEMA},
        {"schema_version": SCHEMA, "docx": []},
        {"schema_version": SCHEMA, "docx": [{"name": "baseline"}] * 7},
        {"schema_version": SCHEMA, "docx": [], "passed": True},
    ):
        with pytest.raises(ValueError):
            validate_format_controls(raw, ("docx",), SnapshotReader(tmp_path), directory, **kwargs)


def test_office_exact_member_identity_preserves_content_changes() -> None:
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("word/document.xml", b"actual member")
    assert _office_members(stream.getvalue()) == {"word/document.xml": b"actual member"}
    with pytest.warns(UserWarning):
        with zipfile.ZipFile(stream, "a") as archive:
            archive.writestr("word/document.xml", b"changed member")
    with pytest.raises(ValueError):
        _office_members(stream.getvalue())


def test_actual_pandoc_deterministic_clock_preserves_every_docx_member(tmp_path: Path) -> None:
    from infrastructure.reporting.native_office_observer import reconstruct_office_control_fixture

    env = {**os.environ, "SOURCE_DATE_EPOCH": "1700000000"}
    observed = []
    for name in ("original", "separate-reader"):
        root = tmp_path / name
        directory = root / "output/readiness/fixture"
        directory.mkdir(parents=True)
        content, contract, pages, tool = reconstruct_office_control_fixture(
            root, directory, "docx", "baseline", env=env, deadline=time.monotonic() + 30, run_id=name
        )
        assert tool is not None and tool["exit_code"] == tool["original_exit_code"] == 0
        assert contract is not None and not pages
        observed.append(_office_members(content))
    assert observed[0] == observed[1]
    assert b"2023-11-14T22:13:20Z" in observed[0]["docProps/core.xml"]


def test_all_epub_source_fixtures_have_exact_deterministic_archive_bytes() -> None:
    from infrastructure.reporting.native_epub_observer import EPUB_CONTROL_CODES, epub_control_bytes

    for name in EPUB_CONTROL_CODES:
        first, chapters = epub_control_bytes(name)
        second, repeated = epub_control_bytes(name)
        assert first == second and chapters == repeated
        parse_native_bytes("epub", first)
        with zipfile.ZipFile(BytesIO(first)) as archive:
            assert all(info.date_time == (2020, 1, 1, 0, 0, 0) for info in archive.infolist())
    assert epub_control_bytes("changed-number")[0] != epub_control_bytes("baseline")[0]

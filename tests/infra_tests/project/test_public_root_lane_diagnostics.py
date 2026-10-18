"""Real original pytest/process diagnostics stay bounded, confined and non-authoritative."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import BoundedSubprocessResult
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.project.public_root_lane_contract import write
from infrastructure.project.public_root_lane_diagnostics import (
    FIELD_BYTES,
    STREAM_BYTES,
    read_output,
    read_reports,
    retain_output,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

ROOT = Path(__file__).resolve().parents[3]
# The real child keeps its own 30-second limit; this includes guardian custody.
pytestmark = pytest.mark.timeout(60)


@pytest.fixture(scope="module")
def original_failure(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, BoundedSubprocessResult]:
    root = tmp_path_factory.mktemp("original-chunk-diagnostics").resolve()
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts=[]\n")
    (root / "test_owned.py").write_text(
        "import sys\ndef test_original_failure():\n"
        f"    print('ORIGINAL CASE STDOUT '+ 'X'*{FIELD_BYTES * 2})\n"
        f"    print('ORIGINAL CASE STDERR '+ 'Y'*{FIELD_BYTES * 2},file=sys.stderr)\n"
        f"    raise AssertionError('ORIGINAL ASSERTION DETAIL '+ 'D'*{FIELD_BYTES * 2})\n"
    )
    code = (
        "import pytest,sys\nfrom pathlib import Path\n"
        "from infrastructure.project.public_root_lane_diagnostics import CaseDiagnostics\n"
        "root=Path.cwd(); observer=CaseDiagnostics()\n"
        f"print('ORIGINAL PROCESS STDOUT '+ 'O'*{STREAM_BYTES + 17})\n"
        f"print('ORIGINAL PROCESS STDERR '+ 'E'*{STREAM_BYTES + 17},file=sys.stderr)\n"
        "original=int(pytest.main(['test_owned.py','-q','--tb=short','-p','no:cacheprovider'],plugins=[observer]))\n"
        "s=root.stat(); observer.retain(root,root/'output/readiness/chunk',[s.st_dev,s.st_ino])\n"
        "raise SystemExit(original)\n"
    )
    observed = run_with_policy(
        [sys.executable, "-B", "-c", code],
        cwd=root,
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT),
            "PYTEST_ADDOPTS": "",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        },
        policy=SubprocessPolicy(
            policy_id="owned-original-diagnostic-control", source_path=__name__, timeout_seconds=30
        ),
    )
    assert observed.returncode == observed.original_returncode == 1
    assert not observed.timed_out and not observed.custody_refused
    return root, observed


def _identity(root: Path) -> list[int]:
    current = root.stat()
    return [current.st_dev, current.st_ino]


def test_original_assertion_and_captured_streams_survive_real_failed_pytest(
    original_failure: tuple[Path, BoundedSubprocessResult], tmp_path: Path
) -> None:
    root, observed = original_failure
    directory = root / "output/readiness/chunk"
    data = (directory / "case-diagnostics.json").read_bytes()
    reports = read_reports(
        SnapshotReader(root),
        directory,
        {"path": "output/readiness/chunk/case-diagnostics.json", "sha256": hashlib.sha256(data).hexdigest()},
    )
    assert len(reports["reports"]) == 1
    report = reports["reports"][0]
    assert report["phase"] == "call" and report["outcome"] == "failed"
    for key, expected in (
        ("longrepr", "ORIGINAL ASSERTION DETAIL"),
        ("stdout", "ORIGINAL CASE STDOUT"),
        ("stderr", "ORIGINAL CASE STDERR"),
    ):
        assert expected in report[key]["text"]
        assert report[key]["truncated"] and report[key]["retained_bytes"] <= FIELD_BYTES
    directory = tmp_path / "output/readiness/chunk"
    binding = retain_output(tmp_path, directory, observed, _identity(tmp_path))
    streams = read_output(SnapshotReader(tmp_path), directory, binding)
    for key in ("stdout", "stderr"):
        original = getattr(observed, key).encode("utf-8")
        assert streams[key]["captured_sha256"] == hashlib.sha256(original).hexdigest()
        assert streams[key]["captured_bytes"] == len(original) > STREAM_BYTES
        assert streams[key]["truncated"] and streams[key]["retained_bytes"] <= STREAM_BYTES
        assert streams[key]["text"].startswith("ORIGINAL PROCESS " + key.upper())
    assert observed.returncode == 1  # Retained diagnostics never replace the original failure.


@pytest.mark.parametrize("fault", ["changed-bytes", "retained-count", "outside-chunk", "oversized"])
def test_rehashed_original_process_output_cannot_bypass_capture_bounds(
    original_failure: tuple[Path, BoundedSubprocessResult], tmp_path: Path, fault: str
) -> None:
    _, observed = original_failure
    directory = tmp_path / "output/readiness/chunk"
    binding = retain_output(tmp_path, directory, observed, _identity(tmp_path))
    target = tmp_path / binding["path"]
    value = json.loads(target.read_bytes())
    if fault == "retained-count":
        value["stdout"]["retained_bytes"] += 1
    elif fault == "oversized":
        value["stdout"].update(
            text="x" * (STREAM_BYTES + 1),
            retained_bytes=STREAM_BYTES + 1,
            captured_bytes=STREAM_BYTES + 1,
            captured_sha256=hashlib.sha256(b"x" * (STREAM_BYTES + 1)).hexdigest(),
            truncated=False,
        )
    elif fault == "outside-chunk":
        target = directory.parent / target.name
    binding = write(tmp_path, target, value, _identity(tmp_path))
    if fault == "changed-bytes":
        target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises((OSError, ValueError)):
        read_output(SnapshotReader(tmp_path), directory, binding)


@pytest.mark.parametrize(
    "fault",
    [
        "changed-bytes",
        "retained-count",
        "captured-commitment",
        "outside-chunk",
        "symlink-leaf",
        "report-size",
        "report-outcome",
    ],
)
def test_rehashed_or_redirected_original_diagnostics_are_refused(
    original_failure: tuple[Path, BoundedSubprocessResult], tmp_path: Path, fault: str
) -> None:
    original, _ = original_failure
    directory = tmp_path / "output/readiness/chunk"
    value = json.loads((original / "output/readiness/chunk/case-diagnostics.json").read_bytes())
    if fault == "retained-count":
        value["retained_text_bytes"] += 1
    elif fault == "captured-commitment":
        assert value["reports"][0]["nodeid"]["truncated"] is False
        value["reports"][0]["nodeid"]["captured_sha256"] = "0" * 64
    elif fault == "report-size":
        text = value["reports"][0]["longrepr"]
        text.update(
            text="x" * (FIELD_BYTES + 1),
            retained_bytes=FIELD_BYTES + 1,
            captured_bytes=FIELD_BYTES + 1,
            captured_sha256=hashlib.sha256(b"x" * (FIELD_BYTES + 1)).hexdigest(),
            truncated=False,
        )
    elif fault == "report-outcome":
        value["reports"][0]["outcome"] = "passed"
    target = directory / "case-diagnostics.json"
    binding = write(tmp_path, target, value, _identity(tmp_path))
    if fault == "changed-bytes":
        target.write_bytes(target.read_bytes() + b" ")
    elif fault == "outside-chunk":
        binding = write(tmp_path, directory.parent / "case-diagnostics.json", value, _identity(tmp_path))
    elif fault == "symlink-leaf":
        external = tmp_path.parent / (tmp_path.name + "-outside-diagnostic")
        external.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(external)
    with pytest.raises((OSError, ValueError)):
        read_reports(SnapshotReader(tmp_path), directory, binding)


@pytest.mark.parametrize("fault", ["leaf", "ancestor"])
def test_original_process_output_cannot_write_through_external_links(
    original_failure: tuple[Path, BoundedSubprocessResult], tmp_path: Path, fault: str
) -> None:
    _, observed = original_failure
    root = tmp_path / "root"
    root.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "process-output.json"
    sentinel.write_bytes(b"original outside bytes")
    directory = root / "output/readiness/chunk"
    directory.parent.mkdir(parents=True)
    if fault == "ancestor":
        directory.symlink_to(external, target_is_directory=True)
    else:
        directory.mkdir()
        (directory / sentinel.name).symlink_to(sentinel)
    with pytest.raises((OSError, ValueError)):
        retain_output(root, directory, observed, _identity(root))
    assert sentinel.read_bytes() == b"original outside bytes"
    assert sorted(p.name for p in external.iterdir()) == [sentinel.name]

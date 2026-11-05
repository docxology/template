"""The real diagnostic CLI retains failures rather than accepting status labels."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


def _run(tmp_path: Path, *extra: str, occupied: bool = False):
    root = Path(__file__).resolve().parents[3]
    destination = root / "output/readiness" / ("arl-reader-refusal-" + uuid.uuid4().hex)
    output = destination / "reader.json"
    if occupied:
        output.parent.mkdir(parents=True)
        output.write_bytes(b"preserved prior evidence\n")
    command = [
        sys.executable,
        "-I",
        "-B",
        "-m",
        "infrastructure.project.public_acceptance_literature_group_cli",
        "--repo-root",
        str(root),
        "--receipt",
        str(destination / "absent-original.json"),
        "--output",
        str(output),
        *extra,
    ]
    result = subprocess.run(
        command, cwd=root, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, check=False
    )
    return result, output


def test_missing_original_cannot_become_a_positive_diagnostic(tmp_path: Path) -> None:
    result, output = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    facts = json.loads(output.read_bytes())
    assert facts["status"] == "failed"
    assert facts["aggregate_acceptance_granted"] is False
    assert facts["release_authorized"] is False


@pytest.mark.parametrize("timeout", ["0", "601", "-1"])
def test_reader_refuses_an_unbounded_or_invalid_budget_before_writing(tmp_path: Path, timeout: str) -> None:
    result, output = _run(tmp_path, "--timeout-seconds", timeout)
    assert result.returncode == 2, result.stdout + result.stderr
    assert not output.exists()


def test_reader_refuses_to_replace_prior_diagnostic_evidence(tmp_path: Path) -> None:
    result, output = _run(tmp_path, occupied=True)
    assert result.returncode == 2, result.stdout + result.stderr
    assert output.read_bytes() == b"preserved prior evidence\n"

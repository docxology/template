"""Script-level tests for the review-artifact generator (real files, no mocks).

``scripts/generate_figures.py`` already has direct script-execution coverage
in ``test_generate_figures_script.py``. ``scripts/generate_review_artifacts.py``
had none: the only related check (``test_review_artifacts_match_fresh_regeneration``
in ``test_protocol.py``) re-derives the same artifacts inline rather than
running the script's own ``main()`` / argparse path, so a break in the script
itself (wrong output filename, wrong summary keys, missing directory
creation) would go undetected. These tests close that gap by invoking the
script the way a user does: through ``main()`` with real ``sys.argv``.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest
from registered_report import freeze_registration, registration_hash

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "generate_review_artifacts.py"

_EXPECTED_ARTIFACTS = {
    "frozen_registration.json",
    "registered_report_review_packet.json",
    "deviation_ledger.json",
    "sensitivity_findings.json",
    "adherence_report.json",
}


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("registered_report_generate_review_artifacts", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_registration(tmp_path: Path) -> Path:
    registration = tmp_path / "example_registration.json"
    shutil.copy(PROJECT_ROOT / "data" / "example_registration.json", registration)
    return registration


def test_main_writes_all_review_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Running the script end to end writes every documented review artifact."""
    module = _load_script_module()
    registration = _copy_registration(tmp_path)
    output_dir = tmp_path / "reports"
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_review_artifacts.py", "--registration", str(registration), "--output-dir", str(output_dir)],
    )

    exit_code = module.main()
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert summary["valid"] is True
    assert set(summary["outputs"]) == _EXPECTED_ARTIFACTS
    for filename in _EXPECTED_ARTIFACTS:
        path = output_dir / filename
        assert path.is_file()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload  # every artifact is non-empty JSON


def test_main_output_matches_direct_library_computation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The script's written packet matches calling the library functions directly."""
    module = _load_script_module()
    registration = _copy_registration(tmp_path)
    output_dir = tmp_path / "reports"
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_review_artifacts.py", "--registration", str(registration), "--output-dir", str(output_dir)],
    )

    module.main()
    capsys.readouterr()

    frozen = freeze_registration(json.loads(registration.read_text(encoding="utf-8")))
    sensitivity_rows = frozen.get("sensitivity_analyses", [])
    expected_packet = module.build_review_packet(
        frozen, module.DEFAULT_EXECUTED, module.DEFAULT_DEVIATIONS, sensitivity_rows
    )
    written_packet = json.loads((output_dir / "registered_report_review_packet.json").read_text(encoding="utf-8"))

    assert json.loads(json.dumps(expected_packet, sort_keys=True)) == written_packet


def test_main_rejects_a_missing_registration_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A registration path that does not exist fails loudly, not silently."""
    module = _load_script_module()
    missing = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_review_artifacts.py", "--registration", str(missing), "--output-dir", str(tmp_path / "reports")],
    )

    with pytest.raises(FileNotFoundError):
        module.main()


@pytest.mark.parametrize("fault", ["missing_analysis_plan", "invalid_sensitivity"])
def test_invalid_registration_returns_nonzero_and_preserves_diagnostics(tmp_path: Path, fault: str) -> None:
    registration = _copy_registration(tmp_path)
    payload = json.loads(registration.read_text(encoding="utf-8"))
    if fault == "missing_analysis_plan":
        payload.pop("analysis_plan")
    else:
        payload["sensitivity_analyses"][0]["decision"] = "invented_decision"
    registration.write_text(json.dumps(payload), encoding="utf-8")
    output_dir = tmp_path / "reports"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--registration", str(registration), "--output-dir", str(output_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 2, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["valid"] is False
    assert set(summary["outputs"]) == _EXPECTED_ARTIFACTS
    packet = json.loads((output_dir / "registered_report_review_packet.json").read_text(encoding="utf-8"))
    assert packet["valid"] is False
    assert any(finding["severity"] == "error" for finding in packet["findings"])
    diagnostic = "adherence_report.json" if fault == "missing_analysis_plan" else "sensitivity_findings.json"
    report = json.loads((output_dir / diagnostic).read_text(encoding="utf-8"))
    assert any(finding["severity"] == "error" for finding in report["findings"])


def _run_review(registration: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--registration", str(registration), "--output-dir", str(output_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


@pytest.mark.parametrize("schema", [None, "template-registered-report/1", "template-registered-report/2"])
def test_producer_preserves_valid_historical_schema_hash_and_noncanonical_bytes(
    tmp_path: Path, schema: str | None
) -> None:
    registration = _copy_registration(tmp_path)
    archived = json.loads(registration.read_text(encoding="utf-8"))
    if schema is None:
        archived.pop("schema_version")
    else:
        archived["schema_version"] = schema
    archived["registration_hash"] = registration_hash(archived)
    original = (json.dumps(archived, indent=4, sort_keys=False) + "\n\n").encode("utf-8")
    registration.write_bytes(original)
    output_dir = tmp_path / "historical-reports"
    output_dir.mkdir()
    frozen_path = output_dir / "frozen_registration.json"
    frozen_path.write_bytes(original)

    completed = _run_review(registration, output_dir)

    assert completed.returncode == 0, completed.stderr
    assert frozen_path.read_bytes() == original
    assert json.loads(frozen_path.read_bytes()) == archived
    packet = json.loads((output_dir / "registered_report_review_packet.json").read_bytes())
    assert packet["registration_hash"] == archived["registration_hash"]


@pytest.mark.parametrize("target", ["hypothesis", "outcome", "analysis"])
def test_changed_draft_refuses_existing_output_and_allows_a_new_version(tmp_path: Path, target: str) -> None:
    registration = _copy_registration(tmp_path)
    output_dir = tmp_path / "original-reports"
    assert _run_review(registration, output_dir).returncode == 0
    originals = {path.name: path.read_bytes() for path in output_dir.iterdir()}
    changed = json.loads(registration.read_bytes())
    if target == "hypothesis":
        changed["hypotheses"][0]["claim"] = "A different prospective hypothesis"
    elif target == "outcome":
        changed["outcomes"][0]["description"] = "A different prospective outcome definition"
    else:
        changed["analysis_plan"]["prospective_note"] = "A different prospective analysis specification"
    registration.write_text(json.dumps(changed), encoding="utf-8")

    refused = _run_review(registration, output_dir)

    assert refused.returncode == 2
    assert "new versioned output directory" in refused.stderr
    assert refused.stdout == ""
    assert {path.name: path.read_bytes() for path in output_dir.iterdir()} == originals
    fresh = tmp_path / "version-2-reports"
    accepted = _run_review(registration, fresh)
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads((fresh / "frozen_registration.json").read_bytes()) == freeze_registration(changed)


@pytest.mark.parametrize("fault", ["changed_intent", "bad_hash", "missing_hash", "invalid_json", "array", "oversized"])
def test_corrupt_existing_frozen_record_is_preserved_and_refused(tmp_path: Path, fault: str) -> None:
    registration = _copy_registration(tmp_path)
    output_dir = tmp_path / "reports"
    assert _run_review(registration, output_dir).returncode == 0
    path = output_dir / "frozen_registration.json"
    corrupted = json.loads(path.read_bytes())
    if fault == "changed_intent":
        corrupted["hypotheses"][0]["claim"] = "Tampered after freezing"
    elif fault == "bad_hash":
        corrupted["registration_hash"] = "0" * 64
    elif fault == "missing_hash":
        corrupted.pop("registration_hash")
    encoded = json.dumps(corrupted).encode("utf-8")
    if fault == "invalid_json":
        encoded = b"{incomplete"
    elif fault == "array":
        encoded = b"[]"
    elif fault == "oversized":
        encoded = b" " * (1024 * 1024 + 1)
    path.write_bytes(encoded)
    originals = {item.name: item.read_bytes() for item in output_dir.iterdir()}

    refused = _run_review(registration, output_dir)

    assert refused.returncode == 2
    assert "new versioned output directory" in refused.stderr
    assert {item.name: item.read_bytes() for item in output_dir.iterdir()} == originals


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory"])
def test_frozen_record_special_files_cannot_redirect_or_block_the_producer(tmp_path: Path, kind: str) -> None:
    registration = _copy_registration(tmp_path)
    outside = tmp_path / "outside-registration.json"
    original = json.dumps(freeze_registration(json.loads(registration.read_bytes()))).encode("utf-8")
    outside.write_bytes(original)
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    frozen_path = output_dir / "frozen_registration.json"
    if kind == "symlink":
        frozen_path.symlink_to(outside)
    elif kind == "fifo":
        os.mkfifo(frozen_path)
    else:
        frozen_path.mkdir()

    refused = _run_review(registration, output_dir)

    assert refused.returncode == 2
    assert "new versioned output directory" in refused.stderr
    assert outside.read_bytes() == original
    assert {path.name for path in output_dir.iterdir()} == {"frozen_registration.json"}


def test_linked_output_ancestor_cannot_write_an_outside_registration(tmp_path: Path) -> None:
    registration = _copy_registration(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "immutable.txt"
    sentinel.write_bytes(b"preserved outside content")
    linked = tmp_path / "linked-reports"
    linked.symlink_to(outside, target_is_directory=True)

    refused = _run_review(registration, linked)

    assert refused.returncode == 2
    assert "new versioned output directory" in refused.stderr
    assert {item.name: item.read_bytes() for item in outside.iterdir()} == {sentinel.name: b"preserved outside content"}


def test_competing_drafts_cannot_replace_the_winning_registration(tmp_path: Path) -> None:
    first = _copy_registration(tmp_path)
    second = tmp_path / "other-registration.json"
    changed = json.loads(first.read_bytes())
    changed["hypotheses"][0]["claim"] = "A different competing registration"
    second.write_text(json.dumps(changed), encoding="utf-8")
    output_dir = tmp_path / "reports"
    processes = [
        subprocess.Popen(
            [sys.executable, str(SCRIPT), "--registration", str(source), "--output-dir", str(output_dir)],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for source in (first, second)
    ]
    results = [process.communicate(timeout=10) for process in processes]
    assert sorted(process.returncode for process in processes) == [0, 2], results
    winning_source = (first, second)[next(index for index, process in enumerate(processes) if process.returncode == 0)]
    winning_record = freeze_registration(json.loads(winning_source.read_bytes()))
    assert json.loads((output_dir / "frozen_registration.json").read_bytes()) == winning_record
    packet = json.loads((output_dir / "registered_report_review_packet.json").read_bytes())
    assert packet["registration_hash"] == winning_record["registration_hash"]

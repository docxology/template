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
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

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

    frozen = module.freeze_registration(json.loads(registration.read_text(encoding="utf-8")))
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

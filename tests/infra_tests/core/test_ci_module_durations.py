"""Measured module durations weight functional shards; they never select work."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.testing.ci_contracts import CONTRACT_MODULES
from infrastructure.core.testing.ci_infra import infrastructure_files
from infrastructure.core.testing.ci_module_durations import (
    MANIFEST_RELATIVE_PATH,
    SCHEMA_VERSION,
    load_module_durations,
    module_weights,
    validate_module_durations,
)

ROOT = Path(__file__).resolve().parents[3]


def _write_manifest(root: Path, payload: object) -> None:
    target = root / MANIFEST_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload), encoding="utf-8")


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "unit": "seconds",
        "provenance": "measured on hosted runners",
        "modules": {"tests/infra_tests/core/test_ci_infra.py": 12.5},
    }
    payload.update(overrides)
    return payload


def test_committed_manifest_measures_real_roster_modules() -> None:
    durations = load_module_durations(ROOT)
    assert durations
    roster = frozenset(infrastructure_files(ROOT)) | CONTRACT_MODULES
    validate_module_durations(durations, roster)
    assert all((ROOT / name).is_file() for name in durations)
    assert all(seconds > 0 for seconds in durations.values())


@pytest.mark.parametrize(
    "fault",
    ["schema", "unit", "provenance", "modules", "duplicate", "negative", "zero", "boolean", "escaping", "not-python"],
)
def test_manifest_refuses_unusable_evidence(tmp_path: Path, fault: str) -> None:
    payload: object = _payload()
    if fault == "schema":
        payload = _payload(schema_version="template-ci-module-durations-v0")
    elif fault == "unit":
        payload = _payload(unit="milliseconds")
    elif fault == "provenance":
        payload = _payload(provenance="   ")
    elif fault == "modules":
        payload = _payload(modules=["tests/infra_tests/core/test_ci_infra.py"])
    elif fault == "duplicate":
        payload = (
            '{"schema_version": "' + SCHEMA_VERSION + '", "unit": "seconds", "provenance": "p", '
            '"modules": {"a.py": 1, "a.py": 2}}'
        )
    elif fault == "negative":
        payload = _payload(modules={"tests/infra_tests/core/test_ci_infra.py": -1})
    elif fault == "zero":
        payload = _payload(modules={"tests/infra_tests/core/test_ci_infra.py": 0})
    elif fault == "boolean":
        payload = _payload(modules={"tests/infra_tests/core/test_ci_infra.py": True})
    elif fault == "escaping":
        payload = _payload(modules={"../outside.py": 1})
    else:
        payload = _payload(modules={"tests/infra_tests/core/test_ci_infra.txt": 1})

    target = tmp_path / MANIFEST_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        target.write_text(payload, encoding="utf-8")
    else:
        _write_manifest(tmp_path, payload)
    with pytest.raises(ValueError):
        load_module_durations(tmp_path)


def test_manifest_requires_a_committed_file(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        load_module_durations(tmp_path)


def test_measurements_must_name_real_roster_modules() -> None:
    roster = infrastructure_files(ROOT)
    validate_module_durations({roster[0]: 12.5}, roster)
    with pytest.raises(ValueError, match="outside the functional roster"):
        validate_module_durations({roster[0]: 12.5, "tests/infra_tests/core/test_unknown_module.py": 1.0}, roster)


def test_measured_seconds_lead_and_byte_size_estimates_the_rest(tmp_path: Path) -> None:
    names = ("tests/a.py", "tests/b.py", "tests/c.py")
    for name, size in zip(names, (100, 200, 400), strict=True):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x" * size)
    weights = module_weights(tmp_path, names, {names[0]: 50.0})
    # The only measurement sets the seconds-per-byte rate (50 s / 100 B).
    assert weights == {names[0]: 50.0, names[1]: 100.0, names[2]: 200.0}
    assert weights == module_weights(tmp_path, names, {names[0]: 50.0})


def test_median_rate_error_does_not_skew_the_estimated_scale(tmp_path: Path) -> None:
    names = ("tests/a.py", "tests/b.py", "tests/c.py")
    for name, size in zip(names, (100, 300, 600), strict=True):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x" * size)
    # Rates 0.5 s/B and 0.1 s/B with an unmeasured heavy outlier in between.
    weights = module_weights(tmp_path, names, {names[0]: 50.0, names[2]: 60.0})
    assert weights[names[0]] == 50.0
    assert weights[names[2]] == 60.0
    assert weights[names[1]] == pytest.approx(150.0)


def test_without_any_measurement_the_previous_byte_balance_is_preserved(tmp_path: Path) -> None:
    names = ("tests/a.py", "tests/b.py")
    for name, size in zip(names, (10, 20), strict=True):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x" * size)
    assert module_weights(tmp_path, names, {}) == {names[0]: 10.0, names[1]: 20.0}

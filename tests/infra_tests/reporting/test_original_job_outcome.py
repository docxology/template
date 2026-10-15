"""Job-status DATA cannot silently omit or hide required original failures."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.original_job_outcome import (
    AUXILIARY_KINDS,
    OTHER_AUXILIARY_OWNERS,
    evaluate_original_outcome,
)
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@pytest.fixture(scope="module")
def declared_requirements():
    root = Path(__file__).resolve().parents[3]
    rows, faults = required_profile(root, SnapshotReader(root), source_fingerprint(root))
    assert not faults
    return rows


def _report(kind, requirements):
    kinds = {"installed", "export"} if kind == "installed" else AUXILIARY_KINDS
    data = {
        "schema_version": SCHEMA_VERSION,
        "source_fingerprint": "a" * 64,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": {r.id: {"status": "pass"} for r in requirements if r.kind in kinds},
    }
    if kind == "installed":
        data["installed_matrix"] = {
            "matrix_complete": True,
            "source_current": True,
            "results": [
                {"scope": scope, "python_version": minor, "status": "pass"}
                for scope in ("root", *PUBLIC_PROJECT_NAMES)
                for minor in CANONICAL_CI_PYTHON_VERSIONS
            ],
        }
    return data


@pytest.mark.parametrize("kind", ["installed", "auxiliary"])
def test_success_is_only_a_diagnostic_summary(declared_requirements, kind):
    result = evaluate_original_outcome(
        kind, _report(kind, declared_requirements), declared_requirements, fingerprint="a" * 64
    )
    assert result["exit_code"] == 0
    assert result["release_acceptance_granted"] is False


@pytest.mark.parametrize("status", ["fail", "blocked"])
def test_linux_ignores_only_other_declared_owners(declared_requirements, status):
    report = _report("auxiliary", declared_requirements)
    for gate in OTHER_AUXILIARY_OWNERS:
        report["gates"][gate]["status"] = status
    assert evaluate_original_outcome("auxiliary", report, declared_requirements, fingerprint="a" * 64)["exit_code"] == 0
    report["gates"]["root:docs_lint"]["status"] = status
    result = evaluate_original_outcome("auxiliary", report, declared_requirements, fingerprint="a" * 64)
    assert result["exit_code"] == 1 and result["unpassed_gates"] == ["root:docs_lint"]


@pytest.mark.parametrize("mutation", ["gate", "cell", "duplicate", "missing", "stale", "invalid"])
def test_installed_failures_and_incomplete_data_cannot_look_green(declared_requirements, mutation):
    report = copy.deepcopy(_report("installed", declared_requirements))
    if mutation == "gate":
        report["gates"]["root:installed"]["status"] = "fail"
    elif mutation == "cell":
        report["installed_matrix"]["results"][0]["status"] = "fail"
    elif mutation == "duplicate":
        report["installed_matrix"]["results"][-1] = report["installed_matrix"]["results"][0]
    elif mutation == "missing":
        del report["gates"]["root:installed"]
    elif mutation == "stale":
        report["source_fingerprint"] = "b" * 64
    else:
        report["gates"]["root:installed"]["status"] = "skipped"
    if mutation in {"gate", "cell"}:
        assert (
            evaluate_original_outcome("installed", report, declared_requirements, fingerprint="a" * 64)["exit_code"]
            == 1
        )
    else:
        with pytest.raises(ValueError):
            evaluate_original_outcome("installed", report, declared_requirements, fingerprint="a" * 64)

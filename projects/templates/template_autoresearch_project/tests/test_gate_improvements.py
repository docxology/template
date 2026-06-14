"""Tests locking the RedTeam-driven hardening improvements (vectors B/C/D/E).

Each proves a gate that previously certified self-consistency or mere shape now
binds real content/provenance, while the healthy positive control still passes.
No mocks: real temp files and real computations.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from infrastructure.autoresearch import BenchmarkTask
from infrastructure.core.pipeline.artifacts import compute_sha256
from src.artifact_schemas import _check_conformance, schema_manifest_payload
from src.models import AutoResearchLoopResult
from src.figures.figures_core import save_figure
from src.security import _provenance_integrity_check, integrity_attestation_payload
from src.writers import (
    _BENCHMARK_CORE_ARTIFACTS,
    _GradingSettings,
    _grade_absent_benchmark,
    _load_grading_settings,
    _ml_accuracy_improved,
    write_schema_manifest,
)

_FQ_SCHEMA = "template-autoresearch-figure-quality-report-v1"


# --------------------------------------------------------------------------- #
# V-B — security integrity binds real provenance, empty file is a failure      #
# --------------------------------------------------------------------------- #


def test_provenance_check_passes_real_fixture(project_root: Path) -> None:
    check = _provenance_integrity_check(project_root)
    assert check is not None
    assert check["status"] == "passed"
    assert check["expected_sha256"] == check["actual_sha256"]


def test_provenance_check_detects_tampered_fixture(tmp_path: Path, project_root: Path) -> None:
    (tmp_path / "data").mkdir()
    shutil.copy(
        project_root / "data" / "mnist_small_provenance.json", tmp_path / "data" / "mnist_small_provenance.json"
    )
    (tmp_path / "data" / "mnist_small.npz").write_bytes(b"TAMPERED")
    check = _provenance_integrity_check(tmp_path)
    assert check is not None
    assert check["status"] == "mismatch"


def test_integrity_empty_required_file_is_failure(tmp_path: Path) -> None:
    artifact = tmp_path / "output" / "data" / "x.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("", encoding="utf-8")  # present but 0 bytes
    inventory = {
        "generated_artifacts": [{"path": "output/data/x.json", "sha256": compute_sha256(artifact), "required": True}]
    }
    payload = integrity_attestation_payload(tmp_path, inventory, generated_at="t")
    assert any(check["status"] == "empty" for check in payload["checks"])
    assert payload["status"] == "failed"


# --------------------------------------------------------------------------- #
# V-C — schema manifest validates payload conformance, not just a tag          #
# --------------------------------------------------------------------------- #


def test_schema_manifest_flags_tag_only_payload(tmp_path: Path) -> None:
    artifact = tmp_path / "output" / "data" / "fq.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(f'{{"schema": "{_FQ_SCHEMA}"}}', encoding="utf-8")  # tag present, fields absent
    manifest = schema_manifest_payload(tmp_path, [artifact], generated_at="t")
    assert manifest["valid"] is False
    assert any(row["path"] == "output/data/fq.json" for row in manifest["nonconforming_schema_artifacts"])


@pytest.mark.parametrize(
    "rel_path",
    [
        "output/data/autoresearch_evidence_overview.json",
        "output/data/benchmark_boundary.json",
    ],
)
def test_governance_contract_artifacts_cannot_fall_back_to_generic_exemptions(
    tmp_path: Path,
    rel_path: str,
) -> None:
    artifact = tmp_path / rel_path
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")

    manifest = schema_manifest_payload(tmp_path, [artifact], generated_at="t")

    assert any(row["path"] == rel_path for row in manifest["missing_schema_artifacts"])
    assert not any(row["path"] == rel_path for row in manifest["generic_table_exemptions"])


def test_write_schema_manifest_hard_gate_raises_on_nonconforming(tmp_path: Path) -> None:
    # V-C is a HARD production gate: a nonconforming governance payload aborts the
    # loop loudly rather than being written as a green manifest.
    artifact = tmp_path / "output" / "data" / "fq.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(f'{{"schema": "{_FQ_SCHEMA}"}}', encoding="utf-8")  # tag only, fields absent
    with pytest.raises(ValueError, match="nonconforming schema"):
        write_schema_manifest(tmp_path, [artifact], generated_at="t")


def test_schema_manifest_accepts_conforming_payload(tmp_path: Path) -> None:
    artifact = tmp_path / "output" / "data" / "fq.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        f'{{"schema": "{_FQ_SCHEMA}", "generated_at": "t", "figure_count": 1, "valid": true, "figures": []}}',
        encoding="utf-8",
    )
    manifest = schema_manifest_payload(tmp_path, [artifact], generated_at="t")
    assert manifest["valid"] is True
    assert not manifest["nonconforming_schema_artifacts"]


def test_schema_conformance_rejects_wrong_type() -> None:
    violations = _check_conformance(
        _FQ_SCHEMA, {"schema": "x", "generated_at": "t", "figure_count": 1, "valid": 1, "figures": []}
    )
    assert any("valid" in violation for violation in violations)


# --------------------------------------------------------------------------- #
# V-D — benchmark grading knobs are config-driven with loud rejection          #
# --------------------------------------------------------------------------- #


def test_grading_settings_defaults_when_absent(tmp_path: Path) -> None:
    settings = _load_grading_settings(tmp_path)  # no autoresearch.yaml
    assert settings.min_accuracy_delta == 0.005
    assert settings.core_artifacts == _BENCHMARK_CORE_ARTIFACTS
    assert settings.metric_direction == "maximize"


def test_grading_settings_reads_config(tmp_path: Path) -> None:
    (tmp_path / "autoresearch.yaml").write_text("grading:\n  min_accuracy_delta: 0.02\n", encoding="utf-8")
    assert _load_grading_settings(tmp_path).min_accuracy_delta == 0.02


@pytest.mark.parametrize(
    "bad_yaml",
    [
        "grading:\n  min_accuracy_delta: -0.1\n",
        "grading:\n  min_accuracy_delta: notanumber\n",
        "grading:\n  min_accuracy_delta: true\n",
        "grading:\n  core_artifacts: []\n",
        "grading: [1, 2, 3]\n",
        "metric_direction: sideways\n",
    ],
)
def test_grading_settings_rejects_bad_config(tmp_path: Path, bad_yaml: str) -> None:
    (tmp_path / "autoresearch.yaml").write_text(bad_yaml, encoding="utf-8")
    with pytest.raises(ValueError):
        _load_grading_settings(tmp_path)


def test_grade_threshold_is_config_driven(tmp_path: Path) -> None:
    (tmp_path / "output" / "data").mkdir(parents=True)
    (tmp_path / "output" / "data" / "ml_task_results.json").write_text('{"accuracy_delta": 0.05}', encoding="utf-8")
    assert _ml_accuracy_improved(tmp_path, _GradingSettings(min_accuracy_delta=0.01)) is True
    assert _ml_accuracy_improved(tmp_path, _GradingSettings(min_accuracy_delta=0.10)) is False


def test_grade_absent_benchmark_uses_loaded_settings(tmp_path: Path) -> None:
    # No evidence at all -> 0.0 incomplete (settings loaded from absent config).
    payload = _grade_absent_benchmark(tmp_path, BenchmarkTask(identifier="x", description="d", grading_output="g.json"))
    assert payload["score"] == 0.0
    assert payload["status"] == "incomplete"


# --------------------------------------------------------------------------- #
# V-E — figures are saved with deterministic (version/date-free) metadata      #
# --------------------------------------------------------------------------- #


def test_save_figure_pins_deterministic_metadata(tmp_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = plt.figure()
    plt.plot([0, 1, 2], [1, 3, 2])
    path = save_figure(figure, tmp_path / "t.png")
    raw = path.read_bytes()
    assert raw[:8] == bytes([137, 80, 78, 71, 13, 10, 26, 10])  # PNG magic
    assert b"Software" not in raw  # version-dependent chunk omitted
    assert b"Creation Time" not in raw  # wall-clock chunk omitted


# --------------------------------------------------------------------------- #
# Refinements (advisor-driven): no dead knob, direction flips, boundary, audit #
# --------------------------------------------------------------------------- #


def test_grading_settings_rejects_unknown_key(tmp_path: Path) -> None:
    # A typo'd knob is loudly rejected, not silently ignored (no dead knob).
    (tmp_path / "autoresearch.yaml").write_text("grading:\n  min_accuracy_detla: 0.01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported grading key"):
        _load_grading_settings(tmp_path)


def test_metric_direction_flips_verdict(tmp_path: Path) -> None:
    (tmp_path / "output" / "data").mkdir(parents=True)
    (tmp_path / "output" / "data" / "ml_task_results.json").write_text('{"accuracy_delta": 0.05}', encoding="utf-8")
    up = _GradingSettings(min_accuracy_delta=0.01, metric_direction="maximize")
    down = _GradingSettings(min_accuracy_delta=0.01, metric_direction="minimize")
    assert _ml_accuracy_improved(tmp_path, up) is True
    assert _ml_accuracy_improved(tmp_path, down) is False


def test_uncontracted_schema_is_not_conformance_checked(tmp_path: Path) -> None:
    # Boundary: a forged tag in an UNCONTRACTED schema still passes (recorded, not
    # nonconforming). The uncontracted schemas are knowingly not yet validated.
    artifact = tmp_path / "output" / "data" / "x.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text('{"schema": "template-autoresearch-not-contracted-v1"}', encoding="utf-8")
    manifest = schema_manifest_payload(tmp_path, [artifact], generated_at="t")
    assert manifest["valid"] is True
    assert any(row["path"] == "output/data/x.json" for row in manifest["schema_artifacts"])
    assert not manifest["nonconforming_schema_artifacts"]


def test_grade_payload_records_effective_threshold(tmp_path: Path) -> None:
    payload = _grade_absent_benchmark(tmp_path, BenchmarkTask(identifier="x", description="d", grading_output="g.json"))
    assert payload["effective_min_accuracy_delta"] == 0.005
    assert payload["effective_metric_direction"] == "maximize"


def test_research_object_manifest_surfaces_empty_artifacts(tmp_path: Path) -> None:
    # The research-object inventory must surface present-but-empty artifacts, not
    # just record their presence.
    from src.research_object import research_object_manifest_payload

    (tmp_path / "output" / "data").mkdir(parents=True)
    empty = tmp_path / "output" / "data" / "empty.json"
    empty.write_text("", encoding="utf-8")
    full = tmp_path / "output" / "data" / "full.json"
    full.write_text('{"value": 1}', encoding="utf-8")
    payload = research_object_manifest_payload(tmp_path, [empty, full], generated_at="t")
    assert payload["empty_artifact_count"] == 1
    assert any(str(a["path"]).endswith("empty.json") and a["empty"] for a in payload["artifacts"])


def test_provenance_blank_declared_hash_fails_closed(tmp_path: Path) -> None:
    # A PRESENT provenance file that declares no hash must fail closed, not vanish.
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "mnist_small_provenance.json").write_text('{"npz_sha256": ""}', encoding="utf-8")
    (tmp_path / "data" / "mnist_small.npz").write_bytes(b"some-fixture-bytes")
    check = _provenance_integrity_check(tmp_path)
    assert check is not None
    assert check["status"] == "missing_declared_hash"


# --------------------------------------------------------------------------- #
# CI gate on the REAL run: schema conformance + integrity bind (not just emit) #
# --------------------------------------------------------------------------- #


def test_real_run_governance_artifacts_are_conformant_and_intact(
    project_root: Path, autoresearch_loop_result: AutoResearchLoopResult
) -> None:
    # Binds V-C and V-B on the real pipeline output: a nonconforming schema payload
    # or a tampered/empty artifact would flip these red and fail CI.
    schema_manifest = json.loads((project_root / "output" / "data" / "autoresearch_schema_manifest.json").read_text())
    assert schema_manifest["valid"] is True
    assert not schema_manifest["nonconforming_schema_artifacts"]

    attestation = json.loads((project_root / "output" / "data" / "autoresearch_integrity_attestation.json").read_text())
    assert attestation["status"] == "passed"
    assert any(
        check["path"] == "data/mnist_small.npz" and check["status"] == "passed" for check in attestation["checks"]
    )

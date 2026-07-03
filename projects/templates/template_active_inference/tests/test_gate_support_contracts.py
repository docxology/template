"""Contract checks for gate artifact bootstrap helpers."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

import gate_support
import pytest


def _load_tests_conftest():
    conftest_path = Path(__file__).with_name("conftest.py")
    spec = importlib.util.spec_from_file_location("active_inference_tests_conftest", conftest_path)
    assert spec is not None
    assert spec.loader is not None
    project_conftest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project_conftest)
    return project_conftest


def test_required_gate_artifact_signature_uses_content_hash(
    monkeypatch,
    tmp_path: Path,
) -> None:
    rel = "output/data/cache_probe.json"
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    fixed_time_ns = 1_700_000_000_000_000_000

    monkeypatch.setattr(gate_support, "_REQUIRED_GATE_ARTIFACTS", (rel,))
    path.write_text("alpha", encoding="utf-8")
    os.utime(path, ns=(fixed_time_ns, fixed_time_ns))
    first = gate_support._required_gate_artifacts_signature(tmp_path)

    path.write_text("bravo", encoding="utf-8")
    os.utime(path, ns=(fixed_time_ns, fixed_time_ns))
    second = gate_support._required_gate_artifacts_signature(tmp_path)

    assert first is not None
    assert second is not None
    assert second != first


def test_session_prewarm_skips_collect_only(monkeypatch) -> None:
    project_conftest = _load_tests_conftest()

    def fail_if_called() -> None:
        raise AssertionError("collect-only discovery must not prewarm gate artifacts")

    monkeypatch.setattr(project_conftest, "_iter_mutable_project_sources", fail_if_called)
    session = SimpleNamespace(config=SimpleNamespace(option=SimpleNamespace(collectonly=True)))

    project_conftest.pytest_sessionstart(session)


def test_mutable_output_snapshot_includes_gate_contract_artifacts() -> None:
    project_conftest = _load_tests_conftest()

    rels = {
        path.relative_to(project_conftest.PROJECT_ROOT).as_posix()
        for path in project_conftest._iter_mutable_project_outputs()
    }

    assert "output/data/artifact_provenance.json" in rels
    assert "output/data/sheaf_gluing_certificate.json" in rels
    assert "output/reports/artifact_diffoscope.json" in rels


def test_ensure_gate_artifacts_reuses_matching_session_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    monkeypatch.setitem(gate_support._BOOTSTRAPPED_SIGNATURES, root, "prepared")

    def fail_if_called(project_root: Path) -> bool:
        raise AssertionError("_gate_artifacts_present should not run for cached signatures")

    monkeypatch.setattr(gate_support, "_required_gate_artifacts_signature", lambda project_root: "prepared")
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", fail_if_called)

    gate_support.ensure_gate_artifacts(root)

    assert root in gate_support._BOOTSTRAPPED_ROOTS


def test_ensure_gate_artifacts_records_complete_bootstrapped_changed_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    validated_roots: list[Path] = []
    monkeypatch.setattr(gate_support, "_BOOTSTRAPPED_ROOTS", {root})
    monkeypatch.setattr(gate_support, "_BOOTSTRAPPED_SIGNATURES", {root: "old"})
    monkeypatch.setattr(gate_support, "_required_gate_artifacts_signature", lambda project_root: "changed")

    def artifacts_are_valid(project_root: Path) -> bool:
        validated_roots.append(project_root)
        return True

    def fail_if_called(*args, **kwargs) -> None:
        raise AssertionError("complete bootstrapped artifact trees should not trigger a fixed-point refresh")

    monkeypatch.setattr(gate_support, "refresh_generated_gate_artifacts", fail_if_called)
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", artifacts_are_valid)
    monkeypatch.setattr(gate_support, "run_analysis", fail_if_called)

    gate_support.ensure_gate_artifacts(root)

    assert gate_support._BOOTSTRAPPED_SIGNATURES[root] == "changed"
    assert validated_roots == [root]


def test_ensure_gate_artifacts_rejects_invalid_bootstrapped_changed_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    monkeypatch.setenv(gate_support._ALLOW_GATE_REBUILD_ENV, "1")
    monkeypatch.setattr(gate_support, "_BOOTSTRAPPED_ROOTS", {root})
    monkeypatch.setattr(gate_support, "_BOOTSTRAPPED_SIGNATURES", {root: "old"})
    monkeypatch.setattr(gate_support, "_required_gate_artifacts_signature", lambda project_root: "changed")
    monkeypatch.setattr(gate_support, "_required_gate_artifacts_exist", lambda project_root: True)
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: False)

    def stop_before_rebuild(*args, **kwargs) -> None:
        raise RuntimeError("full refresh required")

    monkeypatch.setattr(gate_support, "run_analysis", stop_before_rebuild)

    with pytest.raises(RuntimeError, match="full refresh required"):
        gate_support.ensure_gate_artifacts(root)

    assert gate_support._BOOTSTRAPPED_SIGNATURES[root] == "old"


def test_ensure_gate_artifacts_fails_fast_without_rebuild_opt_in(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path.resolve()
    monkeypatch.delenv(gate_support._ALLOW_GATE_REBUILD_ENV, raising=False)
    monkeypatch.setattr(gate_support, "_required_gate_artifacts_signature", lambda project_root: "stale")
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: False)
    monkeypatch.setattr(gate_support, "gate_artifact_readiness_issues", lambda project_root: ("semantic drift",))

    def fail_if_called(*args, **kwargs) -> None:
        raise AssertionError("standard pytest must not rebuild active-inference artifacts")

    monkeypatch.setattr(gate_support, "run_analysis", fail_if_called)

    with pytest.raises(AssertionError, match="Standard pytest runs do not rebuild"):
        gate_support.ensure_gate_artifacts(root)


def test_refresh_generated_gate_artifacts_accepts_valid_changed_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    monkeypatch.setitem(gate_support._BOOTSTRAPPED_SIGNATURES, root, "old")
    monkeypatch.setattr(gate_support, "_required_gate_artifacts_signature", lambda project_root: "changed")
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: True)

    def fail_if_called(project_root: Path, out: Path, *, passes: int | None = None) -> None:
        raise AssertionError("valid changed artifact trees should not rebuild")

    monkeypatch.setattr(gate_support, "_settle_generated_contracts", fail_if_called)

    gate_support.refresh_generated_gate_artifacts(root, force=False)

    assert gate_support._BOOTSTRAPPED_SIGNATURES[root] == "changed"
    assert root in gate_support._BOOTSTRAPPED_ROOTS


def test_refresh_generated_gate_artifacts_rejects_invalid_post_rebuild_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    monkeypatch.setattr(
        gate_support, "_required_gate_artifacts_signature", lambda project_root: "invalid-after-rebuild"
    )
    monkeypatch.setattr(gate_support, "_settle_generated_contracts", lambda project_root, out: None)
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: False)

    with pytest.raises(AssertionError, match="gate artifacts are invalid"):
        gate_support.refresh_generated_gate_artifacts(root)

    assert root not in gate_support._BOOTSTRAPPED_SIGNATURES


def test_settle_generated_contracts_delegates_to_semantic_fixed_point(
    monkeypatch,
    tmp_path: Path,
) -> None:
    import roadmap_tracks.fixed_point as fixed_point

    root = tmp_path.resolve()
    out = root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True)
    out.write_text("{}", encoding="utf-8")
    calls: list[tuple[Path, bool, int]] = []
    sheaf_prerequisite_calls: list[tuple[Path, bool]] = []
    monkeypatch.setattr(gate_support, "generate_all_figures", lambda project_root: None)
    monkeypatch.setattr(gate_support, "write_belief_trajectory_gif", lambda project_root: None)
    monkeypatch.setattr(gate_support, "write_animation_frame_deltas", lambda project_root: None)

    def fail_if_called(*args, **kwargs) -> None:
        raise AssertionError("settle should not run duplicate compose/hydrate/integration phases")

    def write_sheaf_prerequisites(project_root: Path, *, finalize: bool = True) -> dict:
        sheaf_prerequisite_calls.append((project_root, finalize))
        return {}

    monkeypatch.setattr(gate_support, "compose_all_sections", fail_if_called)
    monkeypatch.setattr(gate_support, "_hydrate_fixed_point", fail_if_called)
    monkeypatch.setattr(gate_support, "write_integration_audit_artifacts", fail_if_called)
    monkeypatch.setattr(gate_support, "write_sheaf_track_artifacts", write_sheaf_prerequisites)

    def run_fixed_point(project_root: Path, *, require_analysis_outputs: bool, max_passes: int) -> dict:
        calls.append((project_root, require_analysis_outputs, max_passes))
        return {}

    monkeypatch.setattr(fixed_point, "run_semantic_fixed_point", run_fixed_point)

    gate_support._settle_generated_contracts(root, out, passes=2)

    assert calls == [(root, False, 8), (root, False, 8)]
    assert sheaf_prerequisite_calls == [(root, False), (root, False)]


def test_refresh_gate_artifact_session_signature_records_valid_current_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()

    def fail_if_called(*args, **kwargs) -> None:
        raise AssertionError("session-signature refresh must not regenerate artifacts")

    monkeypatch.setattr(gate_support, "_required_gate_artifacts_signature", lambda project_root: "fresh")
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: True)
    monkeypatch.setattr(gate_support, "_settle_generated_contracts", fail_if_called)

    gate_support.refresh_gate_artifact_session_signature(root)

    assert gate_support._BOOTSTRAPPED_SIGNATURES[root] == "fresh"
    assert root in gate_support._BOOTSTRAPPED_ROOTS


def test_refresh_gate_artifact_session_signature_rejects_invalid_current_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    monkeypatch.setattr(gate_support, "_required_gate_artifacts_signature", lambda project_root: "fresh")
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: False)

    with pytest.raises(AssertionError, match="gate artifacts are invalid"):
        gate_support.refresh_gate_artifact_session_signature(root)

    assert root not in gate_support._BOOTSTRAPPED_SIGNATURES


def test_refresh_output_gate_contracts_reuses_clean_contracts(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path.resolve()
    monkeypatch.setattr(gate_support, "validate_animation_frame_deltas", lambda project_root: [])
    monkeypatch.setattr(gate_support, "validate_integration_audit_artifacts", lambda project_root: [])
    monkeypatch.setattr(gate_support, "validate_sheaf_track_artifacts", lambda project_root: [])
    monkeypatch.setattr(gate_support, "_required_gate_artifacts_signature", lambda project_root: "clean")
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: True)

    def fail_if_called(*args, **kwargs) -> None:
        raise AssertionError("clean output gate contracts should not be regenerated")

    monkeypatch.setattr(gate_support, "write_animation_frame_deltas", fail_if_called)
    monkeypatch.setattr(gate_support, "write_integration_audit_artifacts", fail_if_called)
    monkeypatch.setattr(gate_support, "write_sheaf_track_artifacts", fail_if_called)

    gate_support.refresh_output_gate_contracts(root)

    assert gate_support._BOOTSTRAPPED_SIGNATURES[root] == "clean"


def test_refresh_output_gate_contracts_revalidates_repaired_artifacts(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path.resolve()
    integration_results = iter([["initial integration issue"], ["still bad"]])
    sheaf_results = iter([["initial sheaf issue"], []])

    monkeypatch.setattr(gate_support, "validate_animation_frame_deltas", lambda project_root: [])
    monkeypatch.setattr(
        gate_support,
        "validate_integration_audit_artifacts",
        lambda project_root: next(integration_results),
    )
    monkeypatch.setattr(
        gate_support,
        "validate_sheaf_track_artifacts",
        lambda project_root: next(sheaf_results),
    )
    monkeypatch.setattr(gate_support, "_required_gate_artifacts_signature", lambda project_root: "sig-after-bad")
    monkeypatch.setattr(gate_support, "write_integration_audit_artifacts", lambda project_root: None)
    monkeypatch.setattr(gate_support, "write_sheaf_track_artifacts", lambda project_root: None)

    with pytest.raises(AssertionError, match="output gate contracts remain invalid"):
        gate_support.refresh_output_gate_contracts(root)

    assert root not in gate_support._BOOTSTRAPPED_SIGNATURES


def test_gate_artifacts_present_requires_claim_ledger(monkeypatch, tmp_path: Path) -> None:
    import gates.claim_ledger as claim_ledger
    import manuscript.sheaf.semantic as semantic
    import roadmap_tracks

    monkeypatch.setattr(gate_support, "_required_gate_artifacts_exist", lambda project_root: True)
    monkeypatch.setattr(gate_support, "validate_animation_frame_deltas", lambda project_root: [])
    monkeypatch.setattr(semantic, "validate_semantic_gluing", lambda project_root: [])
    monkeypatch.setattr(roadmap_tracks, "validate_integration_audit_artifacts", lambda project_root: [])
    monkeypatch.setattr(roadmap_tracks, "validate_sheaf_track_artifacts", lambda project_root: [])
    monkeypatch.setattr(claim_ledger, "validate_claim_ledger", lambda project_root: False)

    assert gate_support._gate_artifacts_present(tmp_path) is False


def test_gate_artifacts_present_requires_animation_deltas(monkeypatch, tmp_path: Path) -> None:
    import gates.claim_ledger as claim_ledger
    import manuscript.sheaf.semantic as semantic
    import roadmap_tracks

    monkeypatch.setattr(gate_support, "_required_gate_artifacts_exist", lambda project_root: True)
    monkeypatch.setattr(gate_support, "validate_animation_frame_deltas", lambda project_root: ["bad animation"])
    monkeypatch.setattr(semantic, "validate_semantic_gluing", lambda project_root: [])
    monkeypatch.setattr(roadmap_tracks, "validate_integration_audit_artifacts", lambda project_root: [])
    monkeypatch.setattr(roadmap_tracks, "validate_sheaf_track_artifacts", lambda project_root: [])
    monkeypatch.setattr(claim_ledger, "validate_claim_ledger", lambda project_root: True)

    assert gate_support._gate_artifacts_present(tmp_path) is False


def test_ensure_gate_artifacts_rejects_invalid_post_rebuild_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    monkeypatch.setenv(gate_support._ALLOW_GATE_REBUILD_ENV, "1")
    monkeypatch.setattr(
        gate_support, "_required_gate_artifacts_signature", lambda project_root: "invalid-after-rebuild"
    )
    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: False)
    monkeypatch.setattr(gate_support, "pymdp_available", lambda: True)

    for name in (
        "run_analysis",
        "run_and_persist",
        "write_policy_comparison",
        "write_policy_posterior_grid",
        "write_graph_world_artifacts",
        "write_analysis_statistics",
        "compose_all_sections",
        "ensure_coverage_artifacts",
        "generate_all_figures",
        "write_belief_trajectory_gif",
        "write_animation_frame_deltas",
        "write_validation_spine_artifacts",
        "write_toy_sweep_artifacts",
        "write_formal_interop_artifacts",
        "write_sheaf_track_artifacts",
    ):
        monkeypatch.setattr(gate_support, name, lambda *args, **kwargs: None)
    monkeypatch.setattr(gate_support, "_settle_generated_contracts", lambda project_root, out: None)

    with pytest.raises(AssertionError, match="gate artifacts are invalid"):
        gate_support.ensure_gate_artifacts(root)

    assert root not in gate_support._BOOTSTRAPPED_SIGNATURES


def test_fixed_point_pass_env_override_is_fail_closed(monkeypatch) -> None:
    for raw in ("bad", "0", "-4"):
        monkeypatch.setenv("TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES", raw)
        assert gate_support._fixed_point_passes() == 1

    monkeypatch.setenv("TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES", "3")
    assert gate_support._fixed_point_passes() == 3

"""Contract checks for gate artifact bootstrap helpers."""

from __future__ import annotations

import os
from pathlib import Path

import gate_support


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


def test_gate_artifacts_present_requires_claim_ledger(monkeypatch, tmp_path: Path) -> None:
    import gates.claim_ledger as claim_ledger
    import manuscript.sheaf.semantic as semantic
    import roadmap_tracks

    monkeypatch.setattr(gate_support, "_required_gate_artifacts_exist", lambda project_root: True)
    monkeypatch.setattr(semantic, "validate_semantic_gluing", lambda project_root: [])
    monkeypatch.setattr(roadmap_tracks, "validate_integration_audit_artifacts", lambda project_root: [])
    monkeypatch.setattr(roadmap_tracks, "validate_sheaf_track_artifacts", lambda project_root: [])
    monkeypatch.setattr(claim_ledger, "validate_claim_ledger", lambda project_root: False)

    assert gate_support._gate_artifacts_present(tmp_path) is False


def test_fixed_point_pass_env_override_is_fail_closed(monkeypatch) -> None:
    for raw in ("bad", "0", "-4"):
        monkeypatch.setenv("TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES", raw)
        assert gate_support._fixed_point_passes() == 1

    monkeypatch.setenv("TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES", "3")
    assert gate_support._fixed_point_passes() == 3

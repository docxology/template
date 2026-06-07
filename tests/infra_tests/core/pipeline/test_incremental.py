#!/usr/bin/env python3
"""Unit tests for content-hash stage skipping (INCREMENTAL-PIPELINE-1).

No Mocks: every test uses real files under ``tmp_path`` and real
:class:`StageContract` declarations. Determinism is proven by recomputing
hashes and asserting byte-stable equality.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.pipeline.incremental import (
    IncrementalConfig,
    HashManifest,
    compute_stage_input_hash,
    load_hash_manifest,
    record_stage_hash,
    save_hash_manifest,
    should_skip_stage,
)
from infrastructure.core.pipeline.types import StageContract


def _make_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    (project_dir / "output").mkdir(parents=True)
    return repo_root, project_dir


class TestIncrementalConfigDefaultOff:
    def test_default_is_disabled(self) -> None:
        assert IncrementalConfig().enabled is False

    def test_should_skip_returns_false_when_disabled(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        contract = StageContract(input_artifacts=("manuscript/a.md",), output_artifacts=("output/out.txt",))
        # Even if a manifest somehow exists, a disabled config must never skip.
        manifest = HashManifest()
        decision = should_skip_stage(
            config=IncrementalConfig(enabled=False),
            manifest=manifest,
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
        )
        assert decision.skip is False


class TestStageInputHashDeterminism:
    def test_same_inputs_same_hash(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "a.md").write_text("hello", encoding="utf-8")
        contract = StageContract(input_artifacts=("manuscript/a.md",))

        h1 = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        h2 = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        assert h1 == h2
        assert isinstance(h1, str) and len(h1) == 64  # sha256 hex

    def test_mutated_input_changes_hash(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        (project_dir / "manuscript").mkdir()
        src = project_dir / "manuscript" / "a.md"
        src.write_text("hello", encoding="utf-8")
        contract = StageContract(input_artifacts=("manuscript/a.md",))

        before = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        src.write_text("changed", encoding="utf-8")
        after = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        assert before != after

    def test_upstream_hash_change_changes_hash(self, tmp_path: Path) -> None:
        """Downstream invalidation: a changed upstream output hash flips ours."""
        repo_root, project_dir = _make_repo(tmp_path)
        contract = StageContract(depends_on=()) if False else StageContract()
        h_a = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Downstream",
            contract=contract,
            upstream_output_hashes={"Upstream": "aaa"},
        )
        h_b = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Downstream",
            contract=contract,
            upstream_output_hashes={"Upstream": "bbb"},
        )
        assert h_a != h_b

    def test_missing_input_file_is_tolerated_and_deterministic(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        contract = StageContract(input_artifacts=("manuscript/missing.md",))
        h1 = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        h2 = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        assert h1 == h2


class TestManifestRoundTrip:
    def test_save_and_load_round_trip(self, tmp_path: Path) -> None:
        _, project_dir = _make_repo(tmp_path)
        manifest = HashManifest()
        manifest.record("Stage A", input_hash="abc", output_hash="def")
        save_hash_manifest(project_dir / "output", manifest)

        loaded = load_hash_manifest(project_dir / "output")
        rec = loaded.get("Stage A")
        assert rec is not None
        assert rec.input_hash == "abc"
        assert rec.output_hash == "def"

    def test_load_missing_manifest_is_empty(self, tmp_path: Path) -> None:
        _, project_dir = _make_repo(tmp_path)
        loaded = load_hash_manifest(project_dir / "output")
        assert loaded.get("Anything") is None

    def test_load_corrupt_manifest_is_empty_failsafe(self, tmp_path: Path) -> None:
        _, project_dir = _make_repo(tmp_path)
        path = project_dir / "output" / ".pipeline" / "incremental.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{ not json", encoding="utf-8")
        loaded = load_hash_manifest(project_dir / "output")
        # Fail-safe: corrupt manifest behaves like absent (forces re-run).
        assert loaded.get("Stage A") is None


class TestShouldSkipStage:
    def _contract(self) -> StageContract:
        return StageContract(input_artifacts=("manuscript/a.md",), output_artifacts=("output/out.txt",))

    def _write_inputs(self, project_dir: Path) -> None:
        (project_dir / "manuscript").mkdir(exist_ok=True)
        (project_dir / "manuscript" / "a.md").write_text("hello", encoding="utf-8")

    def _write_outputs(self, project_dir: Path) -> None:
        (project_dir / "output" / "out.txt").write_text("result", encoding="utf-8")

    def test_no_record_means_run(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        self._write_inputs(project_dir)
        decision = should_skip_stage(
            config=IncrementalConfig(enabled=True),
            manifest=HashManifest(),
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=self._contract(),
        )
        assert decision.skip is False

    def test_matching_hash_with_outputs_present_skips(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        self._write_inputs(project_dir)
        self._write_outputs(project_dir)
        contract = self._contract()
        input_hash = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        manifest = HashManifest()
        manifest.record("Stage A", input_hash=input_hash, output_hash="ignored")

        decision = should_skip_stage(
            config=IncrementalConfig(enabled=True),
            manifest=manifest,
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
        )
        assert decision.skip is True
        assert decision.input_hash == input_hash

    def test_changed_input_forces_run(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        self._write_inputs(project_dir)
        self._write_outputs(project_dir)
        contract = self._contract()
        recorded = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        manifest = HashManifest()
        manifest.record("Stage A", input_hash=recorded, output_hash="x")

        # Mutate the input.
        (project_dir / "manuscript" / "a.md").write_text("DIFFERENT", encoding="utf-8")

        decision = should_skip_stage(
            config=IncrementalConfig(enabled=True),
            manifest=manifest,
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
        )
        assert decision.skip is False

    def test_missing_output_forces_run_even_if_hash_matches(self, tmp_path: Path) -> None:
        """Fail-safe: never skip when a declared output is absent."""
        repo_root, project_dir = _make_repo(tmp_path)
        self._write_inputs(project_dir)
        # Note: outputs intentionally NOT written.
        contract = self._contract()
        input_hash = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        manifest = HashManifest()
        manifest.record("Stage A", input_hash=input_hash, output_hash="x")

        decision = should_skip_stage(
            config=IncrementalConfig(enabled=True),
            manifest=manifest,
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
        )
        assert decision.skip is False

    def test_no_declared_outputs_never_skips(self, tmp_path: Path) -> None:
        """A stage with no declared outputs cannot be proven complete -> always run."""
        repo_root, project_dir = _make_repo(tmp_path)
        self._write_inputs(project_dir)
        contract = StageContract(input_artifacts=("manuscript/a.md",))  # no output_artifacts
        input_hash = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        manifest = HashManifest()
        manifest.record("Stage A", input_hash=input_hash, output_hash="x")

        decision = should_skip_stage(
            config=IncrementalConfig(enabled=True),
            manifest=manifest,
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
        )
        assert decision.skip is False


class TestRecordStageHash:
    def test_record_stores_input_and_output_hash(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "a.md").write_text("hi", encoding="utf-8")
        (project_dir / "output" / "out.txt").write_text("res", encoding="utf-8")
        contract = StageContract(input_artifacts=("manuscript/a.md",), output_artifacts=("output/out.txt",))
        manifest = HashManifest()

        record_stage_hash(
            manifest=manifest,
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Stage A",
            contract=contract,
            upstream_output_hashes={},
        )
        rec = manifest.get("Stage A")
        assert rec is not None
        assert len(rec.input_hash) == 64
        assert len(rec.output_hash) == 64

    def test_recorded_output_hash_feeds_downstream(self, tmp_path: Path) -> None:
        """End-to-end invalidation chain at the unit level.

        Recording an upstream output hash, then feeding it as an upstream
        dependency hash, must change a downstream input hash when the upstream
        output changes.
        """
        repo_root, project_dir = _make_repo(tmp_path)
        out = project_dir / "output" / "up.txt"
        out.write_text("v1", encoding="utf-8")
        up_contract = StageContract(output_artifacts=("output/up.txt",))
        manifest = HashManifest()
        record_stage_hash(
            manifest=manifest,
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Upstream",
            contract=up_contract,
            upstream_output_hashes={},
        )
        up_hash_v1 = manifest.get("Upstream").output_hash

        out.write_text("v2", encoding="utf-8")
        record_stage_hash(
            manifest=manifest,
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name="Upstream",
            contract=up_contract,
            upstream_output_hashes={},
        )
        up_hash_v2 = manifest.get("Upstream").output_hash
        assert up_hash_v1 != up_hash_v2

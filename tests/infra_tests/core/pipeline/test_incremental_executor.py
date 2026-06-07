#!/usr/bin/env python3
"""Executor integration tests for incremental stage skipping (INCREMENTAL-PIPELINE-1).

No Mocks: a real :class:`PipelineExecutor` runs a small hand-built stage plan
over a real temp project tree. Stage callables are plain Python closures that
record their invocations and write real output files — no mocking framework.

Proves:
1. DEFAULT-OFF: with incremental disabled (default), every stage runs on both
   the first and the repeated run (byte-identical behavior to today).
2. Incremental ON: a repeated run with unchanged inputs SKIPS unchanged stages.
3. Mutating a stage input re-runs that stage AND its downstream dependents.
4. A missing/stale output forces a re-run even when the input hash matches.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.pipeline.executor import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.incremental import IncrementalConfig
from infrastructure.core.pipeline.types import StageContract, StageSpec


def _make_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    (project_dir / "output").mkdir(parents=True)
    (project_dir / "manuscript").mkdir(parents=True)
    return repo_root, project_dir


def _build_two_stage_plan(project_dir: Path, calls: list[str]) -> list[StageSpec]:
    """Two chained stages: Upstream -> Downstream.

    Upstream reads manuscript/a.md, writes output/up.txt.
    Downstream reads output/up.txt (declared input), writes output/down.txt.
    """
    src = project_dir / "manuscript" / "a.md"
    up_out = project_dir / "output" / "up.txt"
    down_out = project_dir / "output" / "down.txt"

    def run_upstream() -> bool:
        calls.append("Upstream")
        up_out.write_text(src.read_text(encoding="utf-8") + "-up", encoding="utf-8")
        return True

    def run_downstream() -> bool:
        calls.append("Downstream")
        down_out.write_text(up_out.read_text(encoding="utf-8") + "-down", encoding="utf-8")
        return True

    upstream = StageSpec(
        "Upstream",
        run_upstream,
        StageContract(input_artifacts=("manuscript/a.md",), output_artifacts=("output/up.txt",)),
    )
    downstream = StageSpec(
        "Downstream",
        run_downstream,
        StageContract(
            input_artifacts=("output/up.txt",),
            output_artifacts=("output/down.txt",),
            rollback_to="Upstream",
        ),
    )
    return [upstream, downstream]


class TestDefaultOff:
    def test_every_stage_runs_on_repeat_when_disabled(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        (project_dir / "manuscript" / "a.md").write_text("seed", encoding="utf-8")

        # clean=False so outputs survive between runs; default incremental OFF.
        config = PipelineConfig(project_name="p", repo_root=repo_root, clean=False)
        assert config.incremental.enabled is False  # default-off invariant

        calls: list[str] = []
        executor = PipelineExecutor(config)
        plan = _build_two_stage_plan(project_dir, calls)

        executor._execute_pipeline(plan)
        executor._execute_pipeline(plan)

        # Both stages ran on BOTH runs -> 4 invocations, no skipping.
        assert calls == ["Upstream", "Downstream", "Upstream", "Downstream"]
        # No incremental manifest is ever written when disabled.
        assert not (project_dir / "output" / ".pipeline" / "incremental.json").exists()


class TestIncrementalSkip:
    def _config(self, repo_root: Path) -> PipelineConfig:
        return PipelineConfig(
            project_name="p",
            repo_root=repo_root,
            clean=False,
            incremental=IncrementalConfig(enabled=True),
        )

    def test_repeat_run_skips_unchanged_stages(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        (project_dir / "manuscript" / "a.md").write_text("seed", encoding="utf-8")

        config = self._config(repo_root)
        executor = PipelineExecutor(config)

        calls: list[str] = []
        plan = _build_two_stage_plan(project_dir, calls)

        first = executor._execute_pipeline(plan)
        assert calls == ["Upstream", "Downstream"]
        assert all(r.success for r in first)

        calls.clear()
        second_executor = PipelineExecutor(config)
        plan2 = _build_two_stage_plan(project_dir, calls)
        second = second_executor._execute_pipeline(plan2)

        # Nothing changed -> both stages skipped.
        assert calls == []
        # Skipped stages are reported as successful, completed results.
        assert all(r.success for r in second)
        names_skipped = {r.stage_name for r in second if "skip" in r.error_message.lower() or r.lessons}
        # At minimum every stage in the second run reported success without running.
        assert {r.stage_name for r in second} == {"Upstream", "Downstream"}
        assert names_skipped == {"Upstream", "Downstream"}

    def test_mutating_input_reruns_stage_and_downstream(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        src = project_dir / "manuscript" / "a.md"
        src.write_text("seed", encoding="utf-8")

        config = self._config(repo_root)

        calls: list[str] = []
        PipelineExecutor(config)._execute_pipeline(_build_two_stage_plan(project_dir, calls))
        assert calls == ["Upstream", "Downstream"]

        # Mutate Upstream's declared input. Upstream re-runs; its output changes;
        # therefore Downstream's declared input changes -> Downstream re-runs too.
        src.write_text("seed-CHANGED", encoding="utf-8")

        calls.clear()
        PipelineExecutor(config)._execute_pipeline(_build_two_stage_plan(project_dir, calls))
        assert calls == ["Upstream", "Downstream"]

    def test_only_downstream_reruns_when_only_its_own_input_changes(self, tmp_path: Path) -> None:
        """Surgical invalidation: changing only Downstream's input leaves Upstream skipped."""
        repo_root, project_dir = _make_repo(tmp_path)
        (project_dir / "manuscript" / "a.md").write_text("seed", encoding="utf-8")

        # Independent downstream input file (not produced by Upstream).
        extra = project_dir / "manuscript" / "extra.md"
        extra.write_text("x", encoding="utf-8")

        up_out = project_dir / "output" / "up.txt"
        down_out = project_dir / "output" / "down.txt"
        src = project_dir / "manuscript" / "a.md"

        def make_plan(calls: list[str]) -> list[StageSpec]:
            def run_upstream() -> bool:
                calls.append("Upstream")
                up_out.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                return True

            def run_downstream() -> bool:
                calls.append("Downstream")
                down_out.write_text(extra.read_text(encoding="utf-8"), encoding="utf-8")
                return True

            return [
                StageSpec(
                    "Upstream",
                    run_upstream,
                    StageContract(input_artifacts=("manuscript/a.md",), output_artifacts=("output/up.txt",)),
                ),
                StageSpec(
                    "Downstream",
                    run_downstream,
                    StageContract(
                        input_artifacts=("manuscript/extra.md",),
                        output_artifacts=("output/down.txt",),
                    ),
                ),
            ]

        config = self._config(repo_root)
        calls: list[str] = []
        PipelineExecutor(config)._execute_pipeline(make_plan(calls))
        assert calls == ["Upstream", "Downstream"]

        extra.write_text("x-CHANGED", encoding="utf-8")
        calls.clear()
        PipelineExecutor(config)._execute_pipeline(make_plan(calls))
        # Upstream unchanged -> skipped; only Downstream re-runs.
        assert calls == ["Downstream"]

    def test_missing_output_forces_rerun(self, tmp_path: Path) -> None:
        repo_root, project_dir = _make_repo(tmp_path)
        (project_dir / "manuscript" / "a.md").write_text("seed", encoding="utf-8")

        config = self._config(repo_root)
        calls: list[str] = []
        PipelineExecutor(config)._execute_pipeline(_build_two_stage_plan(project_dir, calls))
        assert calls == ["Upstream", "Downstream"]

        # Delete a declared output: fail-safe must force re-run despite matching hash.
        (project_dir / "output" / "up.txt").unlink()

        calls.clear()
        PipelineExecutor(config)._execute_pipeline(_build_two_stage_plan(project_dir, calls))
        # Upstream re-runs (output absent); its rewritten output is identical so
        # Downstream's input hash matches and Downstream stays skipped.
        assert calls == ["Upstream"]

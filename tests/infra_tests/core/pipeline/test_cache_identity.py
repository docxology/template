"""Real child and file controls for effective inputs and precise custody scope."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
import yaml

from infrastructure.core.files.project_lock import _env_var, _lock_key, project_output_lock
from infrastructure.core.pipeline.artifacts import collect_stable_output_inventory
from infrastructure.core.pipeline.execution_environment import (
    VOLATILE_CONTROL_KEYS,
    effective_environment_identity,
    environment_digest,
)
from infrastructure.core.pipeline.execution_custody import execution_guard_result
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.fingerprints import paths_digest, source_fingerprint
from infrastructure.core.pipeline.incremental import (
    CACHE_SCHEMA_VERSION,
    IncrementalConfig,
    compute_stage_input_hash,
    load_hash_manifest,
    _hash_paths,
)
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.pipeline.types import PipelineConfig, StageContract


@pytest.fixture
def isolated_inventory_repository(tmp_path: Path) -> None:
    """Keep synthetic output independent of the caller's packaging ignores."""
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True, capture_output=True)


@contextmanager
def _environment(values: dict[str, str]) -> Iterator[None]:
    previous = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _executor(
    tmp_path: Path,
    *,
    code: str | None = None,
    input_artifacts: tuple[str, ...] = (),
    output_artifacts: tuple[str, ...] = ("projects/{project}/output/value.txt",),
) -> PipelineExecutor:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    if code is None:
        code = (
            "import os\nfrom pathlib import Path\n"
            "Path('projects/demo/output/value.txt').write_text(os.environ['TEMPLATE_CACHE_SCIENTIFIC_VALUE'])\n"
        )
    (scripts / "child.py").write_text(code, encoding="utf-8")
    (project / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {
                "stages": [
                    {
                        "name": "Child",
                        "key": "child",
                        "script": "scripts/child.py",
                        "contract": {
                            "input_artifacts": list(input_artifacts),
                            "output_artifacts": list(output_artifacts),
                        },
                    }
                ],
                "telemetry": {"enabled": False},
            }
        ),
        encoding="utf-8",
    )
    return PipelineExecutor(
        PipelineConfig("demo", tmp_path, clean=False, run_timeout_seconds=90, incremental=IncrementalConfig(True))
    )


def test_environment_digest_omits_only_exact_owned_control_names(tmp_path: Path) -> None:
    base = {"AUTHOR_NAME": "First author", "EXAMPLE_SECRET": "private fixture value"}
    expected = environment_digest(base, project_dir=tmp_path)
    assert len(expected) == 64
    assert "private fixture value" not in expected
    controls = {key: "transient" for key in VOLATILE_CONTROL_KEYS}
    controls[_env_var(_lock_key(tmp_path))] = "1"
    assert environment_digest({**base, **controls}, project_dir=tmp_path) == expected
    assert environment_digest(dict(reversed(list(base.items()))), project_dir=tmp_path) == expected
    for key in ("PIPELINE_RUN_ID_SCIENTIFIC", "TEMPLATE_BOUNDED_RUN_IDS_DATA", "TEMPLATE_PROJECT_LOCK_unrelated"):
        assert environment_digest({**base, key: "scientific value"}, project_dir=tmp_path) != expected
    assert environment_digest({**base, "EXAMPLE_SECRET": "changed fixture value"}, project_dir=tmp_path) != expected


def test_exact_project_lock_marker_does_not_invalidate_resolved_environment(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    before = effective_environment_identity(tmp_path, project)
    with project_output_lock(project, timeout=2):
        assert effective_environment_identity(tmp_path, project) == before
    assert effective_environment_identity(tmp_path, project) == before


@pytest.mark.parametrize("name", ["AUTHOR_NAME", "DOI", "TEMPLATE_CACHE_SCIENTIFIC_VALUE"])
def test_effective_environment_is_part_of_input_hash(tmp_path: Path, name: str) -> None:
    project = tmp_path / "project"
    project.mkdir()
    kwargs = dict(
        repo_root=tmp_path,
        project_dir=project,
        stage_name="Analysis",
        contract=StageContract(),
        upstream_output_hashes={},
    )
    with _environment({name: "first"}):
        first = compute_stage_input_hash(**kwargs)
    with _environment({name: "second"}):
        second = compute_stage_input_hash(**kwargs)
    assert first != second


@pytest.mark.timeout(90)
def test_real_cache_reexecutes_when_effective_environment_changes(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    with _environment({"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "first"}):
        first = executor.execute_pipeline()
        assert executor.run_result(first).complete
        assert executor.execution_plan is not None
        source = executor.execution_plan.source_identity
        original_digest = executor.execution_plan.digest
        reused = executor.execute_pipeline()
        assert reused[0].outcome is not None and reused[0].outcome.status == StageStatus.CACHED
    with _environment({"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "second"}):
        second = executor.execute_pipeline()
        assert executor.run_result(second).complete
        assert second[0].outcome is not None and second[0].outcome.status == StageStatus.SUCCEEDED
        assert executor.execution_plan is not None
        assert executor.execution_plan.source_identity == source
        assert executor.execution_plan.digest != original_digest
    assert (executor.config.project_dir / "output" / "value.txt").read_text() == "second"


def test_frozen_plan_refuses_environment_change_before_child_launch(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    with _environment({"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "first"}):
        assert executor.preview_stage_names() == ("Child",)
    with _environment({"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "second"}):
        results = executor.execute_pipeline()
        assert executor.run_result(results).exit_code == 75
        assert "environment changed" in results[0].error_message
    assert not (executor.config.project_dir / "output" / "value.txt").exists()


@pytest.mark.skipif(os.name != "posix", reason="real signal delivery uses POSIX SIGUSR1")
def test_environment_changed_during_real_child_blocks_success(tmp_path: Path) -> None:
    code = (
        "import os, signal\nfrom pathlib import Path\n"
        "os.kill(int(os.environ['TEMPLATE_CACHE_TEST_PARENT_PID']), signal.SIGUSR1)\n"
        "Path('projects/demo/output/value.txt').write_text('child completed')\n"
    )
    executor = _executor(tmp_path, code=code)
    previous_handler = signal.getsignal(signal.SIGUSR1)

    def change_environment(_signum: int, _frame: object) -> None:
        os.environ["TEMPLATE_CACHE_SCIENTIFIC_VALUE"] = "second"

    signal.signal(signal.SIGUSR1, change_environment)
    try:
        with _environment(
            {"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "first", "TEMPLATE_CACHE_TEST_PARENT_PID": str(os.getpid())}
        ):
            results = executor.execute_pipeline()
            assert executor.run_result(results).exit_code == 75
            assert "environment changed during execution" in results[0].error_message
            assert results[0].outcome is not None and results[0].outcome.child_exit_code == 0
            assert not executor.checkpoint_manager.checkpoint_exists()
    finally:
        signal.signal(signal.SIGUSR1, previous_handler)


def test_completion_guard_rechecks_effective_environment_and_deadline(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    with _environment({"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "first"}):
        executor.preview_stage_names()
        plan = executor.execution_plan
    assert plan is not None
    with _environment({"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "second"}):
        blocked = execution_guard_result(
            config=executor.config, plan=plan, deadline=time.monotonic() + 10, completion=True
        )
        assert blocked is not None and blocked.exit_code == 75
        assert "before completion validation" in blocked.error_message
    with _environment({"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "first"}):
        expired = execution_guard_result(
            config=executor.config, plan=plan, deadline=time.monotonic() - 1, completion=True
        )
        assert expired is not None and expired.exit_code == 124


@pytest.mark.parametrize("frozen", [False, True])
@pytest.mark.timeout(90)
def test_complete_resume_cannot_reuse_another_environment(tmp_path: Path, frozen: bool) -> None:
    executor = _executor(tmp_path)
    with _environment({"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "first"}):
        assert executor.run_result(executor.execute_pipeline()).complete
        if frozen:
            executor.preview_stage_names()
    checkpoint = executor.checkpoint_manager.checkpoint_file
    previous = checkpoint.read_bytes()
    executor.config.resume = True
    with _environment({"TEMPLATE_CACHE_SCIENTIFIC_VALUE": "second"}):
        results = executor.execute_pipeline()
        assert executor.run_result(results).exit_code == 75
    assert checkpoint.read_bytes() == previous
    assert (executor.config.project_dir / "output" / "value.txt").read_text() == "first"


@pytest.mark.parametrize("relative", ["logs/observations.csv", "diagnostics.json", "observations.log"])
@pytest.mark.usefixtures("isolated_inventory_repository")
def test_nested_scientific_runtime_names_affect_directory_identities(tmp_path: Path, relative: str) -> None:
    data = tmp_path / "output" / "data"
    artifact = data / relative
    artifact.parent.mkdir(parents=True)
    artifact.write_text("first", encoding="utf-8")
    input_before = paths_digest((data,))
    output_before = paths_digest((data,), stable_output=True)
    artifact.write_text("changed", encoding="utf-8")
    assert paths_digest((data,)) != input_before
    assert paths_digest((data,), stable_output=True) != output_before
    inventory = collect_stable_output_inventory(tmp_path / "output")
    assert artifact.absolute() in inventory.files


@pytest.mark.usefixtures("isolated_inventory_repository")
def test_runtime_exclusions_follow_actual_output_locations(tmp_path: Path) -> None:
    output = tmp_path / "output"
    data = output / "data"
    data.mkdir(parents=True)
    (output / "pdf").mkdir()
    (data / "value.txt").write_text("stable")
    before = paths_digest((output,), stable_output=True)
    data_before = paths_digest((data,), stable_output=True)
    for relative in (
        "logs/pipeline.log",
        ".pipeline/cache.json",
        "hitl/waiting.json",
        "reports/snapshots/stage.json",
        "reports/diagnostics.json",
        "reports/pipeline_report.json",
        "pdf/render.log",
        "data/.private/token.txt",
    ):
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("runtime")
    assert paths_digest((output,), stable_output=True) == before
    (output / "pdf" / "render.log").write_text("changed renderer intermediate")
    assert paths_digest((output,), stable_output=True) == before
    assert paths_digest((data,), stable_output=True) == data_before
    inventory = collect_stable_output_inventory(output)
    assert inventory.files == ((data / "value.txt").absolute(),)


@pytest.mark.usefixtures("isolated_inventory_repository")
def test_fulltext_inventory_exception_is_bound_without_private_fulltext(tmp_path: Path) -> None:
    fulltext = tmp_path / "output" / "fulltext"
    fulltext.mkdir(parents=True)
    private = fulltext / "acquired.txt"
    private.write_text("private acquired content")
    empty = paths_digest((tmp_path / "output",), stable_output=True)
    private.write_text("changed private content")
    assert paths_digest((tmp_path / "output",), stable_output=True) == empty
    receipt = fulltext / "fulltext_inventory.json"
    receipt.write_text('{"count": 1}')
    before = paths_digest((tmp_path / "output",), stable_output=True)
    receipt.write_text('{"count": 2}')
    assert paths_digest((tmp_path / "output",), stable_output=True) != before
    assert collect_stable_output_inventory(tmp_path / "output").files == (receipt.absolute(),)


def test_source_nested_output_runtime_name_is_consumed(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "src" / "output" / "logs" / "model.py"
    source.parent.mkdir(parents=True)
    source.write_text("first")
    before = source_fingerprint(tmp_path, project)
    source.write_text("changed")
    assert source_fingerprint(tmp_path, project) != before


def test_authored_input_named_output_does_not_inherit_control_filtering(tmp_path: Path) -> None:
    selected_output = tmp_path / "projects" / "demo" / "output"
    authored = tmp_path / "projects" / "other" / "data" / "output"
    artifact = authored / "logs" / "observations.csv"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("first")
    input_before = _hash_paths((authored,), output_roots=(selected_output,))
    raw_before = paths_digest((authored,))
    artifact.write_text("changed")
    assert _hash_paths((authored,), output_roots=(selected_output,)) != input_before
    assert paths_digest((authored,)) != raw_before


def test_only_the_explicit_project_output_root_has_runtime_controls(tmp_path: Path) -> None:
    output = tmp_path / "projects" / "demo" / "output"
    artifact = output / "logs" / "pipeline.log"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("first")
    bound = _hash_paths((output,), output_roots=(output,))
    artifact.write_text("changed")
    assert _hash_paths((output,), output_roots=(output,)) == bound
    assert paths_digest((output,), control_output=True) == paths_digest((output,), stable_output=True)


@pytest.mark.timeout(90)
def test_real_cache_consumes_nested_scientific_input_directory(tmp_path: Path) -> None:
    code = (
        "from pathlib import Path\n"
        "root=Path('projects/demo/output')\n"
        "source=root/'data/logs/observations.csv'\n"
        "(root/'value.txt').write_text(source.read_text())\n"
    )
    executor = _executor(tmp_path, code=code, input_artifacts=("projects/{project}/output/data/",))
    source = executor.config.project_dir / "output" / "data" / "logs" / "observations.csv"
    source.parent.mkdir(parents=True)
    source.write_text("first")
    assert executor.run_result(executor.execute_pipeline()).complete
    reused = executor.execute_pipeline()
    assert reused[0].outcome is not None and reused[0].outcome.status == StageStatus.CACHED
    source.write_text("second")
    changed = executor.execute_pipeline()
    assert executor.run_result(changed).complete
    assert changed[0].outcome is not None and changed[0].outcome.status == StageStatus.SUCCEEDED
    assert (executor.config.project_dir / "output" / "value.txt").read_text() == "second"


@pytest.mark.parametrize("version", [1, 2, True, 3.0])
def test_older_or_malformed_cache_schema_is_an_explicit_miss(tmp_path: Path, version: object) -> None:
    manifest = tmp_path / ".pipeline" / "incremental.json"
    manifest.parent.mkdir()
    manifest.write_text(
        json.dumps({"version": version, "stages": {"child": {"input_hash": "a" * 64, "output_hash": "b" * 64}}})
    )
    assert CACHE_SCHEMA_VERSION == 3
    assert load_hash_manifest(tmp_path).get("child") is None

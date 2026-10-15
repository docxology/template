"""Actual external executables cannot launder unchanged-path cache evidence."""

from __future__ import annotations
import errno
import os
import sys
from pathlib import Path
import pytest
import yaml
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.fingerprints import tool_identities, tool_reuse_refusal
from infrastructure.core.pipeline.fingerprints import source_fingerprint
from infrastructure.core.pipeline.incremental import IncrementalConfig
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.pipeline.types import PipelineConfig

pytestmark = pytest.mark.timeout(300)


def _tool(path: Path, code: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'#!/bin/sh\nprintf "actual-tool-{code}\\n"\nexit {code}\n')
    path.chmod(0o700)


def _executor(root: Path, variable: str) -> PipelineExecutor:
    project = root / "projects/demo"
    project.mkdir(parents=True)
    scripts = root / "scripts"
    scripts.mkdir()
    command = f"[os.environ[{variable!r}]]"
    (scripts / "child.py").write_text(
        "import os, subprocess\nfrom pathlib import Path\n"
        f"result=subprocess.run({command},capture_output=True,text=True,timeout=3)\n"
        "output=Path('projects/demo/output/value.txt');output.parent.mkdir(parents=True,exist_ok=True)\n"
        "output.write_text(result.stdout+result.stderr)\nraise SystemExit(result.returncode)\n"
    )
    (project / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {
                "telemetry": {"enabled": False},
                "stages": [
                    {
                        "name": "Actual external tool",
                        "key": "tool",
                        "script": "scripts/child.py",
                        "contract": {"output_artifacts": ["output/value.txt"]},
                    }
                ],
            }
        )
    )
    return PipelineExecutor(
        PipelineConfig("demo", root, clean=False, run_timeout_seconds=90, incremental=IncrementalConfig(True))
    )


@pytest.mark.parametrize("variable", ["FORMAL_JAVA_BIN", "PANDOC_PATH", "LATEX_COMPILER"])
def test_changed_override_bytes_reexecute_actual_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    selected = tmp_path / "external/selected"
    _tool(selected)
    monkeypatch.setenv(variable, str(selected))
    executor = _executor(tmp_path / "repo", variable)
    assert tool_reuse_refusal(executor.config.repo_root, executor.config.project_dir) is None, (
        "Nominate actual JAVA_HOME on macOS for cache-positive acceptance"
    )
    assert executor.run_result(executor.execute_pipeline()).complete
    executor = PipelineExecutor(executor.config)
    repeat = executor.execute_pipeline()
    assert repeat[0].outcome is not None and repeat[0].outcome.status is StageStatus.CACHED
    _tool(selected, 7)
    executor = PipelineExecutor(executor.config)
    changed = executor.execute_pipeline()
    assert executor.run_result(changed).exit_code == 1
    assert changed[0].outcome is not None and changed[0].outcome.child_exit_code == 7
    assert (executor.config.project_dir / "output/value.txt").read_text() == "actual-tool-7\n"


def test_changed_override_bytes_refuse_resume_and_preserve_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = tmp_path / "external/selected"
    _tool(selected)
    monkeypatch.setenv("FORMAL_JAVA_BIN", str(selected))
    executor = _executor(tmp_path / "repo", "FORMAL_JAVA_BIN")
    assert executor.run_result(executor.execute_pipeline()).complete
    checkpoint = executor.checkpoint_manager.checkpoint_file
    before = checkpoint.read_bytes()
    _tool(selected, 7)
    executor.config.resume = True
    executor = PipelineExecutor(executor.config)
    refused = executor.execute_pipeline()
    assert executor.run_result(refused).exit_code == 75
    assert refused[0].outcome is not None and refused[0].outcome.child_exit_code is None
    assert checkpoint.read_bytes() == before
    assert (executor.config.project_dir / "output/value.txt").read_text() == "actual-tool-0\n"


def test_unresolved_launcher_never_runs_during_fingerprinting_or_grants_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bin_dir = tmp_path / "bin"
    launcher = bin_dir / "elan"
    _tool(launcher)
    marker = tmp_path / "unexpected-fingerprint-launch"
    launcher.write_text(f"#!/bin/sh\ntouch {marker}\nexit 0\n")
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / "unknown-home"))
    monkeypatch.delenv("ELAN_TOOLCHAIN", raising=False)
    selected = tmp_path / "external/selected"
    _tool(selected)
    monkeypatch.setenv("PANDOC_PATH", str(selected))
    executor = _executor(tmp_path / "repo", "PANDOC_PATH")
    assert tool_reuse_refusal(executor.config.repo_root, executor.config.project_dir) is not None
    assert executor.run_result(executor.execute_pipeline()).complete
    second = executor.execute_pipeline()
    assert (
        executor.run_result(second).complete
        and second[0].outcome is not None
        and second[0].outcome.status is StageStatus.SUCCEEDED
    )
    checkpoint = executor.checkpoint_manager.checkpoint_file
    before = checkpoint.read_bytes()
    executor.config.resume = True
    assert executor.run_result(executor.execute_pipeline()).exit_code == 75
    assert checkpoint.read_bytes() == before and not marker.exists()


def test_nonregular_and_over_budget_selected_tool_refuse_before_read(tmp_path: Path) -> None:
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    fifo.chmod(0o700)
    with pytest.raises(ValueError, match="regular"):
        tool_identities(environment={**os.environ, "FORMAL_JAVA_BIN": str(fifo)})
    large = tmp_path / "large"
    large.touch()
    large.chmod(0o700)
    with large.open("r+b") as handle:
        handle.truncate(512 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="read budget"):
        tool_identities(environment={**os.environ, "PANDOC_PATH": str(large)})


def test_exact_declared_lean_and_lake_backend_bytes_bind_without_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bin_dir = tmp_path / "bin"
    launcher = bin_dir / "elan"
    _tool(launcher)
    marker = tmp_path / "unexpected-launch"
    launcher.write_text(f"#!/bin/sh\ntouch {marker}\nexit 0\n")
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])
    home = tmp_path / "elan-home"
    monkeypatch.setenv("ELAN_HOME", str(home))
    project = tmp_path / "repo/projects/demo"
    (project / "lean").mkdir(parents=True)
    (project / "lean/lean-toolchain").write_text("leanprover/lean4:v4.35.0\n")
    backend = home / "toolchains/leanprover--lean4---v4.35.0/bin"
    _tool(backend / "lean")
    _tool(backend / "lake")
    for name in ("lean", "lake"):
        before = source_fingerprint(tmp_path / "repo", project)
        _tool(backend / name, 7)
        assert source_fingerprint(tmp_path / "repo", project) != before
    assert not marker.exists()


def test_missing_elan_home_keeps_declared_backend_unavailable(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _tool(bin_dir / "elan")
    project = tmp_path / "project"
    (project / "lean").mkdir(parents=True)
    (project / "lean/lean-toolchain").write_text("leanprover/lean4:v4.35.0\n")
    environment = {**os.environ, "PATH": str(bin_dir), "ELAN_HOME": str(tmp_path / "cold-home")}
    environment.pop("ELAN_TOOLCHAIN", None)
    rows = tool_identities(project_dir=project, environment=environment)
    assert rows["elan_settings"] == "unavailable"
    assert [value for key, value in rows.items() if key.startswith("elan_backend_")] == [
        "unavailable",
        "unavailable",
    ]
    assert rows["unresolved_backends"] == []


def test_settings_symlink_is_not_misclassified_as_missing_home(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _tool(bin_dir / "elan")
    home = tmp_path / "home"
    home.mkdir()
    settings = tmp_path / "settings.toml"
    settings.write_text('default_toolchain="stable"\n')
    (home / "settings.toml").symlink_to(settings)
    with pytest.raises(OSError) as refused:
        tool_identities(environment={**os.environ, "PATH": str(bin_dir), "ELAN_HOME": str(home)})
    assert refused.value.errno == errno.ELOOP


def test_explicit_system_java_override_requires_actual_runtime_identity() -> None:
    environment = {**os.environ, "FORMAL_JAVA_BIN": "/usr/bin/java"}
    runtime = environment.pop("JAVA_HOME", None)
    if sys.platform == "darwin":
        assert runtime and Path(runtime).is_absolute(), "Nominate actual JAVA_HOME for this macOS control"
        environment["PATH"] = str(Path(runtime) / "bin") + os.pathsep + environment["PATH"]
    rows = tool_identities(environment=environment)
    if sys.platform == "darwin":
        assert "formal_java.launcher" in rows["unresolved_backends"]
        assert "java.launcher" not in rows["unresolved_backends"]
    else:
        assert "formal_java.launcher" not in rows["unresolved_backends"]

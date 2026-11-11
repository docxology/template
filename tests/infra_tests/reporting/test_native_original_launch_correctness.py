"""Actual selected interpreters, genuine Source loader launches and environment DATA."""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

import packaging
import pytest

from infrastructure.core._bounded_kill import _RUN_IDS_ENV
from infrastructure.core.pipeline.stages import PIPELINE_STAGE_TIMEOUT_SECONDS, _stage_launch_deadline
from infrastructure.core.secrets import strip_secret_env
from infrastructure.project.public_acceptance_evidence import bootstrap_command
from infrastructure.reporting.native_environment_custody import capture_native_environment, validate_native_environment
from infrastructure.reporting.native_format_acceptance_contracts import native_environment
from infrastructure.reporting.native_original_supervisor import _worker_environment
from infrastructure.reporting.native_pdf_citation_runtime import NATIVE_OBSERVATION_CEILING_SECONDS, budget
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project.test_public_reference import (
    _clone_complete_reference,
    complete_reference as complete_reference,
)


@pytest.fixture(scope="module")
def cold_python(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Real fresh venv; reuse existing dependencies read-only, without acquisition.

    This proves interpreter selection, not complete Root installation. The exact
    existing dependency site is explicit; no SDK distribution/custody is invented.
    """
    root = tmp_path_factory.mktemp("native-selected-runtime")
    environment = root / "cold"
    result = subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(environment)],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    interpreter = environment / "bin/python"
    site = subprocess.run(
        [str(interpreter), "-I", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert site.returncode == 0, site.stderr
    # The optional prepared-runtime adapter imports packaging even for deps[].
    (Path(site.stdout.strip()) / "owned-readonly-dependencies.pth").write_text(
        str(Path(packaging.__file__).resolve(strict=True).parents[1]) + "\n"
    )
    return interpreter


def _root_probe(tmp_path: Path, interpreter: Path, environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    root = tmp_path / "mirror"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname="owned-runtime-input"\nversion="0.0.0"\ndependencies=[]\n')
    (root / "probe.py").write_text(
        "import sys\nfrom pathlib import Path\n"
        "from infrastructure.core.runtime.prepared_runtime import check_prepared_root_runtime,PreparedRuntimeUnavailable\n"
        "try: check_prepared_root_runtime(Path.cwd())\n"
        "except PreparedRuntimeUnavailable as error:\n"
        " print(type(error).__name__+': '+str(error));raise SystemExit(75)\n"
        "print(str(Path(sys.prefix).absolute()))\n"
    )
    assert not (root / ".venv").exists()
    return subprocess.run(
        bootstrap_command(interpreter, root, "probe"),
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("ambient", ["absent", "wrong"])
def test_actual_cold_selected_root_runtime_overrides_missing_or_wrong_ambient_nomination(
    tmp_path: Path, cold_python: Path, monkeypatch: pytest.MonkeyPatch, ambient: str
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    if ambient == "absent":
        monkeypatch.delenv("TEMPLATE_ROOT_PYTHON", raising=False)
    else:
        monkeypatch.setenv("TEMPLATE_ROOT_PYTHON", str(tmp_path / "wrong/bin/python"))
    env = native_environment(tmp_path, cold_python, tmp_path / "execution")
    assert env["TEMPLATE_ROOT_PYTHON"] == str(cold_python)
    result = _root_probe(tmp_path, cold_python, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == str(cold_python.parent.parent)


def test_missing_root_nomination_still_blocks_actual_prepared_runtime(
    tmp_path: Path, cold_python: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    env = native_environment(tmp_path, cold_python, tmp_path / "execution")
    del env["TEMPLATE_ROOT_PYTHON"]
    result = _root_probe(tmp_path, cold_python, env)
    assert result.returncode == 75
    assert (
        "PreparedRuntimeUnavailable" in result.stdout
        and "missing, broken, or not an absolute executable" in result.stdout
    )


@pytest.mark.parametrize("mutation", ["none", "missing", "wrong", "post-selection-edit"])
def test_actual_popen_environment_matches_held_source_commitment_and_refuses_changed_digest(
    tmp_path: Path, mutation: str
) -> None:
    # These are environment DATA predicates, not a fabricated Original/Source
    # capability. The real Python process observes the exact supplied Popen map.
    source = {"PATH": os.defpath, "LC_ALL": "C", "OWNED_INPUT": "selected-before-launch"}
    selected, digest = _worker_environment(source)
    source["OWNED_INPUT"] = "caller-changed-after-selection"
    token = secrets.token_hex(16)
    bounded = {**strip_secret_env(selected), _RUN_IDS_ENV: token}
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import os,json,sys;print(json.dumps({key:os.environ[key] for key in json.loads(sys.argv[1])}))",
            json.dumps(sorted(bounded)),
        ],
        cwd=tmp_path,
        env=bounded,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    assert actual == bounded and selected["OWNED_INPUT"] == "selected-before-launch"
    custody = capture_native_environment(selected, strip_secret_env(selected), bounded, actual, token, None)
    raw = {"environment_custody": custody, "loader_lifecycle": None}
    tool = {"environment_digest": digest}
    if mutation == "missing":
        tool.clear()
    elif mutation == "wrong":
        tool["environment_digest"] = "0" * 64
    elif mutation == "post-selection-edit":
        tool["environment_digest"] = _worker_environment(source)[1]
    if mutation == "none":
        validate_native_environment(raw, tool, SnapshotReader(tmp_path))
    else:
        with pytest.raises(ValueError, match="Source-selected"):
            validate_native_environment(raw, tool, SnapshotReader(tmp_path))


@pytest.mark.parametrize("remaining", [900.0, 0.01, -1.0])
def test_stage_launch_retains_exact_nearer_or_expired_original_deadline(remaining: float) -> None:
    deadline = time.monotonic() + remaining
    assert _stage_launch_deadline(deadline) == deadline


def test_stage_launch_keeps_existing_phase_ceiling_with_a_later_original_deadline() -> None:
    before = time.monotonic()
    deadline = before + PIPELINE_STAGE_TIMEOUT_SECONDS + 1000
    selected = _stage_launch_deadline(deadline)
    after = time.monotonic()
    assert before + PIPELINE_STAGE_TIMEOUT_SECONDS <= selected <= after + PIPELINE_STAGE_TIMEOUT_SECONDS
    assert selected <= deadline


def test_native_observation_budget_has_one_finite_ceiling_and_refuses_expired_time() -> None:
    assert NATIVE_OBSERVATION_CEILING_SECONDS == 600.0
    assert budget(time.monotonic() + 1200) == 600.0
    with pytest.raises(TimeoutError, match="exhausted its original finite deadline"):
        budget(time.monotonic() - 1)


_GENUINE_PANDOC_INSTALLED_SDK_CHILD = r"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

from contextlib import contextmanager

import infrastructure
from infrastructure.core.implementation_custody import capture_implementation_custody
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_format_acceptance_checks import NativeToolUnavailable
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_loader_observation import NativeLoaderObservation
from infrastructure.reporting.native_loader_qualification import qualify_native_loader_tool
from infrastructure.reporting.native_loader_replay import validate_native_loader_data
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, NATIVE_OBSERVATION_CEILING_SECONDS
from infrastructure.reporting.native_source_external_admission import NativeExternalSourceBindings, admit_external_native_source
from infrastructure.reporting.native_tool_producer import native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@contextmanager
def raises(exception_type, match):
    try:
        yield
    except exception_type as error:
        assert match in str(error), str(error)
    else:
        raise AssertionError(f"Expected {exception_type.__name__} containing {match!r}")


original = Path(sys.argv[1])
commit = sys.argv[2]
fingerprint = sys.argv[3]
mirror = Path(sys.argv[4])
tmp_path = Path(sys.argv[5])
deadline = float(sys.argv[6])
assert infrastructure.__file__ is not None
sdk_root = Path(infrastructure.__file__).resolve(strict=True).parent
assert sdk_root.is_relative_to(Path(sys.prefix).resolve(strict=True))
custody = capture_implementation_custody()
assert custody["binding_kind"] == "installed-distribution"
metadata = mirror.stat()
run_id = uuid4().hex
source = admit_external_native_source(
    NativeExternalSourceBindings(
        original,
        commit,
        fingerprint,
        mirror,
        (metadata.st_dev, metadata.st_ino),
        sdk_root,
        json.dumps(custody, sort_keys=True).encode(),
        run_id,
    ),
    deadline=deadline,
)
environment = {
    "PATH": os.environ.get("PATH", os.defpath),
    "LC_ALL": "C",
    "HOME": str(tmp_path),
}
with native_producer_operation(source, run_id=run_id, deadline=deadline):
    runtime = CitationRuntime(
        mirror,
        mirror / "output/readiness/native-loader-terminal-control",
        env=environment,
        deadline=deadline,
        run_id=run_id,
    )
    observed, qualification_binding, compiled = qualify_native_loader_tool(
        runtime,
        "pandoc",
        ["--version"],
        "pandoc-terminal-success",
    )
    reader = SnapshotReader(mirror)
    qualification = reader.read(qualification_binding["path"]).json_object()
    baseline = reader.read(qualification["baseline_tool"]["path"]).json_object()
    observed = reader.read(qualification["observed_tool"]["path"]).json_object()
    assert baseline["original_exit_code"] == observed["original_exit_code"] == 0
    baseline_stdout = reader.read(baseline["raw_stdout"]["path"]).content
    observed_stdout = reader.read(observed["raw_stdout"]["path"]).content
    assert baseline_stdout == observed_stdout
    assert baseline_stdout.startswith(b"pandoc ")
    native = reader.read(observed["native_process_artifact"]["path"]).json_object()
    lifecycle = reader.read(native["loader_lifecycle"]["path"]).json_object()
    assert native["accepted"] is True and native["diagnostics"] == []
    assert native["cleanup"]["guardian_finished"] is True
    assert native["cleanup"]["root_reaped"] is True
    assert lifecycle["complete_callbacks"] is True and lifecycle["channel_eof"] is True
    assert lifecycle["events"][-1]["kind"] == "done"
    assert len(lifecycle["opened"]) == len(lifecycle["closed"])
    assert set(lifecycle["opened"]) == set(lifecycle["closed"])
    assert lifecycle["resident_terminal"]["original_exit_code"] == 0
    assert (
        validate_native_loader_data(
            native,
            reader,
            original_deadline=deadline,
            original_completion=native["operation_end"]["monotonic"],
        )
        == lifecycle
    )
    for mutation in ("missing-done", "post-done-frame"):
        changed = deepcopy(lifecycle)
        if mutation == "missing-done":
            changed["events"].pop()
        else:
            post_done = deepcopy(changed["events"][-1])
            post_done["sequence"] = len(changed["events"]) + 1
            changed["events"].append(post_done)
        binding = write_json(mirror, runtime.directory / (mutation + ".lifecycle.json"), changed)
        with raises(ValueError, match="validated terminal callback"):
            validate_native_loader_data(
                {**native, "loader_lifecycle": binding},
                reader,
                original_deadline=deadline,
                original_completion=native["operation_end"]["monotonic"],
            )

    purpose = "pandoc-terminal-nonzero"
    leaf = compiled.directory / ("callbacks-" + purpose)
    create_private_native_directory(mirror, leaf)
    observer = NativeLoaderObservation(
        compiled,
        leaf,
        purpose=purpose,
        deadline=min(runtime.deadline, time.monotonic() + NATIVE_OBSERVATION_CEILING_SECONDS),
    )
    with raises(NativeToolUnavailable, match="signed normal consuming-process OS termination"):
        runtime.tool(
            "pandoc",
            ["--definitely-not-a-pandoc-option"],
            purpose,
            loader=observer,
        )
    failed = reader.read(runtime.tools[-1]["path"]).json_object()
    native = reader.read(failed["native_process_artifact"]["path"]).json_object()
    assert failed["original_exit_code"] != 0
    assert observer.done is True and observer.eof is True
    assert native["accepted"] is False and native["cleanup"]["guardian_finished"] is True

    purpose = "python-terminal-premature-eof"
    leaf = compiled.directory / ("callbacks-" + purpose)
    create_private_native_directory(mirror, leaf)
    observer = NativeLoaderObservation(
        compiled,
        leaf,
        purpose=purpose,
        deadline=min(runtime.deadline, time.monotonic() + NATIVE_OBSERVATION_CEILING_SECONDS),
    )
    with raises(NativeToolUnavailable, match="EOF preceded its validated terminal callback"):
        runtime.tool(
            sys.executable,
            ["-I", "-c", "import os; os._exit(0)"],
            purpose,
            loader=observer,
        )
    failed = reader.read(runtime.tools[-1]["path"]).json_object()
    native = reader.read(failed["native_process_artifact"]["path"]).json_object()
    assert failed["original_exit_code"] == 0
    assert observer.done is False
    assert native["accepted"] is False and native["cleanup"]["guardian_finished"] is True

    retained = len(runtime.tools)
    with raises(TimeoutError, match="exhausted its original finite deadline"):
        runtime.tool(
            "pandoc",
            ["--version"],
            "pandoc-terminal-expired",
            phase_deadline=time.monotonic() - 1,
        )
    assert len(runtime.tools) == retained
    assert not (runtime.directory / "pandoc-terminal-expired.native-process.json").exists()
"""


@pytest.mark.timeout(1800)
@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="genuine glibc audit callbacks require Linux")
def test_genuine_pandoc_terminal_success_and_fail_closed_controls(
    complete_reference: tuple[Path, str, str], tmp_path: Path
) -> None:
    """Exercise genuine native controls with installed-wheel SDK custody."""
    if shutil.which("pandoc") is None or shutil.which("cc") is None:
        pytest.skip("genuine Pandoc and the Source-selected C compiler are required")
    original, commit, fingerprint = complete_reference
    deadline = time.monotonic() + 1200
    mirror = _clone_complete_reference(complete_reference, tmp_path / "mirror", deadline=deadline)
    environment = dict(os.environ, UV_OFFLINE="1", UV_PYTHON_DOWNLOADS="never")
    build_environment = dict(environment)
    build_environment.pop("UV_OFFLINE")
    artifacts = tmp_path / "artifacts"
    built = subprocess.run(
        [
            "uv",
            "build",
            "--wheel",
            "--no-create-gitignore",
            "--out-dir",
            str(artifacts),
        ],
        cwd=original,
        env=build_environment,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    wheels = list(artifacts.glob("*.whl"))
    assert len(wheels) == 1
    installed = tmp_path / "installed-sdk"
    created = subprocess.run(
        [
            "uv",
            "venv",
            "--no-project",
            "--no-python-downloads",
            "--python",
            sys.executable,
            str(installed),
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert created.returncode == 0, created.stdout + created.stderr
    selected_python = installed / "bin/python"
    installed_result = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--no-build",
            "--force-reinstall",
            "--python",
            str(selected_python),
            str(wheels[0]),
        ],
        cwd=tmp_path,
        env=build_environment,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert installed_result.returncode == 0, installed_result.stdout + installed_result.stderr
    child = tmp_path / "genuine-pandoc-installed-sdk.py"
    child.write_text(_GENUINE_PANDOC_INSTALLED_SDK_CHILD, encoding="utf-8")
    child_environment = {
        "PATH": os.environ.get("PATH", os.defpath),
        "LC_ALL": "C",
        "HOME": str(tmp_path),
    }
    result = subprocess.run(
        [
            str(selected_python),
            "-I",
            str(child),
            str(original),
            commit,
            fingerprint,
            str(mirror),
            str(tmp_path),
            str(deadline),
        ],
        cwd=tmp_path,
        env=child_environment,
        text=True,
        capture_output=True,
        timeout=max(1.0, deadline - time.monotonic()),
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

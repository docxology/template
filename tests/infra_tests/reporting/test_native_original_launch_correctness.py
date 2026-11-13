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
from infrastructure.project.locked_dependency_export import normalize_locked_dependency_export
from infrastructure.reporting.native_environment_custody import capture_native_environment, validate_native_environment
from infrastructure.reporting.native_format_acceptance_contracts import native_environment
from infrastructure.reporting.native_loader_maps import terminal_kernel_residents
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


@pytest.mark.parametrize(
    "refusal", ["unclosed-file", "missing-close", "duplicate-close", "non-kernel", "aliased-kernel"]
)
def test_terminal_roster_refuses_unclosed_or_aliased_images(refusal: str) -> None:
    opened = {
        1: {"body": {"sha256": "a" * 64}, "path_label": "/proc/self/exe"},
        2: {"body": None, "path_label": "linux-vdso.so.1"},
    }
    active, closed = {2: opened[2]}, [1]
    if refusal == "unclosed-file":
        active[1] = opened[1]
        closed.clear()
    elif refusal == "missing-close":
        closed.clear()
    elif refusal == "duplicate-close":
        closed.append(1)
    elif refusal == "non-kernel":
        opened[2]["path_label"] = "unbacked-consumer.so"
    else:
        opened[3] = {"body": None, "path_label": "linux-vdso.so.2"}
        active[3] = opened[3]
    with pytest.raises(ValueError):
        terminal_kernel_residents(opened, active, closed)


_GENUINE_PANDOC_INSTALLED_SDK_CHILD = r"""
from copy import deepcopy
import json
import hashlib
import os
import socket
from pathlib import Path
import sys
import subprocess
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
from infrastructure.reporting.native_crossref_pair import pair_launcher
from infrastructure.reporting.native_source_provider_bootstrap import (
    CROSSREF_FILTER_WORKER_MODULE,
    format_selected_sdk_native_bootstrap,
    format_selected_sdk_native_script,
)
from infrastructure.reporting.native_tool_producer import native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@contextmanager
def raises(exception_type):
    try:
        yield
    except exception_type:
        pass
    else:
        raise AssertionError(f"Expected {exception_type.__name__}")


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
runtime = custody["runtime_environment"]
assert runtime["python_launcher"] == str(Path(sys.executable).absolute())
assert runtime["python_executable"] == str(Path(sys.executable).resolve(strict=True))
assert runtime["python_launcher"] != runtime["python_executable"]

# These genuine installed-SDK --help executions prove launcher/import/Code
# closure only. Their pair declarations are DATA, not native Source authority.
# No VIRTUAL_ENV or checkout import root is supplied to either entry point.
entry_directory = tmp_path / "cold-crossref-launcher-controls"
entry_directory.mkdir()
implementation_path = entry_directory / "implementation.json"
implementation_bytes = json.dumps(custody, sort_keys=True).encode()
implementation_path.write_bytes(implementation_bytes)
entry_scripts = []
entry_closures = []
for ordinal in range(3):
    leaf = entry_directory / ("slot-" + str(ordinal))
    leaf.mkdir()
    closure = leaf / "closure"
    closure.mkdir()
    held = closure.stat()
    bootstrap = format_selected_sdk_native_bootstrap(
        (sdk_root / "core/bytecode_audit.py").read_bytes(),
        sdk_root,
        (),
        implementation_path,
        hashlib.sha256(implementation_bytes).hexdigest(),
        closure,
        (held.st_dev, held.st_ino),
        deadline,
        required_worker_module=CROSSREF_FILTER_WORKER_MODULE,
    )
    entry = leaf / "source-crossref-filter"
    entry.write_bytes(
        format_selected_sdk_native_script(
            runtime["python_launcher"],
            "import sys\nsys.argv=['native-crossref-worker','--help']\n" + bootstrap,
        )
    )
    entry.chmod(0o700)
    entry_scripts.append(entry)
    entry_closures.append(closure)

pair_directory = entry_directory / "pair"
pair_directory.mkdir()
declaration = {
    "directory": pair_directory.relative_to(tmp_path).as_posix(),
    "deadline_monotonic": deadline,
    "parent_loader": {"environment_injections": {}},
    "slots": [
        {
            "launcher": {
                "path": entry.relative_to(tmp_path).as_posix(),
                "sha256": hashlib.sha256(entry.read_bytes()).hexdigest(),
            }
        }
        for entry in entry_scripts[1:]
    ],
}
pair_entry = pair_directory / "source-crossref-pair"
pair_entry.write_bytes(pair_launcher(tmp_path, declaration, runtime["python_launcher"], "latex"))
pair_entry.chmod(0o700)
entry_environment = {
    "PATH": os.defpath,
    "LC_ALL": "C",
    "HOME": str(tmp_path),
}
for entry in (entry_scripts[0], pair_entry, pair_entry):
    completed = subprocess.run(
        [str(entry), "latex"],
        cwd=tmp_path,
        env=entry_environment,
        capture_output=True,
        text=True,
        timeout=min(NATIVE_OBSERVATION_CEILING_SECONDS, deadline - time.monotonic()),
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
for closure in entry_closures:
    retained = json.loads((closure / "receipt.json").read_text())
    assert retained["status"] == "pass", retained
    assert retained["selected_sdk_package_root"] == str(sdk_root)
    assert retained["worker_outcome"] == {
        "kind": "raised", "class": "SystemExit", "module": "builtins", "system_exit_code": 0,
    }
    assert any(
        row["source_path"] == str(sdk_root / "_version.py") and row["runs"]
        for row in retained["executions"]
    )
assert [json.loads((pair_directory / ("invocation-" + str(slot) + ".json")).read_text())["slot"]
        for slot in range(2)] == [0, 1]
refused = subprocess.run(
    [str(pair_entry), "latex"],
    cwd=tmp_path,
    env=entry_environment,
    capture_output=True,
    text=True,
    timeout=min(NATIVE_OBSERVATION_CEILING_SECONDS, deadline - time.monotonic()),
    check=False,
)
assert refused.returncode != 0
assert "Source paired filter permits exactly two invocations" in refused.stderr

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
    reader = SnapshotReader(mirror)
    try:
        observed, qualification_binding, compiled = qualify_native_loader_tool(
            runtime,
            "pandoc",
            ["--version"],
            "pandoc-terminal-success",
        )
        assert len(os.fsencode(compiled.library)) >= 255
    except BaseException:
        failure_path = runtime.directory / "pandoc-terminal-success.native-process.json"
        if failure_path.exists():
            failure = reader.read(failure_path.relative_to(mirror).as_posix()).json_object()
            print(
                json.dumps(
                    {
                        key: failure[key]
                        for key in (
                            "pid", "original_exit_code", "timed_out", "diagnostics",
                            "operation_begin", "operation_end", "launch_begin",
                            "launch_returned", "cleanup",
                        )
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            print(
                sorted(
                    path.relative_to(runtime.directory).as_posix()
                    for path in runtime.directory.rglob("event-*-maps.bin")
                ),
                flush=True,
            )
        raise
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
    residents = lifecycle["resident_terminal"]["resident_object_ids"]
    assert len(lifecycle["opened"]) == len(lifecycle["closed"]) + len(residents)
    assert set(lifecycle["opened"]) == set(lifecycle["closed"]) | set(residents)
    assert set(lifecycle["closed"]).isdisjoint(residents)
    kernel_opened = {
        event["id"]
        for event in lifecycle["events"]
        if event["kind"] == "open" and event["body"] is None
    }
    assert set(residents) == kernel_opened
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
    for mutation in ("missing-done", "post-done-frame", "library-descriptor", "library-inode"):
        changed = deepcopy(lifecycle)
        if mutation == "missing-done":
            changed["events"].pop()
        elif mutation == "post-done-frame":
            post_done = deepcopy(changed["events"][-1])
            post_done["sequence"] = len(changed["events"]) + 1
            changed["events"].append(post_done)
        elif mutation == "library-descriptor":
            changed["library_descriptor"]["descriptor"] += 1
        else:
            changed["library_descriptor"]["identity"]["inode"] += 1
        binding = write_json(mirror, runtime.directory / (mutation + ".lifecycle.json"), changed)
        with raises(ValueError):
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
    with raises(NativeToolUnavailable):
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

    purpose = "pandoc-terminal-wrong-peer"
    leaf = compiled.directory / ("callbacks-" + purpose)
    create_private_native_directory(mirror, leaf)
    observer = NativeLoaderObservation(
        compiled,
        leaf,
        purpose=purpose,
        deadline=min(runtime.deadline, time.monotonic() + NATIVE_OBSERVATION_CEILING_SECONDS),
    )
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as intruder:
        # This actual owner-PID peer is not the original consuming child.
        # Refusal must release its child, not wait for the child's ACK deadline.
        intruder.connect(observer.address)
        with raises(NativeToolUnavailable):
            runtime.tool("pandoc", ["--version"], purpose, loader=observer)
    failed = reader.read(runtime.tools[-1]["path"]).json_object()
    native = reader.read(failed["native_process_artifact"]["path"]).json_object()
    assert native["pid"] != os.getpid() and native["original_exit_code"] != 0
    assert native["accepted"] is False and native["timed_out"] is False
    assert native["cleanup"]["guardian_finished"] is True
    assert native["cleanup"]["root_reaped"] is True
    assert native["cleanup"]["final_token_sweep_matched_pids"] == []
    assert observer.peer is None and observer.events == []

    purpose = "python-terminal-premature-eof"
    leaf = compiled.directory / ("callbacks-" + purpose)
    create_private_native_directory(mirror, leaf)
    observer = NativeLoaderObservation(
        compiled,
        leaf,
        purpose=purpose,
        deadline=min(runtime.deadline, time.monotonic() + NATIVE_OBSERVATION_CEILING_SECONDS),
    )
    with raises(NativeToolUnavailable):
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
    with raises(TimeoutError):
        runtime.tool(
            "pandoc",
            ["--version"],
            "pandoc-terminal-expired",
            phase_deadline=time.monotonic() - 1,
        )
    assert len(runtime.tools) == retained
    assert not (runtime.directory / "pandoc-terminal-expired.native-process.json").exists()
"""


@pytest.mark.parametrize("runtime_layout", ["plain", "deep-spaces"])
@pytest.mark.timeout(1800)
@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="genuine glibc audit callbacks require Linux")
def test_genuine_pandoc_terminal_success_and_fail_closed_controls(
    complete_reference: tuple[Path, str, str], tmp_path: Path, runtime_layout: str
) -> None:
    """Exercise genuine native custody and cold direct/paired SDK entry points."""
    if shutil.which("pandoc") is None or shutil.which("cc") is None:
        pytest.skip("genuine Pandoc and the Source-selected C compiler are required")
    original, commit, fingerprint = complete_reference
    deadline = time.monotonic() + 1200
    # Real stage/compiler paths exceeded glibc's 254-byte audit-name limit,
    # while the former shallow --version fixture never exercised that boundary.
    nested = tmp_path / ("render-" + "r" * 80) / ("stage-" + "s" * 80)
    nested.mkdir(parents=True)
    mirror = _clone_complete_reference(complete_reference, nested / "mirror", deadline=deadline)
    environment = dict(os.environ, UV_OFFLINE="1", UV_PYTHON_DOWNLOADS="never")
    runtime_requirements = tmp_path / "runtime-requirements.txt"
    artifacts = tmp_path / "artifacts"
    built = subprocess.run(
        [
            "uv",
            "build",
            "--offline",
            "--no-config",
            "--no-build-isolation",
            "--python",
            sys.executable,
            "--wheel",
            "--no-create-gitignore",
            "--out-dir",
            str(artifacts),
        ],
        cwd=original,
        env=environment,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    wheels = list(artifacts.glob("*.whl"))
    assert len(wheels) == 1
    installed = tmp_path / "installed-sdk" if runtime_layout == "plain" else nested / "installed SDK's runtime"
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
    if runtime_layout == "deep-spaces":
        assert len(os.fsencode(selected_python)) > 255 and " " in str(selected_python)
    exported = subprocess.run(
        [
            "uv",
            "export",
            "--offline",
            "--locked",
            "--no-default-groups",
            "--group",
            "rendering",
            "--no-emit-project",
            "--no-emit-local",
            "--no-header",
            "--no-annotate",
            "--output-file",
            str(runtime_requirements),
        ],
        cwd=original,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert exported.returncode == 0, exported.stdout + exported.stderr
    normalize_locked_dependency_export(
        original, runtime_requirements, minor=f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    dependencies = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-build-isolation",
            "--no-deps",
            "--require-hashes",
            "--python",
            str(selected_python),
            "--requirements",
            str(runtime_requirements),
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert dependencies.returncode == 0, dependencies.stdout + dependencies.stderr
    installed_result = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-build",
            "--no-deps",
            "--python",
            str(selected_python),
            str(wheels[0]),
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
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

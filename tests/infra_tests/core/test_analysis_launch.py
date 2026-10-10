"""Actual selected-runtime launches and evidence; no process replacement."""

from __future__ import annotations

import json
import base64
import hashlib
import os
import py_compile
import subprocess
import signal
import sys
import time
import venv
from pathlib import Path

import pytest

from infrastructure.core.analysis_launch import analysis_receipt_path, analysis_stage_key, launch_analysis_script
from infrastructure.core.pipeline.fingerprints import canonical_digest, source_fingerprint
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.incremental import IncrementalConfig, HashManifest, should_skip_stage
from infrastructure.core.pipeline.types import PipelineConfig, StageContract
from infrastructure.core.runtime._python_env import build_analysis_script_cmd_and_env
from infrastructure.core.runtime.python_binding import analysis_runtime_binding, select_analysis_python

pytestmark = pytest.mark.timeout(180)


@pytest.fixture(autouse=True)
def _candidate_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")


def _project(tmp_path: Path, body: str, name: str = "leaf.py") -> tuple[Path, Path, Path]:
    repo = tmp_path.resolve()
    project = repo / "projects/demo"
    for directory in ("src", "scripts", "tests", "output"):
        (project / directory).mkdir(parents=True, exist_ok=True)
    script = project / "scripts" / name
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(body)
    return repo, project, script


def _launch(repo: Path, project: Path, script: Path, *, seconds: float = 60):
    cmd, env = build_analysis_script_cmd_and_env(script, project, repo)
    env.update(PIPELINE_RUN_ID="actual-analysis-control", PIPELINE_PLAN_DIGEST="a" * 64)
    result = launch_analysis_script(script, repo, project, cmd, env, time.monotonic() + seconds)
    receipt = json.loads(analysis_receipt_path(project, env["PIPELINE_RUN_ID"], result.stage_key).read_text())
    return result, receipt


@pytest.mark.parametrize(
    "code,state",
    [
        (0, StageStatus.SUCCEEDED),
        (2, StageStatus.FAILED),
        (7, StageStatus.FAILED),
        (124, StageStatus.TIMED_OUT),
        (130, StageStatus.INTERRUPTED),
    ],
)
def test_actual_leaf_exit_and_source_runtime_evidence(tmp_path: Path, code: int, state: StageStatus) -> None:
    repo, project, script = _project(tmp_path, f"raise SystemExit({code})\n")
    result, receipt = _launch(repo, project, script)
    assert result.status is state and result.child_exit_code == code
    assert result.attempt_exit_codes == (code,)
    assert receipt["schema"] == "template-analysis-leaf/3"
    assert receipt["stage_key"] == "analysis:scripts/leaf.py"
    assert receipt["plan_digest"] == "a" * 64
    assert receipt["outcome"] == json.loads(json.dumps(result.to_dict()))
    assert receipt["complete"] is (code == 0)
    assert receipt["controller_before"] == receipt["controller_after"]
    packet = receipt["worker"]
    assert packet["completion"]["request_digest"] == canonical_digest(packet["request"])
    assert packet["completion"]["actual_runtime"]["executable"] == str(Path(sys.executable).absolute())
    assert packet["completion"]["data_before_digest"] == packet["request"]["data_before"]["content_digest"]
    assert packet["original_process"]["pid"] > 0
    assert packet["original_process"]["original_exit_code"] == code
    assert (
        packet["original_process"]["observed_completion_monotonic"]
        < packet["original_process"]["original_deadline_monotonic"]
    )
    if code in {124, 130}:
        assert "script exited" in result.diagnostic


def test_actual_selected_runtime_has_separate_identity(tmp_path: Path) -> None:
    executable = os.environ.get("TEMPLATE_TEST_SELECTED_PYTHON", sys.executable)
    repo, project, script = _project(
        tmp_path,
        "import json,sys\nfrom pathlib import Path\n"
        "Path(__file__).parents[1].joinpath('output/runtime.json').write_text(json.dumps({'prefix':sys.prefix,'version':sys.version}))\n",
    )
    subprocess.run([executable, "-I", "-m", "venv", "--without-pip", str(project / ".venv")], check=True, timeout=20)
    result, receipt = _launch(repo, project, script)
    assert result.status is StageStatus.SUCCEEDED
    actual = json.loads((project / "output/runtime.json").read_text())
    selected_minor = analysis_runtime_binding(project)["python_minor"]
    assert actual["version"].startswith(str(selected_minor) + ".") and actual["prefix"] == str(project / ".venv")
    packet = receipt["worker"]
    assert packet["request"]["runtime_binding"]["executable"] == str(project / ".venv/bin/python")
    assert packet["completion"]["actual_runtime"]["python_version"].startswith(str(selected_minor) + ".")
    assert packet["request"]["source_content_digest"] == receipt["controller_before"]["source_content_digest"]


def test_actual_stage_retains_incoming_and_written_output_bodies_with_fresh_nonce(tmp_path: Path) -> None:
    repo, project, script = _project(
        tmp_path,
        "import json\nfrom pathlib import Path\n"
        "root=Path(__file__).parents[1]\n"
        "value=root.joinpath('data/input.csv').read_text().splitlines()[1]\n"
        "root.joinpath('output/data/manuscript_variables.json').write_text(json.dumps({'VALUE':value}))\n",
    )
    (project / "data").mkdir()
    (project / "data/input.csv").write_text("value\n-2.50\n")
    (project / "output/data").mkdir()
    target = project / "output/data/manuscript_variables.json"
    old = b'{"VALUE":"2.50"}'
    target.write_bytes(old)
    first, receipt = _launch(repo, project, script)
    assert first.status is StageStatus.SUCCEEDED
    packet = receipt["worker"]
    incoming = {row["path"]: row for row in packet["request"]["data_before"]["records"]}
    outgoing = {row["path"]: row for row in packet["completion"]["data_after"]["records"]}
    name = "output/data/manuscript_variables.json"
    assert project.joinpath(incoming[name]["retained_path"]).read_bytes() == old
    assert project.joinpath(outgoing[name]["retained_path"]).read_bytes() == target.read_bytes()
    assert incoming[name]["sha256"] != outgoing[name]["sha256"]
    assert incoming[name]["native_identity"] != outgoing[name]["native_identity"]
    assert packet["original_process"]["analysis_nonce"] == packet["completion"]["analysis_nonce"]
    second, later = _launch(repo, project, script)
    assert second.status is StageStatus.SUCCEEDED
    assert later["worker"]["request"]["analysis_nonce"] != packet["request"]["analysis_nonce"]
    assert project.joinpath(incoming[name]["retained_path"]).read_bytes() == old


def test_same_binary_distinct_lexical_venvs_are_distinct(tmp_path: Path) -> None:
    first = tmp_path.resolve() / "first"
    second = tmp_path.resolve() / "second"
    for project in (first, second):
        project.mkdir()
        venv.EnvBuilder(with_pip=False, symlinks=True).create(project / ".venv")
    left, right = analysis_runtime_binding(first), analysis_runtime_binding(second)
    assert left["binary_sha256"] == right["binary_sha256"]
    assert left["resolved_executable"] == right["resolved_executable"]
    assert left["executable"] != right["executable"] and canonical_digest(left) != canonical_digest(right)


def test_actual_analysis_ignores_timestamp_valid_domain_cache(tmp_path: Path) -> None:
    repo, project, script = _project(tmp_path, "from calculation import VALUE\nassert VALUE == 17\n")
    source = project / "src/calculation.py"
    marker = project / "output/poison-ran"
    poisoned = f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\nVALUE=17\n".encode()
    authored = b"VALUE=17\n" + b"#" * (len(poisoned) - len(b"VALUE=17\n"))
    source.write_bytes(poisoned)
    cache = source.parent / "__pycache__" / f"{source.stem}.{sys.implementation.cache_tag}.pyc"
    py_compile.compile(
        str(source), cfile=str(cache), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP
    )
    cached = source.stat()
    source.write_bytes(authored)
    os.utime(source, ns=(cached.st_atime_ns, cached.st_mtime_ns))
    ordinary = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);import calculation",
            str(source.parent),
        ],
        check=False,
        timeout=15,
    )
    assert ordinary.returncode == 0 and marker.exists()
    marker.unlink()
    result, receipt = _launch(repo, project, script)
    assert result.status is StageStatus.SUCCEEDED and receipt["complete"] is True
    assert not marker.exists()


def test_unbound_os_exit_zero_cannot_complete(tmp_path: Path) -> None:
    repo, project, script = _project(tmp_path, "import os\nos._exit(0)\n")
    result, receipt = _launch(repo, project, script)
    assert result.status is StageStatus.FAILED and result.child_exit_code == 0
    assert not result.attempt_exit_codes and not receipt["complete"] and receipt["worker"] is None


def test_restored_script_helper_bytes_cannot_launder_actual_executed_code(tmp_path: Path) -> None:
    repo, project, script = _project(
        tmp_path,
        "import os\nfrom pathlib import Path\n"
        "helper=Path(__file__).with_name('script_helper.py')\n"
        "original=helper.read_bytes()\nobserved=helper.stat()\n"
        'helper.write_text("from pathlib import Path\\n'
        "Path(__file__).parents[1].joinpath('output/aba-ran').write_text('actual')\\nVALUE=17\\n\")\n"
        "import script_helper\nassert script_helper.VALUE == 17\n"
        "helper.write_bytes(original)\nos.utime(helper,ns=(observed.st_atime_ns,observed.st_mtime_ns))\n",
    )
    helper = project / "scripts/script_helper.py"
    helper.write_text("VALUE=17\n")
    original = helper.read_bytes()
    result, receipt = _launch(repo, project, script)
    assert (project / "output/aba-ran").read_text() == "actual" and helper.read_bytes() == original
    assert result.status is StageStatus.BLOCKED and result.child_exit_code == 0
    assert result.attempt_exit_codes == (0,) and not receipt["complete"]
    assert "executed public module differs" in result.diagnostic


def test_supervisor_timeout_is_distinct_from_leaf_exit124(tmp_path: Path) -> None:
    repo, project, script = _project(tmp_path, "import time\ntime.sleep(30)\n")
    result, receipt = _launch(repo, project, script, seconds=2)
    assert result.status is StageStatus.TIMED_OUT and not result.complete
    assert not result.attempt_exit_codes and receipt["worker"] is None
    assert "script exited 124" not in result.diagnostic


def test_actual_os_interruption_removes_detached_writer_and_preserves_provenance(tmp_path: Path) -> None:
    repo, project, script = _project(
        tmp_path,
        "import os,time\nfrom pathlib import Path\n"
        "output=Path(__file__).parents[1]/'output'\n"
        "pid=os.fork()\n"
        "if pid == 0:\n    os.setsid()\n"
        "    while True:\n        (output/'heartbeat').write_text(str(time.monotonic()))\n        time.sleep(.03)\n"
        "(output/'started').write_text(str(pid))\ntime.sleep(60)\n",
    )
    implementation = Path(__file__).parents[3]
    driver = (
        "import json,sys,time\nfrom pathlib import Path\n"
        "sys.path.insert(0,sys.argv[1])\n"
        "from infrastructure.core.analysis_launch import launch_analysis_script\n"
        "from infrastructure.core.runtime._python_env import build_analysis_script_cmd_and_env\n"
        "repo,project,script=map(Path,sys.argv[2:])\n"
        "cmd,env=build_analysis_script_cmd_and_env(script,project,repo)\n"
        "env.update(PIPELINE_RUN_ID='os-interruption-control',PIPELINE_PLAN_DIGEST='b'*64)\n"
        "result=launch_analysis_script(script,repo,project,cmd,env,time.monotonic()+60)\n"
        "print(json.dumps(result.to_dict()),flush=True)\n"
    )
    caller = subprocess.Popen(
        [sys.executable, "-I", "-c", driver, str(implementation), str(repo), str(project), str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    detached: int | None = None
    try:
        deadline = time.monotonic() + 40
        while not (project / "output/heartbeat").exists() or not (project / "output/started").exists():
            assert caller.poll() is None, "Analysis caller exited before the actual leaf started"
            assert time.monotonic() < deadline, "Actual detached leaf never started"
            time.sleep(0.03)
        detached = int((project / "output/started").read_text())
        os.kill(caller.pid, signal.SIGINT)
        stdout, stderr = caller.communicate(timeout=40)
        assert caller.returncode == 0, stderr
        outcome = json.loads(stdout.splitlines()[-1])
        assert outcome["status"] == "interrupted" and not outcome["attempt_exit_codes"]
        assert "script exited 130" not in outcome["diagnostic"]
        receipt = json.loads(
            analysis_receipt_path(project, "os-interruption-control", analysis_stage_key(script, project)).read_text()
        )
        assert receipt["outcome"] == outcome and not receipt["complete"]
        heartbeat = (project / "output/heartbeat").read_bytes()
        time.sleep(0.15)
        assert (project / "output/heartbeat").read_bytes() == heartbeat
        with pytest.raises(ProcessLookupError):
            os.kill(detached, 0)
    finally:
        if caller.poll() is None:
            os.killpg(caller.pid, signal.SIGKILL)
            caller.wait(timeout=10)
        if detached is not None:
            try:
                os.kill(detached, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_nested_basename_keys_and_receipt_paths_do_not_collide(tmp_path: Path) -> None:
    project = tmp_path / "project"
    left = analysis_stage_key(project / "scripts/a/leaf.py", project)
    right = analysis_stage_key(project / "scripts/b/leaf.py", project)
    assert left != right
    assert analysis_receipt_path(project, "../../private", left) != analysis_receipt_path(
        project, "../../private", right
    )
    assert analysis_receipt_path(project, "../../private", left).is_relative_to(project / "output/.pipeline/analysis")


def test_selected_metadata_and_configuration_mutation_change_identity(tmp_path: Path) -> None:
    repo, project, _ = _project(tmp_path, "pass\n")
    venv.EnvBuilder(with_pip=False, symlinks=True).create(project / ".venv")
    selected = select_analysis_python(project)
    original = analysis_runtime_binding(project)
    metadata = (
        project
        / f".venv/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/control-1.0.dist-info"
    )
    metadata.mkdir()
    (metadata / "METADATA").write_text("Name: control\nVersion: 1.0\n")
    (metadata / "RECORD").write_text("control.py,,\n")
    first = source_fingerprint(repo, project)
    (metadata / "METADATA").write_text("Name: control\nVersion: 1.1\n")
    assert source_fingerprint(repo, project) != first
    before = analysis_runtime_binding(project)
    cfg = project / ".venv/pyvenv.cfg"
    cfg.write_text(cfg.read_text() + "control = changed\n")
    after = analysis_runtime_binding(project)
    assert before != after and original["executable"] == str(selected)


@pytest.mark.parametrize("kind", ["ancestor", "fifo"])
def test_nominated_runtime_nonregular_admission_refuses(tmp_path: Path, kind: str) -> None:
    _, project, _ = _project(tmp_path, "pass\n")
    venv.EnvBuilder(with_pip=False, symlinks=True).create(project / ".venv")
    if kind == "ancestor":
        binary_directory = project / ".venv/bin"
        binary_directory.rename(project / ".venv/real-bin")
        binary_directory.symlink_to("real-bin", target_is_directory=True)
    else:
        cfg = project / ".venv/pyvenv.cfg"
        cfg.unlink()
        os.mkfifo(cfg)
    started = time.monotonic()
    with pytest.raises((OSError, ValueError)):
        analysis_runtime_binding(project)
    assert time.monotonic() - started < 2


def test_installed_member_mutation_never_reuses_analysis_or_resumes_checkpoint(tmp_path: Path) -> None:
    repo, project, leaf = _project(
        tmp_path,
        "import science\nfrom pathlib import Path\n"
        "target=Path(__file__).parents[1]/'output/data/value.txt'\n"
        "target.parent.mkdir(parents=True,exist_ok=True)\ntarget.write_text(str(science.VALUE))\n",
    )
    venv.EnvBuilder(with_pip=False, symlinks=True).create(project / ".venv")
    site = project / f".venv/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    member = site / "science.py"
    member.write_text("VALUE=17\n")
    declared = base64.urlsafe_b64encode(hashlib.sha256(member.read_bytes()).digest()).rstrip(b"=").decode()
    distribution = site / "science-1.0.dist-info"
    distribution.mkdir()
    (distribution / "METADATA").write_text("Metadata-Version: 2.1\nName: science\nVersion: 1.0\n")
    record = distribution / "RECORD"
    record.write_text(f"science.py,sha256={declared},{member.stat().st_size}\nscience-1.0.dist-info/RECORD,,\n")
    original_declarations = record.read_bytes(), (distribution / "METADATA").read_bytes()
    implementation = Path(__file__).parents[3]
    stage = repo / "scripts/pipeline/stage_02_analysis.py"
    stage.parent.mkdir(parents=True)
    stage.write_bytes((implementation / "scripts/pipeline/stage_02_analysis.py").read_bytes())
    (repo / "scripts/__init__.py").write_bytes((implementation / "scripts/__init__.py").read_bytes())
    (project / "pipeline.yaml").write_text(
        "telemetry:\n  enabled: false\nstages:\n"
        "  - name: Aliased canonical analysis\n    key: scientific-work\n"
        "    script: scripts/pipeline/stage_02_analysis.py\n"
        "    contract:\n      output_artifacts: [output/data/value.txt]\n"
    )
    config = PipelineConfig("demo", repo, clean=False, run_timeout_seconds=120, incremental=IncrementalConfig(True))
    executor = PipelineExecutor(config)
    first = executor.execute_pipeline()
    assert executor.run_result(first).complete and (project / "output/data/value.txt").read_text() == "17"
    checkpoint = executor.checkpoint_manager.checkpoint_file
    checkpoint_before = checkpoint.read_bytes()
    identity = source_fingerprint(repo, project)
    member.write_text("VALUE=23\n")
    assert source_fingerprint(repo, project) == identity
    assert original_declarations == (record.read_bytes(), (distribution / "METADATA").read_bytes())
    config.resume = True
    resumed_executor = PipelineExecutor(config)
    refused = resumed_executor.execute_pipeline()
    assert resumed_executor.run_result(refused).exit_code == 75
    assert refused[0].outcome is not None and "declaration identity only" in refused[0].outcome.diagnostic
    assert checkpoint.read_bytes() == checkpoint_before
    assert (project / "output/data/value.txt").read_text() == "17"
    config.resume = False
    fresh_executor = PipelineExecutor(config)
    second = fresh_executor.execute_pipeline()
    assert fresh_executor.run_result(second).complete
    assert second[0].outcome is not None and second[0].outcome.status is StageStatus.SUCCEEDED
    assert (project / "output/data/value.txt").read_text() == "23"
    assert leaf.exists()


@pytest.mark.parametrize(
    "key,target",
    [("analysis", None), ("analysis:scripts/leaf.py", None), ("alias", "./scripts/pipeline/stage_02_analysis.py")],
)
def test_direct_cache_api_analysis_aliases_always_miss(tmp_path: Path, key: str, target: str | None) -> None:
    repo, project, _ = _project(tmp_path, "pass\n")
    decision = should_skip_stage(
        config=IncrementalConfig(True),
        manifest=HashManifest(),
        repo_root=repo,
        project_dir=project,
        stage_name=key,
        contract=StageContract(output_artifacts=("output/value.txt",)),
        stage_script=target,
    )
    assert not decision.skip and not decision.input_hash


def _metadata_fixture(site: Path, count: int = 1) -> dict[str, str]:
    site.mkdir()
    expected = {}
    for number in range(count):
        distribution = site / f"control{number}-1.0.dist-info"
        distribution.mkdir()
        for leaf in ("METADATA", "RECORD"):
            raw = f"control{number} {leaf} original bytes\n".encode()
            (distribution / leaf).write_bytes(raw)
            expected[f"{distribution.name}/{leaf}"] = hashlib.sha256(raw).hexdigest()
    return expected


def test_metadata_uses_held_site_and_distribution_with_independent_byte_parity(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.fingerprint_files import anchored_parent
    from infrastructure.core.runtime.python_binding import _installation_metadata

    roots = (tmp_path / "site-a", tmp_path / "site-b")
    expected = {
        f"{index}/{key}": value
        for index, root in enumerate(roots)
        for key, value in _metadata_fixture(root, count=20).items()
    }
    original_profiler = sys.getprofile()
    actual_code = anchored_parent.__wrapped__.__code__
    calls = 0

    def observe(frame, event, argument):
        nonlocal calls
        if event == "call" and frame.f_code is actual_code:
            calls += 1
        if original_profiler is not None:
            original_profiler(frame, event, argument)

    try:
        sys.setprofile(observe)
        result = _installation_metadata(roots)
    finally:
        sys.setprofile(original_profiler)
    assert result == expected
    # A generator has one actual entry and one continuation on context exit.
    # Each held site already protects all descendants; no leaf reopens ancestry.
    assert calls == 2 * len(roots)
    first = roots[0] / "control0-1.0.dist-info/METADATA"
    first.write_bytes(b"changed real metadata bytes\n")
    expected["0/control0-1.0.dist-info/METADATA"] = hashlib.sha256(first.read_bytes()).hexdigest()
    assert _installation_metadata(roots) == expected


@pytest.mark.parametrize("fault", ["linked-leaf", "linked-distribution", "fifo", "missing-leaf"])
def test_held_metadata_keeps_real_nonregular_and_missing_refusals(tmp_path: Path, fault: str) -> None:
    from infrastructure.core.runtime.python_binding import AnalysisRuntimeUnavailable, _installation_metadata

    site = tmp_path / "site"
    _metadata_fixture(site)
    distribution = site / "control0-1.0.dist-info"
    metadata = distribution / "METADATA"
    outside = tmp_path / "outside"
    outside.write_bytes(b"external sentinel\n")
    if fault == "linked-distribution":
        distribution.rename(site / "original")
        distribution.symlink_to(site / "original", target_is_directory=True)
    else:
        metadata.unlink()
        if fault == "linked-leaf":
            metadata.symlink_to(outside)
        elif fault == "fifo":
            os.mkfifo(metadata)
    with pytest.raises((ValueError, OSError, AnalysisRuntimeUnavailable)):
        _installation_metadata((site,))
    assert outside.read_bytes() == b"external sentinel\n"


@pytest.mark.parametrize("boundary", ["site", "distribution"])
def test_metadata_real_directory_replacement_during_held_read_is_refused(tmp_path: Path, boundary: str) -> None:
    from infrastructure.core.pipeline.fingerprint_files import digest_file
    from infrastructure.core.runtime.python_binding import _installation_metadata
    import shutil

    site = tmp_path / "site"
    _metadata_fixture(site)
    target = site if boundary == "site" else site / "control0-1.0.dist-info"
    original_profiler = sys.getprofile()
    changed = False

    def observe(frame, event, argument):
        nonlocal changed
        if (
            not changed
            and event == "return"
            and frame.f_code is digest_file.__code__
            and frame.f_locals.get("name") == "METADATA"
        ):
            changed = True
            held = target.with_name(target.name + "-held")
            target.rename(held)
            shutil.copytree(held, target)
        if original_profiler is not None:
            original_profiler(frame, event, argument)

    try:
        sys.setprofile(observe)
        with pytest.raises(ValueError, match="directory changed"):
            _installation_metadata((site,))
    finally:
        sys.setprofile(original_profiler)
    assert changed

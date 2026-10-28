"""Actual source-owned Root lane controls, independent of complete platform acceptance."""

from __future__ import annotations

import copy
import json
import os
import signal
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.public_acceptance_case_policy import POLICY_SCHEMA
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_root_case_admission import PREREQUISITE_SCHEMA, admit_plan, load_policy
from infrastructure.project.public_root_case_census import produce_root_census
from infrastructure.project.public_root_lane_contract import lane_command, write
from infrastructure.project.public_root_lane_producer import coordinator_command, produce_root_lane
from infrastructure.project.public_root_lane_readback import read_lane
from infrastructure.project.public_root_lane_diagnostics import read_output, read_reports
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

pytestmark = pytest.mark.timeout(1200)


def _epoch_call(function: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    names = ("SOURCE_DATE_EPOCH", "TEMPLATE_BUILD_EPOCH_SOURCE")
    original = {name: os.environ.get(name) for name in names}
    try:
        os.environ.update(SOURCE_DATE_EPOCH="0", TEMPLATE_BUILD_EPOCH_SOURCE="explicit-owned-control")
        return function(*args, **kwargs)
    finally:
        for name, value in original.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _genuine_lane_root(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    root = tmp_path_factory.mktemp("actual-root-lanes").resolve()
    (root / "tests").mkdir()
    (root / "infrastructure/config").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname="owned-root-lane-control"\nversion="0.1.0"\nrequires-python=">=3.12"\n'
        '[tool.pytest.ini_options]\naddopts=[]\nmarkers=["requires_ollama: explicit local-model obligation"]\n'
        '[tool.coverage.run]\nbranch=true\nsource=["infrastructure"]\n',
        encoding="utf-8",
    )
    (root / "tests/conftest.py").write_text(
        "from pathlib import Path\nimport pytest,json\n"
        "@pytest.fixture(autouse=True)\ndef owned_fixture():\n"
        "    root=Path(__file__).parents[1]; events=root/'output/readiness/events.txt'\n"
        "    with events.open('a') as stream: stream.write('setup\\n')\n"
        "    yield\n"
        "    action=root/'output/readiness/action.json'\n"
        "    value=json.loads(action.read_text()) if action.exists() else None\n"
        "    with events.open('a') as stream: stream.write('teardown\\n')\n"
        "    if value=='teardown-failure': raise ValueError('actual own teardown failure')\n",
        encoding="utf-8",
    )
    (root / "tests/test_owned.py").write_text(
        "from pathlib import Path\nimport os,json,pytest,shutil,signal,subprocess,sys,time\n"
        "@pytest.mark.parametrize('number',[1,2],ids=['one','two'])\n"
        "def test_core(number,request):\n"
        "    root=Path(__file__).parents[1]; action=root/'output/readiness/action.json'\n"
        "    value=json.loads(action.read_text()) if action.exists() else None\n"
        "    with (root/'output/readiness/events.txt').open('a') as stream: stream.write('call\\n')\n"
        "    if isinstance(value,int):\n"
        "        with request.getfixturevalue('capfd').disabled():\n"
        "            print('ORIGINAL HARD EXIT STDOUT',flush=True)\n"
        "            print('ORIGINAL HARD EXIT STDERR',file=sys.stderr,flush=True)\n"
        "            os._exit(value)\n"
        "    if value=='call-skip': pytest.skip('actual own unexpected skip')\n"
        "    if isinstance(value,dict) and value.get('case') in {'detached-timeout','detached-interrupt'}:\n"
        "        startup=root/'output/readiness/descendant-startup.json'\n"
        "        escaped=root/'output/readiness/descendant-escaped'\n"
        "        token=value['token']\n"
        '        child=("import os,sys,json,time;from pathlib import Path;"\n'
        "               \"Path(sys.argv[1]).write_text(json.dumps({'pid':os.getpid(),'token':sys.argv[3],\"\n"
        "               \"'started_ns':time.monotonic_ns()}));time.sleep(900);\"\n"
        "               \"Path(sys.argv[2]).write_text('escaped')\")\n"
        "        subprocess.Popen([sys.executable,'-I','-B','-c',child,str(startup),str(escaped),token],\n"
        "                         start_new_session=True)\n"
        "        (root/'output/readiness/actual-case-reached').write_text(token)\n"
        "        while not (root/'output/readiness/descendant-live-ack').exists(): time.sleep(.01)\n"
        "        if value['case']=='detached-interrupt': os.kill(os.getpid(),signal.SIGINT)\n"
        "        time.sleep(900)\n"
        "    if value=='case-deadline':\n"
        "        (root/'output/readiness/case-deadline-reached').write_text('actual case timer')\n"
        "        time.sleep(5)\n"
        "    if value=='manual-timeout':\n"
        "        import pytest_timeout\n"
        "        pytest_timeout.timeout_sigalrm(request.node,pytest_timeout._get_item_settings(request.node))\n"
        "    if value=='timeout-message': pytest.fail('Timeout (> 1.0s) from pytest-timeout.')\n"
        "    if number==1 and isinstance(value,dict) and value.get('case')=='coverage-leaf':\n"
        "        Path(value['target']).symlink_to(Path(value['external']))\n"
        "    if number==1 and isinstance(value,dict) and value.get('case')=='coverage-ancestor':\n"
        "        target=Path(value['target']); target.rename(target.with_name(target.name+'-owned-before-link'))\n"
        "        target.symlink_to(Path(value['external']),target_is_directory=True)\n"
        "    if number==1 and isinstance(value,dict) and value.get('case')=='root-replace':\n"
        "        saved=Path(value['saved']); root.rename(saved); shutil.copytree(saved,root)\n"
        "    if value=='source-edit':\n"
        "        source=Path(__file__); source.write_bytes(source.read_bytes()+b'\\n# owned source edit\\n')\n"
        "    assert number>0\n"
        "@pytest.mark.requires_ollama\nclass TestLive:\n"
        "    def test_model(self):\n"
        "        (Path(__file__).parents[1]/'output/readiness/live-body').write_text('actual live body invoked')\n"
        "        raise AssertionError('required local-model fixture is unavailable in this control')\n",
        encoding="utf-8",
    )
    first = _epoch_call(produce_root_census, root, root / "output/readiness/initial", timeout_seconds=180)
    assert first["exit_code"] == 0, first
    from infrastructure.project.public_root_case_contract import _json

    rows = _json(SnapshotReader(root).read(first["receipt_artifact"]["path"]))["census"]["families"]
    assignments = {"tests/test_owned.py::test_core": "core", "tests/test_owned.py::TestLive::test_model": "live-unpaid"}
    assert {row["id"] for row in rows} == set(assignments)
    policy = {
        "schema_version": POLICY_SCHEMA,
        "runtimes": ["3.14", "3.15"],
        "platforms": ["darwin", "linux"],
        "obligations": [{"id": "owned-local-model", "kind": "local-model", "eligibility": None}],
        "families": [
            {key: row[key] for key in ("id", "members", "source_sha256", "metadata_sha256")}
            | {
                "lane": assignments[row["id"]],
                "obligations": ["owned-local-model"] if assignments[row["id"]] == "live-unpaid" else [],
            }
            for row in rows
        ],
    }
    (root / "infrastructure/config/root-case-policy.json").write_text(json.dumps(policy), encoding="utf-8")
    (root / "infrastructure/config/root-case-prerequisites.json").write_text(
        json.dumps(
            {
                "schema_version": PREREQUISITE_SCHEMA,
                "obligations": [
                    {
                        "id": "owned-local-model",
                        "kind": "local-model",
                        "environment_keys": ["TEMPLATE_OWNED_UNAVAILABLE_MODEL_CONFIGURATION"],
                        "executables": ["python"],
                        "platforms": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with (root / "pyproject.toml").open("a") as stream:
        stream.write(
            "[tool.template.root_acceptance]\nschema_version=2\n"
            'policy="infrastructure/config/root-case-policy.json"\n'
            'prerequisites="infrastructure/config/root-case-prerequisites.json"\n'
        )
    with pytest.raises(ValueError):
        admit_plan(SnapshotReader(root), first)
    census = _epoch_call(produce_root_census, root, root / "output/readiness/current", timeout_seconds=180)
    assert census["exit_code"] == 0, census
    admission = admit_plan(SnapshotReader(root), census)
    assert set(admission.plan.nodeids) == {
        "tests/test_owned.py::test_core[one]",
        "tests/test_owned.py::test_core[two]",
        "tests/test_owned.py::TestLive::test_model",
    }
    assert not (root / "output/readiness/events.txt").exists()
    return root, census


@pytest.fixture(scope="module")
def genuine_lane(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    root, census = _genuine_lane_root(tmp_path_factory)
    bundle = _epoch_call(
        produce_root_lane,
        root,
        root / "output/readiness/core",
        census_bundle=census,
        lane="core",
        timeout_seconds=240,
        test_timeout_seconds=60,
    )
    assert bundle["exit_code"] == 0, bundle
    result = read_lane(SnapshotReader(root), bundle)
    assert result["selected_nodes"] == ["tests/test_owned.py::test_core[one]", "tests/test_owned.py::test_core[two]"]
    assert (root / "output/readiness/events.txt").read_text().splitlines() == ["setup", "call", "teardown"] * 2
    assert not (root / "output/readiness/live-body").exists()
    return root, census, bundle


@pytest.mark.parametrize("action_name", ["complete", "case-deadline", "cancel-removed"])
def test_actual_thread_deadline_composes_with_native_guard_and_refuses_expiry_or_tamper(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]], tmp_path: Path, action_name: str
) -> None:
    original_root, _, _ = genuine_lane
    root = tmp_path / "thread-root"
    root.mkdir()
    for name in ("tests", "infrastructure/config"):
        shutil.copytree(original_root / name, root / name)
    shutil.copyfile(original_root / "pyproject.toml", root / "pyproject.toml")
    source = root / "tests/test_owned.py"
    code = source.read_text()
    code = code.replace(
        "@pytest.mark.parametrize('number'",
        "@pytest.mark.timeout(2,method='thread')\n@pytest.mark.parametrize('number'",
        1,
    )
    code = code.replace(
        "    assert number>0\n",
        "    from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard\n"
        "    with native_deadline_guard(time.monotonic()+.25):\n"
        "        assert signal.getitimer(signal.ITIMER_REAL)[0]>0\n"
        "    assert signal.getitimer(signal.ITIMER_REAL)[0]==0\n"
        "    if value=='cancel-removed': request.node.cancel_timeout=None\n"
        "    assert number>0\n",
        1,
    )
    source.write_text(code)
    first = _epoch_call(produce_root_census, root, root / "output/readiness/first", timeout_seconds=180)
    assert first["exit_code"] == 0, first
    from infrastructure.project.public_root_case_contract import _json

    observed = _json(SnapshotReader(root).read(first["receipt_artifact"]["path"]))["census"]["families"]
    policy_path = root / "infrastructure/config/root-case-policy.json"
    policy = json.loads(policy_path.read_bytes())
    prior = {family["id"]: family for family in policy["families"]}
    assert {family["id"] for family in observed} == set(prior)
    policy["families"] = [
        prior[row["id"]] | {key: row[key] for key in ("members", "source_sha256", "metadata_sha256")}
        for row in observed
    ]
    policy_path.write_text(json.dumps(policy))
    census = _epoch_call(produce_root_census, root, root / "output/readiness/current", timeout_seconds=180)
    assert census["exit_code"] == 0, census
    (root / "output/readiness/action.json").write_text(json.dumps(action_name))
    bundle = _epoch_call(
        produce_root_lane,
        root,
        root / "output/readiness/thread",
        census_bundle=census,
        lane="core",
        timeout_seconds=180,
        test_timeout_seconds=60,
    )
    if action_name == "complete":
        assert bundle["exit_code"] == 0, bundle
        result = read_lane(SnapshotReader(root), bundle)
        assert len(result["selected_nodes"]) == 2
    else:
        assert bundle["exit_code"] == 1, bundle
        result = json.loads((root / bundle["result_artifact"]["path"]).read_bytes())
        record = result["records"][0]
        actual = json.loads((root / record["process_artifact"]["path"]).read_bytes())
        assert actual["original_returncode"] == actual["returncode"] == 1
        if action_name == "cancel-removed":
            original = json.loads((root / record["receipt_artifact"]["path"]).read_bytes())
            assert original["original_pytest_exit_code"] == 3
            assert original["exit_code"] == 1
            assert original["bytecode_verified"] is False
            directory = (root / record["process_artifact"]["path"]).parent
            output = read_output(SnapshotReader(root), directory, actual["output_artifact"])
            assert "Root case thread deadline changed or stopped before actual cancellation" in output["stdout"]["text"]
        else:
            assert record.get("receipt_artifact") is None
        assert actual["timed_out"] is False
        assert actual["duration_seconds"] < 30
        with pytest.raises(ValueError):
            read_lane(SnapshotReader(root), bundle)


def test_actual_source_owned_core_selection_and_all_original_phases(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, _, bundle = genuine_lane
    result = read_lane(SnapshotReader(root), bundle)
    for record in result["records"]:
        native = json.loads((root / record["process_artifact"]["path"]).read_bytes())
        actual = json.loads((root / record["receipt_artifact"]["path"]).read_bytes())
        assert native["returncode"] == native["original_returncode"] == 0
        assert native["timed_out"] is native["custody_refused"] is False
        assert actual["bytecode_verified"] is True and actual["interrupted"] is False
        assert actual["original_pytest_exit_code"] == actual["exit_code"] == 0
        directory = (root / record["process_artifact"]["path"]).parent
        assert read_output(SnapshotReader(root), directory, native["output_artifact"])["stdout"]["captured_bytes"] > 0
        assert read_reports(SnapshotReader(root), directory, actual["diagnostics_artifact"])["reports"] == []


@pytest.mark.parametrize("mode", ["core", "live"])
def test_required_live_lane_stays_blocked_without_execution(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]], mode: str
) -> None:
    root, census, _ = genuine_lane
    assert "TEMPLATE_OWNED_UNAVAILABLE_MODEL_CONFIGURATION" not in os.environ
    before = (root / "output/readiness/events.txt").read_bytes()
    bundle = _epoch_call(
        produce_root_lane,
        root,
        root / ("output/readiness/blocked-" + mode),
        census_bundle=census,
        lane="live-unpaid",
        mode=mode,
        timeout_seconds=180,
    )
    assert bundle["exit_code"] == 75, bundle
    assert (root / "output/readiness/events.txt").read_bytes() == before
    assert not (root / "output/readiness/live-body").exists()
    with pytest.raises(ValueError):
        read_lane(SnapshotReader(root), bundle)


@pytest.mark.parametrize("original_exit", [0, 2, 7])
def test_real_case_exit_without_receipt_cannot_pass(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]], original_exit: int
) -> None:
    root, census, _ = genuine_lane
    action = root / "output/readiness/action.json"
    try:
        action.write_text(json.dumps(original_exit), encoding="utf-8")
        bundle = _epoch_call(
            produce_root_lane,
            root,
            root / f"output/readiness/native-exit-{original_exit}",
            census_bundle=census,
            lane="core",
            timeout_seconds=180,
        )
        assert bundle["exit_code"] == 1, bundle
        result = json.loads((root / bundle["result_artifact"]["path"]).read_bytes())
        record = result["records"][0]
        actual = json.loads((root / result["records"][0]["process_artifact"]["path"]).read_bytes())
        output = read_output(
            SnapshotReader(root), (root / record["process_artifact"]["path"]).parent, actual["output_artifact"]
        )
        assert "ORIGINAL HARD EXIT STDOUT" in output["stdout"]["text"]
        assert "ORIGINAL HARD EXIT STDERR" in output["stderr"]["text"]
        assert actual["original_returncode"] == original_exit
        assert actual["receipt_artifact"] is None
        with pytest.raises(ValueError):
            read_lane(SnapshotReader(root), bundle)
    finally:
        action.unlink(missing_ok=True)


@pytest.mark.parametrize("action_name", ["call-skip", "teardown-failure", "source-edit"])
def test_actual_skip_teardown_or_concurrent_source_edit_refuses_success(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]], action_name: str
) -> None:
    root, census, _ = genuine_lane
    source = root / "tests/test_owned.py"
    original = source.read_bytes()
    action = root / "output/readiness/action.json"
    try:
        action.write_text(json.dumps(action_name), encoding="utf-8")
        bundle = _epoch_call(
            produce_root_lane,
            root,
            root / ("output/readiness/action-" + action_name),
            census_bundle=census,
            lane="core",
            timeout_seconds=180,
        )
        assert bundle["exit_code"] == 1, bundle
        result = json.loads((root / bundle["result_artifact"]["path"]).read_bytes())
        record = result["records"][0]
        actual = json.loads((root / record["receipt_artifact"]["path"]).read_bytes())
        directory = (root / record["receipt_artifact"]["path"]).parent
        diagnostics = read_reports(SnapshotReader(root), directory, actual["diagnostics_artifact"])
        assert diagnostics["reports"] or diagnostics["exception"] is not None
        with pytest.raises(ValueError):
            read_lane(SnapshotReader(root), bundle)
    finally:
        action.unlink(missing_ok=True)
        source.write_bytes(original)


@pytest.mark.parametrize("action_name,expected_code", [("detached-timeout", 124), ("detached-interrupt", 130)])
def test_actual_lane_deadline_or_interruption_cleans_launched_detached_child(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]], action_name: str, expected_code: int
) -> None:
    root, census, _ = genuine_lane
    whole_seconds = 180
    token = uuid.uuid4().hex
    action = root / "output/readiness/action.json"
    startup = root / "output/readiness/descendant-startup.json"
    reached = root / "output/readiness/actual-case-reached"
    escaped = root / "output/readiness/descendant-escaped"
    acknowledgement = root / "output/readiness/descendant-live-ack"
    live: list[int] = []
    errors: list[str] = []
    stop = threading.Event()
    monitor_deadline = time.monotonic() + whole_seconds + 2

    def native_state(pid: int) -> str | None:
        observed = subprocess.run(
            ["ps", "-ww", "-p", str(pid), "-o", "pid=", "-o", "stat=", "-o", "args="],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if observed.returncode == 1 and observed.stdout == observed.stderr == "":
            return None
        fields = observed.stdout.strip().split(maxsplit=2)
        if observed.returncode != 0 or observed.stderr or len(fields) < 2 or fields[0] != str(pid):
            raise ValueError("native observation did not establish exact owned descendant identity")
        if not fields[1].startswith("Z") and (len(fields) != 3 or token not in fields[2]):
            raise ValueError("native executable descendant differs from the actual owned token")
        return fields[1]

    def monitor_startup() -> None:
        while not stop.is_set() and time.monotonic() < monitor_deadline:
            try:
                actual = json.loads(startup.read_bytes())
                pid = actual["pid"]
                if (
                    type(pid) is not int
                    or pid <= 1
                    or type(actual["started_ns"]) is not int
                    or actual["token"] != token
                ):
                    raise ValueError("actual descendant startup differs from its owned invocation")
                state = native_state(pid)
                if state is not None and not state.startswith("Z"):
                    live.append(pid)
                    acknowledgement.write_text(token, encoding="utf-8")
                    return
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                errors.append(type(error).__name__)
                return
            stop.wait(0.02)

    monitor = threading.Thread(target=monitor_startup)
    try:
        action.write_text(json.dumps({"case": action_name, "token": token}), encoding="utf-8")
        monitor.start()
        started = time.monotonic()
        bundle = _epoch_call(
            produce_root_lane,
            root,
            root / ("output/readiness/" + action_name),
            census_bundle=census,
            lane="core",
            timeout_seconds=whole_seconds,
            test_timeout_seconds=600,
        )
        stop.set()
        monitor.join(timeout=7)
        assert not monitor.is_alive() and not errors
        assert bundle["exit_code"] == expected_code, bundle
        assert time.monotonic() - started < whole_seconds + 15
        assert reached.read_text() == token, "deadline before actual case call cannot prove descendant cleanup"
        assert live, "native observation must prove the actual detached descendant was executable"
        state = native_state(live[0])
        assert state is None or state.startswith("Z")
        assert not escaped.exists()
        outer = json.loads((root / bundle["coordinator_artifact"]["path"]).read_bytes())
        if expected_code == 124:
            assert outer["timed_out"] is True or outer["returncode"] == 124
        else:
            assert outer["original_returncode"] == outer["returncode"] == 130
            assert outer["timed_out"] is False
        with pytest.raises(ValueError):
            read_lane(SnapshotReader(root), bundle)
    finally:
        stop.set()
        if monitor.ident is not None:
            monitor.join(timeout=7)
        if startup.exists():
            actual = json.loads(startup.read_bytes())
            if actual.get("token") == token and type(actual.get("pid")) is int:
                state = native_state(actual["pid"])
                if state is not None and not state.startswith("Z"):
                    try:
                        os.kill(actual["pid"], signal.SIGKILL)
                    except ProcessLookupError:
                        pass
        for path in (action, startup, reached, escaped, acknowledgement):
            path.unlink(missing_ok=True)


@pytest.mark.parametrize(
    "action_name,expected_code", [("case-deadline", 124), ("manual-timeout", 1), ("timeout-message", 1)]
)
def test_actual_case_timer_is_typed_and_early_callback_or_failure_text_is_not_timeout(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]], action_name: str, expected_code: int
) -> None:
    root, census, _ = genuine_lane
    action = root / "output/readiness/action.json"
    reached = root / "output/readiness/case-deadline-reached"
    try:
        action.write_text(json.dumps(action_name), encoding="utf-8")
        bundle = _epoch_call(
            produce_root_lane,
            root,
            root / ("output/readiness/" + action_name),
            census_bundle=census,
            lane="core",
            timeout_seconds=180,
            test_timeout_seconds=1 if expected_code == 124 else 60,
        )
        assert bundle["exit_code"] == expected_code, bundle
        result = json.loads((root / bundle["result_artifact"]["path"]).read_bytes())
        actual = json.loads((root / result["records"][0]["receipt_artifact"]["path"]).read_bytes())
        assert actual["original_pytest_exit_code"] == 1
        assert actual["timed_out"] is (expected_code == 124)
        assert actual["exit_code"] == expected_code
        directory = (root / result["records"][0]["receipt_artifact"]["path"]).parent
        diagnostics = read_reports(SnapshotReader(root), directory, actual["diagnostics_artifact"])
        assert diagnostics["reports"] and any(row["outcome"] == "failed" for row in diagnostics["reports"])
        if expected_code == 124:
            assert reached.read_text() == "actual case timer"
        with pytest.raises(ValueError):
            read_lane(SnapshotReader(root), bundle)
    finally:
        action.unlink(missing_ok=True)
        reached.unlink(missing_ok=True)


@pytest.mark.parametrize("fault", ["summary-leaf", "chunk-leaf", "chunk-ancestor"])
def test_real_case_cannot_redirect_coverage_evidence_outside_confined_run(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]], tmp_path: Path, fault: str
) -> None:
    root, census, _ = genuine_lane
    directory = root / ("output/readiness/coverage-link-" + fault)
    action = root / "output/readiness/action.json"
    external = tmp_path.resolve() / "invented-outside"
    external.mkdir()
    marker = external / "public-coverage-sentinel"
    original = b"invented public outside evidence must stay identical\n"
    marker.write_bytes(original)
    target = (
        directory / "coverage.json"
        if fault == "summary-leaf"
        else directory / "chunk-0000/coverage-data.json"
        if fault == "chunk-leaf"
        else directory / "chunk-0000"
    )
    try:
        action.write_text(
            json.dumps(
                {
                    "case": "coverage-ancestor" if fault == "chunk-ancestor" else "coverage-leaf",
                    "target": str(target),
                    "external": str(external if fault == "chunk-ancestor" else marker),
                }
            ),
            encoding="utf-8",
        )
        bundle = _epoch_call(produce_root_lane, root, directory, census_bundle=census, lane="core", timeout_seconds=180)
        assert bundle["exit_code"] == 1, bundle
        assert target.is_symlink(), "actual case must create the genuine failing target link"
        assert marker.read_bytes() == original
        assert sorted(path.name for path in external.iterdir()) == [marker.name]
        with pytest.raises(ValueError):
            read_lane(SnapshotReader(root), bundle)
    finally:
        action.unlink(missing_ok=True)
        if target.is_symlink():
            target.unlink()
        if fault == "chunk-ancestor":
            saved = target.with_name(target.name + "-owned-before-link")
            if saved.exists():
                saved.rename(target)


def test_real_case_physical_root_replacement_refuses_writes_with_identical_source_bytes(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    from infrastructure.project.public_acceptance_scope import RuntimeScope

    root, census, _ = genuine_lane
    original_source = RuntimeScope(root, "root").source_identity()
    observed = root.stat()
    identity = [observed.st_dev, observed.st_ino]
    saved = root.with_name(root.name + "-original-physical-root")
    action = root / "output/readiness/action.json"
    try:
        action.write_text(json.dumps({"case": "root-replace", "saved": str(saved)}), encoding="utf-8")
        with pytest.raises(ValueError, match="confinement root changed"):
            _epoch_call(
                produce_root_lane,
                root,
                root / "output/readiness/root-replace",
                census_bundle=census,
                lane="core",
                timeout_seconds=180,
            )
        assert saved.is_dir(), "actual owned case must replace its physical Root"
        assert RuntimeScope(root, "root").source_identity() == original_source
        current = root.stat()
        assert [current.st_dev, current.st_ino] != identity
        with pytest.raises(ValueError, match="confinement root changed"):
            write(
                root,
                root / "output/readiness/root-replace/forbidden-new-root.json",
                {"invented_public_marker": True},
                identity,
            )
        assert not (root / "output/readiness/root-replace/forbidden-new-root.json").exists()
        assert not (root / "output/readiness/root-replace/lane-coordinator-process.json").exists()
    finally:
        if saved.exists():
            if root.exists():
                shutil.rmtree(root)
            saved.rename(root)
        action.unlink(missing_ok=True)


@pytest.mark.parametrize(
    "fault",
    [
        "missing-member",
        "missing-teardown",
        "unexpected-skip",
        "original-case-two",
        "bytecode-unverified",
        "case-timeout",
        "coverage-source",
        "coverage-arcs",
        "coverage-summary",
        "child-native-seven",
        "child-native-boolean",
        "child-timeout",
        "wrong-child-command",
        "wrong-plan",
        "wrong-source",
        "extra-result-field",
        "wrong-outer-run",
        "boolean-outer-zero",
        "extra-outer-field",
        "impossible-outer-timeline",
        "impossible-worker-timeline",
        "impossible-chunk-timeline",
        "missing-output-binding",
        "wrong-output-binding",
        "missing-diagnostics-binding",
        "wrong-diagnostics-binding",
    ],
)
def test_consistently_rehashed_original_lane_evidence_cannot_waive_contract(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]],
    fault: str,
) -> None:
    root, _, original_bundle = genuine_lane
    bundle = copy.deepcopy(original_bundle)
    reader = SnapshotReader(root)
    spec_snapshot = reader.read(bundle["spec_artifact"]["path"])
    paths = {key: root / bundle[key + "_artifact"]["path"] for key in ("result", "process", "coordinator")}
    result, process, outer = [json.loads(paths[key].read_bytes()) for key in ("result", "process", "coordinator")]
    record = result["records"][0]
    paths.update(
        child=root / record["receipt_artifact"]["path"],
        native=root / record["process_artifact"]["path"],
        original=root / outer["bundle_artifact"]["path"],
        coverage_data=root
        / json.loads((root / record["receipt_artifact"]["path"]).read_bytes())["coverage_data_artifact"]["path"],
        coverage=root / result["coverage_artifact"]["path"],
    )
    saved = {key: path.read_bytes() for key, path in paths.items()}
    child, native = json.loads(saved["child"]), json.loads(saved["native"])
    if fault == "missing-member":
        child["nodeids"].pop()
    elif fault == "missing-teardown":
        child["reports"][child["nodeids"][0]].pop()
    elif fault == "unexpected-skip":
        child["reports"][child["nodeids"][0]][1][1] = "skipped"
    elif fault == "original-case-two":
        child["original_pytest_exit_code"] = 2
    elif fault == "bytecode-unverified":
        child["bytecode_verified"] = False
    elif fault == "case-timeout":
        child["timed_out"] = True
    elif fault in ("coverage-source", "coverage-arcs"):
        coverage_data = json.loads(saved["coverage_data"])
        if fault == "coverage-source":
            coverage_data["files"][0]["source_sha256"] = "b" * 64
        else:
            coverage_data["files"][0]["arcs"] = [[True, 1]]
    elif fault == "coverage-summary":
        coverage = json.loads(saved["coverage"])
        coverage["totals"]["covered_lines"] += 1
    elif fault == "child-native-seven":
        native["original_returncode"] = 7
    elif fault == "child-native-boolean":
        native["returncode"] = False
    elif fault == "child-timeout":
        native["timed_out"] = True
    elif fault == "wrong-child-command":
        native["command"].append("--not-original")
    elif fault == "missing-output-binding":
        native.pop("output_artifact")
    elif fault == "wrong-output-binding":
        native["output_artifact"] = child["diagnostics_artifact"]
    elif fault == "missing-diagnostics-binding":
        child.pop("diagnostics_artifact")
    elif fault == "wrong-diagnostics-binding":
        child["diagnostics_artifact"] = native["output_artifact"]
    elif fault == "wrong-plan":
        result["plan_sha256"] = "b" * 64
    elif fault == "wrong-source":
        child["source_identity"] = "b" * 64
    elif fault == "extra-result-field":
        result["waived"] = True
    elif fault == "wrong-outer-run":
        outer["run_id"] = "b" * 32
    elif fault == "boolean-outer-zero":
        outer["returncode"] = False
    elif fault == "extra-outer-field":
        outer["waived"] = True
    elif fault == "impossible-outer-timeline":
        outer["duration_seconds"] = outer["admission_duration_seconds"] / 2
    elif fault == "impossible-worker-timeline":
        result["duration_seconds"] = process["duration_seconds"]
    else:
        native["duration_seconds"] = result["duration_seconds"] + 1
    try:
        if fault in ("coverage-source", "coverage-arcs"):
            child["coverage_data_artifact"] = write_json(root, paths["coverage_data"], coverage_data)
        if fault == "coverage-summary":
            result["coverage_artifact"] = write_json(root, paths["coverage"], coverage)
        record["receipt_artifact"] = write_json(root, paths["child"], child)
        native["receipt_artifact"] = record["receipt_artifact"]
        if fault != "wrong-child-command":
            native["command"] = list(lane_command(root, spec_snapshot, chunk=0))
        record["process_artifact"] = write_json(root, paths["native"], native)
        bundle["result_artifact"] = write_json(root, paths["result"], result)
        process["result_artifact"] = bundle["result_artifact"]
        bundle["process_artifact"] = write_json(root, paths["process"], process)
        outer["bundle_artifact"] = write_json(
            root, paths["original"], {key: value for key, value in bundle.items() if key != "coordinator_artifact"}
        )
        outer["command"] = list(coordinator_command(root, spec_snapshot))
        bundle["coordinator_artifact"] = write_json(root, paths["coordinator"], outer)
        with pytest.raises(ValueError):
            read_lane(SnapshotReader(root), bundle)
    finally:
        for key, path in paths.items():
            path.write_bytes(saved[key])


@pytest.mark.parametrize(
    "fault", ["extra-declaration", "wrong-policy-path", "missing-prerequisite", "credential-in-core-tool"]
)
def test_actual_source_owned_policy_and_prerequisites_cannot_be_replaced(
    genuine_lane: tuple[Path, dict[str, Any], dict[str, Any]],
    fault: str,
) -> None:
    root, _, _ = genuine_lane
    metadata = root / "pyproject.toml"
    prerequisites = root / "infrastructure/config/root-case-prerequisites.json"
    originals = {metadata: metadata.read_bytes(), prerequisites: prerequisites.read_bytes()}
    try:
        if fault == "extra-declaration":
            metadata.write_bytes(originals[metadata] + b"waived=true\n")
        elif fault == "wrong-policy-path":
            metadata.write_bytes(
                originals[metadata].replace(b"infrastructure/config/root-case-policy.json", b"../root-case-policy.json")
            )
        else:
            value = json.loads(originals[prerequisites])
            if fault == "missing-prerequisite":
                value["obligations"] = []
            else:
                value["obligations"][0]["environment_keys"] = ["UNRELATED_API_KEY"]
            prerequisites.write_text(json.dumps(value), encoding="utf-8")
        with pytest.raises(ValueError):
            load_policy(SnapshotReader(root))
    finally:
        for path, original in originals.items():
            path.write_bytes(original)

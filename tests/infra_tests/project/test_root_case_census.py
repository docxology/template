"""Canonical collector controls use actual owned source and original child evidence."""

from __future__ import annotations

import copy
import sys
from dataclasses import asdict
import json
import os
import time
import subprocess
import threading
import signal
import uuid
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_acceptance_case_observer import RootCaseObserver
from infrastructure.project.public_acceptance_case_policy import POLICY_SCHEMA, RootCasePolicy
from infrastructure.project.public_root_case_census import produce_root_census
from infrastructure.project.public_root_case_readback import read_root_census
from infrastructure.project.public_root_case_contract import census_command
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

pytestmark = pytest.mark.timeout(240)


def _produce_control(root: Path, directory: Path, timeout_seconds: int) -> dict[str, Any]:
    """An owned non-Git fixture explicitly nominates its deterministic build epoch."""
    names = ("SOURCE_DATE_EPOCH", "TEMPLATE_BUILD_EPOCH_SOURCE")
    original = {name: os.environ.get(name) for name in names}
    try:
        os.environ.update(SOURCE_DATE_EPOCH="0", TEMPLATE_BUILD_EPOCH_SOURCE="explicit-owned-control")
        return produce_root_census(root, directory, timeout_seconds=timeout_seconds)
    finally:
        for name, value in original.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


@pytest.fixture(scope="module")
def genuine_census(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any], RootCasePolicy]:
    root = tmp_path_factory.mktemp("canonical-root-census").resolve()
    (root / "tests").mkdir()
    marker = root / "body-executed"
    (root / "pyproject.toml").write_text(
        '[project]\nname="owned-root-census-control"\nversion="0.1.0"\nrequires-python=">=3.12"\n'
        '[tool.pytest.ini_options]\naddopts=[]\nmarkers=["requires_ollama: declared local-model contract"]\n',
        encoding="utf-8",
    )
    (root / "tests/conftest.py").write_text(
        "from pathlib import Path\nimport pytest\n@pytest.fixture(autouse=True)\ndef owned_fixture():\n"
        f"    Path({str(marker)!r}).write_text('fixture executed')\n",
        encoding="utf-8",
    )
    (root / "tests/test_owned.py").write_text(
        "from pathlib import Path\nimport pytest\n"
        "@pytest.mark.parametrize('number',[1,2],ids=['one','two'])\ndef test_core(number):\n"
        f"    Path({str(marker)!r}).write_text('case executed')\n    assert number>0\n"
        "@pytest.mark.requires_ollama\nclass TestLive:\n"
        "    def test_model(self): raise AssertionError('collection cannot execute this body')\n",
        encoding="utf-8",
    )
    bundle = _produce_control(root, root / "output/readiness/original", timeout_seconds=180)
    assert bundle["exit_code"] == 0, bundle
    candidate = json.loads((root / bundle["receipt_artifact"]["path"]).read_bytes())["census"]
    assignments = {"tests/test_owned.py::test_core": "core", "tests/test_owned.py::TestLive::test_model": "live-unpaid"}
    assert {family["id"] for family in candidate["families"]} == set(assignments)
    policy = RootCasePolicy.parse(
        {
            "schema_version": POLICY_SCHEMA,
            "runtimes": ["3.12", "3.13", "3.14"],
            "platforms": ["darwin", "linux"],
            "obligations": [{"id": "owned-local-model", "kind": "local-model", "eligibility": None}],
            "families": [
                {key: row[key] for key in ("id", "members", "source_sha256", "metadata_sha256")}
                | {
                    "lane": assignments[row["id"]],
                    "obligations": ["owned-local-model"] if assignments[row["id"]] == "live-unpaid" else [],
                }
                for row in candidate["families"]
            ],
        }
    )
    census = read_root_census(SnapshotReader(root), bundle, policy)
    assert len(census["nodeids"]) == 3 and len(census["families"]) == 2
    assert not marker.exists(), "the actual collector must invoke neither fixture nor test body"
    return root, bundle, policy


def test_genuine_census_readback_preserves_original_process_and_source(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy],
) -> None:
    root, bundle, policy = genuine_census
    process = json.loads((root / bundle["process_artifact"]["path"]).read_text())
    receipt = json.loads((root / bundle["receipt_artifact"]["path"]).read_text())
    assert process["returncode"] == process["original_returncode"] == 0
    assert process["timed_out"] is process["custody_refused"] is False
    assert receipt["original_pytest_exit_code"] == receipt["exit_code"] == receipt["executed_reports"] == 0
    assert receipt["bytecode_verified"] is True and receipt["interrupted"] is False
    assert receipt["role"] == "canonical-collection-only"


def test_readback_observes_actual_implementation_once_per_current_boundary(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy],
) -> None:
    from infrastructure.core.implementation_custody import capture_implementation_custody

    root, bundle, policy = genuine_census
    actual_code = capture_implementation_custody.__code__
    calls = 0
    original_profiler = sys.getprofile()

    def count_actual_call(frame: Any, event: str, argument: Any) -> None:
        nonlocal calls
        if event == "call" and frame.f_code is actual_code:
            calls += 1
        if original_profiler is not None:
            original_profiler(frame, event, argument)

    try:
        sys.setprofile(count_actual_call)
        census = read_root_census(SnapshotReader(root), bundle, policy)
    finally:
        sys.setprofile(original_profiler)
    assert len(census["nodeids"]) == 3
    assert calls == 1, "source/runtime/distribution are captured once at this actual reader boundary"


def test_genuine_plain_reader_preserves_original_worker_bytecode_plane(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy],
) -> None:
    import infrastructure

    root, bundle, policy = genuine_census
    provider = Path(infrastructure.__file__).resolve()
    inputs = root / "output/readiness/plain-reader-inputs.json"
    inputs.write_text(
        json.dumps(
            {
                "bundle": bundle,
                "policy": {
                    "schema_version": POLICY_SCHEMA,
                    "runtimes": list(policy.runtimes),
                    "platforms": list(policy.platforms),
                    "families": [asdict(family) for family in policy.families],
                    "obligations": [asdict(obligation) for obligation in policy.obligations],
                },
            }
        ),
        encoding="utf-8",
    )
    script = (
        "import sys,json;from pathlib import Path;"
        f"sys.path.insert(0,{str(provider.parent.parent)!r});import infrastructure;"
        f"assert Path(infrastructure.__file__).resolve()==Path({str(provider)!r});"
        "assert sys.pycache_prefix is None;"
        "from infrastructure.core.implementation_custody import capture_implementation_custody;"
        "from infrastructure.project.public_root_case_contract import _spec;"
        "from infrastructure.project.public_root_case_readback import read_root_census;"
        "from infrastructure.project.public_acceptance_case_policy import RootCasePolicy;"
        "from infrastructure.reporting.release_readiness_snapshot import SnapshotReader;"
        f"root=Path({str(root)!r});value=json.loads(Path({str(inputs)!r}).read_bytes());"
        "reader=SnapshotReader(root);binding=value['bundle']['spec_artifact'];snapshot=reader.read(binding['path']);"
        "spec=json.loads(snapshot.content);assert spec['implementation']['bytecode_binding']=='fresh-owned-prefix';"
        "actual=capture_implementation_custody();assert actual['bytecode_binding']=='loaded-baseline';"
        "assert actual==dict(spec['implementation'],bytecode_binding='loaded-baseline');"
        "policy=RootCasePolicy.parse(value['policy']);"
        "census=read_root_census(reader,value['bundle'],policy);assert len(census['nodeids'])==3;"
        "print('actual-plain-reader-pass');\n"
        "try:\n    _spec(SnapshotReader(root),snapshot)\n"
        "except ValueError as error:\n    assert 'fresh audited launcher' in str(error)\n"
        "else:\n    raise AssertionError('plain controller must not impersonate audited census worker')\n"
    )
    observed = subprocess.run(
        [sys.executable, "-I", "-c", script], cwd=root, capture_output=True, text=True, timeout=90, check=False
    )
    assert observed.returncode == 0, observed.stderr
    assert observed.stdout.strip() == "actual-plain-reader-pass"


@pytest.mark.parametrize(
    "fault",
    [
        "missing-source-file",
        "wrong-source",
        "wrong-implementation",
        "wrong-implementation-runtime",
        "wrong-implementation-distribution",
        "original-bytecode-baseline",
        "original-bytecode-unknown",
        "wrong-root-inode",
        "wrong-command",
        "boolean-process-zero",
        "expired-budget",
        "wrong-receipt-role",
        "collection-skip",
        "executed-body",
        "case-origin",
        "runtime-fixture-origin",
        "missing-case-metadata",
        "wrong-normalized-census",
        "wrong-run",
        "wrong-coordinator-command",
        "boolean-coordinator-zero",
        "expired-coordinator-budget",
        "wrong-remaining-launch-budget",
        "impossible-outer-timeline",
        "impossible-inner-timeline",
        "extra-process-field",
        "extra-receipt-field",
        "extra-coordinator-field",
        "removed-genuine-marker",
        "removed-genuine-fixture",
        "removed-case-and-nodeid",
    ],
)
def test_consistently_rehashed_evidence_still_cannot_waive_original_contract(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy],
    fault: str,
) -> None:
    root, admitted, policy = genuine_census
    bundle = copy.deepcopy(admitted)
    paths = {kind: root / bundle[kind + "_artifact"]["path"] for kind in ("spec", "process", "receipt", "coordinator")}
    outer = json.loads(paths["coordinator"].read_bytes())
    paths["bundle"] = root / outer["bundle_artifact"]["path"]
    original = {kind: path.read_bytes() for kind, path in paths.items()}
    values = {kind: json.loads(raw) for kind, raw in original.items()}
    spec, process, receipt, outer = values["spec"], values["process"], values["receipt"], values["coordinator"]
    if fault == "missing-source-file":
        spec["test_files"] = []
    elif fault == "wrong-source":
        spec["source_identity"] = "b" * 64
    elif fault == "wrong-implementation":
        spec["implementation"]["files"]["infrastructure/__init__.py"] = "b" * 64
    elif fault == "wrong-implementation-runtime":
        spec["implementation"]["runtime_environment"]["python_sha256"] = "b" * 64
    elif fault == "wrong-implementation-distribution":
        if spec["implementation"]["distribution"] is None:
            spec["implementation"]["distribution"] = {"name": "invented-distribution"}
        else:
            spec["implementation"]["distribution"]["metadata_sha256"] = "b" * 64
    elif fault == "original-bytecode-baseline":
        spec["implementation"]["bytecode_binding"] = "loaded-baseline"
    elif fault == "original-bytecode-unknown":
        spec["implementation"]["bytecode_binding"] = "invented-bytecode-plane"
    elif fault == "wrong-root-inode":
        spec["root_identity"][1] += 1
    elif fault == "wrong-command":
        process["command"].append("--not-original")
    elif fault == "boolean-process-zero":
        process["returncode"] = False
    elif fault == "expired-budget":
        process["duration_seconds"] = spec["timeout_seconds"]
    elif fault == "wrong-receipt-role":
        receipt["role"] = "runtime-acceptance"
    elif fault == "collection-skip":
        receipt["collection_skips"] = ["tests/test_owned.py"]
    elif fault == "executed-body":
        receipt["executed_reports"] = 1
    elif fault == "case-origin":
        receipt["cases"][0]["function_origin"]["sha256"] = "b" * 64
    elif fault == "runtime-fixture-origin":
        origins = [
            definition["origin"]
            for case in receipt["cases"]
            for definitions in case["fixtures"].values()
            for definition in definitions
            if definition["origin"]["scope"].startswith("runtime-")
        ]
        assert origins, "the genuine selected pytest provider fixture must be observed"
        origins[0]["sha256"] = "b" * 64
    elif fault == "missing-case-metadata":
        receipt["cases"].pop()
    elif fault == "wrong-normalized-census":
        receipt["census"]["families"][0]["metadata_sha256"] = "b" * 64
    elif fault == "wrong-run":
        receipt["run_id"] = "b" * 32
    elif fault == "wrong-coordinator-command":
        outer["command"].append("--not-original")
    elif fault == "boolean-coordinator-zero":
        outer["returncode"] = False
    elif fault == "expired-coordinator-budget":
        outer["duration_seconds"] = spec["timeout_seconds"]
    elif fault == "wrong-remaining-launch-budget":
        outer["launch_budget_seconds"] += 1
    elif fault == "impossible-outer-timeline":
        outer["duration_seconds"] = outer["admission_duration_seconds"] / 2
    elif fault == "impossible-inner-timeline":
        process["duration_seconds"] = outer["duration_seconds"]
    elif fault == "extra-process-field":
        process["waived"] = True
    elif fault == "extra-receipt-field":
        receipt["waived"] = True
    elif fault == "extra-coordinator-field":
        outer["waived"] = True
    elif fault == "removed-genuine-marker":
        marked = next(
            case for case in receipt["cases"] if any(mark["name"] == "requires_ollama" for mark in case["markers"])
        )
        marked["markers"] = [mark for mark in marked["markers"] if mark["name"] != "requires_ollama"]
    elif fault == "removed-genuine-fixture":
        assert receipt["cases"][0]["fixtures"]["owned_fixture"]
        receipt["cases"][0]["fixtures"]["owned_fixture"] = []
    else:
        removed = receipt["cases"].pop(0)
        receipt["nodeids"].remove(removed["nodeid"])
    if fault.startswith("removed-"):
        normalizer = RootCaseObserver(SnapshotReader(root), spec["source_hashes"])
        normalizer.cases, normalizer.nodeids = receipt["cases"], receipt["nodeids"]
        receipt["census"] = normalizer.census(
            source_identity=spec["source_identity"],
            runtime=spec["runtime"]["python_version"],
            platform=receipt["census"]["platform"],
        )
    try:
        bundle["spec_artifact"] = write_json(root, paths["spec"], spec)
        process["spec_artifact"] = receipt["spec_artifact"] = bundle["spec_artifact"]
        if fault != "wrong-command":
            process["command"] = list(census_command(root, paths["spec"].parent, bundle["spec_artifact"]))
        bundle["receipt_artifact"] = write_json(root, paths["receipt"], receipt)
        process["receipt_artifact"] = bundle["receipt_artifact"]
        bundle["process_artifact"] = write_json(root, paths["process"], process)
        original_bundle = {key: value for key, value in bundle.items() if key != "coordinator_artifact"}
        outer["bundle_artifact"] = write_json(root, paths["bundle"], original_bundle)
        bundle["coordinator_artifact"] = write_json(root, paths["coordinator"], outer)
        with pytest.raises((OSError, ValueError)):
            read_root_census(SnapshotReader(root), bundle, policy)
    finally:
        for kind, path in paths.items():
            path.write_bytes(original[kind])


def test_actual_source_edit_after_collection_refuses_census(
    genuine_census: tuple[Path, dict[str, Any], RootCasePolicy],
) -> None:
    root, bundle, policy = genuine_census
    source = root / "tests/test_owned.py"
    original = source.read_bytes()
    try:
        source.write_bytes(original + b"\n# genuine source mutation after the actual collection\n")
        with pytest.raises(ValueError):
            read_root_census(SnapshotReader(root), bundle, policy)
    finally:
        source.write_bytes(original)


@pytest.mark.parametrize("original_exit", [0, 2, 7])
def test_real_collection_process_exit_without_receipt_cannot_pass(
    tmp_path: Path, original_exit: int, genuine_census: tuple[Path, dict[str, Any], RootCasePolicy]
) -> None:
    policy = genuine_census[2]
    root = tmp_path.resolve()
    (root / "tests").mkdir()
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts=[]\n", encoding="utf-8")
    (root / "tests/conftest.py").write_text(f"import os\nos._exit({original_exit})\n", encoding="utf-8")
    (root / "tests/test_original.py").write_text("def test_original(): assert True\n", encoding="utf-8")
    bundle = _produce_control(root, root / "output/readiness/native-exit", timeout_seconds=120)
    assert bundle["exit_code"] == 1
    process = json.loads((root / bundle["process_artifact"]["path"]).read_bytes())
    assert process["original_returncode"] == original_exit
    assert bundle["receipt_artifact"] is None
    with pytest.raises(ValueError):
        read_root_census(SnapshotReader(root), bundle, policy)


def test_whole_collection_deadline_kills_actual_detached_import_descendant(
    tmp_path: Path, genuine_census: tuple[Path, dict[str, Any], RootCasePolicy]
) -> None:
    policy = genuine_census[2]
    root = tmp_path.resolve()
    (root / "tests").mkdir()
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts=[]\n", encoding="utf-8")
    reached, startup, escaped = (
        root / "actual-import-reached",
        root / "actual-descendant-startup.json",
        root / "detached-descendant-escaped",
    )
    # The retained 2026-10-05 successful fixture took 109.96s under measured
    # host contention; native non-receipt cases took up to 50.06s. A 30s outer
    # cap did not reach collection. This finite control allowance includes cold
    # admission; the longer import/child waits cannot finish within that cap.
    whole_timeout_seconds = 120
    token = uuid.uuid4().hex
    descendant = (
        "import os,sys,json,time;from pathlib import Path;"
        f"Path({str(startup)!r}).write_text(json.dumps({{'pid':os.getpid(),'token':sys.argv[1],'started_ns':time.monotonic_ns()}}));"
        f"time.sleep(300);Path({str(escaped)!r}).write_text('escaped')"
    )
    (root / "tests/test_waiting.py").write_text(
        "import subprocess,sys,time\nfrom pathlib import Path\n"
        f"subprocess.Popen([sys.executable,'-I','-c',{descendant!r},{token!r}],start_new_session=True)\n"
        f"Path({str(reached)!r}).write_text('actual collected source imported')\n"
        "time.sleep(360)\ndef test_waiting(): assert True\n",
        encoding="utf-8",
    )
    live: list[int] = []
    errors: list[str] = []
    stop = threading.Event()
    monitor_deadline = time.monotonic() + whole_timeout_seconds + 2

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
            raise ValueError("native process observation did not establish exact owned PID/token identity")
        if not fields[1].startswith("Z") and (len(fields) != 3 or token not in fields[2]):
            raise ValueError("native executable process differs from the actual controlled child token")
        return fields[1]

    def observe_actual_startup() -> None:
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
                    raise ValueError("descendant startup identity differs from its actual owned invocation")
                state = native_state(pid)
                if state is not None and not state.startswith("Z"):
                    live.append(pid)
                    return
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                errors.append(type(error).__name__)
                return
            stop.wait(0.02)

    monitor = threading.Thread(target=observe_actual_startup)
    monitor.start()
    started = time.monotonic()
    try:
        bundle = _produce_control(root, root / "output/readiness/deadline", timeout_seconds=whole_timeout_seconds)
        stop.set()
        monitor.join(timeout=7)
        assert not monitor.is_alive() and not errors
        assert bundle["exit_code"] == 124
        assert time.monotonic() - started < whole_timeout_seconds + 15
        assert reached.exists(), "deadline exhausted before actual import; descendant cleanup remains unproven"
        assert reached.read_text() == "actual collected source imported"
        assert live, "native observation must prove the genuine detached descendant was alive before timeout"
        state = native_state(live[0])
        assert state is None or state.startswith("Z"), "actual detached child remains executable"
        assert not escaped.exists()
        with pytest.raises(ValueError):
            read_root_census(SnapshotReader(root), bundle, policy)
    finally:
        stop.set()
        monitor.join(timeout=7)
        # On a failed cleanup assertion, kill only the still-owned controlled child.
        if startup.exists():
            actual = json.loads(startup.read_bytes())
            if actual.get("token") == token and type(actual.get("pid")) is int:
                pid = actual["pid"]
                state = native_state(pid)
                if state is not None and not state.startswith("Z"):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

"""Genuine selected-runtime cohort and original-reader controls; separate from production acceptance."""

from __future__ import annotations

import copy
import json
import os
import signal
import subprocess
import threading
import time
import sys
import shutil
import tomllib
import uuid
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.public_acceptance import _probe_runtime
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_root_case_admission import load_policy
from infrastructure.project.public_root_case_contract import _root_identity, _json
from infrastructure.project.public_root_lane_contract import write
from infrastructure.project.public_root_runtime_producer import produce_runtime_cohort, read_selected_runtime
from infrastructure.project.public_root_case_acceptance import run_root_case_acceptance
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.public_root_runtime_readback import read_runtime_cohort
from infrastructure.project.public_root_runtime_worker import coordinate, lane_blockers
from infrastructure.reporting.release_readiness_root_cases import case_requirements, validate_root_cases
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project import test_root_case_lanes as lane_controls

# These real nested coordinator/census/case acceptance controls belong in the
# existing explicit slow lane; they do not alter ordinary CI's marker policy.
pytestmark = [pytest.mark.slow, pytest.mark.timeout(2400)]


@pytest.fixture(scope="module")
def genuine_runtime(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    root, _, _ = lane_controls.genuine_lane.__wrapped__(tmp_path_factory)
    probe = _probe_runtime(
        root,
        root / "output/readiness/runtime-probe",
        f"{sys.version_info.major}.{sys.version_info.minor}",
        Path(sys.executable),
    )
    assert probe["status"] == "pass", probe
    before = (root / "output/readiness/events.txt").read_bytes()
    produced = lane_controls._epoch_call(
        produce_runtime_cohort,
        root,
        root / "output/readiness/runtime-cohort",
        interpreter=Path(sys.executable),
        runtime_probe=probe["runtime"],
        timeout_seconds=720,
        census_timeout_seconds=180,
        test_timeout_seconds=60,
    )
    assert produced["bundle"]["exit_code"] == 0, produced
    observed = read_runtime_cohort(SnapshotReader(root), produced["bundle"])
    assert observed["passed_counts"] == {"core": 2}
    assert observed["selected_units"] == ["core"]
    assert (root / "output/readiness/events.txt").read_bytes()[len(before) :].decode().splitlines() == [
        "setup",
        "call",
        "teardown",
    ] * 2
    assert not (root / "output/readiness/live-body").exists()
    return root, produced, probe


def test_original_selected_interpreter_collects_once_and_retains_every_required_cell(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, produced, _ = genuine_runtime
    bundle = produced["bundle"]
    native = json.loads((root / bundle["process_artifact"]["path"]).read_bytes())
    assert native["returncode"] == native["original_returncode"] == 0
    assert native["timed_out"] is native["custody_refused"] is False
    observed = read_runtime_cohort(SnapshotReader(root), bundle)
    assert {(cell["platform"], cell["runtime"]) for cell in observed["required_cells"]} == {
        (platform, runtime) for platform in ("darwin", "linux") for runtime in ("3.12", "3.13", "3.14")
    }
    actual = json.loads((root / bundle["result_artifact"]["path"]).read_bytes())
    census_bundle = json.loads((root / actual["census_bundle_artifact"]["path"]).read_bytes())
    census = _json(SnapshotReader(root).read(census_bundle["receipt_artifact"]["path"]))
    assert census["original_pytest_exit_code"] == census["exit_code"] == census["executed_reports"] == 0
    assert len(census["nodeids"]) == 3
    assert len(list((root / "output/readiness/runtime-cohort/census").rglob("census.json"))) == 1
    excluded = next(row for row in actual["units"] if row["unit"] == "live-unpaid")
    assert excluded["attempted"] is False and excluded["exit_code"] == 75 and excluded["bundle_artifact"] is None
    assert excluded["blockers"] == [{"id": "live-unpaid", "reason": "explicit-live-mode-required"}]


def test_actual_audited_selected_reader_verifies_original_interpreter_and_case_counts(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, produced, _ = genuine_runtime
    observed = read_selected_runtime(SnapshotReader(root), produced["bundle_artifact"])
    assert observed["runtime"]["executable"] == sys.executable
    assert observed["runtime"]["python_version"] == f"{sys.version_info.major}.{sys.version_info.minor}"
    assert observed["passed_counts"] == {"core": 2}
    assert observed["exit_code"] == 0


def test_source_owned_profile_declares_every_exact_case_unit_target_and_never_waives_live(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root = genuine_runtime[0]
    scope = RuntimeScope(root, "root")
    reader = SnapshotReader(root)
    policy, _, _, _ = load_policy(reader)
    rows = case_requirements(
        reader,
        version="0.1.0",
        package="owned-root-lane-control",
        fingerprint=scope.source_identity(),
        deliverables=scope.deliverables_identity(),
        source_files=(),
        test_files=scope.test_files(),
    )
    assert len(rows) == 13 and rows[0].id == "root:case-policy"
    assert {row.python_version for row in rows[1:]} == {"3.12", "3.13", "3.14"}
    assert {row.case_platform for row in rows[1:]} == {"darwin", "linux"}
    assert all(row.case_policy_sha256 == policy.sha256 for row in rows)
    assert {row.case_unit for row in rows[1:]} == {"core", "live-unpaid"}
    assert len({row.id for row in rows}) == len(rows)
    assert {unit.id for unit in scope.require_case_units(reader)} == {"core", "live-unpaid"}
    with pytest.raises(ValueError):
        scope.require_case_policy(reader)


@pytest.mark.parametrize(
    "fault",
    [
        "drop-required-live",
        "omit-core",
        "invent-unit",
        "wrong-minor",
        "wrong-host",
        "boolean-code",
        "impossible-timeline",
        "alter-coverage",
    ],
)
def test_consistently_rehashed_original_runtime_assertions_cannot_waive_source_owned_contract(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]],
    fault: str,
) -> None:
    root, produced, _ = genuine_runtime
    bundle = copy.deepcopy(produced["bundle"])
    native_path = root / bundle["process_artifact"]["path"]
    result_path = root / bundle["result_artifact"]["path"]
    saved = {native_path: native_path.read_bytes(), result_path: result_path.read_bytes()}
    native, result = json.loads(saved[native_path]), json.loads(saved[result_path])
    try:
        if fault == "drop-required-live":
            result["required_cells"] = [cell for cell in result["required_cells"] if cell["unit"] == "core"]
        elif fault == "omit-core":
            result["units"] = [row for row in result["units"] if row["unit"] != "core"]
        elif fault == "invent-unit":
            result["selected_units"].append("invented-success")
        elif fault == "wrong-minor":
            result["runtime"]["python_version"] = "3.12" if result["runtime"]["python_version"] != "3.12" else "3.13"
        elif fault == "wrong-host":
            result["platform"] = "linux" if result["platform"] == "darwin" else "darwin"
        elif fault == "boolean-code":
            result["exit_code"] = False
        elif fault == "impossible-timeline":
            native["admission_duration_seconds"] = native["duration_seconds"] + 1
        else:
            coverage_path = root / result["coverage_artifact"]["path"]
            saved[coverage_path] = coverage_path.read_bytes()
            coverage = json.loads(saved[coverage_path])
            coverage["totals"]["percent_covered"] = 100
            coverage["files"] = {}
            result["coverage_artifact"] = write(root, coverage_path, coverage, _root_identity(root))
        rebound = write(root, result_path, result, _root_identity(root))
        native["result_artifact"] = rebound
        bundle["result_artifact"] = rebound
        bundle["process_artifact"] = write(root, native_path, native, _root_identity(root))
        with pytest.raises(ValueError):
            read_runtime_cohort(SnapshotReader(root), bundle)
    finally:
        for path, raw in saved.items():
            path.write_bytes(raw)


@pytest.mark.parametrize("original_code", [0, 2, 7])
def test_real_case_exit_zero_two_seven_cannot_create_a_passing_runtime_cohort(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]],
    original_code: int,
) -> None:
    root, _, probe = genuine_runtime
    action = root / "output/readiness/action.json"
    try:
        action.write_text(json.dumps(original_code))
        produced = lane_controls._epoch_call(
            produce_runtime_cohort,
            root,
            root / ("output/readiness/case-exit-" + str(original_code)),
            interpreter=Path(sys.executable),
            runtime_probe=probe["runtime"],
            timeout_seconds=720,
            census_timeout_seconds=180,
            test_timeout_seconds=60,
        )
        assert produced["bundle"]["exit_code"] == 1, produced
        cohort = json.loads((root / produced["bundle"]["result_artifact"]["path"]).read_bytes())
        lane_row = next(row for row in cohort["units"] if row["unit"] == "core")
        lane = json.loads((root / lane_row["bundle_artifact"]["path"]).read_bytes())
        child = json.loads((root / lane["process_artifact"]["path"]).read_bytes())
        assert child["returncode"] == 1, "the real lane must refuse an original incomplete child"
        inner_result = json.loads((root / lane["result_artifact"]["path"]).read_bytes())
        chunk = inner_result["records"][0]
        native = json.loads((root / chunk["process_artifact"]["path"]).read_bytes())
        assert native["original_returncode"] == original_code
        with pytest.raises(ValueError):
            read_runtime_cohort(SnapshotReader(root), produced["bundle"])
    finally:
        action.unlink(missing_ok=True)


def test_actual_per_case_deadline_retains_original_pytest_failure_and_cohort_timeout(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, _, probe = genuine_runtime
    action = root / "output/readiness/action.json"
    try:
        action.write_text(json.dumps("case-deadline"))
        produced = lane_controls._epoch_call(
            produce_runtime_cohort,
            root,
            root / "output/readiness/cohort-case-timeout",
            interpreter=Path(sys.executable),
            runtime_probe=probe["runtime"],
            timeout_seconds=720,
            census_timeout_seconds=180,
            test_timeout_seconds=1,
        )
        assert produced["bundle"]["exit_code"] == 124, produced
        cohort = json.loads((root / produced["bundle"]["result_artifact"]["path"]).read_bytes())
        row = next(row for row in cohort["units"] if row["unit"] == "core")
        assert row["exit_code"] == 124 and (root / "output/readiness/case-deadline-reached").exists()
        with pytest.raises(ValueError):
            read_runtime_cohort(SnapshotReader(root), produced["bundle"])
    finally:
        action.unlink(missing_ok=True)
        (root / "output/readiness/case-deadline-reached").unlink(missing_ok=True)


@pytest.mark.parametrize("fault", ["expired-budget", "bad-mode", "wrong-interpreter", "wrong-runtime"])
def test_runtime_invocation_refuses_before_any_new_source_case_body(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]],
    fault: str,
) -> None:
    root, _, probe = genuine_runtime
    before = (root / "output/readiness/events.txt").read_bytes()
    runtime = copy.deepcopy(probe["runtime"])
    arguments: dict[str, Any] = {
        "interpreter": Path(sys.executable),
        "runtime_probe": runtime,
        "timeout_seconds": 720,
        "census_timeout_seconds": 180,
    }
    if fault == "expired-budget":
        arguments["timeout_seconds"] = 1
    elif fault == "bad-mode":
        arguments["mode"] = "ambient"
    elif fault == "wrong-interpreter":
        arguments["interpreter"] = Path(sys.executable).with_name("missing-prepared-interpreter")
    else:
        runtime["python_version"] = "0.0"
    with pytest.raises(ValueError):
        produce_runtime_cohort(root, root / ("output/readiness/invalid-" + uuid.uuid4().hex), **arguments)
    assert (root / "output/readiness/events.txt").read_bytes() == before


@pytest.mark.parametrize("action_name,expected_code", [("detached-timeout", 124), ("detached-interrupt", 130)])
def test_actual_runtime_whole_deadline_or_interruption_cleans_launched_detached_child(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]], action_name: str, expected_code: int
) -> None:
    root, _, probe = genuine_runtime
    whole_seconds = 300
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
        produced = lane_controls._epoch_call(
            produce_runtime_cohort,
            root,
            root / ("output/readiness/runtime-" + action_name),
            interpreter=Path(sys.executable),
            runtime_probe=probe["runtime"],
            census_timeout_seconds=180,
            timeout_seconds=whole_seconds,
            test_timeout_seconds=600,
        )
        bundle = produced["bundle"]
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
        outer = json.loads((root / bundle["process_artifact"]["path"]).read_bytes())
        if expected_code == 124:
            assert outer["timed_out"] is True or outer["returncode"] == 124
        else:
            assert outer["original_returncode"] == outer["returncode"] == 130
            assert outer["timed_out"] is False
        with pytest.raises(ValueError):
            read_runtime_cohort(SnapshotReader(root), bundle)
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


def test_actual_selected_reader_deadline_refuses_without_reexecuting_cases(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, produced, _ = genuine_runtime
    before = (root / "output/readiness/events.txt").read_bytes()
    with pytest.raises(TimeoutError):
        read_selected_runtime(SnapshotReader(root), produced["bundle_artifact"], timeout_seconds=1)
    assert (root / "output/readiness/events.txt").read_bytes() == before


@pytest.mark.parametrize("fault", ["packages", "interpreter-hash"])
def test_rehashed_actual_raw_probe_must_match_true_original_selected_runtime(
    genuine_runtime: tuple[Path, dict[str, Any], dict[str, Any]],
    fault: str,
) -> None:
    root, produced, probe = genuine_runtime
    reader = SnapshotReader(root)
    observed = read_runtime_cohort(reader, produced["bundle"])
    scope = RuntimeScope(root, "root")
    policy, _, _, _ = load_policy(reader)
    requirement = case_requirements(
        reader,
        version="0.1.0",
        package="owned-root-lane-control",
        fingerprint=scope.source_identity(),
        deliverables=scope.deliverables_identity(),
        source_files=(),
        test_files=scope.test_files(),
    )[0]
    details = {
        "root_case_bundle_artifact": produced["bundle_artifact"],
        "case_policy_sha256": policy.sha256,
        "policy_artifact_sha256": observed["policy_artifact"]["sha256"],
        "python_version": observed["runtime"]["python_version"],
        "interpreter": observed["runtime"]["executable"],
        "runtime_artifact": probe["binding"],
    }
    validate_root_cases(requirement, details, SnapshotReader(root))
    path = root / probe["binding"]["path"]
    original = path.read_bytes()
    raw = json.loads(original)
    try:
        if fault == "packages":
            raw["packages"]["pytest"] = "invented-compatible-version"
        else:
            raw["interpreter_sha256"] = "0" * 64
        rebound = write(root, path, raw, _root_identity(root))
        with pytest.raises(ValueError, match="stale policy/source/selected-runtime"):
            validate_root_cases(requirement, {**details, "runtime_artifact": rebound}, SnapshotReader(root))
    finally:
        path.write_bytes(original)


def test_whole_root_case_api_refuses_replacement_without_new_gate_probe_or_receipt_writes(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    root, _, _ = lane_controls.genuine_lane.__wrapped__(tmp_path_factory)
    source = Path(__file__).resolve().parents[3]
    # This is an explicitly partial owned Root fixture. Its metadata inputs are
    # exact copies of the selected public platform and exemplar declarations;
    # they do not prove exemplar algorithms or production Root acceptance.
    for name in (".python-version", "CHANGELOG.md", "infrastructure/_version.py"):
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, destination)
    actual = tomllib.loads((source / "pyproject.toml").read_text())["project"]
    metadata = (root / "pyproject.toml").read_text()
    metadata = metadata.replace('name="owned-root-lane-control"', "name=" + json.dumps(actual["name"]))
    metadata = metadata.replace('version="0.1.0"', "version=" + json.dumps(actual["version"]))
    (root / "pyproject.toml").write_text(metadata)
    for scope in PUBLIC_PROJECT_NAMES:
        for name in ("pyproject.toml", "manuscript/config.yaml"):
            destination = root / "projects" / scope / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / "projects" / scope / name, destination)
    saved = root.with_name(root.name + "-original-before-api-replacement")
    action = root / "output/readiness/action.json"
    try:
        action.write_text(json.dumps({"case": "root-replace", "saved": str(saved)}))
        with pytest.raises(RuntimeError, match="original Root evidence write refused"):
            lane_controls._epoch_call(
                run_root_case_acceptance,
                root,
                {f"{sys.version_info.major}.{sys.version_info.minor}": Path(sys.executable)},
                evidence_dir=root / "output/readiness/whole-api-replacement",
                timeout_seconds=720,
            )
        assert saved.is_dir() and root.is_dir(), "a genuine case must replace its owned Root"
        # The replacement is a same-content copy at the case boundary. No new
        # runtime/gate/final evidence may be added by the admitted API afterward.
        original_paths = {path.relative_to(saved) for path in saved.rglob("*") if path.is_file()}
        replacement_paths = {path.relative_to(root) for path in root.rglob("*") if path.is_file()}
        assert replacement_paths <= original_paths
        for relative in replacement_paths:
            assert (root / relative).read_bytes() == (saved / relative).read_bytes()
        assert not (root / "output/readiness/whole-api-replacement/receipt.json").exists()
        selected_directory = (
            root / "output/readiness/whole-api-replacement" / f"{sys.version_info.major}.{sys.version_info.minor}"
        )
        assert not list(selected_directory.rglob("*-gate.json"))
    finally:
        if saved.exists():
            shutil.rmtree(root)
            saved.rename(root)
        action.unlink(missing_ok=True)


def test_real_blocked_unit_then_original_executed_guard_failure_precedes_unavailable(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    root, _, _ = lane_controls.genuine_lane.__wrapped__(tmp_path_factory)
    policy_path = root / "infrastructure/config/root-case-policy.json"
    prerequisite_path = root / "infrastructure/config/root-case-prerequisites.json"
    policy = json.loads(policy_path.read_bytes())
    policy["obligations"].append({"id": "owned-required-unavailable-tool", "kind": "tool", "eligibility": None})
    for family in policy["families"]:
        if family["lane"] == "core":
            family["obligations"].append("owned-required-unavailable-tool")
    prerequisites = json.loads(prerequisite_path.read_bytes())
    prerequisites["obligations"].append(
        {
            "id": "owned-required-unavailable-tool",
            "kind": "tool",
            "environment_keys": [],
            "executables": ["template-owned-intentionally-unavailable-tool-for-case-control"],
            "platforms": [],
        }
    )
    policy_path.write_text(json.dumps(policy))
    prerequisite_path.write_text(json.dumps(prerequisites))
    probe = _probe_runtime(
        root,
        root / "output/readiness/blocked-guard-probe",
        f"{sys.version_info.major}.{sys.version_info.minor}",
        Path(sys.executable),
    )
    assert probe["status"] == "pass"
    original = lane_controls._epoch_call(
        produce_runtime_cohort,
        root,
        root / "output/readiness/original-blocked-cohort",
        interpreter=Path(sys.executable),
        runtime_probe=probe["runtime"],
        timeout_seconds=720,
        census_timeout_seconds=180,
        test_timeout_seconds=60,
    )
    assert original["bundle"]["exit_code"] == 75, original
    actual = json.loads((root / original["bundle"]["result_artifact"]["path"]).read_bytes())
    assert next(row for row in actual["units"] if row["unit"] == "core")["exit_code"] == 75
    spec = json.loads((root / original["bundle"]["spec_artifact"]["path"]).read_bytes())
    spec["directory"] = "output/readiness/blocked-then-executed-failure"
    spec["run_id"], spec["nonce"] = uuid.uuid4().hex, uuid.uuid4().hex
    binding = write(root, root / spec["directory"] / "runtime-spec.json", spec, _root_identity(root))
    source = root / "tests/test_owned.py"
    saved = source.read_bytes()
    seen = []
    previous = sys.getprofile()

    def actual_observation(frame: Any, event: str, value: Any) -> None:
        # Observe the real function return; preserve its actual original result.
        # This hook replaces no dependency or implementation. The independent
        # worker entrypoint remains the exact source-owned code under test.
        if frame.f_code is lane_blockers.__code__ and event == "return" and value and not seen:
            seen.append(copy.deepcopy(value))
            source.write_bytes(saved + b"\n# actual owned source mutation after unavailable unit observation\n")

    try:
        sys.setprofile(actual_observation)
        code = lane_controls._epoch_call(coordinate, root, root / binding["path"], binding["sha256"])
        assert code == 1
        assert seen and source.read_bytes() != saved
        current = json.loads((root / spec["directory"] / "runtime-cell.json").read_bytes())
        assert current["exit_code"] == 1 and current["diagnostic"]
        assert next(row for row in current["units"] if row["unit"] == "core")["exit_code"] == 75
        assert not (root / "output/readiness/live-body").exists()
    finally:
        sys.setprofile(previous)
        source.write_bytes(saved)

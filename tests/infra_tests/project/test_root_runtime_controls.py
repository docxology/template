"""Distinct actual lock, exit, coverage and replay controls for the current Root path."""

from __future__ import annotations

import copy
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.project.public_acceptance import _probe_runtime
from infrastructure.project.public_acceptance_case_policy import POLICY_SCHEMA
from infrastructure.project.public_acceptance_evidence import cell_environment, write_json
from infrastructure.project.public_root_case_admission import load_policy
from infrastructure.project.public_root_case_census import produce_root_census
from infrastructure.project.public_root_case_contract import _json
from infrastructure.project.public_root_lane_producer import produce_root_lane
from infrastructure.project.public_root_runtime_producer import produce_runtime_cohort
from infrastructure.project.public_root_runtime_readback import read_runtime_cohort
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance
from tests.infra_tests.project.test_root_case_lanes import _epoch_call
from tests.infra_tests.reporting.test_required_readiness import _declarations

pytestmark = [pytest.mark.slow, pytest.mark.timeout(1200)]

_TEST = """import importlib.util
from pathlib import Path

def test_owned_root_branches():
    root = Path(__file__).resolve().parents[1]
    path = root / 'infrastructure/probe.py'
    spec = importlib.util.spec_from_file_location('_owned_root_probe', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.score(True) == 1
    assert module.score(False) == 0
    (root / 'output/readiness/actual-case.txt').write_text('actual owned case')
"""


def _prepared_root(root: Path, *, conftest: str = "", interrupted: bool = False) -> None:
    _declarations(root)
    (root / "tests/test_source_declaration.py").unlink()
    (root / "tests/test_owned.py").write_text(
        _TEST + ("    raise KeyboardInterrupt('owned interrupted child')\n" if interrupted else "")
    )
    (root / "conftest.py").write_text(conftest)
    module = "def score(value):\n    if value:\n        return 1\n    return 0\n"
    (root / "infrastructure/probe.py").write_text(module)
    with (root / "pyproject.toml").open("a") as stream:
        stream.write(
            '[tool.coverage.run]\nbranch=true\nsource=["infrastructure"]\nomit=["infrastructure/_version.py"]\n'
        )
    initial = _epoch_call(produce_root_census, root, root / "output/readiness/authoring", timeout_seconds=180)
    assert initial["exit_code"] == 0, initial
    actual = _json(SnapshotReader(root).read(initial["receipt_artifact"]["path"]))["census"]
    policy = {
        "schema_version": POLICY_SCHEMA,
        "runtimes": ["3.14", "3.15"],
        "platforms": ["darwin", "linux"],
        "obligations": [],
        "families": [
            {key: family[key] for key in ("id", "members", "source_sha256", "metadata_sha256")}
            | {"lane": "core", "obligations": []}
            for family in actual["families"]
        ],
    }
    (root / "infrastructure/config/root-case-policy.json").write_text(json.dumps(policy))
    assert not (root / "output/readiness/actual-case.txt").exists()


def _cohort(root: Path) -> tuple[dict, dict]:
    probe = _probe_runtime(
        root,
        root / "output/readiness/probe",
        f"{sys.version_info.major}.{sys.version_info.minor}",
        Path(sys.executable),
    )
    assert probe["status"] == "pass", probe
    produced = _epoch_call(
        produce_runtime_cohort,
        root,
        root / "output/readiness/runtime",
        interpreter=Path(sys.executable),
        runtime_probe=probe["runtime"],
        timeout_seconds=720,
        census_timeout_seconds=180,
        test_timeout_seconds=60,
    )
    return produced, probe


@pytest.fixture(scope="module")
def actual_runtime(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict, dict]:
    root = tmp_path_factory.mktemp("root-runtime-controls").resolve()
    _prepared_root(root)
    produced, probe = _cohort(root)
    assert produced["bundle"]["exit_code"] == 0, produced
    assert (root / "output/readiness/actual-case.txt").read_text() == "actual owned case"
    return root, produced, probe


def test_actual_early_zero_root_child_cannot_replay_complete_previous_receipts(actual_runtime) -> None:
    root, produced, _ = actual_runtime
    bundle = copy.deepcopy(produced["bundle"])
    original = json.loads((root / bundle["process_artifact"]["path"]).read_text())
    command = list(original["command"])
    command[command.index("-c") + 1] = "raise SystemExit(0)\n" + command[command.index("-c") + 1]
    task = ProjectTestTask(
        0,
        "owned-early-zero",
        tuple(command),
        root,
        cell_environment(Path(command[0]), root / "output/readiness/early-zero", repo_root=root),
        60,
        True,
    )
    observed = run_project_test_matrix([task], workers=1)[0]
    assert observed.returncode == 0 and not observed.timed_out
    original.update(
        command=command,
        returncode=observed.returncode,
        original_returncode=observed.returncode,
        timed_out=observed.timed_out,
    )
    bundle["process_artifact"] = write_json(root, root / "output/readiness/early-zero/process.json", original)
    # The complete earlier successful census, case, coverage and receipt tree remains in place.
    with pytest.raises(ValueError):
        read_runtime_cohort(SnapshotReader(root), bundle)


def test_root_coverage_cannot_fall_back_to_generic_case_receipts(actual_runtime) -> None:
    from infrastructure.project.public_root_case_acceptance import _details

    root, produced, probe = actual_runtime
    observed = read_runtime_cohort(SnapshotReader(root), produced["bundle"])
    policy, _, _, _ = load_policy(SnapshotReader(root))
    requirements, faults = required_profile(root, SnapshotReader(root), source_fingerprint(root))
    assert not faults
    requirement = replace(
        next(item for item in requirements if item.id == "root:coverage"),
        python_version=probe["runtime"]["python_version"],
    )
    details = _details(probe, produced["bundle_artifact"], observed, policy.sha256)
    details.update(
        coverage_artifact=observed["coverage_artifact"],
        branch_coverage=True,
        percent=observed["coverage"]["totals"]["percent_covered"],
    )
    details.pop("root_case_bundle_artifact")
    with pytest.raises(ValueError, match="complete case-policy runtime bundle"):
        validate_acceptance(requirement, {"details": details}, SnapshotReader(root))


def test_actual_root_branch_coverage_below_sixty_refuses_success(actual_runtime) -> None:
    from infrastructure.project.public_root_case_acceptance import _details

    root, produced, probe = actual_runtime
    observed = read_runtime_cohort(SnapshotReader(root), produced["bundle"])
    assert observed["coverage"]["totals"]["percent_covered"] < 60
    policy, _, _, _ = load_policy(SnapshotReader(root))
    requirements, faults = required_profile(root, SnapshotReader(root), source_fingerprint(root))
    assert not faults
    requirement = replace(
        next(item for item in requirements if item.id == "root:coverage"),
        python_version=probe["runtime"]["python_version"],
    )
    details = _details(probe, produced["bundle_artifact"], observed, policy.sha256)
    details.update(
        coverage_artifact=observed["coverage_artifact"],
        branch_coverage=True,
        percent=observed["coverage"]["totals"]["percent_covered"],
    )
    with pytest.raises(ValueError, match="coverage"):
        validate_acceptance(requirement, {"details": details}, SnapshotReader(root))


def test_actual_empty_root_collection_cannot_pass(tmp_path: Path) -> None:
    _prepared_root(tmp_path)
    (tmp_path / "tests/test_owned.py").unlink()
    produced, _ = _cohort(tmp_path)
    assert produced["bundle"]["exit_code"] != 0
    assert not (tmp_path / "output/readiness/actual-case.txt").exists()
    with pytest.raises(ValueError):
        read_runtime_cohort(SnapshotReader(tmp_path), produced["bundle"])


@pytest.mark.parametrize("exit_code", [124, 130])
def test_actual_root_pytest_receipt_preserves_forced_exit_before_outcome_validation(
    tmp_path: Path, exit_code: int
) -> None:
    conftest = (
        "def pytest_sessionfinish(session, exitstatus):\n"
        "    if not session.config.option.collectonly:\n"
        f"        session.exitstatus = {exit_code}\n"
    )
    _prepared_root(tmp_path, conftest=conftest, interrupted=True)
    produced, _ = _cohort(tmp_path)
    assert (tmp_path / "output/readiness/actual-case.txt").read_text() == "actual owned case"
    assert produced["bundle"]["exit_code"] == exit_code, produced
    receipts = list((tmp_path / "output/readiness/runtime").rglob("chunk-0000/receipt.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text())
    process = json.loads(receipts[0].with_name("process.json").read_text())
    assert receipt["original_pytest_exit_code"] == receipt["exit_code"] == process["returncode"] == exit_code
    assert process["timed_out"] is False
    assert receipt["interrupted"] is True
    assert not all(
        phases == [["setup", "passed"], ["call", "passed"], ["teardown", "passed"]]
        for phases in receipt["reports"].values()
    )
    assert (
        process["receipt_artifact"]["sha256"]
        == SnapshotReader(tmp_path).read(receipts[0].relative_to(tmp_path).as_posix()).sha256
    )
    with pytest.raises(ValueError):
        read_runtime_cohort(SnapshotReader(tmp_path), produced["bundle"])


def test_actual_held_root_output_lock_exhausts_deadline_before_pytest(tmp_path: Path) -> None:
    _prepared_root(tmp_path)
    census = _epoch_call(produce_root_census, tmp_path, tmp_path / "output/readiness/current", timeout_seconds=180)
    assert census["exit_code"] == 0, census
    with project_output_lock(tmp_path, timeout=5):
        with pytest.MonkeyPatch.context() as environment:
            for name in tuple(os.environ):
                if name.startswith("TEMPLATE_PROJECT_LOCK_"):
                    environment.delenv(name)
            produced = _epoch_call(
                produce_root_lane,
                tmp_path,
                tmp_path / "output/readiness/locked",
                census_bundle=census,
                lane="core",
                timeout_seconds=20,
                test_timeout_seconds=5,
            )
    assert produced["exit_code"] == 124, produced
    assert not (tmp_path / "output/readiness/actual-case.txt").exists()
    assert not list((tmp_path / "output/readiness/locked").rglob("chunk-*/receipt.json"))
    assert not produced.get("records")

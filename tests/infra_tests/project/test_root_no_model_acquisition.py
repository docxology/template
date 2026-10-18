"""Real Root environment pinning and missing declared preparation, without acquisition."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.project.public_acceptance_case_policy import POLICY_SCHEMA
from infrastructure.project.public_root_case_admission import PREREQUISITE_SCHEMA, admit_plan
from infrastructure.project.public_root_case_census import produce_root_census
from infrastructure.project.public_root_case_contract import _json
from infrastructure.project.public_root_lane_producer import produce_root_lane
from infrastructure.project.public_root_lane_readback import read_lane
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project.test_root_case_lanes import _epoch_call

pytestmark = pytest.mark.timeout(1200)


@pytest.fixture(scope="module")
def no_acquisition_root(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    root = tmp_path_factory.mktemp("actual-root-no-acquisition").resolve()
    (root / "tests").mkdir()
    (root / "infrastructure/config").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname="owned-no-model-acquisition"\nversion="0.1.0"\nrequires-python=">=3.12"\n'
        '[tool.pytest.ini_options]\naddopts=[]\nmarkers=["requires_ollama: explicit local-model obligation"]\n'
        '[tool.coverage.run]\nbranch=true\nsource=["infrastructure"]\n',
        encoding="utf-8",
    )
    (root / "tests/conftest.py").write_text(
        """from pathlib import Path
import json, os, sys, pytest
from infrastructure.llm.utils.ollama import pull_ollama_model

@pytest.fixture(autouse=True)
def prepared_only():
    root = Path(__file__).parents[1]
    actual_code = pull_ollama_model.__code__
    prior = sys.getprofile()
    attempts = 0
    def observe(frame, event, argument):
        nonlocal attempts
        if event == 'call' and frame.f_code is actual_code:
            attempts += 1
            (root / 'output/readiness/model-pull-attempt').write_text('actual original function call')
            # An unexpected attempt fails before the original body can acquire.
            raise AssertionError('Root acceptance attempted model acquisition')
        if prior is not None:
            prior(frame, event, argument)
    try:
        sys.setprofile(observe)
        if os.environ.get('OLLAMA_SKIP_TEST_MODEL_PULL') != '1':
            pull_ollama_model('owned-control-no-download', timeout=1)
        yield
    finally:
        sys.setprofile(prior)
        (root / 'output/readiness/environment.json').write_text(json.dumps({
            'pin': os.environ.get('OLLAMA_SKIP_TEST_MODEL_PULL'),
            'original_pull_calls': attempts,
            'profiler_restored': sys.getprofile() is prior,
        }))
""",
        encoding="utf-8",
    )
    (root / "tests/test_owned.py").write_text(
        """from pathlib import Path
import os, pytest

def test_environment():
    assert os.environ.get('OLLAMA_SKIP_TEST_MODEL_PULL') == '1'
    (Path(__file__).parents[1] / 'output/readiness/core-body').write_text('actual case')

@pytest.mark.requires_ollama
def test_required_prepared_model():
    (Path(__file__).parents[1] / 'output/readiness/model-body').write_text('actual model case')
    raise AssertionError('missing source-declared preparation must block before this case')
""",
        encoding="utf-8",
    )
    first = _epoch_call(produce_root_census, root, root / "output/readiness/initial", timeout_seconds=180)
    assert first["exit_code"] == 0, first
    reader = SnapshotReader(root)
    held = reader.read(first["receipt_artifact"]["path"])
    assert held.sha256 == first["receipt_artifact"]["sha256"]
    rows = _json(held)["census"]["families"]
    assert reader.unchanged()
    expected = {
        "tests/test_owned.py::test_environment": "core",
        "tests/test_owned.py::test_required_prepared_model": "live-unpaid",
    }
    assert {row["id"] for row in rows} == set(expected)
    obligations = [
        {"id": "prepared-model-configuration", "kind": "local-model", "eligibility": None},
        {"id": "owned-pin-overlay", "kind": "tool", "eligibility": None},
    ]
    policy = {
        "schema_version": POLICY_SCHEMA,
        "runtimes": ["3.12", "3.13", "3.14"],
        "platforms": ["darwin", "linux"],
        "obligations": obligations,
        "families": [
            {key: row[key] for key in ("id", "members", "source_sha256", "metadata_sha256")}
            | {
                "lane": expected[row["id"]],
                "obligations": ["prepared-model-configuration"]
                if expected[row["id"]] == "live-unpaid"
                else ["owned-pin-overlay"],
            }
            for row in rows
        ],
    }
    prerequisites = {
        "schema_version": PREREQUISITE_SCHEMA,
        "obligations": [
            {
                "id": "prepared-model-configuration",
                "kind": "local-model",
                "environment_keys": ["OLLAMA_MODEL"],
                "executables": ["python"],
                "platforms": [],
            },
            {
                "id": "owned-pin-overlay",
                "kind": "tool",
                "environment_keys": [],
                "executables": ["python"],
                "platforms": [],
            },
        ],
    }
    (root / "infrastructure/config/root-case-policy.json").write_text(json.dumps(policy), encoding="utf-8")
    (root / "infrastructure/config/root-case-prerequisites.json").write_text(
        json.dumps(prerequisites), encoding="utf-8"
    )
    with (root / "pyproject.toml").open("a") as stream:
        stream.write(
            "[tool.template.root_acceptance]\nschema_version=2\n"
            'policy="infrastructure/config/root-case-policy.json"\n'
            'prerequisites="infrastructure/config/root-case-prerequisites.json"\n'
        )
    census = _epoch_call(produce_root_census, root, root / "output/readiness/current", timeout_seconds=180)
    assert census["exit_code"] == 0, census
    assert set(admit_plan(SnapshotReader(root), census).plan.nodeids) == set(expected)
    assert not (root / "output/readiness/model-pull-attempt").exists()
    return root, census


@pytest.mark.parametrize("caller", [None, "0"], ids=["unset", "zero"])
@pytest.mark.parametrize("mode", ["core", "live"])
def test_actual_root_worker_pins_no_pull_after_caller_and_declared_overlays(no_acquisition_root, caller, mode):
    root, census = no_acquisition_root
    previous = os.environ.get("OLLAMA_SKIP_TEST_MODEL_PULL")
    try:
        if caller is None:
            os.environ.pop("OLLAMA_SKIP_TEST_MODEL_PULL", None)
        else:
            os.environ["OLLAMA_SKIP_TEST_MODEL_PULL"] = caller
        # Each parametrized lane must produce its own observations; a stale
        # file from an earlier case can never satisfy these assertions.
        for name in ("environment.json", "core-body"):
            (root / "output/readiness" / name).unlink(missing_ok=True)
        bundle = _epoch_call(
            produce_root_lane,
            root,
            root / f"output/readiness/environment-{mode}-{caller}",
            census_bundle=census,
            lane="core",
            mode=mode,
            timeout_seconds=360,
            test_timeout_seconds=60,
        )
        assert bundle["exit_code"] == 0, bundle
        actual = read_lane(SnapshotReader(root), bundle)
        assert actual["selected_nodes"] == ["tests/test_owned.py::test_environment"]
        observed = json.loads((root / "output/readiness/environment.json").read_bytes())
        assert observed == {"pin": "1", "original_pull_calls": 0, "profiler_restored": True}
        assert (root / "output/readiness/core-body").read_text() == "actual case"
        assert not (root / "output/readiness/model-pull-attempt").exists()
        assert os.environ.get("OLLAMA_SKIP_TEST_MODEL_PULL") == caller
    finally:
        if previous is None:
            os.environ.pop("OLLAMA_SKIP_TEST_MODEL_PULL", None)
        else:
            os.environ["OLLAMA_SKIP_TEST_MODEL_PULL"] = previous


def test_prerequisite_declaring_the_pinned_key_is_refused_at_admission(no_acquisition_root):
    """The pin could satisfy such a declaration, so admission refuses it outright."""
    root, census = no_acquisition_root
    inventory = root / "infrastructure/config/root-case-prerequisites.json"
    original = inventory.read_bytes()
    try:
        forged = json.loads(original)
        for row in forged["obligations"]:
            if row["id"] == "owned-pin-overlay":
                row["environment_keys"] = ["OLLAMA_SKIP_TEST_MODEL_PULL"]
        inventory.write_text(json.dumps(forged), encoding="utf-8")
        with pytest.raises(ValueError, match="platform-pinned no-model-acquisition key"):
            admit_plan(SnapshotReader(root), census)
    finally:
        inventory.write_bytes(original)
    assert set(admit_plan(SnapshotReader(root), census).plan.nodeids)


def test_missing_declared_prepared_model_configuration_is_original_blocked_without_case_or_pull(no_acquisition_root):
    root, census = no_acquisition_root
    previous = os.environ.get("OLLAMA_MODEL")
    try:
        os.environ.pop("OLLAMA_MODEL", None)
        # Presence-aware pre-state: this case must also hold when selected
        # alone, before any positive lane has written the observation file.
        observation = root / "output/readiness/environment.json"
        before = observation.read_bytes() if observation.exists() else None
        bundle = _epoch_call(
            produce_root_lane,
            root,
            root / "output/readiness/missing-prepared-configuration",
            census_bundle=census,
            lane="live-unpaid",
            mode="live",
            timeout_seconds=180,
        )
        assert bundle["exit_code"] == 75, bundle
        native = json.loads((root / bundle["coordinator_artifact"]["path"]).read_bytes())
        assert native["returncode"] == native["original_returncode"] == 75
        assert native["timed_out"] is native["custody_refused"] is False
        after = observation.read_bytes() if observation.exists() else None
        assert after == before, "a blocked lane must not run the owned session fixture"
        assert not (root / "output/readiness/model-body").exists()
        assert not (root / "output/readiness/model-pull-attempt").exists()
        with pytest.raises(ValueError):
            read_lane(SnapshotReader(root), bundle)
    finally:
        if previous is None:
            os.environ.pop("OLLAMA_MODEL", None)
        else:
            os.environ["OLLAMA_MODEL"] = previous


def test_actual_model_pull_observer_control_executes_original_body_with_genuinely_absent_cli(tmp_path):
    import infrastructure

    provider = Path(infrastructure.__file__).absolute().parent.parent
    cache = tmp_path.resolve() / "actual-fresh-cache"
    cache.mkdir()
    empty = tmp_path.resolve() / "empty-path"
    empty.mkdir()
    code = bytecode_audit_bootstrap((provider / "infrastructure", provider / "scripts"), cache)
    code += """
import json, os
sys.path.insert(0, sys.argv[1])
from infrastructure.llm.utils.ollama import pull_ollama_model
actual_code = pull_ollama_model.__code__
prior = sys.getprofile()
calls = 0
def observe(frame, event, argument):
    global calls
    if event == 'call' and frame.f_code is actual_code:
        calls += 1
    if prior is not None:
        prior(frame, event, argument)
try:
    sys.setprofile(observe)
    original_path = os.environ.get('PATH')
    os.environ['PATH'] = sys.argv[2]
    ok, diagnostic = pull_ollama_model('owned-control-no-download', timeout=1)
finally:
    sys.setprofile(prior)
    if original_path is None:
        os.environ.pop('PATH', None)
    else:
        os.environ['PATH'] = original_path
assert ok is False and diagnostic == 'ollama CLI not found in PATH'
assert calls == 1 and sys.getprofile() is prior
print(json.dumps({'original_pull_calls': calls, 'actual_missing_cli': True}))
"""
    observed = run_with_policy(
        [sys.executable, "-I", "-X", f"pycache_prefix={cache}", "-c", code, str(provider), str(empty)],
        cwd=tmp_path.resolve(),
        env=os.environ.copy(),
        policy=SubprocessPolicy(
            policy_id="root-no-acquisition-positive-observer",
            source_path=__name__,
            timeout_seconds=120,
            credential_free=True,
        ),
    )
    assert observed.returncode == 0 and not observed.timed_out, observed.stderr
    # The original function also reports its own diagnostic on stdout; the
    # observer's JSON summary is the final line.
    assert json.loads(observed.stdout.strip().splitlines()[-1]) == {
        "original_pull_calls": 1,
        "actual_missing_cli": True,
    }

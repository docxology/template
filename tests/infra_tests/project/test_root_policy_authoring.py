"""Literal classifications need genuine collection and exhaustive public source review data."""

from __future__ import annotations

import copy
import json
import os
import shutil
import shlex
import time
import sys
import subprocess
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_root_case_admission import load_policy
from infrastructure.project.public_root_case_census import produce_root_census
from infrastructure.project.public_reference_git import _PINNED_SUBMODULE, native_git
from infrastructure.project.public_root_policy_authoring import DECISIONS_SCHEMA, _tracked, author_policy, family_ledger
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project import test_root_case_lanes as lane_controls

pytestmark = [pytest.mark.slow, pytest.mark.timeout(1200)]


def _native_setup() -> tuple[str, dict[str, str]]:
    executable = shutil.which("git", path=os.defpath)
    assert executable is not None
    return executable, {
        "PATH": os.defpath,
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }


@pytest.fixture(scope="module")
def genuine_reviewed_decisions(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    root, _, _ = lane_controls.genuine_lane.__wrapped__(tmp_path_factory)
    # A real owned Git index establishes this fixture's public source inventory.
    # The helper does not invent tracking, checkout metadata or provider identity.
    executable, environment = _native_setup()
    for command in ([executable, "init", "-q"], [executable, "add", "--", "tests"]):
        observed = subprocess.run(command, cwd=root, env=environment, capture_output=True, timeout=30, check=False)
        assert observed.returncode == 0, observed.stderr
    original = lane_controls._epoch_call(
        produce_root_census, root, root / "output/readiness/policy-authoring-census", timeout_seconds=180
    )
    assert original["exit_code"] == 0, original
    reader = SnapshotReader(root)
    ledger = family_ledger(reader, original)
    assert ledger["role"] == "root-case-policy-authoring-candidate-only"
    policy, _, _, _ = load_policy(reader)
    module = ledger["modules"][0]
    assert len(ledger["modules"]) == 1
    decisions = {
        "schema_version": DECISIONS_SCHEMA,
        "source_identity": ledger["source_identity"],
        "census_sha256": ledger["census_sha256"],
        "modules": [
            {
                "path": module["path"],
                "source_sha256": module["source_sha256"],
                "families": [family["id"] for family in module["families"]],
                "decision": {"lane": "core", "obligations": []},
                "exceptions": [
                    {
                        "id": "tests/test_owned.py::TestLive::test_model",
                        "lane": "live-unpaid",
                        "obligations": ["owned-local-model"],
                    }
                ],
                "evidence": [{"path": module["path"], "source_sha256": module["source_sha256"], "line": 1}],
            }
        ],
        "obligations": [{"id": item.id, "kind": item.kind, "eligibility": None} for item in policy.obligations],
    }
    assert reader.unchanged()
    return root, original, decisions


@pytest.mark.parametrize("policy_schema", ["template-root-case-policy-v2", "template-root-case-policy-v3"])
def test_literal_draft_preserves_original_all_families_members_and_live_obligation(
    genuine_reviewed_decisions: tuple[Path, dict[str, Any], dict[str, Any]],
    policy_schema: str,
) -> None:
    root, original, decisions = genuine_reviewed_decisions
    reference = write_json(root, root / "output/readiness/explicit-reviewed-decisions.json", decisions)
    reader = SnapshotReader(root)
    actual = author_policy(reader, original, reference["path"], policy_schema=policy_schema)
    assert actual["schema_version"] == policy_schema
    ledger = family_ledger(reader, original)
    observed = [family for module in ledger["modules"] for family in module["families"]]
    assert {row["id"] for row in actual["families"]} == {row["id"] for row in observed}
    assert {member["nodeid"] for row in actual["families"] for member in row["members"]} == {
        member["nodeid"] for row in observed for member in row["members"]
    }
    live = next(row for row in actual["families"] if row["id"].endswith("::test_model"))
    assert live["lane"] == "live-unpaid" and live["obligations"] == ["owned-local-model"]
    assert actual["runtimes"] == ["3.14", "3.15"]
    assert actual["platforms"] == ["darwin", "linux"]
    assert not (root / "output/readiness/live-body").exists()


@pytest.mark.parametrize(
    "fault",
    [
        "module-omitted",
        "family-omitted",
        "stale-source",
        "no-decision",
        "no-evidence",
        "untracked-evidence",
        "outside-line",
        "duplicate-exception",
        "live-defaulted-core",
        "optin-added-to-core",
    ],
)
def test_genuine_census_cannot_default_or_omit_classification_and_public_source_evidence(
    genuine_reviewed_decisions: tuple[Path, dict[str, Any], dict[str, Any]],
    fault: str,
) -> None:
    root, original, baseline = genuine_reviewed_decisions
    decisions = copy.deepcopy(baseline)
    module = decisions["modules"][0]
    if fault == "module-omitted":
        decisions["modules"] = []
    elif fault == "family-omitted":
        module["families"].pop()
    elif fault == "stale-source":
        module["source_sha256"] = "0" * 64
    elif fault == "no-decision":
        del module["decision"]
    elif fault == "no-evidence":
        module["evidence"] = []
    elif fault == "untracked-evidence":
        module["evidence"][0]["path"] = "output/readiness/invented-untracked-origin.txt"
    elif fault == "outside-line":
        module["evidence"][0]["line"] = 10**6
    elif fault == "duplicate-exception":
        module["exceptions"].append(copy.deepcopy(module["exceptions"][0]))
    elif fault == "live-defaulted-core":
        module["exceptions"] = []
    else:
        module["decision"]["obligations"] = ["owned-local-model"]
    reference = write_json(root, root / ("output/readiness/decisions-" + fault + ".json"), decisions)
    with pytest.raises(ValueError):
        author_policy(SnapshotReader(root), original, reference["path"])
    assert not (root / "output/readiness/live-body").exists()


def test_rehashed_outer_failure_record_cannot_authorize_a_literal_policy(
    genuine_reviewed_decisions: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, original, decisions = genuine_reviewed_decisions
    rebound = copy.deepcopy(original)
    path = root / rebound["coordinator_artifact"]["path"]
    original_raw = path.read_bytes()
    current = json.loads(original_raw)
    try:
        current["returncode"] = current["original_returncode"] = 7
        rebound["coordinator_artifact"] = write_json(root, path, current)
        reference = write_json(root, root / "output/readiness/outer-refused-decisions.json", decisions)
        with pytest.raises(ValueError):
            author_policy(SnapshotReader(root), rebound, reference["path"])
    finally:
        path.write_bytes(original_raw)


@pytest.mark.parametrize("routing", ["forged-path", "alternate-index"])
def test_genuine_untracked_case_cannot_enter_public_policy_through_ambient_git_routing(
    tmp_path_factory: pytest.TempPathFactory,
    routing: str,
) -> None:
    root, _, _ = lane_controls.genuine_lane.__wrapped__(tmp_path_factory)
    executable, environment = _native_setup()
    for arguments in (("init", "-q"),):
        outcome = subprocess.run(
            [executable, *arguments], cwd=root, env=environment, capture_output=True, timeout=30, check=False
        )
        assert outcome.returncode == 0, outcome.stderr
    alternate = root / ".git/owned-alternate-index"
    setup = subprocess.run(
        [executable, "add", "--", "tests"],
        cwd=root,
        env={**environment, "GIT_INDEX_FILE": str(alternate)},
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert setup.returncode == 0, setup.stderr
    assert native_git(root, time.monotonic() + 30, "ls-files", "--stage", "-z") == b""
    original = lane_controls._epoch_call(
        produce_root_census,
        root,
        root / ("output/readiness/untracked-" + routing),
        timeout_seconds=180,
    )
    assert original["exit_code"] == 0, original
    saved = {key: os.environ.get(key) for key in ("PATH", "GIT_INDEX_FILE")}
    marker = root / "output/readiness/forged-git-executed"
    try:
        if routing == "forged-path":
            directory = root / "output/readiness/forged-native-bin"
            directory.mkdir()
            script = directory / "git"
            script.write_text(
                "#!/bin/sh\nprintf 'live' > "
                + shlex.quote(str(marker))
                + "\nprintf 'tests/test_owned.py\\000tests/conftest.py\\000'\n"
            )
            script.chmod(0o700)
            os.environ["PATH"] = str(directory) + os.pathsep + os.defpath
        else:
            os.environ["GIT_INDEX_FILE"] = str(alternate)
        # A real nonisolated positive proves the ambient forgery/alternate index
        # is live before the fixed original native inventory refuses it.
        positive = subprocess.run(
            ["git" if routing == "forged-path" else executable, "ls-files", "-z"],
            cwd=root,
            env={
                **environment,
                "PATH": os.environ["PATH"],
                **({"GIT_INDEX_FILE": str(alternate)} if routing == "alternate-index" else {}),
            },
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert positive.returncode == 0 and b"tests/test_owned.py" in positive.stdout
        if routing == "forged-path":
            assert marker.read_text() == "live"
            marker.unlink()
        with pytest.raises(ValueError, match="outside its actual tracked public test inventory"):
            family_ledger(SnapshotReader(root), original)
        assert not marker.exists()
        assert native_git(root, time.monotonic() + 30, "ls-files", "--stage", "-z") == b""
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_actual_pinned_gitlink_is_inert_and_never_consumed_as_public_source_evidence(
    genuine_reviewed_decisions: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, original, decisions = genuine_reviewed_decisions
    source = Path(__file__).resolve().parents[3]
    actual = [
        row
        for row in native_git(source, time.monotonic() + 30, "ls-files", "--stage", "-z").split(b"\0")
        if row.endswith(b"\t" + _PINNED_SUBMODULE.encode())
    ]
    assert len(actual) == 1
    header, _ = actual[0].split(b"\t", 1)
    mode, oid, stage = header.decode().split(" ")
    assert mode == "160000" and stage == "0"
    executable, environment = _native_setup()
    result = subprocess.run(
        [executable, "update-index", "--add", "--cacheinfo", mode, oid, _PINNED_SUBMODULE],
        cwd=root,
        env=environment,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    try:
        ledger = family_ledger(SnapshotReader(root), original)
        assert len(ledger["modules"]) == 1
        reference = write_json(root, root / "output/readiness/gitlink-aware-decisions.json", decisions)
        authored = author_policy(SnapshotReader(root), original, reference["path"])
        assert len(authored["families"]) == 2
        bad = copy.deepcopy(decisions)
        bad["modules"][0]["evidence"][0]["path"] = _PINNED_SUBMODULE
        bad_reference = write_json(root, root / "output/readiness/gitlink-consumed-decisions.json", bad)
        with pytest.raises(ValueError, match="review evidence"):
            author_policy(SnapshotReader(root), original, bad_reference["path"])
    finally:
        result = subprocess.run(
            [executable, "update-index", "--force-remove", "--", _PINNED_SUBMODULE],
            cwd=root,
            env=environment,
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr


def test_original_native_same_path_index_oid_change_is_refused_during_authoring(
    genuine_reviewed_decisions: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, original, decisions = genuine_reviewed_decisions
    baseline = _tracked(SnapshotReader(root))
    mode, oid = baseline["tests/test_owned.py"]
    executable, environment = _native_setup()
    blob = subprocess.run(
        [executable, "hash-object", "-w", "--stdin"],
        cwd=root,
        env=environment,
        input=b"actual owned alternate staged content\n",
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert blob.returncode == 0, blob.stderr
    alternate = blob.stdout.decode().strip()
    reference = write_json(root, root / "output/readiness/concurrent-index-decisions.json", decisions)
    previous = sys.getprofile()
    observed = []

    def actual_profile(frame: Any, event: str, value: Any) -> None:
        if frame.f_code is _tracked.__code__ and event == "return" and not observed:
            observed.append(copy.deepcopy(value))
            outcome = subprocess.run(
                [executable, "update-index", "--cacheinfo", mode, alternate, "tests/test_owned.py"],
                cwd=root,
                env=environment,
                capture_output=True,
                timeout=30,
                check=False,
            )
            assert outcome.returncode == 0, outcome.stderr

    try:
        sys.setprofile(actual_profile)
        with pytest.raises(ValueError, match="original public index changed"):
            author_policy(SnapshotReader(root), original, reference["path"])
        assert observed and _tracked(SnapshotReader(root))["tests/test_owned.py"] != baseline["tests/test_owned.py"]
    finally:
        sys.setprofile(previous)
        outcome = subprocess.run(
            [executable, "update-index", "--cacheinfo", mode, oid, "tests/test_owned.py"],
            cwd=root,
            env=environment,
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert outcome.returncode == 0, outcome.stderr

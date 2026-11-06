"""Real review-DATA/filesystem/delivery controls; no fixture grants census origin."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

import pytest
import yaml

from infrastructure.project.public_acceptance_case_policy import PLATFORMS, RUNTIMES, digest
from infrastructure.project.public_root_policy_census import TEMPLATE_SCHEMA, fresh_decisions, reviewed_template
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/root-policy-census.yml"


def _review_data() -> tuple[dict, dict]:
    family = {
        "id": "tests/test_example.py::test_real",
        "members": [{"nodeid": "tests/test_example.py::test_real", "parameter_id": None}],
        "source_sha256": "a" * 64,
        "metadata_sha256": "b" * 64,
        "markers": [],
        "public_closure": True,
    }
    module = {"path": "tests/test_example.py", "source_sha256": "a" * 64, "families": [family]}
    ledger = {
        "role": "root-case-policy-authoring-candidate-only",
        "source_identity": "c" * 64,
        "census_sha256": "d" * 64,
        "modules": [module],
    }
    template = {
        "schema_version": TEMPLATE_SCHEMA,
        "modules": [
            {
                "path": module["path"],
                "source_sha256": module["source_sha256"],
                "families": [family["id"]],
                "family_observations_sha256": digest(module["families"]),
                "decision": {"lane": "core", "obligations": []},
                "exceptions": [],
                "evidence": [{"path": module["path"], "source_sha256": module["source_sha256"], "line": 1}],
            }
        ],
        "obligations": [],
    }
    return template, ledger


def test_fresh_decisions_bind_current_census_and_preserve_only_explicit_reviewed_classifications() -> None:
    template, ledger = _review_data()
    original = copy.deepcopy(template)
    result = fresh_decisions(template, ledger)
    assert result["source_identity"] == ledger["source_identity"] and result["census_sha256"] == ledger["census_sha256"]
    assert result["modules"][0]["decision"] == template["modules"][0]["decision"]
    assert "family_observations_sha256" not in result["modules"][0]
    assert template == original
    # This component creates DATA, never a policy or original process capability.
    assert set(result) == {"schema_version", "source_identity", "census_sha256", "modules", "obligations"}


@pytest.mark.parametrize(
    "defect",
    [
        "missing-module",
        "extra-module",
        "duplicate-module",
        "missing-decision",
        "changed-source",
        "new-family",
        "new-parameter",
        "fixture-drift",
        "noncandidate",
        "extra-field",
    ],
)
def test_review_refuses_missing_or_changed_family_member_and_fixture_metadata(defect: str) -> None:
    template, ledger = _review_data()
    if defect == "missing-module":
        template["modules"] = []
    elif defect == "extra-module":
        template["modules"][0]["path"] = "tests/foreign.py"
    elif defect == "duplicate-module":
        template["modules"].append(copy.deepcopy(template["modules"][0]))
    elif defect == "missing-decision":
        del template["modules"][0]["decision"]
    elif defect == "changed-source":
        ledger["modules"][0]["source_sha256"] = "e" * 64
    elif defect == "new-family":
        ledger["modules"][0]["families"].append(
            {**ledger["modules"][0]["families"][0], "id": "tests/test_example.py::test_new"}
        )
    elif defect == "new-parameter":
        ledger["modules"][0]["families"][0]["members"].append(
            {"nodeid": "tests/test_example.py::test_real[new]", "parameter_id": "new"}
        )
    elif defect == "fixture-drift":
        ledger["modules"][0]["families"][0]["metadata_sha256"] = "f" * 64
    elif defect == "noncandidate":
        ledger["role"] = "passed"
    elif defect == "extra-field":
        template["modules"][0]["allow_new_cases"] = True
    with pytest.raises(ValueError):
        fresh_decisions(template, ledger)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stdin=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=30
    ).strip()


@pytest.fixture
def template_source(tmp_path: Path) -> tuple[Path, Path, str, str]:
    root = tmp_path / "source"
    root.mkdir()
    path = root / "infrastructure/config/review.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(_review_data()[0]))
    _git(root, "init", "-b", "main")
    _git(root, "add", "infrastructure/config/review.json")
    _git(root, "-c", "user.name=Control", "-c", "user.email=control@example.invalid", "commit", "-m", "Source fixture")
    return root, path, _git(root, "rev-parse", "HEAD"), hashlib.sha256(path.read_bytes()).hexdigest()


def test_template_reads_only_the_actual_committed_regular_source_bytes(template_source: tuple) -> None:
    root, path, commit, expected = template_source
    path.chmod(0o600)  # A normal nonexecutable file remains Git mode100644.
    value = reviewed_template(SnapshotReader(root), path.relative_to(root).as_posix(), expected, commit)
    assert value == _review_data()[0]


@pytest.mark.parametrize(
    "defect",
    [
        "hash",
        "dirty",
        "staged",
        "symlink",
        "hardlink",
        "executable",
        "untracked",
        "traversal",
        "absolute",
        "outside-config",
        "not-json",
    ],
)
def test_template_refuses_foreign_mutable_or_uncommitted_nominations(template_source: tuple, defect: str) -> None:
    root, path, commit, expected = template_source
    relative = path.relative_to(root).as_posix()
    if defect == "hash":
        expected = "0" * 64
    elif defect in {"dirty", "staged"}:
        path.write_bytes(path.read_bytes() + b" ")
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        if defect == "staged":
            _git(root, "add", relative)
    elif defect == "symlink":
        original = root / "original.json"
        path.rename(original)
        path.symlink_to(original)
    elif defect == "hardlink":
        os.link(path, root / "alias.json")
    elif defect == "executable":
        path.chmod(0o755)
    elif defect == "untracked":
        path = path.with_name("untracked.json")
        path.write_text("{}")
        relative = path.relative_to(root).as_posix()
    elif defect == "traversal":
        relative = "infrastructure/config/../config/review.json"
    elif defect == "absolute":
        relative = str(path)
    elif defect == "outside-config":
        relative = "tests/review.json"
    elif defect == "not-json":
        relative = "infrastructure/config/review.txt"
    with pytest.raises((ValueError, OSError)):
        reviewed_template(SnapshotReader(root), relative, expected, commit)


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


@pytest.mark.parametrize(
    "source,mode,path,sha,accepted",
    [
        ("a" * 40, "collect", "", "", True),
        ("b" * 40, "collect", "", "", False),
        ("a" * 40, "author", "infrastructure/config/review.json", "c" * 64, True),
        ("a" * 40, "author", "infrastructure/config/../review.json", "c" * 64, False),
        ("a" * 40, "collect", "infrastructure/config/review.json", "c" * 64, False),
        ("a" * 40, "author", "", "", False),
    ],
)
def test_actual_workflow_shell_admits_only_exact_source_and_unambiguous_review_inputs(
    tmp_path: Path, source: str, mode: str, path: str, sha: str, accepted: bool
) -> None:
    step = _workflow()["jobs"]["census"]["steps"][0]
    env = {
        "PATH": os.environ["PATH"],
        "GITHUB_SHA": "a" * 40,
        "REQUESTED_SOURCE": source,
        "REQUESTED_MODE": mode,
        "REVIEW_PATH": path,
        "REVIEW_SHA256": sha,
    }
    result = subprocess.run(
        ["bash", "-c", step["run"]], cwd=tmp_path, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=10
    )
    assert (result.returncode == 0) is accepted


def test_actual_macos_export_program_keeps_hidden_evidence_and_excludes_only_declared_pytest_scratch(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    source = root / "output/readiness/root-policy-census/darwin-3.14/collection"
    source.mkdir(parents=True)
    (source / "census-spec.json").write_text("{}")
    hidden = source / ".hidden/actual.bin"
    hidden.parent.mkdir()
    hidden.write_bytes(b"original\x00DATA")
    scratch = source / "pytest-tmp"
    scratch.mkdir()
    (scratch / "unrelated-fixture").write_text("disposable")
    temporary = tmp_path / "runner"
    temporary.mkdir()
    envfile = temporary / "github-env"
    envfile.touch()
    step = next(row for row in _workflow()["jobs"]["census"]["steps"] if row.get("id") == "darwin_export")
    program = step["run"].split("<<'PYTHON'\n", 1)[1].rsplit("\nPYTHON", 1)[0]
    env = {**os.environ, "PYTHONPATH": str(ROOT), "RUNNER_TEMP": str(temporary), "GITHUB_ENV": str(envfile)}
    result = subprocess.run(
        [sys.executable, "-B", "-c", program],
        cwd=root,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    destination = Path(envfile.read_text().strip().split("=", 1)[1])
    assert (destination / hidden.relative_to(root / "output/readiness")).read_bytes() == b"original\x00DATA"
    assert not (destination / scratch.relative_to(root / "output/readiness")).exists()
    assert hidden.read_bytes() == b"original\x00DATA" and (scratch / "unrelated-fixture").read_text() == "disposable"


def test_census_delivery_matches_current_root_frontdoor_and_all_supported_targets() -> None:
    workflow = _workflow()
    required = yaml.safe_load((ROOT / ".github/workflows/platform-required-acceptance.yml").read_text())
    job = workflow["jobs"]["census"]
    steps = job["steps"]
    root_steps = required["jobs"]["root-original"]["steps"]
    assert {(row["host"], row["python"]) for row in job["strategy"]["matrix"]["include"]} == {
        (host, minor) for host in PLATFORMS for minor in RUNTIMES
    }
    assert workflow["permissions"] == {"contents": "read"}
    uses = [row["uses"] for row in steps if "uses" in row]
    expected = [
        row["uses"] for row in root_steps if "uses" in row and not row["uses"].startswith("actions/upload-artifact@")
    ]
    assert uses[: len(expected)] == expected
    sync = next(row["run"] for row in steps if row.get("name") == "Prepare the own locked collection environment")
    root_sync = next(row["run"] for row in root_steps if row.get("name") == "Prepare selected locked environment")
    assert re.findall(r"--group ([\w-]+)", sync) == re.findall(r"--group ([\w-]+)", root_sync)
    for name in (
        "Prepare exact Source-locked PDFium wheel fixture",
        "Prepare source-locked browser math dependencies",
        "Stop only the owned model daemon and descendants",
    ):
        assert next(row["run"] for row in steps if row.get("name") == name) == next(
            row["run"] for row in root_steps if row.get("name") == name
        )
    uploads = [row for row in steps if row.get("uses", "").startswith("actions/upload-artifact@")]
    assert len(uploads) == 2 and all(
        row["if"] == "always()" and row["with"]["include-hidden-files"] is True for row in uploads
    )
    assert all(row["with"]["if-no-files-found"] == "error" for row in uploads)


def test_actual_cli_refuses_wrong_source_before_collecting_or_writing_evidence() -> None:
    target = ROOT / "output/readiness" / ("root-policy-control-" + uuid.uuid4().hex)
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "infrastructure.project.public_root_policy_census",
            "--repo-root",
            str(ROOT),
            "--source-sha",
            "0" * 40,
            "--directory",
            str(target),
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0 and "differs from current Source" in result.stderr
    assert not target.exists()


def test_real_failed_coordinator_retains_its_actual_streams_without_acceptance(tmp_path: Path) -> None:
    from infrastructure.project.public_root_case_census import produce_root_census

    root = tmp_path / "invalid-source"
    root.mkdir()
    (root / "pyproject.toml").write_text("[not valid TOML\n")
    directory = root / "output/readiness/failed-census"
    result = produce_root_census(root, directory, timeout_seconds=60)
    process = json.loads((directory / "coordinator-process.json").read_text())
    assert result["exit_code"] != 0
    assert type(process["original_returncode"]) is int and process["original_returncode"] != 0
    assert (directory / "coordinator.stdout").is_file()
    assert (directory / "coordinator.stderr").read_bytes()
    assert "stdout" not in process and "stderr" not in process
    assert result["role"] == "canonical-collection-only"

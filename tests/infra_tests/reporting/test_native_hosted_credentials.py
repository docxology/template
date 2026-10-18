"""Credential DATA never relaxes ordinary native Popen/readback custody."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest

from infrastructure.core.execution_boundary import build_bounded_env, build_bounded_run_env
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting._native_hosted_launch import fixed_prepared_reader_launch
from infrastructure.reporting.native_environment_custody import (
    _capture_hosted_reader_environment,
    _validate_hosted_reader_environment,
    validate_native_environment,
)
from infrastructure.reporting.native_tool_process import run_native_tool_process
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project.test_public_reference import (
    _clone_complete_reference,
    complete_reference as complete_reference,
)


def test_actual_ordinary_native_child_and_records_remain_credential_free(tmp_path: Path) -> None:
    sentinel = "harmless-" + uuid4().hex
    directory = tmp_path / "process"
    directory.mkdir()
    source = {**build_bounded_env(), "GH_TOKEN": sentinel, "OTHER_TOKEN": sentinel}
    result = run_native_tool_process(
        directory,
        sys.executable,
        ["-I", "-c", "import os,json;print(json.dumps({k:k in os.environ for k in ['GH_TOKEN','OTHER_TOKEN']}))"],
        cwd=tmp_path,
        env=source,
        deadline=time.monotonic() + 30,
        purpose="ordinary-credential-control",
    )
    assert result["accepted"] and result["original_exit_code"] == 0 and not result["timed_out"]
    assert json.loads(result["stdout"]) == {"GH_TOKEN": False, "OTHER_TOKEN": False}
    assert "GH_TOKEN" not in result["environment_custody"]["actual_commitments"]
    assert "OTHER_TOKEN" not in result["environment_custody"]["actual_commitments"]
    assert sentinel not in json.dumps(result)
    assert all(sentinel not in p.read_text() for p in directory.glob("*.json"))
    assert result["cleanup"]["guardian_finished"]


def test_hosted_environment_commits_exact_job_input_and_rejects_rewritten_data(tmp_path: Path) -> None:
    records = []
    for _ in range(2):
        sentinel = "harmless-" + uuid4().hex
        source = {**build_bounded_env(), "GH_TOKEN": sentinel, "OTHER_TOKEN": sentinel}
        selected = build_bounded_env(source)
        bounded, token = build_bounded_run_env(selected)
        raw = _capture_hosted_reader_environment(source, selected, bounded, {**bounded, "GH_TOKEN": sentinel}, token)
        _validate_hosted_reader_environment(raw, source)
        assert raw["credential_commitments"] == {"GH_TOKEN": hashlib.sha256(sentinel.encode()).hexdigest()}
        assert "OTHER_TOKEN" not in raw["actual_commitments"]
        assert sentinel not in json.dumps(raw)
        changed = copy.deepcopy(raw)
        changed["actual_commitments"]["GH_TOKEN"] = "0" * 64
        with pytest.raises(ValueError, match="commitment"):
            _validate_hosted_reader_environment(changed, source)
        # Ordinary portable tools cannot adopt the distinct outer reader route.
        with pytest.raises(ValueError, match="original Source-selected commitment"):
            validate_native_environment(
                {"environment_custody": raw}, {"environment_digest": canonical_digest(source)}, SnapshotReader(tmp_path)
            )
        records.append(raw)
    assert records[0]["credential_commitments"] != records[1]["credential_commitments"]


def test_hosted_launch_refuses_arbitrary_preparation_without_a_real_factory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="actual independently verified prepared runtime"):
        with fixed_prepared_reader_launch(
            object(),
            tmp_path / "input.json",
            b"{}",
            roots=(),
            closure=tmp_path,
            body="raise SystemExit(0)",
            arguments=(),
            environment=build_bounded_env(),
        ):
            raise AssertionError("arbitrary caller acquired a privileged launch")


@pytest.mark.timeout(1200)
def test_genuine_installed_reader_popen_has_only_fixed_credential_route(
    complete_reference: tuple[Path, str, str], tmp_path: Path
) -> None:
    """Real Source/wheel/locked install and audited reader --help; no native acceptance claim."""
    import shutil

    from infrastructure.reporting.native_installed_preparation import (
        NativePreparationFailure,
        prepare_native_installed_runtime,
    )
    from infrastructure.reporting.native_installed_invocation import capture_prepared_sdk, launch_prepared_native
    from infrastructure.reporting.native_source_provider_bootstrap import NATIVE_READER_MODULE

    original, commit, source_identity = complete_reference
    started = time.monotonic()
    budget = 1100
    deadline = started + budget
    current = _clone_complete_reference(complete_reference, tmp_path / "current", deadline=deadline)
    install = tmp_path / "installed"
    install.mkdir()
    evidence = current / "output/readiness/fixed-hosted-reader-control"
    evidence.mkdir(parents=True)
    environment = {**build_bounded_env(), "UV_LINK_MODE": "copy", "UV_PYTHON_DOWNLOADS": "never"}
    uv = shutil.which("uv")
    assert uv is not None
    try:
        prepared = prepare_native_installed_runtime(
            original,
            current,
            install,
            evidence,
            python=Path(sys.executable).absolute(),
            uv=Path(uv).absolute(),
            source_commit=commit,
            source_identity=source_identity,
            operation_started=started,
            deadline=deadline,
            env=environment,
            scopes=("templates/template_code_project",),
        )
    except NativePreparationFailure as error:
        # Retain the original bounded child body in hosted failure logs.
        # Preparation precedes creation of this control's credential sentinel.
        error.add_note(json.dumps(error.result, sort_keys=True))
        raise
    implementation, raw = capture_prepared_sdk(prepared, environment=environment)
    sentinel = "harmless-" + uuid4().hex
    nominated = {**environment, "GH_TOKEN": sentinel, "UNRELATED_TOKEN": sentinel}
    arguments = (
        "--repo-root",
        str(current),
        "--revision",
        commit,
        "--sdk-package-root",
        str(prepared.sdk_package_root),
        "--implementation-input",
        str(implementation),
        "--implementation-sha256",
        hashlib.sha256(raw).hexdigest(),
        "--operation-started-monotonic",
        repr(started),
        "--timeout",
        str(budget),
        "--help",
    )
    result = launch_prepared_native(
        prepared,
        implementation,
        raw,
        role=NATIVE_READER_MODULE,
        arguments=arguments,
        pdfium_roots=(),
        pdfium_sources={},
        environment=nominated,
    )
    assert result["accepted"] and result["original_exit_code"] == 0 and not result["timed_out"]
    assert "usage:" in result["stdout"]
    custody = result["environment_custody"]
    assert custody["credential_commitments"] == {"GH_TOKEN": hashlib.sha256(sentinel.encode()).hexdigest()}
    assert "GH_TOKEN" not in custody["ordinary"]["actual_commitments"]
    assert "UNRELATED_TOKEN" not in custody["actual_commitments"]
    assert sentinel not in json.dumps(result)
    assert all(sentinel not in p.read_text() for p in evidence.rglob("*.json"))
    assert result["cleanup"]["guardian_finished"]
    assert time.monotonic() < deadline

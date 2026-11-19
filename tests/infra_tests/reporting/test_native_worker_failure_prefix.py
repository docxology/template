"""Genuine installed Source/stage controls; no render or release acceptance claim.

The canonical renderer's real argument-error exit supplies a failed stage prefix
without executing research or rendering. Owner and packets come only from the
production Source admission, fixed stage factory and supervised OS processes.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from infrastructure.project.locked_dependency_export import normalize_locked_dependency_export
from tests.infra_tests.project.test_public_reference import (
    _clone_complete_reference,
    complete_reference as complete_reference,
)


_STAGE_PREFIX_CHILD = r"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import infrastructure
from infrastructure.core.implementation_custody import capture_implementation_custody
from infrastructure.core.pipeline.fingerprints import source_fingerprint
from infrastructure.core.pipeline.stage_launch import launch_python_stage
from infrastructure.reporting.native_format_acceptance_contracts import native_environment, public_source_digest
from infrastructure.reporting.native_format_acceptance_worker import _retained_native_stage_prefix
from infrastructure.reporting.native_format_acceptance_worker_closing import close_native_worker_custody
from infrastructure.reporting.native_format_portable_custody import executable_observation
from infrastructure.reporting.native_format_process_custody import native_host_observation
from infrastructure.reporting.native_format_scope_replay import _verify_native_stage_prefix
from infrastructure.reporting.native_source_external_admission import NativeExternalSourceBindings, admit_external_native_source
from infrastructure.reporting.native_tool_producer import native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

original, mirror = Path(sys.argv[1]), Path(sys.argv[4])
commit, fingerprint, deadline = sys.argv[2], sys.argv[3], float(sys.argv[5])
run_id = uuid4().hex
scope = "templates/template_code_project"
project = mirror / "projects" / scope
sdk = Path(infrastructure.__file__).resolve(strict=True).parent
assert sdk.is_relative_to(Path(sys.prefix).resolve(strict=True))
custody = capture_implementation_custody()
assert custody["binding_kind"] == "installed-distribution"
metadata = mirror.stat()
source = admit_external_native_source(
    NativeExternalSourceBindings(
        original, commit, fingerprint, mirror, (metadata.st_dev, metadata.st_ino),
        sdk, json.dumps(custody, sort_keys=True).encode(), run_id,
    ),
    deadline=deadline,
)
directory = mirror / "output/readiness/native-failed-prefix-control"
directory.mkdir(parents=True)
environment = native_environment(mirror, Path(sys.executable), directory)
identity = source_fingerprint(mirror, project)
pipeline_run = uuid4().hex


def stage(argument):
    return launch_python_stage(
        repo=mirror, project=project,
        argv=[sys.executable, str(mirror / "scripts/pipeline/stage_03_render.py"), argument],
        env=environment, deadline=deadline, stage_key="render_pdf", run_id=pipeline_run,
        source_digest=identity, definition=None, skip_path=directory / "skip.json", allow_skip=False,
    )


with native_producer_operation(source, run_id=run_id, deadline=deadline, scope=scope, directory=directory) as owner:
    raw = {"status": "fail", "execution_exit_code": 1, "diagnostic": "", "stage_children": [], "pipeline": {}}
    try:
        with _retained_native_stage_prefix(raw, owner):
            first = stage("--help")
            assert first.child_exit_code == 0, first
            failed = stage("--owned-unknown-render-option")
            assert failed.child_exit_code == 2, failed
            raw["pipeline"] = {"outcomes": [first.to_dict(), failed.to_dict()]}
            raise ValueError("fresh source-owned core execution did not complete: " + failed.diagnostic)
    except ValueError as error:
        raw["diagnostic"] = str(error)
    primary = raw["diagnostic"]
    assert "Stage script exited 2" in primary
    assert raw["status"] == "fail" and raw["execution_exit_code"] == 1
    assert len(raw["stage_children"]) == 2
    assert raw["stage_children"] == list(owner.stage_children)
    assert "analysis_data_graph" not in raw and "hydration_reconstruction" not in raw
    _verify_native_stage_prefix(raw, owner)
    reader = SnapshotReader(mirror, native_producer_operation=owner)
    packets = [reader.read(row["path"]).json_object() for row in raw["stage_children"]]
    # The live owner has already independently authenticated every packet. Keep
    # its actual signed process failures in addition to the controller outcomes.
    assert len({row["path"] for row in raw["stage_children"]}) == 2
    assert [packet["original_exit_code"] for packet in packets] == [0, 2]
    original_pipeline = deepcopy(raw["pipeline"])

    # A genuinely later authenticated stage must not replace a captured prefix,
    # including when an exception occurs after the graph capture boundary.
    frozen = {"status": "fail", "execution_exit_code": 1, "diagnostic": primary, "stage_children": []}
    try:
        with _retained_native_stage_prefix(frozen, owner) as capture:
            capture()
            held = deepcopy(frozen["stage_children"])
            later = stage("--help")
            assert later.child_exit_code == 0, later
            try:
                capture()
            except ValueError as error:
                assert "already captured" in str(error)
            else:
                raise AssertionError("a second capture must refuse")
            raise RuntimeError("observer failed after capture")
    except RuntimeError:
        pass
    assert frozen["stage_children"] == held and len(held) == 2
    assert len(owner.stage_children) == 3
    try:
        _verify_native_stage_prefix(frozen, owner)
    except ValueError as error:
        assert "completed=2, expected=3" in str(error)
    else:
        raise AssertionError("a genuinely changed authenticated prefix must refuse")

    raw.update(library_custody_before={}, runtime_providers={"before": {}, "after": {}})
    before = public_source_digest(mirror)
    host = native_host_observation()
    interpreter = executable_observation(Path(sys.executable))
    closing_arguments = dict(
        root=mirror, before=before, formats=(), directory=directory,
        specification={"source_inputs": {"providers": {}}}, source_context=source,
        native_reader=SnapshotReader(mirror, native_producer_operation=owner), runtime={}, deadline=deadline,
        host_before=host, interpreter_before=interpreter,
    )
    close_native_worker_custody(raw, **closing_arguments)
    assert raw["primary_diagnostic"] == raw["diagnostic"] == primary
    assert raw.get("closing_custody_diagnostics", []) == []

    # Real post-capture Source mutation, not substituted providers or authority.
    # No later operation reuses this invalidated Source context.
    target = mirror / "README.md"
    target.write_bytes(target.read_bytes() + b"\nOwned closing-custody refusal control.\n")
    close_native_worker_custody(raw, **closing_arguments)
    assert raw["primary_diagnostic"] == primary
    assert len(raw["closing_custody_diagnostics"]) >= 2
    assert "public source changed during native execution" in raw["closing_custody_diagnostics"]
    assert any("source/provider closing custody failed" in reason for reason in raw["closing_custody_diagnostics"])
    assert raw["diagnostic"].startswith(primary + "; ")
    assert all(reason in raw["diagnostic"] for reason in raw["closing_custody_diagnostics"])
    assert raw["pipeline"] == original_pipeline
    assert raw["status"] == "fail" and raw["execution_exit_code"] == 1
"""


@pytest.mark.timeout(1800)
def test_genuine_failed_stage_prefix_and_changed_capture_preserve_primary_closing_diagnostics(
    complete_reference: tuple[Path, str, str], tmp_path: Path
) -> None:
    original, commit, fingerprint = complete_reference
    deadline = time.monotonic() + 1200
    mirror = _clone_complete_reference(complete_reference, tmp_path / "mirror", deadline=deadline)
    environment = dict(os.environ, UV_OFFLINE="1", UV_PYTHON_DOWNLOADS="never")

    def run(arguments: list[str], *, cwd: Path, timeout: float) -> None:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
            timeout=min(timeout, max(1.0, deadline - time.monotonic())),
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    artifacts = tmp_path / "artifacts"
    run(
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
        timeout=90,
    )
    wheels = list(artifacts.glob("*.whl"))
    assert len(wheels) == 1
    installed = tmp_path / "installed-sdk"
    run(
        ["uv", "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(installed)],
        cwd=tmp_path,
        timeout=15,
    )
    python = installed / "bin/python"
    requirements = tmp_path / "runtime-requirements.txt"
    run(
        [
            "uv",
            "export",
            "--offline",
            "--locked",
            "--no-default-groups",
            "--group",
            "rendering",
            "--group",
            "dev",
            "--no-emit-package",
            "desloppify",
            "--no-emit-project",
            "--no-emit-local",
            "--no-header",
            "--no-annotate",
            "--output-file",
            str(requirements),
        ],
        cwd=original,
        timeout=30,
    )
    normalize_locked_dependency_export(
        original, requirements, minor=f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    run(
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
            str(python),
            "--requirements",
            str(requirements),
        ],
        cwd=tmp_path,
        timeout=120,
    )
    run(
        [
            "uv",
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-build",
            "--no-deps",
            "--python",
            str(python),
            str(wheels[0]),
        ],
        cwd=tmp_path,
        timeout=30,
    )
    child = tmp_path / "genuine-native-prefix.py"
    child.write_text(_STAGE_PREFIX_CHILD, encoding="utf-8")
    prefix = tmp_path / "fresh-owned-bytecode-prefix"
    prefix.mkdir()
    result = subprocess.run(
        [
            str(python),
            "-I",
            "-X",
            f"pycache_prefix={prefix}",
            str(child),
            str(original),
            commit,
            fingerprint,
            str(mirror),
            str(deadline),
        ],
        cwd=tmp_path,
        env={"PATH": os.environ.get("PATH", os.defpath), "LC_ALL": "C", "HOME": str(tmp_path)},
        text=True,
        capture_output=True,
        timeout=max(1.0, deadline - time.monotonic()),
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

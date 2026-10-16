"""Actual selected interpreters and environment DATA; no Source owner fabricated."""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

import packaging
import pytest

from infrastructure.core._bounded_kill import _RUN_IDS_ENV
from infrastructure.core.pipeline.stages import PIPELINE_STAGE_TIMEOUT_SECONDS, _stage_launch_deadline
from infrastructure.core.secrets import strip_secret_env
from infrastructure.project.public_acceptance_evidence import bootstrap_command
from infrastructure.reporting.native_environment_custody import capture_native_environment, validate_native_environment
from infrastructure.reporting.native_format_acceptance_contracts import native_environment
from infrastructure.reporting.native_original_supervisor import _worker_environment
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@pytest.fixture(scope="module")
def cold_python(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Real fresh venv; reuse existing dependencies read-only, without acquisition.

    This proves interpreter selection, not complete Root installation. The exact
    existing dependency site is explicit; no SDK distribution/custody is invented.
    """
    root = tmp_path_factory.mktemp("native-selected-runtime")
    environment = root / "cold"
    result = subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(environment)],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    interpreter = environment / "bin/python"
    site = subprocess.run(
        [str(interpreter), "-I", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert site.returncode == 0, site.stderr
    # The optional prepared-runtime adapter imports packaging even for deps[].
    (Path(site.stdout.strip()) / "owned-readonly-dependencies.pth").write_text(
        str(Path(packaging.__file__).resolve(strict=True).parents[1]) + "\n"
    )
    return interpreter


def _root_probe(tmp_path: Path, interpreter: Path, environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    root = tmp_path / "mirror"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname="owned-runtime-input"\nversion="0.0.0"\ndependencies=[]\n')
    (root / "probe.py").write_text(
        "import sys\nfrom pathlib import Path\n"
        "from infrastructure.core.runtime.prepared_runtime import check_prepared_root_runtime,PreparedRuntimeUnavailable\n"
        "try: check_prepared_root_runtime(Path.cwd())\n"
        "except PreparedRuntimeUnavailable as error:\n"
        " print(type(error).__name__+': '+str(error));raise SystemExit(75)\n"
        "print(str(Path(sys.prefix).absolute()))\n"
    )
    assert not (root / ".venv").exists()
    return subprocess.run(
        bootstrap_command(interpreter, root, "probe"),
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("ambient", ["absent", "wrong"])
def test_actual_cold_selected_root_runtime_overrides_missing_or_wrong_ambient_nomination(
    tmp_path: Path, cold_python: Path, monkeypatch: pytest.MonkeyPatch, ambient: str
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    if ambient == "absent":
        monkeypatch.delenv("TEMPLATE_ROOT_PYTHON", raising=False)
    else:
        monkeypatch.setenv("TEMPLATE_ROOT_PYTHON", str(tmp_path / "wrong/bin/python"))
    env = native_environment(tmp_path, cold_python, tmp_path / "execution")
    assert env["TEMPLATE_ROOT_PYTHON"] == str(cold_python)
    result = _root_probe(tmp_path, cold_python, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == str(cold_python.parent.parent)


def test_missing_root_nomination_still_blocks_actual_prepared_runtime(
    tmp_path: Path, cold_python: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    env = native_environment(tmp_path, cold_python, tmp_path / "execution")
    del env["TEMPLATE_ROOT_PYTHON"]
    result = _root_probe(tmp_path, cold_python, env)
    assert result.returncode == 75
    assert (
        "PreparedRuntimeUnavailable" in result.stdout
        and "missing, broken, or not an absolute executable" in result.stdout
    )


@pytest.mark.parametrize("mutation", ["none", "missing", "wrong", "post-selection-edit"])
def test_actual_popen_environment_matches_held_source_commitment_and_refuses_changed_digest(
    tmp_path: Path, mutation: str
) -> None:
    # These are environment DATA predicates, not a fabricated Original/Source
    # capability. The real Python process observes the exact supplied Popen map.
    source = {"PATH": os.defpath, "LC_ALL": "C", "OWNED_INPUT": "selected-before-launch"}
    selected, digest = _worker_environment(source)
    source["OWNED_INPUT"] = "caller-changed-after-selection"
    token = secrets.token_hex(16)
    bounded = {**strip_secret_env(selected), _RUN_IDS_ENV: token}
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import os,json,sys;print(json.dumps({key:os.environ[key] for key in json.loads(sys.argv[1])}))",
            json.dumps(sorted(bounded)),
        ],
        cwd=tmp_path,
        env=bounded,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    assert actual == bounded and selected["OWNED_INPUT"] == "selected-before-launch"
    custody = capture_native_environment(selected, strip_secret_env(selected), bounded, actual, token, None)
    raw = {"environment_custody": custody, "loader_lifecycle": None}
    tool = {"environment_digest": digest}
    if mutation == "missing":
        tool.clear()
    elif mutation == "wrong":
        tool["environment_digest"] = "0" * 64
    elif mutation == "post-selection-edit":
        tool["environment_digest"] = _worker_environment(source)[1]
    if mutation == "none":
        validate_native_environment(raw, tool, SnapshotReader(tmp_path))
    else:
        with pytest.raises(ValueError, match="Source-selected"):
            validate_native_environment(raw, tool, SnapshotReader(tmp_path))


@pytest.mark.parametrize("remaining", [900.0, 0.01, -1.0])
def test_stage_launch_retains_exact_nearer_or_expired_original_deadline(remaining: float) -> None:
    deadline = time.monotonic() + remaining
    assert _stage_launch_deadline(deadline) == deadline


def test_stage_launch_keeps_existing_phase_ceiling_with_a_later_original_deadline() -> None:
    before = time.monotonic()
    deadline = before + PIPELINE_STAGE_TIMEOUT_SECONDS + 1000
    selected = _stage_launch_deadline(deadline)
    after = time.monotonic()
    assert before + PIPELINE_STAGE_TIMEOUT_SECONDS <= selected <= after + PIPELINE_STAGE_TIMEOUT_SECONDS
    assert selected <= deadline

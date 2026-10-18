"""Fixed transport boundaries use real processes, never replacement GitHub tools."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.project._hosted_api import bind_reader_credentials, fixed_hosted_api
from infrastructure.project.public_hosted_origin import _api_command


def _api(tmp_path: Path, **changes):
    directory = tmp_path / "output/readiness/hosted-control"
    directory.mkdir(parents=True, exist_ok=True)
    arguments = dict(
        repository="docxology/template",
        run_id=1,
        head_sha="a" * 40,
        deadline=time.monotonic() + 20,
        environment=build_bounded_env(),
    )
    arguments.update(changes)
    return fixed_hosted_api(tmp_path, directory, **arguments)


@pytest.mark.parametrize(
    "repository",
    [
        "./template",
        "../template",
        "docxology/.",
        "docxology/..",
        "docxology/template/extra",
        "https://github.com/x/y",
        "x/y?query=1",
    ],
)
def test_fixed_api_refuses_ambiguous_repository_before_any_process(tmp_path: Path, repository: str) -> None:
    with pytest.raises(ValueError, match="repository|designated"):
        _api(tmp_path, repository=repository)


@pytest.mark.parametrize(
    "method,value",
    [
        ("artifact_page", 0),
        ("artifact_page", 12),
        ("job_page", -1),
        ("job_page", True),
        ("artifact_metadata", False),
        ("artifact_metadata", -2),
    ],
)
def test_fixed_api_rejects_invalid_identity_and_page_before_launch(tmp_path: Path, method: str, value: int) -> None:
    api = _api(tmp_path)
    with pytest.raises(ValueError, match="integer|bound"):
        getattr(api, method)(value)
    assert not tuple((tmp_path / "output/readiness/hosted-control").glob("*-process.json"))


@pytest.mark.parametrize("deadline", [float("nan"), float("inf"), -1.0])
def test_fixed_api_preserves_finite_existing_deadline(tmp_path: Path, deadline: float) -> None:
    with pytest.raises((ValueError, TimeoutError)):
        _api(tmp_path, deadline=deadline)


@pytest.mark.parametrize(
    "command",
    [
        [sys.executable, "-c", "raise SystemExit(0)"],
        _api_command("https://example.invalid/leak"),
        _api_command("repos/another/owner/actions/runs/1"),
    ],
)
def test_even_private_executor_refuses_arbitrary_command_host_and_owner(tmp_path: Path, command: list[str]) -> None:
    api = _api(tmp_path, environment={**build_bounded_env(), "GH_TOKEN": "harmless-" + uuid4().hex})
    with pytest.raises(ValueError, match="arbitrary"):
        api._execute(command, "rejected")
    assert not tuple((tmp_path / "output/readiness/hosted-control").glob("*-process.json"))


def test_credential_binding_refuses_data_instead_of_genuine_source() -> None:
    with pytest.raises(ValueError, match="genuine admitted Source"):
        bind_reader_credentials(object(), deadline=time.monotonic() + 20)


def test_actual_reader_entry_consumes_nomination_without_minting_source(tmp_path: Path) -> None:
    directory = tmp_path / "output/readiness/hosted-control"
    directory.mkdir(parents=True)
    root = Path(__file__).resolve().parents[3]
    sentinel = "harmless-" + uuid4().hex
    program = """import os,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from infrastructure.project._hosted_api import reader_credential_nomination,fixed_hosted_api
with reader_credential_nomination():
 assert 'GH_TOKEN' not in os.environ
 try:
  fixed_hosted_api(Path(sys.argv[2]),Path(sys.argv[3]),repository='docxology/template',run_id=1,
                  head_sha='a'*40,deadline=time.monotonic()+10,environment=dict(os.environ))
 except ValueError as error:
  assert 'admitted reader Source' in str(error)
 else:raise AssertionError('nomination DATA minted an admitted credential owner')
assert 'GH_TOKEN' not in os.environ
print('consumed-only-no-source-authority')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", program, str(root), str(tmp_path), str(directory)],
        env={**build_bounded_env(), "GH_TOKEN": sentinel},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "consumed-only-no-source-authority"
    assert sentinel not in result.stdout + result.stderr
    assert not tuple(directory.glob("*-process.json"))

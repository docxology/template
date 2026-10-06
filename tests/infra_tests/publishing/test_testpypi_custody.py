"""Actual children and genuine native wheel controls for canonical TestPyPI custody.

No index/upload/install is performed by this offline module. The genuine build
control uses only prepared native uv and backend tools; missing tools fail it.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tarfile
from io import BytesIO
from pathlib import Path

import pytest

from infrastructure.publishing.pypi import PyPIAdapter, PyPIConfig
from infrastructure.publishing.pypi_release import (
    Deadline,
    Distribution,
    TestPyPIError,
    admit_retrieved,
    admit_sdist,
    build_package,
    freeze_build_source,
    run_command,
    run_test_pypi_release,
    verify_candidate_wheel,
)

pytestmark = pytest.mark.timeout(60)


def _root(root: Path) -> Path:
    root.mkdir()
    (root / "infrastructure").mkdir()
    (root / "infrastructure/__init__.py").write_text("def measure():\n    return 17\n")
    (root / "README.md").write_text("# Owned package\n\nMeasured control.\n")
    (root / "LICENSE").write_text("Invented fixture license\n")
    (root / "pyproject.toml").write_text(
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n'
        '[project]\nname="research-project-template"\nversion="4.0.0"\n'
        'requires-python=">=3.12"\nreadme="README.md"\nlicense={file="LICENSE"}\n'
        '[tool.hatch.build.targets.wheel]\npackages=["infrastructure"]\n'
        '[tool.hatch.build.targets.sdist]\ninclude=["/infrastructure","/README.md","/LICENSE","/pyproject.toml"]\n'
    )
    return root


@pytest.mark.parametrize("code", [0, 2, 7])
def test_real_child_exit_codes_are_retained(tmp_path: Path, code: int) -> None:
    result = run_command(
        (sys.executable, "-I", "-c", f"raise SystemExit({code})"), tmp_path, check=False, deadline=Deadline.start(15)
    )
    assert result.returncode == code
    assert result.original_returncode == code
    assert result.timed_out is False
    if code:
        with pytest.raises(TestPyPIError, match=f"exit {code}") as caught:
            run_command(
                (sys.executable, "-I", "-c", f"raise SystemExit({code})"), tmp_path, deadline=Deadline.start(15)
            )
        assert caught.value.state == "fail" and caught.value.exit_code == 1


def test_real_child_both_channels_and_error_redact_credentials(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    token = "invented-pypi-token"
    code = "import os,sys; value=os.environ['TWINE_PASSWORD']; print(value); print(value,file=sys.stderr); sys.exit(7)"
    with pytest.raises(TestPyPIError) as caught:
        run_command(
            (sys.executable, "-I", "-c", code),
            tmp_path,
            deadline=Deadline.start(15),
            env={**os.environ, "TWINE_PASSWORD": token},
            sensitive_values=(token,),
        )
    captured = capsys.readouterr()
    assert token not in captured.out + captured.err + str(caught.value)
    assert "<redacted>" in captured.out and "<redacted>" in captured.err
    assert caught.value.exit_code == 1


@pytest.mark.parametrize("code", ["raise SystemExit(130)", "import os,signal; os.kill(os.getpid(),signal.SIGINT)"])
def test_actual_child_interruption_preserves_130(tmp_path: Path, code: str) -> None:
    with pytest.raises(TestPyPIError) as caught:
        run_command((sys.executable, "-I", "-c", code), tmp_path, deadline=Deadline.start(15))
    assert caught.value.state == "interrupted" and caught.value.exit_code == 130


def test_actual_timeout_kills_detached_descendant(tmp_path: Path) -> None:
    pid = tmp_path / "detached.pid"
    child = "import os,pathlib,time; pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(60)" % str(pid)
    parent = (
        "import subprocess,sys,time; subprocess.Popen([sys.executable,'-I','-c',%r],start_new_session=True); time.sleep(60)"
        % child
    )
    with pytest.raises(TestPyPIError) as caught:
        run_command((sys.executable, "-I", "-c", parent), tmp_path, deadline=Deadline.start(4))
    assert caught.value.state == "timed_out" and caught.value.exit_code == 124
    assert pid.is_file(), "the real detached child must have launched"
    descendant = int(pid.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(descendant, 0)


@pytest.mark.parametrize("seconds", [0, -1, float("inf"), float("nan"), True])
def test_invalid_deadline_refuses_before_execution(seconds: float) -> None:
    with pytest.raises(ValueError, match="positive and finite"):
        Deadline.start(seconds)


def test_source_snapshot_preserves_existing_dist_and_rejects_real_mutation(tmp_path: Path) -> None:
    root = _root(tmp_path / "root")
    old = root / "dist/previous.whl"
    old.parent.mkdir()
    old.write_bytes(b"retained previous release")
    scratch = tmp_path / "private"
    scratch.mkdir()
    deadline = Deadline.start(30)
    source = freeze_build_source(root, scratch, deadline)
    assert source.requirement.package == "research-project-template"
    assert source.requirement.version == source.requirement.platform_version == "4.0.0"
    assert old.read_bytes() == b"retained previous release"
    run_command(
        (
            sys.executable,
            "-I",
            "-c",
            "import pathlib; pathlib.Path(%r).write_text('def measure(): return 99\\n')"
            % str(root / "infrastructure/__init__.py"),
        ),
        scratch,
        deadline=deadline,
    )
    with pytest.raises(TestPyPIError, match="public source changed"):
        source.assert_current(deadline)
    assert old.read_bytes() == b"retained previous release"


def test_genuine_uv_build_admits_metadata_and_source_sdist_with_negative_control(tmp_path: Path) -> None:
    root = _root(tmp_path / "root")
    old = root / "dist/retained.whl"
    old.parent.mkdir()
    old.write_bytes(b"immutable old distribution")
    scratch = tmp_path / "private"
    scratch.mkdir()
    deadline = Deadline.start(45)
    source = freeze_build_source(root, scratch, deadline)
    uv = shutil.which("uv")
    assert uv is not None, "repository's prepared uv is required"
    wheel, artifacts = build_package(source, scratch, uv, deadline)
    assert wheel.package == "research-project-template"
    assert "infrastructure/__init__.py" in wheel.members
    assert len(artifacts) == 2
    assert old.read_bytes() == b"immutable old distribution"
    sdist = next(item for item in artifacts if item.kind == "sdist")
    admit_sdist(sdist.content, sdist.path.name, source)
    # A genuine tar is rewritten with different runtime bytes, preserving its
    # canonical metadata/name. Identity alone must not authorize these bytes.
    buffer = BytesIO()
    with tarfile.open(fileobj=BytesIO(sdist.content), mode="r:gz") as original:
        with tarfile.open(fileobj=buffer, mode="w:gz") as changed:
            for member in original:
                stream = original.extractfile(member) if member.isfile() else None
                if member.name.endswith("infrastructure/__init__.py"):
                    content = b"def measure(): return 99\n"
                    member.size = len(content)
                    changed.addfile(member, BytesIO(content))
                else:
                    changed.addfile(member, stream)
    with pytest.raises(ValueError, match="unowned or different source"):
        admit_sdist(buffer.getvalue(), sdist.path.name, source)
    with pytest.raises(ValueError, match="filename differs"):
        admit_sdist(sdist.content, "template-4.0.0.tar.gz", source)


def _retrieval(scratch: Path) -> tuple[tuple[Distribution, ...], dict[str, object]]:
    content = b"original uploaded artifact"
    name = "research_project_template-4.0.0-py3-none-any.whl"
    original = scratch / "original" / name
    original.parent.mkdir()
    original.write_bytes(content)
    returned = scratch / "retrieval/downloaded" / name
    returned.parent.mkdir(parents=True)
    returned.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    artifacts = (Distribution(original, content, digest, "wheel"),)
    observation: dict[str, object] = {
        "package": "research-project-template",
        "version": "4.0.0",
        "nonce": "a" * 32,
        "artifacts": [
            {
                "filename": name,
                "sha256": digest,
                "size": len(content),
                "url": "https://test-files.pythonhosted.org/packages/owned/" + name,
            }
        ],
    }
    return artifacts, observation


def test_actual_retrieved_bytes_reject_forged_new_hash_and_wrong_identity(tmp_path: Path) -> None:
    artifacts, observation = _retrieval(tmp_path)
    kwargs = {"package": "research-project-template", "version": "4.0.0", "nonce": "a" * 32}
    returned = admit_retrieved(tmp_path, artifacts, observation, **kwargs)
    assert returned[0].content == artifacts[0].content
    run_command(
        (
            sys.executable,
            "-I",
            "-c",
            "import pathlib; pathlib.Path(%r).write_bytes(b'forged bytes')" % str(returned[0].path),
        ),
        tmp_path,
        deadline=Deadline.start(15),
    )
    forged = json.loads(json.dumps(observation))
    forged["artifacts"][0].update(sha256=hashlib.sha256(b"forged bytes").hexdigest(), size=len(b"forged bytes"))
    with pytest.raises(ValueError, match="originally uploaded bytes"):
        admit_retrieved(tmp_path, artifacts, forged, **kwargs)
    for field, value in (("package", "template"), ("version", "3.0.0"), ("nonce", "b" * 32)):
        wrong = {**observation, field: value}
        with pytest.raises(ValueError, match="package/version/run identity"):
            admit_retrieved(tmp_path, artifacts, wrong, **kwargs)


def test_missing_credentials_and_production_contract_are_blocked(tmp_path: Path) -> None:
    with pytest.raises(TestPyPIError) as caught:
        run_test_pypi_release("", repo_root=tmp_path)
    assert caught.value.state == "blocked" and caught.value.exit_code == 75
    result = PyPIAdapter(PyPIConfig(test=False, token="invented"), env={}).publish(tmp_path, dry_run=False)
    assert result.status == "blocked" and result.ok is False
    assert result.receipt is None
    wrong_destination = PyPIAdapter(PyPIConfig(test=True, repository_url="https://other.invalid/upload"), env={})
    refused = wrong_destination.publish(tmp_path, dry_run=False)
    assert refused.status == "error" and refused.ok is False


def test_explicit_wheel_verifier_rejects_original_hash_before_runtime(tmp_path: Path) -> None:
    wheel = tmp_path / "candidate.whl"
    wheel.write_bytes(b"changed candidate")
    with pytest.raises(ValueError, match="supplied original wheel hash"):
        verify_candidate_wheel(wheel, hashlib.sha256(b"original candidate").hexdigest(), repo_root=tmp_path)
    with pytest.raises(ValueError, match="original wheel SHA"):
        verify_candidate_wheel(wheel, "", repo_root=tmp_path)


def test_cli_missing_original_identity_cannot_contact_index(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    environment = {key: value for key, value in os.environ.items() if key != "TEST_PYPI_API_TOKEN"}
    result = run_command(
        (sys.executable, str(root / "scripts/publish/verify_install.py")),
        tmp_path,
        env=environment,
        check=False,
        deadline=Deadline.start(20),
    )
    assert result.returncode == 2 and "--wheel" in result.stderr and "--sha256" in result.stderr
    blocked = run_command(
        (sys.executable, str(root / "scripts/publish/test_pypi.py")),
        tmp_path,
        env=environment,
        check=False,
        deadline=Deadline.start(20),
    )
    assert blocked.returncode == 75 and "blocked" in blocked.stderr

"""Real portable controls for the hosted execution-user preparation boundary.

No local test creates an account, invokes sudo, or replaces an OS dependency.
The actual Linux credential transition remains a hosted integration obligation.
"""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

from infrastructure.core.testing.ci_execution_user import _environment, _git, _hosted, _payload
from infrastructure.core.testing._ci_execution_files import (
    _checkout_link,
    _copy_cache,
    _detach,
    _export,
    _open_physical,
    _physical,
    _signature,
    _stable_copy,
    _tool_assets,
    _tool_entries,
)


def test_environment_carries_declared_runtime_data_without_credentials() -> None:
    values = {
        "GITHUB_SHA": "a" * 40,
        "TEMPLATE_FORMAL_TLC_JAR": "/tmp/template-fixtures/tla2tools.jar",
        "UV_FROZEN": "true",
        "UV_PYTHON_INSTALL_DIR": "/tmp/runner-temp/uv-python-dir",
        "GITHUB_TOKEN": "private-token",
        "AWS_SECRET_ACCESS_KEY": "private-key",
        "LD_PRELOAD": "/private/injection.so",
        "BASH_ENV": "/private/shell",
        "PYTHONHOME": "/private/runtime",
        "HOME": "/private/original-home",
    }
    assert _environment(values) == {
        key: values[key] for key in ("GITHUB_SHA", "TEMPLATE_FORMAL_TLC_JAR", "UV_FROZEN", "UV_PYTHON_INSTALL_DIR")
    }
    with pytest.raises(ValueError, match="invalid runtime DATA"):
        _environment({"SHARD": "1\nGITHUB_TOKEN=secret"})


def test_physical_paths_and_descriptor_reads_refuse_real_parent_symlinks(tmp_path: Path) -> None:
    root = tmp_path.resolve(strict=True)
    outside = root / "outside"
    outside.mkdir()
    (outside / "private").write_bytes(b"private")
    link = root / "linked"
    link.symlink_to(outside, target_is_directory=True)
    assert _physical(outside) == outside
    with pytest.raises(ValueError, match="symlinked"):
        _physical(link)
    with pytest.raises(OSError):
        _open_physical(link / "private", os.O_RDONLY)
    with pytest.raises(ValueError, match="absolute physical"):
        _physical(Path("relative"))
    temporary = root / "runner-temp"
    temporary.mkdir()
    managed = temporary / "uv-python-dir"
    environment, selected, assets, admitted = _tool_assets(
        {"UV_PYTHON_INSTALL_DIR": str(managed)},
        ["/usr/bin", str(managed)],
        temporary,
        temporary / "template-ci-execution",
    )
    assert selected == ["/usr/bin"] and assets == set() and admitted is None
    assert "UV_PYTHON_INSTALL_DIR" not in environment
    managed.mkdir()
    managed.chmod(0o755)
    (managed / "bin").mkdir()
    (managed / "bin").chmod(0o755)
    executable = managed / "bin/python"
    executable.write_bytes(b"public tool fixture, never executed")
    executable.chmod(0o755)
    public = root / "public-runtime-donor"
    public.write_bytes(b"shared public runtime bytes")
    public.chmod(0o644)
    shared = managed / "shared-library"
    shared.hardlink_to(public)
    shared_before = _signature(public.stat())
    environment, selected, assets, admitted = _tool_assets(
        {"UV_PYTHON_INSTALL_DIR": str(managed)},
        ["/usr/bin", str(managed)],
        temporary,
        temporary / "template-ci-execution",
    )
    assert environment["UV_PYTHON_INSTALL_DIR"] == str(managed)
    assert selected == ["/usr/bin", str(managed)] and assets == {managed} and admitted == managed
    assert _tool_entries(assets, admitted, time.monotonic() + 10) == []
    assert _signature(public.stat()) == shared_before
    checkout = root / "checkout"
    venv_bin = checkout / ".venv/bin"
    venv_bin.mkdir(parents=True)
    python = venv_bin / "python"
    python.symlink_to(executable)
    assert _checkout_link(python, checkout, admitted) == executable
    with pytest.raises(ValueError, match="escaping checkout"):
        _checkout_link(python, checkout, None)
    (checkout / "outside-venv").symlink_to(executable)
    with pytest.raises(ValueError, match="escaping checkout"):
        _checkout_link(checkout / "outside-venv", checkout, admitted)
    with pytest.raises(ValueError, match="unrecognized job tool root"):
        _tool_assets(environment, [str(temporary / "unrelated")], temporary, temporary / "template-ci-execution")
    with pytest.raises(ValueError, match="unrecognized managed Python root"):
        _tool_assets(
            {"UV_PYTHON_INSTALL_DIR": str(outside)}, [str(outside)], temporary, temporary / "template-ci-execution"
        )
    with pytest.raises(ValueError, match="no admitted physical root"):
        _tool_assets({}, [str(managed)], temporary, temporary / "template-ci-execution")
    with pytest.raises(ValueError, match="no admitted physical root"):
        _tool_assets(environment, [str(managed / "../unrelated")], temporary, temporary / "template-ci-execution")
    private_runtime = managed / "private-runtime"
    private_runtime.write_bytes(b"public runtime requiring a read ACL")
    private_runtime.chmod(0o600)
    assert _tool_entries(assets, admitted, time.monotonic() + 10) == [private_runtime]
    private_link = root / "private-runtime-donor"
    private_link.hardlink_to(private_runtime)
    with pytest.raises(ValueError, match="unsafe job tool entry"):
        _tool_entries(assets, admitted, time.monotonic() + 10)
    private_link.unlink()
    (managed / "credential-link").symlink_to(outside / "private")
    with pytest.raises(ValueError, match="escaping job tool link"):
        _tool_entries(assets, admitted, time.monotonic() + 10)
    (managed / "credential-link").unlink()
    (managed / ".netrc").write_bytes(b"credential fixture")
    with pytest.raises(ValueError, match="credential/config managed Python"):
        _tool_entries(assets, admitted, time.monotonic() + 10)
    symlink_temp = root / "symlink-temp"
    symlink_temp.mkdir()
    symlink_python = symlink_temp / "uv-python-dir"
    symlink_python.symlink_to(managed, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinked or noncanonical"):
        _tool_assets(
            {"UV_PYTHON_INSTALL_DIR": str(symlink_python)},
            [str(symlink_python)],
            symlink_temp,
            symlink_temp / "template-ci-execution",
        )
    symlink_python.unlink()
    symlink_python.symlink_to(symlink_temp / "missing", target_is_directory=True)
    with pytest.raises(FileNotFoundError):
        _tool_assets(
            {"UV_PYTHON_INSTALL_DIR": str(symlink_python)},
            [str(symlink_python)],
            symlink_temp,
            symlink_temp / "template-ci-execution",
        )
    if os.geteuid() != 0:
        symlink_temp.chmod(0)
        try:
            with pytest.raises(PermissionError):
                _tool_assets(
                    {"UV_PYTHON_INSTALL_DIR": str(symlink_python)},
                    [str(symlink_python)],
                    symlink_temp,
                    symlink_temp / "template-ci-execution",
                )
        finally:
            symlink_temp.chmod(0o700)


def test_actual_cold_copy_ignores_atime_and_preserves_source_identity(tmp_path: Path) -> None:
    root = tmp_path.resolve(strict=True)
    source, copied = root / "original", root / "copy"
    source.write_bytes(bytes(range(256)) * 8192)
    source.chmod(0o600)
    os.utime(source, ns=(1_000_000_000, 2_000_000_000))
    before = _signature(source.stat())
    assert _stable_copy(source, copied, time.monotonic() + 10, mode=0o644) == 2 * 1024**2
    assert copied.read_bytes() == source.read_bytes()
    assert _signature(source.stat()) == before
    assert stat.S_IMODE(copied.stat().st_mode) == 0o644
    assert copied.stat().st_ino != source.stat().st_ino
    with pytest.raises(FileExistsError):
        _stable_copy(source, copied, time.monotonic() + 10)


def test_hardlink_detachment_keeps_donor_bytes_owner_and_mode(tmp_path: Path) -> None:
    root = tmp_path.resolve(strict=True)
    donor, checkout = root / "donor", root / "checkout"
    donor.write_bytes(b"prepared locked runtime")
    donor.chmod(0o755)
    checkout.hardlink_to(donor)
    before = donor.stat()
    _detach(checkout, time.monotonic() + 10)
    assert checkout.read_bytes() == donor.read_bytes() == b"prepared locked runtime"
    after = donor.stat()
    assert (after.st_ino, after.st_uid, after.st_gid, after.st_mode) == (
        before.st_ino,
        before.st_uid,
        before.st_gid,
        before.st_mode,
    )
    assert checkout.stat().st_ino != after.st_ino
    assert checkout.stat().st_nlink == after.st_nlink == 1


def test_public_cache_copy_uses_independent_files_and_confined_links(tmp_path: Path) -> None:
    root = tmp_path.resolve(strict=True)
    cache, copied = root / "public-cache", root / "private-cache"
    (cache / "packages").mkdir(parents=True)
    original = cache / "packages/runtime"
    original.write_bytes(b"authentic public dependency bytes")
    original.chmod(0o755)
    (cache / "runtime").symlink_to("packages/runtime")
    _copy_cache(cache, copied, time.monotonic() + 10)
    assert (copied / "runtime").read_bytes() == original.read_bytes()
    assert (copied / "runtime").resolve() == copied / "packages/runtime"
    assert (copied / "packages/runtime").stat().st_ino != original.stat().st_ino
    assert original.stat().st_nlink == 1


def test_public_cache_escaping_link_is_refused_without_copying_target(tmp_path: Path) -> None:
    root = tmp_path.resolve(strict=True)
    cache, copied = root / "public-cache", root / "private-cache"
    cache.mkdir()
    private = root / "credential"
    private.write_bytes(b"private")
    (cache / "escape").symlink_to(private)
    with pytest.raises(ValueError, match="escaping public cache link"):
        _copy_cache(cache, copied, time.monotonic() + 10)
    assert private.read_bytes() == b"private" and not (copied / "escape").exists()


def test_failed_readiness_evidence_exports_exactly_without_runtime_admission(tmp_path: Path) -> None:
    root = tmp_path.resolve(strict=True)
    readiness, stage = root / "output/readiness", root / "artifacts"
    (readiness / "failed-original").mkdir(parents=True)
    stage.mkdir()
    source = readiness / "failed-original/receipt.json"
    source.write_bytes(b'{"exit_code":17,"accepted":false}\n')
    source.chmod(0o600)
    (readiness / "failed-original/census-spec.json").write_bytes(b"{}\n")
    scratch = readiness / "failed-original/pytest-tmp"
    scratch.mkdir()
    (scratch / "test-symlink").symlink_to(source)
    os.mkfifo(scratch / "test-fifo")
    before = _signature(source.stat())
    excluded: list[str] = []
    assert _export(readiness, stage, time.monotonic() + 10, exclusions=excluded) == source.stat().st_size + 3
    assert excluded == ["failed-original/pytest-tmp"]
    assert not (stage / "failed-original/pytest-tmp").exists()
    copied = stage / "failed-original/receipt.json"
    assert copied.read_bytes() == source.read_bytes()
    assert stat.S_IMODE(copied.stat().st_mode) == 0o644
    assert stat.S_IMODE(copied.parent.stat().st_mode) == 0o755
    assert _signature(source.stat()) == before
    with pytest.raises(ValueError, match="fresh artifact"):
        _export(readiness, stage, time.monotonic() + 10)


def test_artifact_export_refuses_real_symlinks_and_special_files(tmp_path: Path) -> None:
    root = tmp_path.resolve(strict=True)
    readiness, stage = root / "readiness", root / "artifacts"
    readiness.mkdir()
    stage.mkdir()
    outside = root / "private"
    outside.write_bytes(b"private")
    link = readiness / "escape"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="link/special"):
        _export(readiness, stage, time.monotonic() + 10)
    link.unlink()
    os.mkfifo(readiness / "fifo")
    with pytest.raises(ValueError, match="link/special"):
        _export(readiness, stage, time.monotonic() + 10)
    assert not any(stage.iterdir()) and outside.read_bytes() == b"private"


def test_original_argv_output_and_nonzero_exit_survive_real_subprocess(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path.resolve(strict=True)
    literal = "literal ; $(touch injected) ' \" value"
    program = "import pathlib,sys; pathlib.Path('observed').write_text(sys.argv[1]); print('original-output'); raise SystemExit(17)"
    assert _payload([sys.executable, "-I", "-B", "-c", program, literal], {"PATH": "/usr/bin:/bin"}, root) == 17
    assert capfd.readouterr().out == "original-output\n"
    assert (root / "observed").read_text() == literal
    assert not (root / "injected").exists()
    assert _payload([sys.executable, "-I", "-B", "-c", "raise SystemExit(0)"], {}, root) == 0
    assert (
        _payload([sys.executable, "-I", "-B", "-c", "import os,signal; os.kill(os.getpid(),signal.SIGTERM)"], {}, root)
        == -15
    )


def test_actual_platform_refuses_privileged_setup_without_hosted_authority(tmp_path: Path) -> None:
    values = {"GITHUB_ACTIONS": "false", "RUNNER_OS": "Linux", "RUNNER_ENVIRONMENT": "github-hosted"}
    with pytest.raises(ValueError, match="requires"):
        _hosted(values)
    command = [
        sys.executable,
        "-B",
        "-m",
        "infrastructure.core.testing.ci_execution_user",
        "prepare",
        "--state",
        str(tmp_path / "state.json"),
    ]
    result = subprocess.run(
        command, env={"PATH": os.environ.get("PATH", "")}, capture_output=True, timeout=10, check=False
    )
    assert result.returncode == 1
    assert b'"execution_profile_error": "ValueError"' in result.stderr
    assert not (tmp_path / "state.json").exists()


def test_real_git_binds_clean_initialized_and_uninitialized_submodules(tmp_path: Path) -> None:
    root = tmp_path.resolve(strict=True)
    parent, donor = root / "parent", root / "donor"
    parent.mkdir()
    donor.mkdir()
    environment = {
        "PATH": "/usr/bin:/bin",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "Execution profile fixture",
        "GIT_AUTHOR_EMAIL": "execution-profile@example.invalid",
        "GIT_COMMITTER_NAME": "Execution profile fixture",
        "GIT_COMMITTER_EMAIL": "execution-profile@example.invalid",
    }

    def git(directory: Path, *arguments: str) -> bytes:
        return subprocess.run(
            [
                "/usr/bin/git",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "commit.gpgsign=false",
                "-C",
                str(directory),
                *arguments,
            ],
            env=environment,
            capture_output=True,
            timeout=10,
            check=True,
        ).stdout

    git(donor, "init", "--quiet")
    (donor / "tracked").write_bytes(b"committed child bytes\n")
    git(donor, "add", "tracked")
    git(donor, "commit", "--quiet", "-m", "Initial child")
    git(parent, "init", "--quiet")
    git(parent, "-c", "protocol.file.allow=always", "submodule", "add", "--quiet", str(donor), "vendor/real")
    git(parent, "commit", "--quiet", "-m", "Pin actual child")
    initialized = git(parent, "submodule", "status", "--recursive")
    assert initialized.startswith(b" ")
    first = _git(parent, time.monotonic() + 10)
    assert first["submodules"] == hashlib.sha256(initialized).hexdigest()
    git(parent, "submodule", "deinit", "--force", "--", "vendor/real")
    uninitialized = git(parent, "submodule", "status", "--recursive")
    assert uninitialized.startswith(b"-")
    second = _git(parent, time.monotonic() + 10)
    assert second["submodules"] == hashlib.sha256(uninitialized).hexdigest() != first["submodules"]
    assert {key: first[key] for key in ("head", "tree", "index")} == {
        key: second[key] for key in ("head", "tree", "index")
    }
    git(parent, "-c", "protocol.file.allow=always", "submodule", "update", "--init", "--", "vendor/real")
    assert (
        _git(parent, time.monotonic() + 10)["submodules"]
        == hashlib.sha256(git(parent, "submodule", "status", "--recursive")).hexdigest()
    )
    child = parent / "vendor/real"
    (child / "tracked").write_bytes(b"actual dirty child bytes\n")
    with pytest.raises(ValueError, match="tracked checkout changes"):
        _git(parent, time.monotonic() + 10)
    git(child, "add", "tracked")
    git(child, "commit", "--quiet", "-m", "Advance child beyond pin")
    assert git(parent, "submodule", "status", "--recursive").startswith(b"+")
    with pytest.raises(ValueError, match="tracked checkout changes"):
        _git(parent, time.monotonic() + 10)

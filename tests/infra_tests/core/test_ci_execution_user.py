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

from infrastructure.core.testing.ci_execution_user import _environment, _git, _hosted, _payload, _source_identity
from infrastructure.core.testing._ci_execution_files import (
    _checkout_link,
    _copy_cache,
    _detach,
    _export,
    _export_pytest_case_diagnostics,
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
        "TEMPLATE_TEST_PDFIUM_WHEEL": "/tmp/template-pdfium-wheel-owned/provider.whl",
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
        key: values[key]
        for key in (
            "GITHUB_SHA",
            "TEMPLATE_FORMAL_TLC_JAR",
            "TEMPLATE_TEST_PDFIUM_WHEEL",
            "UV_FROZEN",
            "UV_PYTHON_INSTALL_DIR",
        )
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
    wheel_directory = temporary / "template-pdfium-wheel-owned"
    wheel_directory.mkdir()
    wheel = wheel_directory / "provider.whl"
    wheel.write_bytes(b"Owned transport DATA, not an installed provider")
    projected = _environment({"TEMPLATE_TEST_PDFIUM_WHEEL": str(wheel)})
    wheel_environment, _, wheel_assets, wheel_python = _tool_assets(
        projected, ["/usr/bin"], temporary, temporary / "template-ci-execution"
    )
    assert wheel_environment["TEMPLATE_TEST_PDFIUM_WHEEL"] == str(wheel)
    assert wheel_assets == {wheel_directory} and wheel_python is None
    assert _tool_entries(wheel_assets, wheel_python, time.monotonic() + 10)
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


@pytest.mark.parametrize("reader_mode", (0o700, 0o750, 0o755))
def test_case_diagnostics_keep_numbered_failures_without_traversing_source(tmp_path: Path, reader_mode: int) -> None:
    base = tmp_path.resolve(strict=True)
    base.chmod(reader_mode)
    root, destination = base / "pytest-of-owner", base / "case-artifacts"
    originals = {
        "pytest-8/popen-gw1/test_child_failure0/worker.stderr": b"original\x00stderr\n",
        "pytest-8/popen-gw1/test_child_failure0/cli-observations/child/exit.json": b'{"returncode":7}\n',
        "pytest-8/popen-gw1/complete-public-source-data0.git-stage.trace2.json": b'{"event":"exit","code":0}\n',
        "pytest-7/test_guard1/runtime-observation.json": b'{"accepted":false}\n',
        "pytest-7/test_guard1/output/readiness/evidence/native.stdout": b"original native refusal\n",
        "pytest-7/test_guard1/output/readiness/evidence/html-python-source-owned0/closure.json": b'{"closed":false}\n',
    }
    for relative, payload in originals.items():
        source = root / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(payload)
    private = base / "private"
    private.mkdir()
    (private / "private.stdout").write_bytes(b"must never be transported")
    (private / "readiness/evidence").mkdir(parents=True)
    (private / "readiness/evidence/never-copy.stderr").write_bytes(b"private aliased fixture bytes")
    case = root / "pytest-8/popen-gw1/test_child_failure0"
    (case / "checkout").symlink_to(private, target_is_directory=True)
    (case / "output").symlink_to(private, target_is_directory=True)
    source_fixture = root / "pytest-8/popen-gw1/complete-public-source-data0"
    source_fixture.mkdir()
    (source_fixture / "never-copy.stdout").write_bytes(b"private fixture Source bytes")
    (case / "browser-profile").mkdir()
    os.mkfifo(case / "browser-profile/never-read.stdout")
    (root / "pytest-current").symlink_to(root / "pytest-8", target_is_directory=True)
    before = {relative: _signature((root / relative).lstat()) for relative in originals}
    assert _export_pytest_case_diagnostics(root, destination, time.monotonic() + 10, uid=os.getuid()) == sum(
        len(payload) for payload in originals.values()
    )
    assert {
        path.relative_to(destination).as_posix(): path.read_bytes() for path in destination.rglob("*") if path.is_file()
    } == originals
    assert {relative: _signature((root / relative).lstat()) for relative in originals} == before
    assert stat.S_IMODE(destination.stat().st_mode) == reader_mode
    assert not (destination / "pytest-current").exists()
    assert not (destination / "pytest-8/popen-gw1/test_child_failure0/checkout").exists()
    assert not (destination / "pytest-8/popen-gw1/test_child_failure0/output").exists()
    assert not (destination / "pytest-8/popen-gw1/complete-public-source-data0").exists()
    assert (private / "private.stdout").read_bytes() == b"must never be transported"


def test_case_diagnostics_refuse_post_census_hardlinks_before_artifact_exposure(tmp_path: Path) -> None:
    base = tmp_path.resolve(strict=True)
    root, destination = base / "pytest-of-owner", base / "case-artifacts"
    source = root / "pytest-0/test_original0/original.stderr"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"original stderr")
    private = base / "private"
    private.write_bytes(b"private substituted bytes")
    changed = False

    def substitute(frame, event, _arg):
        nonlocal changed
        if frame.f_code is _stable_copy.__code__ and event == "call" and not changed:
            changed = True
            source.unlink()
            os.link(private, source)
        return None

    previous = sys.gettrace()
    try:
        sys.settrace(substitute)
        with pytest.raises(ValueError):
            _export_pytest_case_diagnostics(root, destination, time.monotonic() + 10, uid=os.getuid())
    finally:
        sys.settrace(previous)
    assert changed and not destination.exists()
    assert private.read_bytes() == b"private substituted bytes"


@pytest.mark.parametrize("kind", ("symlink", "hardlink", "fifo", "directory"))
def test_case_diagnostics_refuse_physical_payload_substitution(tmp_path: Path, kind: str) -> None:
    base = tmp_path.resolve(strict=True)
    root, destination = base / "pytest-of-owner", base / "case-artifacts"
    case = root / "pytest-0/popen-gw0/test_refusal0"
    case.mkdir(parents=True)
    outside = base / "private"
    outside.write_bytes(b"never copy substituted private bytes")
    payload = case / "original.stderr"
    if kind == "symlink":
        payload.symlink_to(outside)
    elif kind == "hardlink":
        os.link(outside, payload)
    elif kind == "fifo":
        os.mkfifo(payload)
    else:
        payload.mkdir()
    with pytest.raises(ValueError):
        _export_pytest_case_diagnostics(root, destination, time.monotonic() + 10, uid=os.getuid())
    assert not destination.exists() and outside.read_bytes() == b"never copy substituted private bytes"


@pytest.mark.parametrize("boundary", ("bytes", "entries", "deadline", "owner"))
def test_case_diagnostics_retain_combined_budget_and_account_boundaries(tmp_path: Path, boundary: str) -> None:
    base = tmp_path.resolve(strict=True)
    root, destination = base / "pytest-of-owner", base / "case-artifacts"
    case = root / "pytest-0/test_budget0"
    case.mkdir(parents=True)
    payload = case / "original.stdout"
    payload.write_bytes(b"original")
    before = _signature(payload.lstat())
    with pytest.raises(ValueError):
        _export_pytest_case_diagnostics(
            root,
            destination,
            time.monotonic() - 1 if boundary == "deadline" else time.monotonic() + 10,
            uid=os.getuid() + (boundary == "owner"),
            byte_budget=7 if boundary == "bytes" else 100,
            entry_budget=3 if boundary == "entries" else 100,
        )
    assert not destination.exists() and payload.read_bytes() == b"original"
    assert _signature(payload.lstat()) == before


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


def test_real_git_rejects_parent_as_checkout_source(tmp_path: Path) -> None:
    root = tmp_path.resolve(strict=True)
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

    def git(*arguments: str) -> bytes:
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
                str(root),
                *arguments,
            ],
            env=environment,
            capture_output=True,
            timeout=10,
            check=True,
        ).stdout

    git("init", "--quiet")
    (root / "tracked").write_bytes(b"original Source\n")
    git("add", "tracked")
    git("commit", "--quiet", "-m", "Original Source")
    expected = git("rev-parse", "HEAD").decode().strip()
    (root / "tracked").write_bytes(b"different child Source\n")
    git("add", "tracked")
    git("commit", "--quiet", "-m", "Different child Source")
    actual = git("rev-parse", "HEAD").decode().strip()
    assert git("rev-list", "--parents", "-n", "1", "HEAD").decode().split()[1:] == [expected]

    with pytest.raises(ValueError, match="checkout differs from GitHub Source identity"):
        _source_identity(root, time.monotonic() + 10, expected)

    assert _source_identity(root, time.monotonic() + 10, actual)["head"] == actual

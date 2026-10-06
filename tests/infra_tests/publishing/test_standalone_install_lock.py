"""Exact lock transformations plus genuine UV installation from an owned Git fixture."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.standalone_install_lock import (
    PROVIDER_URLS,
    ROOT_PACKAGE,
    checkout_providers,
    third_party_lock_sha256,
    transform_install_files,
)

ROOT = Path(__file__).resolve().parents[3]


def _metadata() -> bytes:
    return (
        '[project]\nname = "installation-fixture"\nversion = "1.0.0"\nrequires-python = ">=3.12"\n'
        'dependencies = ["research-project-template==4.0.0"]\n\n'
        '[tool.uv.sources]\nresearch-project-template = { path = "../../..", editable = true }\n'
    ).encode()


def _lock(*, third_party: bool = True) -> bytes:
    content = (
        'version = 1\nrevision = 3\nrequires-python = ">=3.12"\n\n'
        '[[package]]\nname = "installation-fixture"\nversion = "1.0.0"\nsource = { virtual = "." }\n'
        'dependencies = [{ name = "research-project-template" }]\n\n'
        '[package.metadata]\nrequires-dist = [{ name = "research-project-template", editable = "../../../" }]\n\n'
        '[[package]]\nname = "research-project-template"\nversion = "4.0.0"\n'
        'source = { editable = "../../../" }\n\n'
    )
    if third_party:
        content += (
            "# This exact scientific package block must survive.\n"
            '[[package]]\nname = "scientific-fixture"\nversion = "2.0.0"\n'
            'source = { registry = "https://pypi.org/simple" }\n'
            'wheels = [{ url = "https://example.invalid/fixture.whl", hash = "sha256:00", size = 1 }]\n'
        )
    return content.encode()


def _pins(version: str = "4.0.0") -> dict[str, dict[str, str]]:
    return {ROOT_PACKAGE: {"version": version, "repository": PROVIDER_URLS[ROOT_PACKAGE], "commit": "a" * 40}}


@pytest.mark.parametrize("scope", PUBLIC_PROJECT_NAMES)
def test_every_actual_public_lock_projects_without_changing_third_party_blocks(scope):
    project = ROOT / "projects" / scope
    metadata, lock = (project / "pyproject.toml").read_bytes(), (project / "uv.lock").read_bytes()
    versions = checkout_providers(metadata, lock)
    pins = {
        name: {"version": version, "repository": PROVIDER_URLS[name], "commit": "a" * 40}
        for name, version in versions.items()
    }
    projected_metadata, projected_lock, unchanged = transform_install_files(metadata, lock, pins)
    own = tomllib.loads(metadata.decode())["project"]["name"]
    assert unchanged == third_party_lock_sha256(lock, own)
    assert unchanged == third_party_lock_sha256(projected_lock, own)
    for name, pin in pins.items():
        assert tomllib.loads(projected_metadata.decode())["tool"]["uv"]["sources"][name] == {
            "git": pin["repository"],
            "rev": pin["commit"],
        }


@pytest.mark.parametrize(
    "fault", ["unknown", "conditional", "not-editable", "wrong-path", "missing-lock", "noncanonical", "duplicate"]
)
def test_refuse_unadmitted_checkout_shapes(fault):
    metadata, lock = _metadata(), _lock()
    if fault == "unknown":
        metadata = metadata.replace(b"research-project-template = {", b"unknown-provider = {")
    elif fault == "conditional":
        metadata = metadata.replace(
            b'{ path = "../../..", editable = true }', b'[{ path = "../../..", editable = true }]'
        )
    elif fault == "not-editable":
        metadata = metadata.replace(b"editable = true", b"editable = false")
    elif fault == "wrong-path":
        metadata = metadata.replace(b'path = "../../.."', b'path = "../../../private"')
    elif fault == "missing-lock":
        lock = lock.replace(
            b'source = { editable = "../../../" }', b'source = { registry = "https://pypi.org/simple" }'
        )
    elif fault == "noncanonical":
        metadata = metadata.replace(b"research-project-template = {", b"research_project_template = {")
    else:
        lock += b'\n[[package]]\nname="research-project-template"\nversion="4.0.0"\nsource={editable="../../../"}\n'
    with pytest.raises(ValueError):
        transform_install_files(metadata, lock, _pins())


def test_refuse_locked_provider_version_substitution():
    with pytest.raises(ValueError, match="versions differ"):
        transform_install_files(_metadata(), _lock(), _pins("3.0.0"))


def test_original_third_party_bytes_and_headers_survive_projection():
    metadata, lock = _metadata(), _lock()
    projected_metadata, projected_lock, _ = transform_install_files(metadata, lock, _pins())
    assert projected_metadata.split(b"[tool.uv.sources]", 1)[0] == metadata.split(b"[tool.uv.sources]", 1)[0]
    assert projected_lock.split(b"# This exact scientific", 1)[1] == lock.split(b"# This exact scientific", 1)[1]
    assert projected_lock.split(b"[[package]]", 1)[0] == lock.split(b"[[package]]", 1)[0]


@pytest.mark.parametrize("name", ["installation-fixture", "Installation_Fixture", "INSTALLATION.FIXTURE"])
def test_third_party_digest_normalizes_the_actual_project_identity(name):
    _, projected, digest = transform_install_files(_metadata(), _lock(), _pins())
    assert third_party_lock_sha256(_lock(), name) == digest
    assert third_party_lock_sha256(projected, name) == digest


def test_actual_uv_locked_offline_install_accepts_transformed_git_fields(tmp_path):
    """Owned file:// Git proves encoding/installation, not public remote availability."""
    uv = shutil.which("uv")
    assert uv is not None, "the declared UV toolchain must be prepared"
    parent = tmp_path.resolve()
    provider = parent / "provider"
    provider.mkdir()
    (provider / "pyproject.toml").write_text(
        '[project]\nname="research-project-template"\nversion="4.0.0"\nrequires-python=">=3.12"\n'
        '[build-system]\nrequires=[]\nbuild-backend="fixture_backend"\nbackend-path=["."]\n'
    )
    (provider / "fixture_backend.py").write_text(
        "import pathlib, zipfile\n"
        "def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):\n"
        "    name='research_project_template-4.0.0-py3-none-any.whl'\n"
        "    prefix='research_project_template-4.0.0.dist-info/'\n"
        "    files={'infrastructure/__init__.py':'VALUE=7\\n',\n"
        "      prefix+'METADATA':'Metadata-Version: 2.1\\nName: research-project-template\\nVersion: 4.0.0\\n',\n"
        "      prefix+'WHEEL':'Wheel-Version: 1.0\\nGenerator: public-fixture\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n'}\n"
        "    files[prefix+'RECORD']=''.join(key+',,\\n' for key in files)+prefix+'RECORD,,\\n'\n"
        "    with zipfile.ZipFile(pathlib.Path(wheel_directory)/name,'w') as archive:\n"
        "        for key, value in files.items(): archive.writestr(key,value)\n"
        "    return name\n"
    )
    environment = {key: value for key, value in os.environ.items() if not key.startswith(("GIT_", "UV_", "PYTHON"))}
    environment.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")
    for args in (
        ["init", "-q"],
        ["config", "user.name", "Public fixture"],
        ["config", "user.email", "fixture@example.invalid"],
        ["add", "-A"],
        ["commit", "-qm", "Local codec fixture"],
    ):
        subprocess.run(["git", *args], cwd=provider, env=environment, capture_output=True, timeout=20, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=provider,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    ).stdout.strip()
    pins = {ROOT_PACKAGE: {"version": "4.0.0", "repository": provider.as_uri(), "commit": commit}}
    metadata, lock, _ = transform_install_files(_metadata(), _lock(third_party=False), pins)
    project = parent / "consumer"
    project.mkdir()
    (project / "pyproject.toml").write_bytes(metadata)
    (project / "uv.lock").write_bytes(lock)
    before = (metadata, lock)
    environment.update(UV_CACHE_DIR=str(parent / "cache"), UV_PYTHON_DOWNLOADS="never")
    # Initial preparation reads only the explicitly owned file:// provider.
    # The next invocation proves ordinary reuse with networking disabled.
    for offline in (False, True):
        if offline:
            environment["UV_OFFLINE"] = "1"
        installed = subprocess.run(
            [
                uv,
                "sync",
                "--locked",
                *(["--offline"] if offline else []),
                "--no-python-downloads",
                "--no-build-isolation",
                "--python",
                sys.executable,
            ],
            cwd=project,
            env=environment,
            capture_output=True,
            text=True,
            timeout=90,
        )
        assert installed.returncode == 0, installed.stderr
    assert ((project / "pyproject.toml").read_bytes(), (project / "uv.lock").read_bytes()) == before
    actual = subprocess.run(
        [
            str(project / ".venv/bin/python"),
            "-I",
            "-c",
            "import infrastructure; assert infrastructure.VALUE == 7; print(infrastructure.__file__)",
        ],
        cwd=parent,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    assert "site-packages" in actual.stdout and str(provider) not in actual.stdout

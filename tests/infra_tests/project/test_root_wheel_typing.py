"""Actual distributions and isolated installed consumers prove the public type boundary."""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.timeout(180)
def test_actual_wheel_and_sdist_ship_types_for_independent_strict_consumers(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    environment = dict(os.environ, UV_OFFLINE="1", UV_PYTHON_DOWNLOADS="never")
    built = subprocess.run(
        ["uv", "build", "--offline", "--no-build-isolation", "--no-create-gitignore", "--out-dir", str(artifacts)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    wheels, sources = list(artifacts.glob("*.whl")), list(artifacts.glob("*.tar.gz"))
    assert len(wheels) == len(sources) == 1
    marker = (ROOT / "infrastructure/py.typed").read_bytes()
    native_roots = tuple(
        "infrastructure/steganography/kmyth/" + relative + "/"
        for relative in ("bin", "lib", "obj", "logger/obj", "utils/obj")
    )
    authored_native = "infrastructure/steganography/kmyth/src/main/seal.c"
    with zipfile.ZipFile(wheels[0]) as archive:
        assert archive.read("infrastructure/py.typed") == marker
        assert not any(name.startswith(native_roots) for name in archive.namelist())
        assert archive.read(authored_native) == (ROOT / authored_native).read_bytes()
    with tarfile.open(sources[0], "r:gz") as archive:
        all_members = archive.getmembers()
        assert not any(member.name.split("/", 1)[-1].startswith(native_roots) for member in all_members)
        (source_member,) = [member for member in all_members if member.name.endswith("/" + authored_native)]
        source_stream = archive.extractfile(source_member)
        assert source_stream is not None and source_stream.read() == (ROOT / authored_native).read_bytes()
        members = [member for member in all_members if member.name.endswith("/infrastructure/py.typed")]
        assert len(members) == 1 and members[0].isfile()
        stream = archive.extractfile(members[0])
        assert stream is not None and stream.read() == marker
    isolated = tmp_path / "isolated"
    created = subprocess.run(
        ["uv", "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(isolated)],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert created.returncode == 0, created.stdout + created.stderr
    selected_python = isolated / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    installed = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--offline",
            "--no-deps",
            "--no-build",
            "--python",
            str(selected_python),
            str(wheels[0]),
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr
    expected_version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    imported = subprocess.run(
        [
            str(selected_python),
            "-I",
            "-c",
            "from pathlib import Path;import infrastructure,sys;"
            "source=Path(infrastructure.__file__).resolve();"
            "assert source.is_relative_to(Path(sys.prefix).resolve());"
            "assert (source.parent/'py.typed').is_file();"
            "assert infrastructure.__version__==sys.argv[1]",
            expected_version,
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert imported.returncode == 0, imported.stdout + imported.stderr
    consumer = tmp_path / "consumer.py"
    actual_types = (
        "from infrastructure.core.execution_boundary import BoundedSubprocessResult\n"
        "def original_exit(outcome: BoundedSubprocessResult) -> int:\n"
        "    return outcome.returncode\n"
    )
    environment.pop("MYPYPATH", None)
    environment.pop("PYTHONPATH", None)
    check_command = [
        sys.executable,
        "-I",
        "-m",
        "mypy",
        "--strict",
        "--no-incremental",
        "--no-error-summary",
        "--config-file",
        os.devnull,
        "--python-executable",
        str(selected_python),
        str(consumer),
    ]
    for invalid in (False, True):
        consumer.write_text(actual_types.replace("-> int", "-> str") if invalid else actual_types)
        checked = subprocess.run(
            check_command,
            cwd=tmp_path,
            env=environment,
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
        if invalid:
            assert (
                checked.returncode == 1
                and 'Incompatible return value type (got "int", expected "str")' in checked.stdout
            )
        else:
            assert checked.returncode == 0, checked.stdout + checked.stderr
        assert "import-untyped" not in checked.stdout
    installed_markers = list(isolated.glob("lib/python*/site-packages/infrastructure/py.typed"))
    if os.name == "nt":
        installed_markers = [isolated / "Lib/site-packages/infrastructure/py.typed"]
    assert len(installed_markers) == 1 and installed_markers[0].read_bytes() == marker
    installed_markers[0].unlink()  # Owned negative: installed-package discovery requires the marker.
    consumer.write_text(actual_types)
    missing_marker = subprocess.run(
        check_command,
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    assert missing_marker.returncode == 1 and "import-untyped" in missing_marker.stdout
    assert (ROOT / "infrastructure/py.typed").read_bytes() == marker

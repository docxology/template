"""TestPyPI build, upload, and installation verification helpers."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path


def _redact(text: str, sensitive_values: Sequence[str] = ()) -> str:
    redacted = text
    for value in sensitive_values:
        if value:
            redacted = redacted.replace(value, "<redacted>")
    return redacted


def _display_command(cmd: Sequence[str], sensitive_values: Sequence[str] = ()) -> str:
    return _redact(" ".join(cmd), sensitive_values)


def _twine_token_env(token: str) -> dict[str, str]:
    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = token
    return env


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    *,
    env: Mapping[str, str] | None = None,
    sensitive_values: Sequence[str] = (),
) -> subprocess.CompletedProcess[str]:
    """Run a command and stream output."""
    display = _display_command(cmd, sensitive_values)
    print(f"> {display}")
    result = subprocess.run(cmd, cwd=cwd, env=dict(env) if env is not None else None, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {display}")
    return result


def build_package() -> Path:
    """Build the package distribution using uv."""
    print("\n=== Building package with uv build ===")
    dist_dir = Path("dist").absolute()
    if dist_dir.exists():
        for path in dist_dir.iterdir():
            path.unlink()
    run_command(["uv", "build"])
    wheels = list(Path("dist").glob("*.whl"))
    sdists = list(Path("dist").glob("*.tar.gz"))
    if not wheels and not sdists:
        raise RuntimeError("Build failed: no distribution files found in dist/")
    print(f"Built {len(wheels)} wheel(s), {len(sdists)} sdist(s)")
    return dist_dir


def upload_to_testpypi(dist_dir: Path, token: str) -> None:
    """Upload distributions to TestPyPI using twine."""
    print("\n=== Uploading to TestPyPI ===")
    run_command([sys.executable, "-m", "pip", "install", "twine", "-q"])
    dist_files = sorted(dist_dir.glob("*.whl")) + sorted(dist_dir.glob("*.tar.gz"))
    if not dist_files:
        raise RuntimeError(f"No distribution files found in {dist_dir}")
    run_command(
        [
            sys.executable,
            "-m",
            "twine",
            "upload",
            "--repository",
            "testpypi",
            *[str(path) for path in dist_files],
        ],
        env=_twine_token_env(token),
        sensitive_values=(token,),
    )
    print("Uploaded to TestPyPI")


def install_and_verify(package_name: str = "template") -> None:
    """Create a fresh venv, install from TestPyPI, and run doctor."""
    print("\n=== Installing from TestPyPI in clean venv ===")
    with tempfile.TemporaryDirectory() as tmp:
        venv_path = Path(tmp) / "test_venv"
        run_command([sys.executable, "-m", "venv", str(venv_path)])
        pip_path = _venv_executable(venv_path, "pip")

        run_command([str(pip_path), "install", "--upgrade", "pip", "setuptools", "wheel", "-q"])
        print(f"Installing '{package_name}' from TestPyPI...")
        run_command(
            [
                str(pip_path),
                "install",
                "--index-url",
                "https://test.pypi.org/simple/",
                "--no-deps",
                package_name,
            ]
        )

        cli_path = _venv_executable(venv_path, "template")
        print(f"\nRunning: {cli_path} doctor")
        result = subprocess.run([str(cli_path), "doctor"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            raise RuntimeError("Installation verification failed: template doctor returned non-zero")
        print("\nInstallation verification passed: template doctor succeeded")


def run_test_pypi_release(token: str, package_name: str = "template") -> None:
    """Build, upload, and verify a package through TestPyPI."""
    dist_dir = build_package()
    upload_to_testpypi(dist_dir, token)
    install_and_verify(package_name)
    print("\n=== SUCCESS: Package is ready for PyPI release ===")


def _venv_executable(venv_path: Path, name: str) -> Path:
    unix_path = venv_path / "bin" / name
    if unix_path.exists():
        return unix_path
    return venv_path / "Scripts" / f"{name}.exe"

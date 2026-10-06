"""Check prepared installed requirements without resolver or installer activity."""

from __future__ import annotations

import importlib.metadata
import os
import sys
import sysconfig
import tomllib
from pathlib import Path

from infrastructure.core.files.secure_write import read_text_confined


class PreparedRuntimeUnavailable(RuntimeError):
    """A selected existing runtime or declared dependency is unavailable."""


def check_prepared_packages(requirements: list[str]) -> None:
    """Bind declared names and versions to actual selected distribution metadata.

    This is availability evidence, not proof of all installed member bytes.
    """
    from packaging.requirements import Requirement

    missing: list[str] = []
    for declaration in requirements:
        requirement = Requirement(declaration)
        if requirement.marker is not None and not requirement.marker.evaluate():
            continue
        try:
            version = importlib.metadata.version(requirement.name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(str(requirement))
            continue
        if requirement.specifier and not requirement.specifier.contains(version, prereleases=True):
            missing.append(f"{requirement} (installed {version})")
    if missing:
        raise PreparedRuntimeUnavailable("Prepared dependencies unavailable: " + ", ".join(missing))


def _prepared_venv(selected: Path) -> tuple[Path, dict[str, str]]:
    """Admit the selected lexical venv metadata without running site code."""
    if (
        not selected.is_absolute()
        or ".." in selected.parts
        or not selected.is_file()
        or not os.access(selected, os.X_OK)
    ):
        raise PreparedRuntimeUnavailable("Selected root interpreter is missing, broken, or not an absolute executable")
    if Path(sys.executable).absolute() != selected:
        raise PreparedRuntimeUnavailable("Actual interpreter differs from the selected lexical root interpreter")
    prefix = selected.parent.parent
    try:
        text = read_text_confined(prefix, prefix / "pyvenv.cfg", max_bytes=65536)
    except (OSError, ValueError) as exc:
        raise PreparedRuntimeUnavailable("Selected prepared venv lacks a regular no-follow pyvenv.cfg") from exc
    configuration = {
        key.strip().lower(): value.strip()
        for line in text.splitlines()
        for key, separator, value in [line.partition("=")]
        if separator
    }
    if not configuration.get("home") or prefix == Path(sys.base_prefix).absolute():
        raise PreparedRuntimeUnavailable("Selected prepared interpreter is not a virtual environment")
    return prefix, configuration


def configure_prepared_site(selected: Path, *, observed_prefix: str) -> None:
    """Expose declared venv package directories under -S without executing .pth.

    CPython 3.12–3.13 establishes venv prefixes in site initialization; 3.14
    establishes them before site. The outer seed records that actual initial
    prefix, then sets its lexical candidate before importing this stdlib-only
    admission module. Normal site processing belongs to the supervised CLI child.
    """
    if not sys.flags.no_site or sys.implementation.name != "cpython" or sys.version_info < (3, 12):
        raise PreparedRuntimeUnavailable("Prepared site admission requires isolated CPython 3.12+ with -S")
    prefix, configuration = _prepared_venv(selected)
    expected = prefix if sys.version_info >= (3, 14) else Path(sys.base_prefix).absolute()
    if Path(observed_prefix).absolute() != expected:
        raise PreparedRuntimeUnavailable("Observed no-site interpreter prefix differs from its selected venv")
    sys.prefix = sys.exec_prefix = str(prefix)
    bases = [(str(prefix), str(prefix))]
    if configuration.get("include-system-site-packages", "").lower() == "true":
        bases.append((sys.base_prefix, sys.base_exec_prefix))
    for base, platbase in bases:
        paths = sysconfig.get_paths(scheme="posix_prefix", vars={"base": base, "platbase": platbase})
        for name in ("purelib", "platlib"):
            directory = paths[name]
            if directory not in sys.path and Path(directory).is_dir():
                sys.path.append(directory)


def check_prepared_root_runtime(repo_root: Path, *, secure: bool = False) -> None:
    """Require the actual nominated interpreter and existing root dependencies."""
    if sys.version_info < (3, 12):
        raise PreparedRuntimeUnavailable("Python 3.12 or newer must be prepared explicitly")
    nomination = os.environ.get("TEMPLATE_ROOT_PYTHON")
    selected = Path(nomination) if nomination is not None else repo_root / ".venv/bin/python"
    prefix, _configuration = _prepared_venv(selected)
    if Path(sys.prefix).absolute() != prefix or sys.prefix == sys.base_prefix:
        raise PreparedRuntimeUnavailable("Actual runtime is outside the selected prepared venv")
    raw = tomllib.loads(read_text_confined(repo_root, repo_root / "pyproject.toml", max_bytes=1024 * 1024))
    project = raw.get("project")
    if not isinstance(project, dict):
        raise ValueError("Root pyproject requires a project declaration")
    requirements = project.get("dependencies", [])
    if not isinstance(requirements, list) or any(not isinstance(item, str) for item in requirements):
        raise ValueError("Root dependencies must be an array of requirement strings")
    check_prepared_packages(requirements)
    if secure:
        groups = raw.get("dependency-groups", {})
        secure_requirements = groups.get("steganography") if isinstance(groups, dict) else None
        if not isinstance(secure_requirements, list) or any(not isinstance(item, str) for item in secure_requirements):
            raise ValueError("Secure dispatch requires its declared steganography requirement group")
        check_prepared_packages(secure_requirements)


__all__ = [
    "PreparedRuntimeUnavailable",
    "check_prepared_packages",
    "check_prepared_root_runtime",
    "configure_prepared_site",
]

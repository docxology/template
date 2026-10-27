"""Filesystem admission of an explicitly selected analysis interpreter.

Binary bytes, lexical virtual-environment identity, and installed metadata are
separate from public source and executed-code custody. No resolver is invoked.
"""

from __future__ import annotations

import os
import hashlib
import re
import stat
import sys
import sysconfig
from pathlib import Path

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprint_files import anchored_parent, digest_file, observation, open_directory

SCHEMA = "template-selected-python-runtime/1"
MAX_SITE_ENTRIES = 32768
MAX_DISTRIBUTIONS = 2048
MAX_METADATA_BYTES = 64 * 1024 * 1024
ANALYSIS_REUSE_REFUSAL = (
    "Selected analysis dependencies have declaration identity only; installed member-byte custody "
    "cannot authorize reuse. Preserve the checkpoint and start a fresh run without --resume"
)


def is_analysis_capability(key: str | None, script: str | None = None, method: str | None = None) -> bool:
    """Stable keys and the canonical producer target prevent alias-based reuse."""
    return (
        key == "analysis"
        or (isinstance(key, str) and key.startswith("analysis:"))
        or (script is not None and Path(script).parts[-3:] == ("scripts", "pipeline", "stage_02_analysis.py"))
        or method == "run_analysis"
    )


class AnalysisRuntimeUnavailable(FileNotFoundError):
    """A nominated runtime is positively missing or unsupported for admission."""


def select_analysis_python(project_root: Path) -> Path:
    """Preserve the lexical interpreter that determines the actual venv prefix."""
    venv = project_root.absolute() / ".venv"
    if not os.path.lexists(venv):
        return Path(sys.executable).absolute()
    with anchored_parent(venv) as parent:
        if parent is None:
            raise AnalysisRuntimeUnavailable("Nominated project runtime is unavailable")
        metadata = os.stat(venv.name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError("Nominated project runtime must be a real directory")
    selected = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not selected.exists() or not os.access(selected, os.X_OK):
        raise AnalysisRuntimeUnavailable("Nominated project runtime has no usable Python interpreter")
    return selected


def _digest(path: Path, *, max_bytes: int) -> str:
    with anchored_parent(path) as parent:
        if parent is None:
            raise AnalysisRuntimeUnavailable("Selected runtime metadata is unavailable")
        try:
            observed = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError as exc:
            raise AnalysisRuntimeUnavailable("Selected runtime metadata is unavailable") from exc
        return digest_file(path, parent, path.name, observed, max_bytes=max_bytes)


def _configuration(prefix: Path) -> tuple[str, str]:
    cfg = prefix / "pyvenv.cfg"
    try:
        raw = read_bytes_confined(prefix, cfg, max_bytes=65536)
    except FileNotFoundError as exc:
        raise AnalysisRuntimeUnavailable("Nominated project runtime lacks pyvenv.cfg") from exc
    values: dict[str, str] = {}
    for line in raw.decode("utf-8").splitlines():
        key, separator, value = line.partition("=")
        if not separator:
            continue
        key, value = key.strip(), value.strip()
        if key in values:
            raise ValueError("Runtime configuration contains duplicate fields")
        values[key] = value
    version = values.get("version_info", values.get("version", ""))
    match = re.fullmatch(r"(3)\.(\d+)(?:\.[0-9]+)?(?:[A-Za-z0-9_.+-]*)", version)
    if match is None or int(match[2]) < 14:
        raise AnalysisRuntimeUnavailable("Nominated runtime must declare Python 3.14 or newer")
    if values.get("include-system-site-packages", "false").lower() != "false":
        raise AnalysisRuntimeUnavailable("Nominated runtime must isolate its declared site packages")
    return f"{match[1]}.{match[2]}", hashlib.sha256(raw).hexdigest()


def _installation_metadata(roots: tuple[Path, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    total = 0
    total_bytes = 0
    for index, root in enumerate(roots):
        with anchored_parent(root) as parent:
            if parent is None:
                continue
            try:
                metadata = os.stat(root.name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                continue
            if not stat.S_ISDIR(metadata.st_mode):
                raise ValueError("Selected site-packages root must be a real directory")
            with open_directory(parent, root.name) as descriptor:
                names: list[str] = []
                with os.scandir(descriptor) as entries:
                    for entry in entries:
                        total += 1
                        if total > MAX_SITE_ENTRIES:
                            raise ValueError("Runtime metadata entry ceiling exceeded")
                        if entry.name.endswith(".dist-info"):
                            names.append(entry.name)
                if len(names) > MAX_DISTRIBUTIONS:
                    raise ValueError("Runtime distribution ceiling exceeded")
                for name in sorted(names):
                    with open_directory(descriptor, name) as distribution:
                        for leaf in ("METADATA", "RECORD"):
                            target = root / name / leaf
                            try:
                                observed = os.stat(leaf, dir_fd=distribution, follow_symlinks=False)
                            except FileNotFoundError as exc:
                                raise AnalysisRuntimeUnavailable(
                                    "Selected distribution metadata is unavailable"
                                ) from exc
                            result[f"{index}/{name}/{leaf}"] = digest_file(
                                target,
                                distribution,
                                leaf,
                                observed,
                                max_bytes=min(16 * 1024 * 1024, MAX_METADATA_BYTES - total_bytes),
                            )
                            total_bytes += observed.st_size
                current: list[str] = []
                with os.scandir(descriptor) as entries:
                    for count, entry in enumerate(entries, 1):
                        if count > MAX_SITE_ENTRIES:
                            raise ValueError("Runtime metadata entry ceiling exceeded")
                        if entry.name.endswith(".dist-info"):
                            current.append(entry.name)
                if sorted(current) != sorted(names):
                    raise ValueError("Runtime distribution set changed during admission")
    return result


def analysis_runtime_binding(project_root: Path, *, interpreter: Path | None = None) -> dict[str, object]:
    """Bind the selected binary, prefix, configuration and metadata declarations."""
    selected = select_analysis_python(project_root) if interpreter is None else interpreter.absolute()
    with anchored_parent(selected) as parent:
        if parent is None:
            raise AnalysisRuntimeUnavailable("Selected interpreter is unavailable")
        try:
            initial = os.stat(selected.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError as exc:
            raise AnalysisRuntimeUnavailable("Selected interpreter is unavailable") from exc
        if not (stat.S_ISREG(initial.st_mode) or stat.S_ISLNK(initial.st_mode)):
            raise ValueError("Selected interpreter must nominate a regular executable")
        result = _runtime_binding(project_root, selected)
        if observation(os.stat(selected.name, dir_fd=parent, follow_symlinks=False)) != observation(initial):
            raise ValueError("Selected interpreter nomination changed during admission")
        return result


def _runtime_binding(project_root: Path, selected: Path) -> dict[str, object]:
    nominated = project_root.absolute() / ".venv"
    project_venv = selected == nominated / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    roots: tuple[Path, ...]
    if project_venv:
        prefix = nominated
        minor, configuration = _configuration(prefix)
        roots = (prefix / ("Lib/site-packages" if os.name == "nt" else f"lib/python{minor}/site-packages"),)
    else:
        if selected != Path(sys.executable).absolute():
            raise AnalysisRuntimeUnavailable("Analysis interpreter is outside the nominated runtime")
        prefix = Path(sys.prefix).absolute()
        minor = f"{sys.version_info.major}.{sys.version_info.minor}"
        roots = tuple(sorted({Path(sysconfig.get_path(name)).absolute() for name in ("purelib", "platlib")}))
        configuration = _digest(prefix / "pyvenv.cfg", max_bytes=65536) if (prefix / "pyvenv.cfg").exists() else ""
    binary = selected.resolve()
    identity: dict[str, object] = {
        "schema": SCHEMA,
        "executable": str(selected),
        "resolved_executable": str(binary),
        "binary_sha256": _digest(binary, max_bytes=512 * 1024 * 1024),
        "prefix": str(prefix),
        "python_minor": minor,
        "configuration_sha256": configuration,
        "site_roots": [str(path) for path in roots],
        "installation_metadata": _installation_metadata(roots),
        "dependency_scope": "metadata-record-declarations",
    }
    if selected.resolve() != binary:
        raise ValueError("Selected analysis interpreter changed during admission")
    return identity


def admit_current_analysis_runtime(project_root: Path, expected: dict[str, object]) -> dict[str, object]:
    """Observe actual selected-runtime facts before public domain execution."""
    actual = analysis_runtime_binding(project_root, interpreter=Path(sys.executable).absolute())
    if actual != expected:
        raise ValueError("Selected analysis runtime differs from its admitted binary/prefix/metadata")
    sites = sorted({str(Path(sysconfig.get_path(name)).absolute()) for name in ("purelib", "platlib")})
    if (
        (sys.version_info.major, sys.version_info.minor) < (3, 14)
        or f"{sys.version_info.major}.{sys.version_info.minor}" != expected["python_minor"]
        or str(Path(sys.prefix).absolute()) != expected["prefix"]
        or sites != expected["site_roots"]
    ):
        raise ValueError("Actual analysis runtime version/prefix/site roots do not match its admission")
    return {
        "executable": str(Path(sys.executable).absolute()),
        "prefix": str(Path(sys.prefix).absolute()),
        "python_version": sys.version,
        "implementation": sys.implementation.name,
        "site_roots": sites,
    }


def admitted_runtime_report(value: object, expected: dict[str, object]) -> bool:
    """Validate actual pre-domain observations against parent-admitted files."""
    return (
        isinstance(value, dict)
        and set(value) == {"executable", "prefix", "python_version", "implementation", "site_roots"}
        and value["executable"] == expected.get("executable")
        and value["prefix"] == expected.get("prefix")
        and value["site_roots"] == expected.get("site_roots")
        and isinstance(value["implementation"], str)
        and isinstance(value["python_version"], str)
        and isinstance(expected.get("python_minor"), str)
        and value["python_version"].startswith(str(expected["python_minor"]) + ".")
    )

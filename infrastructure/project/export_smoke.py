"""Clean-install and import-smoke exported public exemplars."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]

from infrastructure.project.copy_exemplar import export_exemplar
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


@dataclass(frozen=True)
class ExportSmokeResult:
    """Evidence from one clean exemplar export smoke test."""

    project_name: str
    import_targets: tuple[str, ...]
    manifest_files: int


def discover_import_targets(src_root: Path) -> tuple[str, ...]:
    """Return importable top-level modules and packages under ``src_root``."""
    targets: set[str] = set()
    if not src_root.is_dir():
        return ()
    # Several exemplars intentionally use ``src`` itself as their package
    # (``from src.analysis import ...``). In that layout, importing children as
    # unrelated top-level modules breaks their relative imports and would not
    # represent the documented standalone runtime.
    if (src_root / "__init__.py").is_file():
        return ("src",)
    for child in src_root.iterdir():
        if child.name.startswith("_"):
            continue
        if child.is_file() and child.suffix == ".py" and child.stem.isidentifier():
            targets.add(child.stem)
        elif child.is_dir() and child.name.isidentifier() and any(child.rglob("*.py")):
            targets.add(child.name)
    return tuple(sorted(targets))


def _sync_command(destination: Path, uv: str) -> list[str]:
    command = [uv, "sync", "--directory", str(destination)]
    pyproject = tomllib.loads((destination / "pyproject.toml").read_text(encoding="utf-8"))
    optional = pyproject.get("project", {}).get("optional-dependencies", {})
    if isinstance(optional, dict) and "dev" in optional:
        command.extend(("--extra", "dev"))
    if (destination / "uv.lock").is_file():
        command.append("--locked")
    return command


def smoke_exported_exemplar(
    repo_root: Path,
    project_name: str,
    destination: Path,
    *,
    timeout_seconds: int = 300,
) -> ExportSmokeResult:
    """Export, clean-install, and import every top-level ``src`` target."""
    export_exemplar(repo_root, project_name, destination)
    manifest = json.loads((destination / ".template-export.json").read_text(encoding="utf-8"))
    targets = discover_import_targets(destination / "src")
    if not targets:
        raise RuntimeError(f"{project_name}: exported src tree has no import targets")

    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required for clean exemplar export smoke tests")
    sync = subprocess.run(
        _sync_command(destination, uv),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if sync.returncode != 0:
        detail = sync.stderr.strip() or sync.stdout.strip()
        raise RuntimeError(f"{project_name}: clean install failed: {detail}")

    probe = "import importlib\n" + "\n".join(f"importlib.import_module({target!r})" for target in targets)
    env = os.environ.copy()
    python_root = destination if targets == ("src",) else destination / "src"
    bundled_resources = destination / "_template_resources"
    roots = [python_root]
    if bundled_resources.is_dir():
        roots.append(bundled_resources)
    env["PYTHONPATH"] = os.pathsep.join(str(root) for root in roots)
    smoke = subprocess.run(
        [uv, "run", "--directory", str(destination), "--no-sync", "python", "-c", probe],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        env=env,
    )
    if smoke.returncode != 0:
        detail = smoke.stderr.strip() or smoke.stdout.strip()
        raise RuntimeError(f"{project_name}: import smoke failed for {targets}: {detail}")
    return ExportSmokeResult(
        project_name=project_name,
        import_targets=targets,
        manifest_files=len(manifest.get("files", {})),
    )


def smoke_public_exemplars(
    repo_root: Path,
    projects: tuple[str, ...] = PUBLIC_PROJECT_NAMES,
    *,
    timeout_seconds: int = 300,
) -> tuple[ExportSmokeResult, ...]:
    """Run the clean export contract for each public exemplar in isolation."""
    results: list[ExportSmokeResult] = []
    with tempfile.TemporaryDirectory(prefix="template-export-smoke-") as temporary:
        base = Path(temporary)
        for project_name in projects:
            destination = base / project_name.split("/")[-1]
            results.append(
                smoke_exported_exemplar(
                    repo_root,
                    project_name,
                    destination,
                    timeout_seconds=timeout_seconds,
                )
            )
    return tuple(results)


__all__ = [
    "ExportSmokeResult",
    "discover_import_targets",
    "smoke_exported_exemplar",
    "smoke_public_exemplars",
]

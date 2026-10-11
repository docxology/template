"""Actual Root-checkout metadata poison controls for the child execution boundary."""

from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest
from infrastructure.core.project_paths import find_repo_root, resolve_project_root

ROOT = find_repo_root()
PROJECT = resolve_project_root(ROOT, "templates/template_autopoiesis")


def _copy_project(destination: Path) -> Path:
    shutil.copytree(
        PROJECT,
        destination,
        ignore=shutil.ignore_patterns("output", ".venv", "__pycache__", ".pytest_cache", ".coverage*", "*.egg-info"),
    )
    return destination


def _run(generator: Path, reference: Path, *, platform: Path) -> subprocess.CompletedProcess[str]:
    script = (
        "import sys,importlib.util;from pathlib import Path;"
        f"sys.path.insert(0,{str(platform)!r});"
        f"spec=importlib.util.spec_from_file_location('auto_bootstrap',{str(generator / 'scripts/_bootstrap.py')!r});"
        "assert spec is not None and spec.loader is not None;"
        "module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);"
        f"module.bootstrap_project(Path({str(generator)!r}));"
        "from template_autopoiesis.gates.realization_contract import realize_selected_children;"
        f"realize_selected_children(Path({str(reference)!r}),single=True)"
    )
    return subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=reference.parent,
        capture_output=True,
        text=True,
        timeout=150,
        check=False,
    )


@pytest.mark.timeout(180)
@pytest.mark.parametrize("fault", ["identity", "missing-lock"])
def test_actual_platform_checkout_metadata_faults_fail_before_materialization(tmp_path: Path, fault: str) -> None:
    platform = tmp_path / "platform"
    platform.mkdir()
    for name in ("infrastructure", "scripts"):
        shutil.copytree(ROOT / name, platform / name, ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("pyproject.toml", "uv.lock", ".python-version"):
        shutil.copy2(ROOT / name, platform / name)
    if fault == "identity":
        metadata = platform / "pyproject.toml"
        metadata.write_text(
            metadata.read_text().replace('name = "research-project-template"', 'name = "wrong-platform"')
        )
    else:
        (platform / "uv.lock").unlink()
    generator = _copy_project(tmp_path / "generator")
    reference = _copy_project(tmp_path / "reference")
    result = _run(generator, reference, platform=platform)
    assert result.returncode != 0, result.stdout
    receipt = json.loads((reference / "output/.pipeline/child_realization/single.json").read_text())
    assert receipt["status"] == "failed" and receipt["executed_children"] == []
    assert not (reference / "output/.pipeline/child_realization/workspaces").exists()

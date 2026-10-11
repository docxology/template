"""Fresh-export hydration against an actual independently installed platform wheel."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import time
import tomllib
from collections.abc import Iterator
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.project.copy_exemplar import export_exemplar
from infrastructure.project.installed_acceptance_artifacts import freeze_wheel_bytes
from infrastructure.project.installed_acceptance_runtime import freeze_locked_metadata, install_admitted_wheels
from infrastructure.project.installed_acceptance_worker import _environment
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import Requirement


@pytest.fixture(scope="module")
def genuine_platform_environment(
    repo_root: Path, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, dict[str, str]]:
    """Build the real current package with locked tools, then install its admitted bytes."""
    scratch = tmp_path_factory.mktemp("genuine-platform-wheel").resolve()
    environment = _environment(Path(sys.executable), scratch)
    uv = shutil.which("uv")
    assert uv is not None, "the declared installed acceptance requires uv"
    deadline = time.monotonic() + 600

    def run(command: tuple[str, ...], label: str):
        remaining = deadline - time.monotonic()
        assert remaining > 0, "genuine platform preparation exhausted its total deadline"
        observed = run_bounded_subprocess(command, cwd=scratch, env=environment, timeout=remaining)
        assert observed.returncode == 0 and not observed.timed_out, (
            f"{label}: {observed.stdout}\n{observed.stderr}\n{observed.command_error}"
        )
        return observed

    metadata = freeze_locked_metadata(repo_root, scratch)
    build_requirements = scratch / "build-requirements.txt"
    run(
        (
            uv,
            "export",
            "--directory",
            str(metadata.root),
            "--locked",
            "--offline",
            "--no-python-downloads",
            "--python",
            sys.executable,
            "--only-group",
            "installed-build",
            "--no-emit-project",
            "--no-header",
            "--no-annotate",
            "--output-file",
            str(build_requirements),
        ),
        "locked build tools",
    )
    build = scratch / "build-environment"
    run((uv, "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(build)), "build venv")
    run(
        (
            uv,
            "pip",
            "sync",
            "--offline",
            "--no-config",
            "--no-build",
            "--require-hashes",
            "--python",
            str(build / "bin/python"),
            str(build_requirements),
        ),
        "locked build installation",
    )
    wheels = scratch / "wheels"
    run(
        (
            uv,
            "build",
            "--wheel",
            "--offline",
            "--no-config",
            "--no-python-downloads",
            "--no-build-isolation",
            "--python",
            str(build / "bin/python"),
            "--out-dir",
            str(wheels),
            str(repo_root),
        ),
        "actual platform wheel",
    )
    candidates = tuple(wheels.glob("*.whl"))
    assert len(candidates) == 1
    root_metadata = tomllib.loads((repo_root / "pyproject.toml").read_text())["project"]
    version = root_metadata["version"]
    requirement = Requirement(
        "root:installed",
        "installed",
        "root",
        version,
        version,
        source_fingerprint(repo_root),
        package=root_metadata["name"],
    )
    admitted = freeze_wheel_bytes(
        repo_root, requirement, read_bytes_confined(scratch, candidates[0]), scratch, candidates[0].name
    )
    dependencies = scratch / "runtime-requirements.txt"
    run(
        (
            uv,
            "export",
            "--directory",
            str(metadata.root / "projects/templates/template_autoresearch_project"),
            "--locked",
            "--offline",
            "--no-python-downloads",
            "--python",
            sys.executable,
            "--no-default-groups",
            "--no-emit-project",
            "--no-emit-local",
            "--no-header",
            "--no-annotate",
            "--output-file",
            str(dependencies),
        ),
        "locked standalone dependencies",
    )
    assert metadata.unchanged()
    installed = scratch / "installed-environment"
    run(
        (uv, "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(installed)),
        "runtime venv",
    )
    python = installed / "bin/python"
    run(
        (
            uv,
            "pip",
            "sync",
            "--offline",
            "--no-config",
            "--no-build",
            "--require-hashes",
            "--python",
            str(python),
            str(dependencies),
        ),
        "locked runtime installation",
    )
    install_admitted_wheels(scratch, python, uv, [admitted], run)
    run((uv, "pip", "check", "--python", str(python)), "installed dependency check")
    return python, environment


@pytest.fixture
def standalone_workspace() -> Iterator[Path]:
    """Keep the real standalone outside pytest's possibly in-checkout basetemp."""
    with tempfile.TemporaryDirectory(prefix="autoresearch-installed-standalone-") as temporary:
        workspace = Path(temporary).resolve()
        assert all(not (ancestor / "infrastructure").is_dir() for ancestor in (workspace, *workspace.parents))
        yield workspace


@pytest.mark.parametrize("invalid_readiness", [False, True], ids=["complete", "invalid-domain-output"])
def test_fresh_export_hydrates_with_actual_platform_distribution(
    repo_root: Path,
    project_root: Path,
    genuine_platform_environment: tuple[Path, dict[str, str]],
    standalone_workspace: Path,
    invalid_readiness: bool,
) -> None:
    python, environment = genuine_platform_environment
    standalone = standalone_workspace / "template_autoresearch_project"
    export_exemplar(repo_root, "templates/template_autoresearch_project", standalone)
    assert all(not (ancestor / "infrastructure").is_dir() for ancestor in (standalone, *standalone.parents))
    # Hydration consumes real baseline domain outputs. The fresh source export
    # deliberately excludes outputs, and the control must recreate hydration results.
    shutil.copytree(
        project_root / "output",
        standalone / "output",
        ignore=shutil.ignore_patterns("__pycache__", ".pipeline", "logs", "telemetry"),
    )
    shutil.rmtree(standalone / "output/manuscript", ignore_errors=True)
    for relative in (
        "output/data/manuscript_variables.json",
        "output/data/manuscript_variable_provenance.json",
        "output/data/manuscript_figure_blocks.json",
        "output/reports/artifact_manifest.json",
    ):
        (standalone / relative).unlink(missing_ok=True)
    if invalid_readiness:
        payload_path = standalone / "output/data/autoresearch_loop.json"
        payload = json.loads(payload_path.read_text())
        payload["metrics"]["readiness_valid"] = False
        payload_path.write_text(json.dumps(payload))
    site = next((python.parent.parent / "lib").glob("python*/site-packages"))
    prefix = standalone_workspace / "fresh-bytecode"
    prefix.mkdir()
    audit = bytecode_audit_bootstrap(
        (site / "infrastructure", standalone / "scripts", standalone / "src"),
        prefix,
        audit_path=site / "infrastructure/core/bytecode_audit.py",
    )
    code = (
        audit
        + """
import importlib.metadata, json, runpy, sys
from pathlib import Path
project=Path(sys.argv[1]); script=project/'scripts/z_generate_manuscript_variables.py'
sys.path.insert(0,str(script.parent)); sys.argv=[str(script)]
import infrastructure
origin=Path(infrastructure.__file__).resolve()
assert origin.is_relative_to(Path(sys.prefix).resolve())
assert importlib.metadata.version('research-project-template')=='4.0.1'
try:
    runpy.run_path(str(script),run_name='__main__')
except SystemExit as error:
    if error.code not in (None,0): raise
for root in (origin.parent,project/'scripts',project/'src'):
    _audit_scope['verify_executed_source_code'](root,Path(sys.pycache_prefix))
print(json.dumps({'actual_platform_origin':str(origin),'platform_version':infrastructure.__version__}))
"""
    )
    observed = run_bounded_subprocess(
        (str(python), "-I", "-X", f"pycache_prefix={prefix}", "-c", code, str(standalone)),
        cwd=standalone_workspace,
        env=environment,
        timeout=120,
    )
    resolved = standalone / "output/manuscript/00_abstract.md"
    manifest = standalone / "output/reports/artifact_manifest.json"
    assert not observed.timed_out
    if invalid_readiness:
        assert observed.returncode != 0 and "valid final readiness" in observed.stderr
        assert not resolved.exists() and not manifest.exists()
    else:
        assert observed.returncode == 0, observed.stdout + observed.stderr
        assert "actual_platform_origin" in observed.stdout
        assert resolved.is_file() and "{{" not in resolved.read_text()
        rows = json.loads(manifest.read_text())["entries"]
        variables = standalone / "output/data/manuscript_variables.json"
        record = next(row for row in rows if row["path"] == "output/data/manuscript_variables.json")
        assert record["sha256"] == hashlib.sha256(variables.read_bytes()).hexdigest()

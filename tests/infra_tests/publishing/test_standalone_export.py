"""Actual canonical exporter imports reject replayed implementation bytecode."""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    tmp_path = tmp_path.resolve()
    original = Path(__file__).resolve().parents[3]
    implementation = tmp_path / "implementation"
    shutil.copytree(
        original / "infrastructure",
        implementation / "infrastructure",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".ruff_cache", ".mypy_cache"),
    )
    shutil.copyfile(original / "pyproject.toml", implementation / "pyproject.toml")
    snapshot = tmp_path / "snapshot"
    project = snapshot / "projects/templates/template_code_project/src"
    project.mkdir(parents=True)
    (project / "model.py").write_text("CURRENT_PUBLIC_SOURCE = True\n")
    (snapshot / "pyproject.toml").write_text('[project]\nversion="4.0.1"\n')
    return implementation, snapshot


def _environment() -> dict[str, str]:
    environment = {
        name: value for name, value in build_bounded_env().items() if not name.startswith(("PYTHON", "GIT_"))
    }
    environment.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return environment


def _invoke(implementation: Path, snapshot: Path, destination: Path) -> subprocess.CompletedProcess[str]:
    destination = destination.resolve()
    prefix = snapshot.parent / "caller-bytecode"
    prefix.mkdir()
    code = bytecode_audit_bootstrap(
        (implementation / "infrastructure",),
        prefix,
        audit_path=implementation / "infrastructure/core/bytecode_audit.py",
    )
    code += (
        "import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
        "from infrastructure.publishing._standalone_export import canonical_snapshot_export; "
        "from infrastructure.publishing.publication_tree import _Budget; "
        "canonical_snapshot_export(Path(sys.argv[2]),'projects/templates/template_code_project',"
        "Path(sys.argv[3]),None,_Budget()); "
        "_audit_scope['verify_executed_source_code'](Path(sys.argv[1])/'infrastructure',Path(sys.pycache_prefix))"
    )
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={prefix}",
            "-c",
            code,
            str(implementation),
            str(snapshot),
            str(destination),
        ],
        cwd=snapshot.parent,
        env=_environment(),
        capture_output=True,
        text=True,
        timeout=90,
    )


def test_actual_stale_adjacent_exporter_cache_cannot_execute_in_canonical_child(tmp_path: Path) -> None:
    implementation, snapshot = _fixture(tmp_path)
    exporter = implementation / "infrastructure/project/copy_exemplar.py"
    current = exporter.read_bytes()
    marker = tmp_path / "invented-stale-exporter-executed"
    exporter.write_bytes(current + f"\nPath({str(marker)!r}).write_text('replayed stale exporter')\n".encode())
    py_compile.compile(str(exporter), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
    exporter.write_bytes(current)
    unsafe = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);"
            "from infrastructure.project.copy_exemplar import export_exemplar",
            str(implementation),
        ],
        cwd=tmp_path,
        env=_environment(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert unsafe.returncode == 0, unsafe.stderr
    assert marker.read_text() == "replayed stale exporter"
    marker.unlink()
    destination = tmp_path / "template_code_project"
    observed = _invoke(implementation, snapshot, destination)
    assert observed.returncode == 0, observed.stdout + observed.stderr
    assert not marker.exists()
    assert (destination / "src/model.py").read_text() == "CURRENT_PUBLIC_SOURCE = True\n"
    assert json.loads((destination / ".template-export.json").read_text())["source_commit"] == "unknown"


def test_actual_selected_prefix_exporter_cache_is_refused_before_payload(tmp_path: Path) -> None:
    implementation, snapshot = _fixture(tmp_path)
    initializer = implementation / "infrastructure/__init__.py"
    marker = tmp_path / "invented-cache-payload-executed"
    poisoned = tmp_path / "invented-selected-prefix-poisoned"
    payload_suffix = f"\nPath({str(marker)!r}).write_text('cache payload executed')\n".encode()
    # A real imported fixture module writes an unchecked cache into the actual
    # inner exporter's fresh prefix. Parent imports must reach that child first.
    initializer.write_text(
        initializer.read_text() + "\nimport importlib.util as _fixture_util\n"
        "from importlib._bootstrap_external import _code_to_hash_pyc as _fixture_pyc\n"
        "import sys as _fixture_sys\n"
        "from pathlib import Path as _FixturePath\n"
        "if _FixturePath(_fixture_sys.pycache_prefix).name.startswith('export-bytecode-'):\n"
        "    _fixture_source=_FixturePath(__file__).parent/'project/copy_exemplar.py'\n"
        "    _fixture_raw=_fixture_source.read_bytes()\n"
        f"    _fixture_payload=compile(_fixture_raw+{payload_suffix!r},str(_fixture_source),'exec')\n"
        "    _fixture_cache=_FixturePath(_fixture_util.cache_from_source(str(_fixture_source)))\n"
        "    _fixture_cache.parent.mkdir(parents=True,exist_ok=True)\n"
        "    _fixture_cache.write_bytes(_fixture_pyc(_fixture_payload,_fixture_util.source_hash(_fixture_raw),checked=False))\n"
        f"    _FixturePath({str(poisoned)!r}).write_text(str(_fixture_sys.pycache_prefix))\n"
    )
    destination = tmp_path / "template_code_project"
    observed = _invoke(implementation, snapshot, destination)
    assert observed.returncode != 0, observed.stdout + observed.stderr
    assert "canonical standalone export failed" in observed.stderr
    assert "export-bytecode-" in poisoned.read_text(), "the real inner child reached its owned prefix"
    assert not marker.exists()
    assert not destination.exists()

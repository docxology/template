"""Real source-execution attacks against the canonical Root collection boundary."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.project.public_acceptance_evidence import cell_environment
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_root_case_contract import _json
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project.test_root_case_census import _produce_control

pytestmark = pytest.mark.timeout(240)


def _source_root(root: Path, conftest: str) -> Path:
    """Collection precedes case-policy classification and must reject altered code."""
    (root / "tests").mkdir(parents=True)
    (root / "infrastructure").mkdir()
    (root / "pyproject.toml").write_text(
        '[project]\nname="owned-source-control"\nversion="0.1.0"\nrequires-python=">=3.14"\n'
        "[tool.pytest.ini_options]\naddopts=[]\n",
        encoding="utf-8",
    )
    (root / "conftest.py").write_text(conftest, encoding="utf-8")
    (root / "tests/test_owned.py").write_text("def test_owned():\n    assert True\n", encoding="utf-8")
    probe = root / "infrastructure/probe.py"
    probe.write_bytes(b"VALUE = 1\n#" + b"x" * 1024 + b"\n")
    return probe


def _refused_census(root: Path) -> dict[str, Any]:
    bundle = _produce_control(root, root / "output/readiness/current-census", timeout_seconds=180)
    assert bundle["exit_code"] == 1, bundle
    reader = SnapshotReader(root)
    outer = reader.read(bundle["coordinator_artifact"]["path"]).json_object()
    assert outer["timed_out"] is False
    assert outer["custody_refused"] is False, outer
    process = reader.read(bundle["process_artifact"]["path"]).json_object()
    assert process["returncode"] == process["original_returncode"] == 1
    assert process["timed_out"] is process["custody_refused"] is False
    receipt = _json(reader.read(bundle["receipt_artifact"]["path"]))
    assert receipt["exit_code"] == 1 and receipt["bytecode_verified"] is False
    assert receipt["census"] is None and receipt["executed_reports"] == 0
    return receipt


def test_nominated_source_poison_cannot_execute_from_actual_fresh_cache(tmp_path: Path) -> None:
    root = tmp_path.resolve() / "candidate"
    marker = tmp_path / "stale-code-executed"
    probe = root / "infrastructure/probe.py"
    injected = (
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('stale candidate code')\nraise SystemExit(77)\n"
    ).encode()
    conftest = (
        "import importlib.util,os,py_compile\nfrom pathlib import Path\n"
        f"probe=Path({str(probe)!r})\noriginal=probe.read_bytes(); observed=probe.stat()\n"
        f"injected={injected!r}\nassert len(injected)<len(original)\n"
        "probe.write_bytes(injected.ljust(len(original),b' '))\n"
        "os.utime(probe,ns=(observed.st_atime_ns,observed.st_mtime_ns))\n"
        "py_compile.compile(str(probe),doraise=True,invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)\n"
        "probe.write_bytes(original)\n"
        "os.utime(probe,ns=(observed.st_atime_ns,observed.st_mtime_ns))\n"
        "spec=importlib.util.spec_from_file_location('_owned_candidate_probe',probe)\n"
        "module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)\n"
    )
    _source_root(root, conftest)
    original = probe.read_bytes()
    fingerprint = RuntimeScope(root, "root").source_identity()
    environment = cell_environment(Path(sys.executable), tmp_path / "ordinary-evidence", repo_root=root)
    command = (
        sys.executable,
        "-I",
        "-X",
        f"pycache_prefix={tmp_path / 'ordinary-prefix'}",
        "-c",
        "import runpy,sys;runpy.run_path(sys.argv[1])",
        str(root / "conftest.py"),
    )
    ordinary = run_project_test_matrix([ProjectTestTask(0, "ordinary-poison", command, root, environment, 20, True)])[0]
    assert ordinary.returncode == 77 and not ordinary.timed_out
    assert marker.read_text() == "stale candidate code"
    marker.unlink()
    receipt = _refused_census(root)
    assert receipt["original_pytest_exit_code"] == 4
    assert not marker.exists() and probe.read_bytes() == original
    assert RuntimeScope(root, "root").source_identity() == fingerprint


def test_restored_conftest_cannot_hide_actual_substituted_execution(tmp_path: Path) -> None:
    root = tmp_path.resolve() / "candidate"
    marker = tmp_path / "substituted-root-conftest.txt"
    replacement = f"from pathlib import Path\nPath({str(marker)!r}).write_text('changed root code executed')\n"
    conftest = (
        "import importlib.util\nfrom pathlib import Path\n"
        "owned=Path(__file__)\noriginal=owned.read_bytes()\n"
        f"owned.write_text({replacement!r})\n"
        "try:\n"
        "    spec=importlib.util.spec_from_file_location('_changed_root_conftest',owned)\n"
        "    module=importlib.util.module_from_spec(spec)\n"
        "    spec.loader.exec_module(module)\n"
        "finally:\n    owned.write_bytes(original)\n"
    )
    _source_root(root, conftest)
    fingerprint = RuntimeScope(root, "root").source_identity()
    receipt = _refused_census(root)
    assert marker.read_text() == "changed root code executed"
    assert (root / "conftest.py").read_text() == conftest
    assert RuntimeScope(root, "root").source_identity() == fingerprint
    assert receipt["original_pytest_exit_code"] == 0

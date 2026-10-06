"""Actual pytest producer consumption of an admitted installed public provider."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.project.public_acceptance_dependencies import MissingRuntimeProvider, admit_runtime_providers
from infrastructure.project.public_acceptance_evidence import (
    aggregate_pytest,
    write_json,
    runtime_identity,
    cell_environment,
)
from infrastructure.project.public_acceptance_cases import PYTEST_SPEC_SCHEMA, project_python_hashes, pytest_command
from infrastructure.reporting.readiness_receipts import project_source_identity, deliverable_identity
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.reporting.test_readiness_dependencies import (
    MODULE,
    _provider_control,
    PACKAGE,
    PROJECT,
    PROVIDER,
)
from tests.infra_tests.reporting.test_readiness_dependencies import provider_evidence as provider_evidence

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.timeout(45)


def _producer(
    root: Path,
    providers: dict,
    name: str,
    *,
    collect: bool,
    body: str,
    installed: bool = True,
    conftest: str | None = None,
) -> dict:
    project = root / "projects" / PROJECT
    (project / "src").mkdir(exist_ok=True)
    (project / "tests").mkdir(exist_ok=True)
    (project / "src/model.py").write_text(
        f"from {MODULE} import measured_value\ndef score(positive):\n"
        "    if positive:\n        return measured_value()\n    return -measured_value()\n"
    )
    (project / "tests/test_model.py").write_text(body)
    if conftest is not None:
        (project / "conftest.py").write_text(conftest)
    directory = root / "output/readiness" / name
    spec = directory / "dependency-spec.json"
    write_json(root, spec, providers)
    receipt = directory / "pytest.json"
    prefix = root.parent / (name + "-bytecode")
    prefix.mkdir(mode=0o700)
    site = root.parent / "installed-site"
    audit = bytecode_audit_bootstrap(
        (
            ROOT / "infrastructure",
            project / "src",
            project / "scripts",
            site / MODULE,
            project / "tests",
            *sorted(project.glob("*.py")),
        ),
        prefix,
    )
    bootstrap = (
        audit + "import runpy,sys\n"
        f"sys.path[:0]={[str(ROOT), *([str(site)] if installed else [])]!r}\n"
        "runpy.run_module('infrastructure.project.public_acceptance_pytest',run_name='__main__')\n"
    )
    execution_spec = directory / "execution-spec.json"
    spec_value = {
        "schema_version": PYTEST_SPEC_SCHEMA,
        "root": str(root),
        "scope": PROJECT,
        "directory": directory.relative_to(root).as_posix(),
        "run_id": "actual-provider-producer",
        "nonce": "a" * 32,
        "receipt": receipt.relative_to(root).as_posix(),
        "collect": collect,
        "selectors": ["tests/test_model.py"],
        "test_timeout_seconds": 10,
        "source_identity": project_source_identity(root, PROJECT),
        "deliverables_identity": deliverable_identity(root, PROJECT),
        "source_hashes": project_python_hashes(root, PROJECT),
        "runtime": runtime_identity(),
        "dependency_providers": providers,
        "audit_roots": [str(site / MODULE)],
    }
    spec_binding = write_json(root, execution_spec, spec_value)
    canonical = pytest_command(
        Path(sys.executable),
        root,
        directory,
        "actual-provider-producer",
        PROJECT,
        receipt,
        execution_spec,
        ["tests/test_model.py"],
        spec_sha256=spec_binding["sha256"],
        collect=collect,
        test_timeout=10,
        audit_roots=(site / MODULE,),
    )
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={prefix}",
            "-c",
            bootstrap,
            "--root",
            str(root),
            "--project-root",
            str(project),
            "--receipt",
            str(receipt),
            "--run-id",
            "actual-provider-producer",
            "--dependency-spec",
            str(spec),
            "--execution-spec",
            str(execution_spec),
            "--execution-spec-sha256",
            spec_binding["sha256"],
            "--",
            *canonical[canonical.index("--") + 1 :],
        ],
        cwd=root.parent,
        env=cell_environment(Path(sys.executable), directory),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert receipt.is_file(), result.stdout + result.stderr
    raw = json.loads(receipt.read_text())
    assert raw["exit_code"] == result.returncode
    snapshot = SnapshotReader(root).read(receipt.relative_to(root).as_posix())
    return {"raw": raw, "binding": {"path": snapshot.relative, "sha256": snapshot.sha256}}


GOOD = "from model import score\ndef test_positive():\n    assert score(True)==17\ndef test_negative():\n    assert score(False)==-17\n"


def test_actual_collection_and_execution_producer_bind_provider_custody(provider_evidence) -> None:
    root, existing = provider_evidence
    requirements = {
        f"{PROVIDER}:installed": Requirement(
            f"{PROVIDER}:installed", "installed", PROVIDER, "0.2.0", "4.0.0", "", package=PACKAGE
        )
    }
    wheel = root / existing["dependency_providers"][PROVIDER]["wheel_artifact"]["path"]
    providers = admit_runtime_providers(root, PROJECT, {PROVIDER: wheel}, requirements, SnapshotReader(root))
    baseline = _producer(root, providers, "producer-collection", collect=True, body=GOOD)
    cases = _producer(root, providers, "producer-cases", collect=False, body=GOOD)
    counts = aggregate_pytest(baseline["raw"], [cases["raw"]], "actual-provider-producer")
    assert counts["collected"] == counts["passed"] == 2
    details = {
        **existing,
        **counts,
        "run_id": "actual-provider-producer",
        "dependency_providers": providers,
        "collection_artifact": baseline["binding"],
        "case_artifacts": [cases["binding"]],
    }
    for kind in ("runtime", "coverage"):
        requirement = Requirement(f"{PROJECT}:{kind}", kind, PROJECT, "0.2.0", "4.0.0", "a" * 64)
        _provider_control(requirement, details, SnapshotReader(root))
    for raw in (baseline["raw"], cases["raw"]):
        assert raw["dependency_custody"][PROVIDER]["before"] == raw["dependency_custody"][PROVIDER]["after"]
        assert set(raw["dependency_artifacts"][PROVIDER]) == {"metadata", "record"}


def test_actual_provider_mutation_after_passing_case_refuses_producer_receipt(provider_evidence) -> None:
    root, existing = provider_evidence
    body = GOOD + (
        f"import {MODULE}\nfrom pathlib import Path\n"
        f"def test_actual_mutation():\n    path=Path({MODULE}.__file__)\n"
        "    path.write_bytes(path.read_bytes()+b'\\n# actual installed source mutation\\n')\n"
    )
    source = root.parent / "installed-site" / MODULE / "__init__.py"
    original = source.read_bytes()
    try:
        result = _producer(root, existing["dependency_providers"], "producer-mutation", collect=False, body=body)
    finally:
        source.write_bytes(original)
    assert result["raw"]["exit_code"] == 1
    assert set(result["raw"]["outcomes"].values()) == {"passed"}
    assert "differs" in result["raw"]["diagnostic"]


@pytest.mark.parametrize("exit_code", [130, 124])
def test_actual_post_pytest_provider_loss_retains_original_interruption_or_timeout(
    provider_evidence, tmp_path: Path, exit_code: int
) -> None:
    original_root, existing = provider_evidence
    original_site = original_root.parent / "installed-site"
    original_metadata = original_site / f"{MODULE}-0.2.0.dist-info/METADATA"
    original_bytes = original_metadata.read_bytes()
    scratch = tmp_path.resolve() / "owned-provider-loss"
    root, site = scratch / "repository", scratch / "installed-site"
    shutil.copytree(original_root, root)
    shutil.copytree(original_site, site)
    owned_metadata = site / original_metadata.parent.name
    assert owned_metadata.resolve().is_relative_to(scratch)
    assert not owned_metadata.resolve().is_relative_to(original_site)
    interrupted_marker, removed_marker = scratch / "interrupted.txt", scratch / "removed.txt"
    body = (
        "from model import score\nfrom pathlib import Path\n"
        "def test_actual_interruption():\n    assert score(True)==17\n"
        f"    Path({str(interrupted_marker)!r}).write_text('actual provider consumed before interruption')\n"
        "    raise KeyboardInterrupt('owned interrupted provider consumer')\n"
    )
    conftest = (
        "import shutil\nfrom pathlib import Path\n"
        "def pytest_sessionfinish(session, exitstatus):\n"
        f"    session.exitstatus={exit_code}\n"
        f"    shutil.rmtree(Path({str(owned_metadata)!r}))\n"
        f"    Path({str(removed_marker)!r}).write_text('owned installed metadata removed after pytest')\n"
    )
    result = _producer(
        root,
        existing["dependency_providers"],
        f"producer-post-interruption-provider-loss-{exit_code}",
        collect=False,
        body=body,
        conftest=conftest,
    )
    assert interrupted_marker.read_text() == "actual provider consumed before interruption"
    assert removed_marker.read_text() == "owned installed metadata removed after pytest"
    assert not owned_metadata.exists()
    assert original_metadata.read_bytes() == original_bytes
    raw = result["raw"]
    assert raw["pytest_exit_code"] == raw["exit_code"] == exit_code
    assert "not installed" in raw["diagnostic"]
    assert raw["nodeids"] and set(raw["outcomes"].values()) == {"incomplete"}
    assert raw["dependency_artifacts"][PROVIDER]["metadata"]["sha256"]


def test_missing_admitted_provider_wheel_is_a_typed_blocker(provider_evidence) -> None:
    root, _ = provider_evidence
    with pytest.raises(MissingRuntimeProvider):
        admit_runtime_providers(root, PROJECT, {}, {}, SnapshotReader(root))


def test_actual_missing_installed_provider_does_not_execute_pytest(provider_evidence) -> None:
    root, existing = provider_evidence
    result = _producer(
        root,
        existing["dependency_providers"],
        "producer-missing",
        collect=False,
        body="def test_must_not_run():\n    raise AssertionError('missing provider reached tests')\n",
        installed=False,
    )
    assert result["raw"]["exit_code"] == 75
    assert result["raw"]["nodeids"] == []
    assert "not installed" in result["raw"]["diagnostic"]

"""Actual provider consumption and fail-closed runtime evidence controls."""

from __future__ import annotations

import base64
import copy
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from io import StringIO
from pathlib import Path

import pytest

from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.reporting.release_readiness_dependencies import _validate_provider_receipts
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

PROJECT = "templates/template_advanced_literature_review"
PROVIDER = "templates/template_literature_meta_analysis"
PACKAGE = "template-literature-meta-analysis"
MODULE = "template_literature_meta_analysis"
pytestmark = pytest.mark.timeout(40)


def _binding(root: Path, path: Path, content: bytes) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(content).hexdigest()}


def _json(root: Path, path: Path, value: object) -> dict[str, str]:
    return _binding(root, path, json.dumps(value).encode())


@pytest.fixture(scope="module")
def provider_evidence(tmp_path_factory):
    scratch = tmp_path_factory.mktemp("provider-custody").resolve()
    # Keep owned fixture collection independent of ancestor pytest configuration.
    config = scratch / "pytest.ini"
    config.write_text("[pytest]\n")
    root, site = scratch / "repository", scratch / "installed-site"
    source = root / "projects" / PROVIDER
    source.joinpath("src").mkdir(parents=True)
    source.joinpath("src/__init__.py").write_text("def measured_value():\n    return 17\n")
    source.joinpath("pyproject.toml").write_text(
        f'[project]\nname="{PACKAGE}"\nversion="0.2.0"\n[tool.setuptools.package-dir]\n{MODULE}="src"\n'
    )
    selected = root / "projects" / PROJECT
    selected.mkdir(parents=True)
    selected.joinpath("pyproject.toml").write_text(
        f'[project]\nname="template-advanced-literature-review"\nversion="0.2.0"\n'
        f'dependencies=["{PACKAGE}>=0.2.0,<0.3"]\n'
        f'[tool.uv.sources]\n{PACKAGE}={{path="../template_literature_meta_analysis"}}\n'
    )
    metadata = f"{MODULE}-0.2.0.dist-info"
    members = {
        f"{MODULE}/__init__.py": source.joinpath("src/__init__.py").read_bytes(),
        f"{metadata}/METADATA": f"Metadata-Version: 2.1\nName: {PACKAGE}\nVersion: 0.2.0\n".encode(),
        f"{metadata}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    buffer = StringIO()
    writer = csv.writer(buffer)
    for name, content in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
        writer.writerow([name, "sha256=" + digest, str(len(content))])
    writer.writerow([f"{metadata}/RECORD", "", ""])
    members[f"{metadata}/RECORD"] = buffer.getvalue().encode()
    wheel = root / "output/readiness" / f"{MODULE}-0.2.0-py3-none-any.whl"
    wheel.parent.mkdir(parents=True)
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    uv = shutil.which("uv")
    assert uv is not None
    installation = subprocess.run(
        [
            uv,
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-deps",
            "--no-build",
            "--python",
            sys.executable,
            "--target",
            str(site),
            str(wheel),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert installation.returncode == 0, installation.stderr
    test = scratch / "test_consumed_provider.py"
    test.write_text(
        f"import {MODULE}\ndef test_actual_dependency_computation():\n    assert {MODULE}.measured_value() == 17\n"
    )
    checkout = Path(__file__).resolve().parents[3]
    bootstrap = """
import importlib,importlib.metadata,json,os,sys,tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as cache:
 sys.pycache_prefix=str(Path(cache).resolve())
 # AUDIT
 checkout,site,root,test,receipt,collect,config=sys.argv[1:]
 sys.path[:0]=[site,checkout]
 from infrastructure.core.implementation_custody import capture_dependency_custody
 from infrastructure.project.public_acceptance_pytest import CollectionEvidence
 from infrastructure.project.public_acceptance_evidence import write_json,runtime_identity,PYTEST_RECEIPT_SCHEMA
 import pytest
 package=importlib.import_module("template_literature_meta_analysis")
 source=Path(package.__file__).parent
 before=capture_dependency_custody("template-literature-meta-analysis",source,fresh_pycache_prefix=Path(cache).resolve())
 observer=CollectionEvidence()
 os.chdir(Path(test).parent)
 code=int(pytest.main(["-c",config,"--rootdir",str(Path(test).parent),"--confcutdir",str(Path(test).parent),
  "-o","addopts=","-q","-p","no:cacheprovider",*(["--collect-only"] if collect=="yes" else []),test],plugins=[observer]))
 after=capture_dependency_custody("template-literature-meta-analysis",source,fresh_pycache_prefix=Path(cache).resolve())
 dist=importlib.metadata.distribution("template-literature-meta-analysis")
 bindings={}
 for kind in ("METADATA","RECORD"):
  selected=[str(path) for path in dist.files if str(path).endswith(".dist-info/"+kind)]
  assert len(selected)==1
  content=Path(dist.locate_file(selected[0])).read_bytes()
  path=Path(receipt).parent/(Path(receipt).stem+"-"+kind)
  path.write_bytes(content)
  import hashlib
  bindings[kind.lower()]={"path":path.relative_to(root).as_posix(),"sha256":hashlib.sha256(content).hexdigest()}
 payload={"schema_version":PYTEST_RECEIPT_SCHEMA,"run_id":"provider-control","exit_code":code,
  "runtime":runtime_identity(),"nodeids":observer.nodeids,"deselected":observer.deselected,
  "collection_errors":observer.collection_errors,"collection_skips":observer.collection_skips,
  "outcomes":observer.outcomes(),"reasons":observer.reasons,
  "dependency_custody":{"templates/template_literature_meta_analysis":{"before":before,"after":after}},
  "dependency_artifacts":{"templates/template_literature_meta_analysis":bindings}}
 write_json(Path(root),Path(receipt),payload)
 sys.exit(code)
"""
    receipts = []
    audit = bytecode_audit_bootstrap((checkout / "infrastructure", site / MODULE), None)
    bootstrap = bootstrap.replace(" # AUDIT\n", "".join(" " + line + "\n" for line in audit.splitlines()))
    for name, collect in (("collection", "yes"), ("chunk", "no")):
        receipt = root / f"output/readiness/{name}.json"
        observed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                bootstrap,
                str(checkout),
                str(site),
                str(root),
                str(test),
                str(receipt),
                collect,
                str(config),
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert observed.returncode == 0, observed.stdout + observed.stderr
        receipts.append(_binding(root, receipt, receipt.read_bytes()))
    runtime = json.loads((root / receipts[0]["path"]).read_text())["runtime"]
    probe = _json(
        root,
        root / "output/readiness/runtime.json",
        dict(runtime, execution_exit_code=0, command=[sys.executable, "-I", "-c", bootstrap]),
    )
    details = {
        "run_id": "provider-control",
        "dependency_providers": {
            PROVIDER: {
                "package": PACKAGE,
                "version": "0.2.0",
                "wheel_artifact": _binding(root, wheel, wheel.read_bytes()),
            }
        },
        "collection_artifact": receipts[0],
        "case_artifacts": receipts[1:],
        "runtime_artifact": probe,
        "collected": 1,
        "passed": 1,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "deselected": 0,
    }
    return root, details


def _provider_control(requirement: Requirement, details: dict, reader: SnapshotReader) -> None:
    """Validate real provider custody only; this isolated fixture cannot grant runtime acceptance."""
    bindings = [details.get("collection_artifact"), *details.get("case_artifacts", [])]
    receipts = []
    names = []
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ValueError("provider control omitted a bound actual receipt")
        snapshot = reader.read(binding["path"])
        if snapshot.sha256 != binding["sha256"]:
            raise ValueError("provider control changed its actual receipt")
        names.append(snapshot.relative)
        receipts.append(snapshot.json_object())
    if len(set(names)) != len(names):
        raise ValueError("provider control duplicates actual receipt")
    _validate_provider_receipts(requirement, details, reader, receipts)


def _requirement(kind: str = "runtime") -> Requirement:
    return Requirement(f"{PROJECT}:{kind}", kind, PROJECT, "0.2.0", "4.0.1", "a" * 64)


def test_actual_installed_provider_pytest_and_metadata_pass_narrow_custody_control(provider_evidence) -> None:
    root, details = provider_evidence
    for kind in ("runtime", "coverage"):
        _provider_control(_requirement(kind), details, SnapshotReader(root))


@pytest.mark.parametrize(
    "fault",
    [
        "missing-provider",
        "invented-provider",
        "stale-version",
        "missing-collection",
        "duplicate-chunk",
        "stale-run",
        "changed-after",
        "checkout-binding",
        "stale-metadata",
        "unbound-record",
        "missing-python",
        "invented-file",
        "failed-case",
        "false-count",
        "wrong-runtime",
    ],
)
def test_provider_runtime_faults_cannot_grant_readiness(provider_evidence, fault: str) -> None:
    root, original = provider_evidence
    details = copy.deepcopy(original)
    if fault == "missing-provider":
        details["dependency_providers"] = {}
    elif fault == "invented-provider":
        details["dependency_providers"]["templates/template_code_project"] = details["dependency_providers"][PROVIDER]
    elif fault == "stale-version":
        details["dependency_providers"][PROVIDER]["version"] = "0.1.0"
    elif fault == "missing-collection":
        details.pop("collection_artifact")
    elif fault == "duplicate-chunk":
        details["case_artifacts"] *= 2
    elif fault == "stale-run":
        details["run_id"] = "unrelated-run"
    elif fault == "false-count":
        details["passed"] = 100
    else:
        raw = json.loads((root / details["case_artifacts"][0]["path"]).read_text())
        before = raw["dependency_custody"][PROVIDER]["before"]
        if fault == "changed-after":
            raw["dependency_custody"][PROVIDER]["after"]["distribution"]["version"] = "0.1.0"
        elif fault == "checkout-binding":
            before["binding_kind"] = "source-checkout"
        elif fault == "stale-metadata":
            before["distribution"]["metadata_sha256"] = "b" * 64
        elif fault == "unbound-record":
            before["distribution"]["declared_files"] = {}
        elif fault == "missing-python":
            before["files"] = {}
        elif fault == "invented-file":
            before["distribution"]["file_sha256"]["invented.py"] = "a" * 64
        elif fault == "failed-case":
            raw["outcomes"] = {node: "failed" for node in raw["nodeids"]}
        elif fault == "wrong-runtime":
            raw["runtime"]["executable"] = "/unrelated/python"
        if fault != "changed-after":
            raw["dependency_custody"][PROVIDER]["after"] = copy.deepcopy(before)
        details["case_artifacts"] = [_json(root, root / f"output/readiness/fault-{fault}.json", raw)]
    with pytest.raises(ValueError):
        _provider_control(_requirement(), details, SnapshotReader(root))


def test_current_provider_source_change_refuses_old_wheel(provider_evidence) -> None:
    root, details = provider_evidence
    path = root / "projects" / PROVIDER / "src/__init__.py"
    original = path.read_bytes()
    try:
        path.write_text("def measured_value():\n    return 99\n")
        with pytest.raises(ValueError, match="current exact source"):
            _provider_control(_requirement(), details, SnapshotReader(root))
    finally:
        path.write_bytes(original)

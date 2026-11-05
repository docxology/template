"""Exact public exports and installed-wheel provenance for isolated acceptance."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
import zipfile
from dataclasses import dataclass
from io import BytesIO
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.project.copy_exemplar import export_exemplar
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.reporting.readiness_receipts import public_resource_source_paths, public_source_paths
from infrastructure.core.files.archive_members import bounded_members
from infrastructure.reporting.release_readiness_artifacts import (
    validate_source_archive,
    validate_wheel_members,
    validate_wheel_source,
)
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def write_binary(root: Path, path: Path, content: bytes) -> dict[str, str]:
    """Persist public native artifacts through the same confined evidence lane."""
    path = evidence_directory(root, path.parent) / path.name
    atomic_write_bytes_confined(root.resolve(), path, content)
    return {"path": path.relative_to(root.resolve()).as_posix(), "sha256": hashlib.sha256(content).hexdigest()}


def prepare_export(
    root: Path,
    requirement: Requirement,
    scratch: Path,
    directory: Path,
    *,
    deadline_monotonic: float | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Reuse canonical exemplar export, then bind its exact complete public bytes."""
    reader = SnapshotReader(root)
    scope = requirement.scope
    destination = scratch / ("source" if scope == "root" else Path(scope).name)
    destination.mkdir()
    base = root if scope == "root" else root / "projects" / scope
    expected = {
        path.relative_to(base).as_posix(): reader.read(path.relative_to(root).as_posix()).sha256
        for path in public_source_paths(root, None if scope == "root" else scope)
    }
    if scope == "root":
        for relative in expected:
            atomic_write_bytes_confined(destination, destination / relative, reader.read(relative).content)
    else:
        export_exemplar(root, scope, destination, deadline_monotonic=deadline_monotonic)
        embedded = json.loads((destination / ".template-export.json").read_text())
        for dependency in embedded["resource_dependencies"]:
            resource = root / dependency
            for path in public_resource_source_paths(root, dependency):
                source = reader.read(path.relative_to(root).as_posix())
                expected[f"_template_resources/{dependency}/{path.relative_to(resource).as_posix()}"] = source.sha256
        copied = {
            path.relative_to(destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in destination.rglob("*")
            if path.is_file() and path.name != ".template-export.json"
        }
        missing = expected.keys() - copied.keys()
        if (
            embedded.get("files") != copied
            or copied.keys() - expected.keys()
            or any(copied[path] != expected[path] for path in copied.keys() & expected.keys())
            or any(Path(path).parts[0] != "rendered" for path in missing)
        ):
            raise ValueError("canonical export differs outside retained publication proofs")
        # Forks intentionally omit deposited proofs. Acceptance archives must
        # still bind those exact public snapshot bytes, without inheriting any
        # other ignored or missing source member from the copier.
        for relative in sorted(missing):
            held = reader.read((base / relative).relative_to(root).as_posix())
            atomic_write_bytes_confined(destination, destination / relative, held.content)
            embedded["files"][relative] = held.sha256
        if missing:
            atomic_write_bytes_confined(
                destination,
                destination / ".template-export.json",
                (json.dumps(embedded, indent=2, sort_keys=True) + "\n").encode(),
            )
    actual = {
        path.relative_to(destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in destination.rglob("*")
        if path.is_file() and path.name != ".template-export.json"
    }
    if actual != expected or not reader.unchanged():
        raise ValueError("canonical export differs from the complete current public source snapshot")
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in sorted(actual):
            archive.writestr(relative, (destination / relative).read_bytes())
        if scope != "root":
            archive.writestr(".template-export.json", (destination / ".template-export.json").read_bytes())
    content = buffer.getvalue()
    manifest = {
        "version": requirement.version,
        "platform_version": requirement.platform_version,
        "source_identity": requirement.source_identity,
        "deliverables_identity": requirement.deliverables_identity,
        "bundle_sha256": hashlib.sha256(content).hexdigest(),
        "files": expected,
    }
    if scope != "root":
        manifest["source_commit"] = embedded["source_commit"]
    validate_source_archive(scope, manifest, content, reader)
    details = {
        "execution_exit_code": 0,
        "bundle_artifact": write_binary(root, directory / "source.zip", content),
        "manifest_artifact": write_json(root, directory / "source-manifest.json", manifest),
    }
    return destination, details


def inspect_wheel(root: Path, requirement: Requirement, wheel: Path) -> tuple[tuple[str, ...], dict[str, str]]:
    """Reject stale/incomplete wheels before discovering their actual import surface."""
    wheel = wheel.absolute()
    return inspect_wheel_bytes(root, requirement, read_bytes_confined(wheel.parent, wheel, max_bytes=64 * 1024 * 1024))


def inspect_wheel_bytes(
    root: Path, requirement: Requirement, content: bytes, *, reader: SnapshotReader | None = None
) -> tuple[tuple[str, ...], dict[str, str]]:
    """Admit one immutable byte observation using the shared closed-wheel oracle."""
    with zipfile.ZipFile(BytesIO(content)) as archive:
        names = bounded_members(archive)
        targets = set()
        for name in names:
            parts = Path(name).parts
            if not name.endswith(".py") or ".dist-info" in parts[0] or ".data" in parts[0]:
                continue
            target = Path(parts[0]).stem if len(parts) == 1 else parts[0]
            if target.isidentifier() and not target.startswith("_"):
                targets.add(target)
        if not targets:
            raise ValueError("wheel has no actual importable implementation")
        validate_wheel_members(archive, sorted(targets))
        validate_wheel_source(requirement.scope, archive, reader or SnapshotReader(root))
        metadata = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            raise ValueError("provider wheel requires one METADATA identity")
        fields = BytesParser().parsebytes(archive.read(metadata[0]))
        from packaging.utils import canonicalize_name

        if (
            len(fields.get_all("Name", [])) != 1
            or fields.get_all("Version") != [requirement.version]
            or canonicalize_name(fields["Name"]) != canonicalize_name(requirement.package)
        ):
            raise ValueError("provider wheel differs from its intended package/version")
        hashes = {name: hashlib.sha256(archive.read(name)).hexdigest() for name in names if ".dist-info/" not in name}
    return tuple(sorted(targets)), hashes


@dataclass(frozen=True)
class AdmittedWheel:
    """One inspected byte observation and its fresh private installation copy."""

    path: Path
    content: bytes
    sha256: str
    targets: tuple[str, ...]
    members: dict[str, str]
    package: str


def freeze_wheel_bytes(
    root: Path,
    requirement: Requirement,
    content: bytes,
    scratch: Path,
    filename: str,
    *,
    reader: SnapshotReader | None = None,
) -> AdmittedWheel:
    """Inspect, copy and hash exactly the same bytes, never the mutable origin."""
    if not isinstance(filename, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*\.whl", filename) is None:
        raise ValueError("admitted wheel must have a safe native wheel filename")
    from packaging.utils import canonicalize_name

    package = canonicalize_name(requirement.package, validate=True)
    reader = reader or SnapshotReader(root)
    targets, members = inspect_wheel_bytes(root, requirement, content, reader=reader)
    if not reader.unchanged():
        raise ValueError("wheel source changed during byte admission")
    target = scratch / "admitted-wheels" / uuid.uuid4().hex / filename
    atomic_write_bytes_confined(scratch, target, content, mode=0o400)
    return AdmittedWheel(target, content, hashlib.sha256(content).hexdigest(), targets, members, package)


def admit_provider_wheel(
    root: Path, requirement: Requirement, artifact: dict[str, str], scratch: Path
) -> AdmittedWheel:
    """Retain the provider's original artifact hash before copying public bytes."""
    if (
        set(artifact) != {"path", "sha256"}
        or not isinstance(artifact["path"], str)
        or not isinstance(artifact["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]) is None
    ):
        raise ValueError("provider wheel requires its original exact artifact binding")
    reader = SnapshotReader(root)
    snapshot = reader.read(artifact["path"])
    if snapshot.sha256 != artifact["sha256"]:
        raise ValueError("provider wheel changed after its original admission")
    return freeze_wheel_bytes(root, requirement, snapshot.content, scratch, snapshot.path.name, reader=reader)


INSTALLED_PROBE = r"""
import hashlib, importlib, importlib.metadata, json, os, pathlib, platform, subprocess, sys, sysconfig
spec_bytes=pathlib.Path(sys.argv[1]).read_bytes()
spec=json.loads(spec_bytes)
minor=f'{sys.version_info.major}.{sys.version_info.minor}'
if spec['python_version'] != minor:
    raise ValueError('installed interpreter differs from selected runtime minor')
nonce=spec['run_nonce']
if not isinstance(nonce,str) or len(nonce)!=32 or any(c not in '0123456789abcdef' for c in nonce):
    raise ValueError('installed probe requires its fresh run nonce')
prefix=pathlib.Path(sys.prefix).resolve()
for forbidden in spec['forbidden_roots']:
    forbidden=pathlib.Path(forbidden).resolve()
    if pathlib.Path.cwd().resolve().is_relative_to(forbidden):
        raise ValueError('installed probe cwd is inside source')
    if any(pathlib.Path(entry).resolve().is_relative_to(forbidden) for entry in sys.path if entry):
        raise ValueError('source path contamination')
if not sys.flags.isolated:
    raise ValueError('installed probe requires isolated interpreter startup')
if not sys.pycache_prefix:
    raise ValueError('installed probe requires its fresh launcher-owned bytecode prefix')
if importlib.metadata.version(spec['package']) != spec['version']:
    raise ValueError('installed distribution version differs from candidate')
origins={}
for target in spec['targets']:
    module=importlib.import_module(target)
    if getattr(module,'__file__',None):
        locations=[pathlib.Path(module.__file__).resolve()]
    else:
        locations=[pathlib.Path(p).resolve() for p in module.__path__]
    if not locations or any(not path.is_relative_to(prefix) for path in locations):
        raise ValueError('module imported outside the isolated installed environment')
    origins[target]=[str(path) for path in locations]
sites=[pathlib.Path(sysconfig.get_path(name)).resolve() for name in ('purelib','platlib')]
providers=spec.get('dependency_providers',[])
provider_observations=[]
admitted=dict(spec['wheel_members'])
for provider in providers:
    provider_origins={}
    if importlib.metadata.version(provider['package']) != provider['version']:
        raise ValueError('installed provider distribution version differs from candidate')
    for target in provider['targets']:
        module=importlib.import_module(target)
        origin=pathlib.Path(module.__file__).resolve()
        if not origin.is_relative_to(prefix):
            raise ValueError('provider imported outside isolated installed environment')
        provider_origins[target]=str(origin)
    for name,digest in provider['wheel_members'].items():
        if name in admitted:
            raise ValueError('provider wheels have overlapping installed members')
        admitted[name]=digest
    provider_observations.append({'scope':provider['scope'],'package':provider['package'],
        'version':provider['version'],'wheel_artifact':provider['wheel_artifact'],
        'imported_modules':provider['targets'],'origins':provider_origins})
for name,expected in admitted.items():
    candidates=[site/name for site in sites if (site/name).is_file()]
    if not candidates or any(path.is_symlink() or
        hashlib.sha256(path.read_bytes()).hexdigest()!=expected for path in candidates):
        raise ValueError('installed bytes differ from admitted wheel member: '+name)
domain={}
custody=None
platform_provider=next((item for item in providers if item['scope']=='root'),None)
if spec['scope']=='root' or platform_provider is not None:
    from infrastructure.core.implementation_custody import (
        capture_implementation_custody,verify_implementation_custody,verify_fresh_module_bytecode)
    custody=capture_implementation_custody(fresh_pycache_prefix=pathlib.Path(sys.pycache_prefix))
    if custody['binding_kind']!='installed-distribution' or custody['bytecode_binding']!='fresh-owned-prefix':
        raise ValueError('provider custody is not an actual fresh installed distribution')
if spec['scope']=='root':
    from infrastructure.core.pipeline.outcomes import StageOutcome,StageStatus
    accepted=StageOutcome('installed',StageStatus.SUCCEEDED,0)
    refused=StageOutcome('installed',StageStatus.PAUSED,0)
    if not accepted.complete or refused.complete:
        raise ValueError('installed completion policy did not execute correctly')
    domain={'completion_policy':True}
if spec['scope']=='templates/template_pools_rules_tools':
    from template_pools_rules_tools.tools.integration import run_integration_demo
    from template_pools_rules_tools.tools.fonds_reader import get_fonds_root
    from template_pools_rules_tools.rules.rules_applier import get_rules_root
    from template_pools_rules_tools.tools.tools_invoker import get_tools_root
    roots=[get_fonds_root(),get_rules_root(),get_tools_root()]
    if any(not root.resolve().is_relative_to(prefix) for root in roots):
        raise ValueError('pools resources escaped the installed environment')
    result=run_integration_demo(); summary=result['summary']
    if (summary['fonds_loaded']!=3 or summary['rules_sets_ok']!=2 or summary['tools_valid']<1
        or any(summary[key]<1 for key in ('bib_entries','contacts','datasets'))):
        raise ValueError('installed pools domain computation has missing bundled resources')
    executor=roots[2]/'template_code_executor/src/code_executor.py'
    executed=subprocess.run([sys.executable,'-I',str(executor)],
        input=json.dumps({'code':'print(2+2)','timeout_s':5}),capture_output=True,text=True,timeout=20)
    tool_result=json.loads(executed.stdout)
    if (executed.returncode or tool_result.get('exit_code')!=0
        or tool_result.get('child_exit_code')!=0 or tool_result.get('stdout')!='4\n'):
        raise ValueError('actual installed bundled executor domain computation failed')
    domain={'summary':summary,'resource_roots':[str(root) for root in roots],'code_executor':tool_result}
if spec['scope']=='templates/template_literature_meta_analysis':
    from template_literature_meta_analysis.deep_research.deep_research_adapter import (
        default_fixture_path,replay_recorded_report)
    fixture=default_fixture_path()
    if fixture.is_symlink() or not fixture.resolve(strict=True).is_relative_to(prefix):
        raise ValueError('Meta replay fixture escaped the installed environment')
    report=replay_recorded_report()
    domain={'fixture_path':str(fixture),'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'replay':{'provider':report.provider,'job_id':report.job_id,'status':report.status,
            'query':report.query,'output_text':report.output_text,'citations':list(report.citations),
            'citation_count':report.citation_count}}
if spec['scope']=='templates/template_autopoiesis':
    from infrastructure.project.installed_domain_acceptance import run_autopoiesis_installed
    project=pathlib.Path(spec['domain_inputs']['project_root'])
    if str(project) not in spec['forbidden_roots']:
        raise ValueError('installed child fixture must remain a forbidden import source')
    domain=run_autopoiesis_installed(project,prefix)
for name in admitted:
    if name.endswith('.py'):
        for site in set(sites):
            path=site/name
            if path.is_file():
                _audit_scope['verify_executed_source_code'](path,pathlib.Path(sys.pycache_prefix))
if custody is not None:
    verify_implementation_custody(custody,fresh_pycache_prefix=pathlib.Path(sys.pycache_prefix))
result={'schema_version':'template-installed-probe-v2','execution_exit_code':0,'isolated':True,
 'run_nonce':nonce,'probe_spec_sha256':hashlib.sha256(spec_bytes).hexdigest(),
 'spec_path':sys.argv[1],'observation_path':sys.argv[2],
    'build_policy':{name:os.environ[name] for name in
        ('SOURCE_DATE_EPOCH','TEMPLATE_BUILD_EPOCH_SOURCE','TEMPLATE_EXECUTION_MODE') if name in os.environ},
 'bytecode_binding':'fresh-owned-prefix',
 'source_path_contamination':False,'package':spec['package'],'version':spec['version'],
 'python_version':minor,
 'python_full_version':platform.python_version(),'implementation':platform.python_implementation(),
 'prefix':str(prefix),
 'interpreter':sys.executable,'interpreter_sha256':hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest(),
 'imported_modules':spec['targets'],'origins':origins,'domain':domain}
if provider_observations:
    result['dependency_providers']=provider_observations
if custody is not None:
    result['implementation_custody']=custody
pathlib.Path(sys.argv[2]).write_text(json.dumps(result,sort_keys=True))
"""

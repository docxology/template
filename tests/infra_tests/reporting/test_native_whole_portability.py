"""Native custody from a relocated checkout: retained DATA never self-authorizes.

Native conformance admission needs the original controller's complete pinned
worker launch (spec, Source descriptor, selected SDK implementation, audit
closure, Mermaid/Chrome runtime, PDFium and Office font pins; see
``native_format_joint_source.worker_arguments``) and, for any later reader, an
externally admitted ``NativeReaderOperation``. Production mints both only inside
the installed Source controller or the authenticated hosted collector, after
``admit_public_reference`` admits the complete public exemplar roster at a real
Git commit with an installed platform 4.0.1 SDK. A one-project fixture cannot
pass that admission, so the full positive producer/reader path belongs to the
``native-original`` and ``complete`` jobs of platform-required-acceptance.yml.

This test drives the actual worker and reader without that custody. The worker
must refuse a bare or partially pinned launch before any work. The relocated
spec and process DATA must stay byte-exact for a separate interpreter. Without
custody, that reader must still refuse admission.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import run_bounded_subprocess
from tests.infra_tests.reporting._native_portability_fixture import create_native_fixture

REPO = Path(__file__).absolute().parents[3]
pytestmark = pytest.mark.timeout(600)

# Worker refusal when any original command-bound pin is absent (argparse exit 2).
PIN_REFUSAL = "native worker requires all original command-bound source/SDK/spec/closure pins"
# Reader refusal when no externally admitted Source/original launch is held.
UNADMITTED = "native replay requires externally admitted source and original launch custody"

PRODUCE = r"""
import sys,time,json,uuid
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
from infrastructure.reporting.native_format_acceptance_contracts import public_source_digest,native_environment,WORKER_MODULE,PROCESS_SCHEMA,create_private_native_directory
from infrastructure.project.public_acceptance_evidence import bootstrap_command,write_json
from infrastructure.core.execution_boundary import run_bounded_subprocess
cell=root/'output/readiness/whole-native'
create_private_native_directory(root,cell)
spec={'scope':'templates/template_code_project','run_id':uuid.uuid4().hex,'directory':str(cell.relative_to(root)),'formats':['pdf'],'source_digest':public_source_digest(root),'timeout_seconds':360,'deadline_monotonic':time.monotonic()+360}
spec_binding=write_json(root,cell/'spec.json',spec)
def launch(*pins):
 command=bootstrap_command(Path(sys.executable),root,WORKER_MODULE,'--root',str(root),'--spec',str(cell/'spec.json'),*pins)
 result=run_bounded_subprocess(command,cwd=root,env=native_environment(root,Path(sys.executable),cell),timeout=120,capture_output=True)
 return command,result
def observed(result):
 return {'exit_code':result.returncode,'original_exit_code':result.original_returncode,'timed_out':result.timed_out,'custody_refused':result.custody_refused,'stderr':result.stderr}
# Bare launch, then the spec digest alone: pins are all-or-none, never partially trusted.
command,bare=launch()
_,partial=launch('--spec-sha256',spec_binding['sha256'])
evidence=sorted(path.relative_to(cell).as_posix() for path in cell.rglob('*.json'))
process_binding=write_json(root,cell/'process.json',{'schema_version':PROCESS_SCHEMA,'run_id':spec['run_id'],'command':list(command),'exit_code':bare.returncode,'original_exit_code':bare.original_returncode,'timed_out':bare.timed_out,'custody_refused':bare.custody_refused,'diagnostic':bare.command_error,'stdout':bare.stdout,'stderr':bare.stderr})
print(json.dumps({'bare':observed(bare),'partial':observed(partial),'evidence_after_launch':evidence,'specification_artifact':spec_binding,'process_artifact':process_binding}))
"""

ADMIT = r"""
import sys,json
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
produced=json.loads(sys.argv[2])
from infrastructure.reporting.native_format_acceptance_validation import validate_native_conformance
from infrastructure.reporting.native_format_acceptance_contracts import NATIVE_SCHEMA
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.readiness_receipts import project_source_identity,deliverable_identity
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
cell=root/'output/readiness/whole-native'
reader=SnapshotReader(root)
# Custody-free readback: relocated DATA is byte-exact under the producer's own bindings.
retained={}
for key in ('specification_artifact','process_artifact'):
 binding=produced[key];snapshot=reader.read(binding['path'])
 assert snapshot.sha256==binding['sha256'],key
 retained[key]=snapshot.json_object()
spec,process=retained['specification_artifact'],retained['process_artifact']
command=process['command'];original_root=command[command.index('--root')+1]
assert not Path(original_root).exists() and original_root!=str(root)
assert sys.executable!=command[0]
assert process['run_id']==spec['run_id'] and process['exit_code']==2 and process['timed_out'] is False
assert not (cell/'native-execution.json').exists()
requirement=Requirement('fixture:formats','formats','templates/template_code_project','3.0.0','4.0.1',project_source_identity(root,'templates/template_code_project'),deliverables_identity=deliverable_identity(root,'templates/template_code_project'),formats=('pdf',))
details={'schema_version':NATIVE_SCHEMA,'run_id':spec['run_id'],'formats':spec['formats'],'specification_artifact':produced['specification_artifact'],'process_artifact':produced['process_artifact']}
refusals={}
# A bare reader, and a reader handed retained DATA in place of a live operation, both refuse.
for name,candidate in (('bare',SnapshotReader(root)),('retained-data',SnapshotReader(root,native_operation=process))):
 try: validate_native_conformance(requirement,dict(details),candidate)
 except ProjectionSourceUnsupported as error: refusals[name]=str(error)
 else: raise AssertionError(f'{name} reader admitted native conformance without external custody')
print(json.dumps({'conformance':'refused','refusals':refusals}))
"""


def test_relocated_whole_native_data_survives_but_launch_and_reader_require_custody(tmp_path: Path) -> None:
    producer = tmp_path / "producer"
    create_native_fixture(REPO, producer)
    env = os.environ.copy()
    env.update(SOURCE_DATE_EPOCH="1700000000", MPLCONFIGDIR=str(tmp_path / "matplotlib"))
    setup = run_bounded_subprocess(
        ["uv", "sync", "--locked", "--offline", "--group", "dev", "--python", sys.executable],
        cwd=producer,
        # `--locked` verifies the lockfile itself; an inherited UV_FROZEN conflicts with it.
        env={name: value for name, value in env.items() if name != "UV_FROZEN"},
        timeout=90,
        capture_output=True,
    )
    assert setup.returncode == 0, setup.stderr
    interpreter = producer / ".venv/bin/python"
    status = run_bounded_subprocess(
        [
            str(interpreter),
            "-m",
            "infrastructure.publishing.status_report",
            "--project",
            "projects/templates/template_code_project",
            "--write",
            "--init-after",
            "# Native portability fixture",
        ],
        cwd=producer,
        env=env,
        timeout=30,
        capture_output=True,
    )
    assert status.returncode == 0, status.stderr
    # Genuine project checks pass, so the refusals below come from missing custody, not a broken project.
    preflight = run_bounded_subprocess(
        [
            str(interpreter),
            str(producer / "scripts/pipeline/stage_01_test.py"),
            "--project",
            "templates/template_code_project",
            "--project-only",
        ],
        cwd=producer,
        env=env,
        timeout=90,
        capture_output=True,
    )
    assert preflight.returncode == 0, preflight.stderr
    result = run_bounded_subprocess(
        [str(interpreter), "-I", "-c", PRODUCE, str(producer)],
        cwd=producer,
        env=env,
        timeout=300,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    produced = json.loads(result.stdout.splitlines()[-1])
    for launch in ("bare", "partial"):
        observed = produced[launch]
        assert observed["exit_code"] == observed["original_exit_code"] == 2, observed
        assert observed["timed_out"] is False and observed["custody_refused"] is False, observed
        assert PIN_REFUSAL in observed["stderr"], observed["stderr"]
    # Refused before any work: no native execution receipt or other evidence beside the spec.
    assert produced["evidence_after_launch"] == ["spec.json"]

    relocated = tmp_path / "reader"
    shutil.copytree(producer, relocated, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.rmtree(producer)
    reader_env = {**env, "SOURCE_DATE_EPOCH": "946684800"}
    bindings = {key: produced[key] for key in ("specification_artifact", "process_artifact")}
    result = run_bounded_subprocess(
        [sys.executable, "-I", "-c", ADMIT, str(relocated), json.dumps(bindings)],
        cwd=relocated,
        env=reader_env,
        timeout=90,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout.splitlines()[-1]) == {
        "conformance": "refused",
        "refusals": {"bare": UNADMITTED, "retained-data": UNADMITTED},
    }

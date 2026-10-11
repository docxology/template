"""Complete original native conformance readback from a relocated checkout."""

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

PRODUCE = r"""
import sys,time,json,uuid
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
from infrastructure.reporting.native_format_acceptance_contracts import public_source_digest,native_environment,WORKER_MODULE,PROCESS_SCHEMA,create_private_native_directory
from infrastructure.project.public_acceptance_evidence import bootstrap_command,write_json,read_json
from infrastructure.core.execution_boundary import run_bounded_subprocess
cell=root/'output/readiness/whole-native'
create_private_native_directory(root,cell)
spec={'scope':'templates/template_code_project','run_id':uuid.uuid4().hex,'directory':str(cell.relative_to(root)),'formats':['pdf'],'source_digest':public_source_digest(root),'timeout_seconds':360,'deadline_monotonic':time.monotonic()+360}
write_json(root,cell/'spec.json',spec)
command=bootstrap_command(Path(sys.executable),root,WORKER_MODULE,'--root',str(root),'--spec',str(cell/'spec.json'))
result=run_bounded_subprocess(command,cwd=root,env=native_environment(root,Path(sys.executable),cell),timeout=360,capture_output=True)
write_json(root,cell/'process.json',{'schema_version':PROCESS_SCHEMA,'run_id':spec['run_id'],'command':list(command),'exit_code':result.returncode,'original_exit_code':result.original_returncode,'timed_out':result.timed_out,'custody_refused':result.custody_refused,'diagnostic':result.command_error,'stdout':result.stdout,'stderr':result.stderr})
raw=read_json(root,cell/'native-execution.json')
assert result.returncode in (0,75) and raw['status'] in ('pass','blocked'), raw['diagnostic']
assert all(row['status']=='succeeded' for row in raw['pipeline']['outcomes'])
print(json.dumps({'status':raw['status'],'exit_code':result.returncode}))
"""

ADMIT = r"""
import sys,json,hashlib
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_format_acceptance_validation import validate_native_conformance
from infrastructure.reporting.native_format_acceptance_contracts import NATIVE_SCHEMA
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.readiness_receipts import project_source_identity,deliverable_identity
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
cell=root/'output/readiness/whole-native'
def binding(path):
 return {'path':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
rawpath=cell/'native-execution.json';raw=json.loads(rawpath.read_text())
requirement=Requirement('fixture:formats','formats','templates/template_code_project','3.0.0','4.0.1',project_source_identity(root,'templates/template_code_project'),deliverables_identity=deliverable_identity(root,'templates/template_code_project'),formats=('pdf',))
details={'schema_version':NATIVE_SCHEMA,'run_id':raw['run_id'],'formats':raw['formats'],'native_execution_artifact':binding(rawpath),'specification_artifact':binding(cell/'spec.json'),'process_artifact':binding(cell/'process.json')}
validate_native_conformance(requirement,details,SnapshotReader(root))
assert not Path(raw['producer_custody']['root']).exists()
assert sys.executable != raw['runtime']['executable']
assert raw['status']=='blocked' and raw['blockers']
# Rehashed metadata changes must still be refused after complete positive replay.
original=rawpath.read_bytes()
for change in ({'run_id':'e'*32},{'execution_exit_code':1},{'producer_custody':{**raw['producer_custody'],'root':'/invented/other-original'}}):
 details['native_execution_artifact']=write_json(root,rawpath,{**raw,**change})
 try: validate_native_conformance(requirement,details,SnapshotReader(root))
 except (ValueError,OSError): pass
 else: raise AssertionError('changed original observation admitted')
rawpath.write_bytes(original);details['native_execution_artifact']=binding(rawpath)
source=root/'projects/templates/template_code_project/src/model.py';before=source.read_bytes();source.write_bytes(before+b'CHANGED=1\n')
try: validate_native_conformance(requirement,details,SnapshotReader(root))
except (ValueError,OSError): pass
else: raise AssertionError('changed current source admitted')
source.write_bytes(before)
validate_native_conformance(requirement,details,SnapshotReader(root))
print(json.dumps({'conformance':'admitted','overall_status':raw['status']}))
"""


def test_actual_whole_native_receipt_survives_relocation_and_separate_reader(tmp_path: Path) -> None:
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
    # Execute genuine project checks before freezing source for native admission.
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
        timeout=380,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    relocated = tmp_path / "reader"
    shutil.copytree(producer, relocated, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.rmtree(producer)
    reader_env = {**env, "SOURCE_DATE_EPOCH": "946684800"}
    result = run_bounded_subprocess(
        [sys.executable, "-I", "-c", ADMIT, str(relocated)],
        cwd=relocated,
        env=reader_env,
        timeout=90,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout.splitlines()[-1]) == {"conformance": "admitted", "overall_status": "blocked"}

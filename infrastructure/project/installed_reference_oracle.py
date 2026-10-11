"""Bounded current-reference recomputation, distinct from installed execution."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap, source_file_manifest
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.project.installed_domain_acceptance import validate_autopoiesis_observation

if TYPE_CHECKING:
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

_ORACLE = """
import json, pathlib, sys
source=pathlib.Path(sys.argv[1])
sys.path.insert(0,str(source))
from template_autopoiesis.gates.child_results import verify_analysis_results
cases=json.loads(pathlib.Path(sys.argv[2]).read_bytes())
results=[verify_analysis_results(pathlib.Path(case['path']),case['domain']) for case in cases]
for name,module in tuple(sys.modules.items()):
    if name=='template_autopoiesis' or name.startswith('template_autopoiesis.'):
        origin=getattr(module,'__file__',None)
        if not isinstance(origin,str) or not pathlib.Path(origin).resolve().is_relative_to(source):
            raise ValueError('reference oracle imported outside its frozen source snapshot')
_audit_scope['verify_executed_source_code'](source/'template_autopoiesis',pathlib.Path(sys.pycache_prefix))
print(json.dumps({'schema_version':'template-autopoiesis-reference-oracle-v1','verdicts':results},sort_keys=True))
"""


def verify_autopoiesis_reference_results(
    value: object, reader: SnapshotReader, *, timeout_seconds: int = 30
) -> dict[str, Any]:
    """Recompute all current Layer 2 kernels against exact observed result bytes.

    Source imports occur only in this separate numerical oracle. No source
    path enters an installed-wheel probe or its environment, and no fictional
    distribution or checkout markers are created in the frozen source tree.
    """
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 60:
        raise ValueError("reference oracle deadline must be an integer in [1,60]")
    receipt = validate_autopoiesis_observation(value)
    assert isinstance(value, dict)
    base = reader.root / "projects/templates/template_autopoiesis/src"
    paths = sorted((base / "template_autopoiesis").rglob("*.py"))
    if not paths:
        raise ValueError("current Autopoiesis reference package is missing")
    snapshots = [reader.read(path.relative_to(reader.root).as_posix()) for path in paths]
    with TemporaryDirectory(prefix="template-reference-oracle-") as temporary:
        scratch = Path(temporary).resolve()
        source = scratch / "reference-source"
        source.mkdir()
        expected = {}
        for snapshot in snapshots:
            relative = snapshot.path.relative_to(base).as_posix()
            atomic_write_bytes_confined(source, source / relative, snapshot.content, mode=0o400)
            expected[relative] = snapshot.sha256
        cases = []
        hashes = {}
        for index, observation in enumerate(value["children"]):
            child = scratch / "results" / str(index)
            path = child / "output/data/analysis_results.json"
            content = base64.b64decode(observation["analysis"]["content_base64"], validate=True)
            atomic_write_bytes_confined(scratch, path, content, mode=0o400)
            hashes[path.relative_to(scratch).as_posix()] = hashlib.sha256(content).hexdigest()
            cases.append({"path": str(child), "domain": observation["domain"]})
        case_path = scratch / "cases.json"
        case_bytes = json.dumps(cases, sort_keys=True).encode()
        atomic_write_bytes_confined(scratch, case_path, case_bytes, mode=0o400)
        bytecode = scratch / "fresh-bytecode"
        bytecode.mkdir()
        bootstrap = bytecode_audit_bootstrap((source / "template_autopoiesis",), bytecode)
        command = [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={bytecode}",
            "-c",
            bootstrap + "\n" + _ORACLE,
            str(source),
            str(case_path),
        ]
        outcome = run_with_policy(
            command,
            cwd=scratch,
            env={"PATH": str(Path(sys.executable).parent), "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"},
            policy=SubprocessPolicy(
                policy_id="autopoiesis-installed-reference-oracle",
                source_path="infrastructure/project/installed_reference_oracle.py",
                timeout_seconds=timeout_seconds,
                capture_output=True,
                credential_free=True,
            ),
        )
        if outcome.returncode != 0 or outcome.timed_out or outcome.command_error:
            raise ValueError(f"independent installed-reference recomputation failed: {outcome.stderr[-4000:]}")
        observation = json.loads(outcome.stdout)
        expected_verdicts = [record["independent_analysis"] for record in receipt["executed_children"]]
        if (
            observation != {"schema_version": "template-autopoiesis-reference-oracle-v1", "verdicts": expected_verdicts}
            or source_file_manifest(source, frozenset({".py"})) != expected
            or read_bytes_confined(scratch, case_path) != case_bytes
            or any(
                hashlib.sha256(read_bytes_confined(scratch, scratch / name)).hexdigest() != digest
                for name, digest in hashes.items()
            )
            or not reader.unchanged()
        ):
            raise ValueError("reference source/results changed or recomputed verdicts disagree")
    return {
        "source_sha256": expected,
        "analysis_sha256": hashes,
        "verdicts": expected_verdicts,
        "exit_code": outcome.returncode,
    }

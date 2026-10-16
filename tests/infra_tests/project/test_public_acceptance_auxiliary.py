"""Real child-process and production-checker controls for auxiliary evidence."""

from __future__ import annotations

import errno
import os
import shutil
import stat
import sys
import time
from pathlib import Path

import pytest

from infrastructure.project.public_acceptance_auxiliary import supervise
from infrastructure.project.public_acceptance_auxiliary_worker import negative_control

UNADMITTED = "externally admitted source and original launch custody"
# Witness faults that validate_print_witness refuses before it authenticates any
# native tool receipt, with the specific refusal each one must produce.
PRINT_WITNESS_FAULTS = {
    "worker": "lacks exact worker/source custody",
    "source": "complete print source/SDK inventory differs or changed",
    "font-roles": "original complete font selection changed or was omitted",
    "font-before-after": "original complete font selection changed or was omitted",
    "font-private-path": "original print font path/identity is malformed",
    "library-files": "native decoder provider file custody changed",
    "tool": "actual native tool command/run/outcome differs",
}


def _copy_prepared_runtime_file(original: str, copied: str) -> str:
    """Retain prepared bytes without hard-linking another owner's runtime inode."""
    try:
        os.lstat(copied)
    except FileNotFoundError:
        pass
    else:
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), copied)
    metadata = os.lstat(original)
    if os.name == "posix" and stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.geteuid():
        try:
            os.link(original, copied)
        except OSError as error:
            if error.errno not in {errno.EPERM, errno.EXDEV}:
                raise
        else:
            return copied
    return shutil.copy2(original, copied)


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="requires actual nonroot POSIX file ownership")
def test_prepared_runtime_copy_preserves_owned_and_foreign_file_boundaries(tmp_path: Path) -> None:
    owned = tmp_path / "owned-runtime"
    owned.write_bytes(b"actual owned prepared runtime")
    owned.chmod(0o640)
    owned_copy = tmp_path / "owned-copy"
    assert _copy_prepared_runtime_file(str(owned), str(owned_copy)) == str(owned_copy)
    assert (owned.stat().st_dev, owned.stat().st_ino) == (owned_copy.stat().st_dev, owned_copy.stat().st_ino)
    assert owned.stat().st_nlink == owned_copy.stat().st_nlink == 2
    assert owned_copy.read_bytes() == owned.read_bytes()
    assert stat.S_IMODE(owned_copy.stat().st_mode) == 0o640

    foreign = Path("/usr/share/zoneinfo/UTC").resolve(strict=True)
    metadata = foreign.stat()
    assert stat.S_ISREG(metadata.st_mode) and metadata.st_uid == 0 != os.geteuid()
    assert 0 < metadata.st_size <= 65536
    fields = ("st_uid", "st_dev", "st_ino", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
    before = tuple(getattr(metadata, field) for field in fields)
    contents = foreign.read_bytes()
    foreign_copy = tmp_path / "foreign-copy"
    assert _copy_prepared_runtime_file(str(foreign), str(foreign_copy)) == str(foreign_copy)
    copied = foreign_copy.stat()
    assert foreign_copy.read_bytes() == contents
    assert stat.S_IMODE(copied.st_mode) == stat.S_IMODE(metadata.st_mode)
    assert (copied.st_dev, copied.st_ino) != (metadata.st_dev, metadata.st_ino)
    assert copied.st_uid == os.geteuid() and copied.st_nlink == 1

    sentinel = tmp_path / "existing-destination"
    sentinel.write_bytes(b"must not overwrite")
    for original in (owned, foreign):
        with pytest.raises(FileExistsError):
            _copy_prepared_runtime_file(str(original), str(sentinel))
        assert sentinel.read_bytes() == b"must not overwrite"
    absent_copy = tmp_path / "absent-copy"
    with pytest.raises(FileNotFoundError):
        _copy_prepared_runtime_file(str(tmp_path / "missing-source"), str(absent_copy))
    assert not absent_copy.exists()
    assert tuple(getattr(foreign.stat(), field) for field in fields) == before


def test_supervision_preserves_original_failure_and_bound_streams(tmp_path: Path) -> None:
    process = supervise(
        [sys.executable, "-I", "-c", "print('actual child'); raise SystemExit(17)"],
        tmp_path,
        tmp_path / "output/readiness/failure",
        time.monotonic() + 10,
    )
    assert process["exit_code"] == 17
    assert process["timed_out"] is False
    stdout = tmp_path / process["streams"]["stdout"]["path"]
    assert stdout.read_text() == "actual child\n"


@pytest.mark.timeout(20)
def test_supervision_kills_actual_timeout(tmp_path: Path) -> None:
    process = supervise(
        [sys.executable, "-I", "-c", "import time; time.sleep(30)"],
        tmp_path,
        tmp_path / "output/readiness/timeout",
        time.monotonic() + 10,
    )
    assert type(process["pid"]) is int
    assert process["timed_out"] is True
    assert process["exit_code"] < 0
    assert process["accepted"] is process["cleanup"]["verified"] is False
    assert process["duration_seconds"] < 15


def test_supervision_refuses_evidence_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="canonical path"):
        supervise([sys.executable, "-c", "pass"], tmp_path, tmp_path / "outside", time.monotonic() + 5)


@pytest.mark.parametrize("gate", ["root:docs_lint", "root:methods", "root:macos:process"])
def test_negative_controls_execute_real_production_paths(gate: str) -> None:
    assert negative_control(Path.cwd(), gate) == 23


@pytest.mark.parametrize(
    "gate",
    [
        "templates/template_formal:live:network-faults",
        "templates/template_pools_rules_tools:live:bundled-resource-execution",
        "templates/template_code_project:live:local-review",
        "templates/template_pitch_deck:live:pdf-pptx",
    ],
)
def test_specialized_negative_controls_execute_actual_checkers(gate: str) -> None:
    assert negative_control(Path.cwd(), gate) == 23


def test_unselected_model_and_docker_image_are_blocked_without_acquisition(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_native import native_execution
    from infrastructure.project.public_acceptance_auxiliary_worker import MissingAuxiliaryProvider

    for gate in (
        "templates/template_sia:live:docker-sandbox",
        "templates/template_code_project:live:local-review",
    ):
        with pytest.raises(MissingAuxiliaryProvider, match="explicitly selected"):
            native_execution(Path.cwd(), gate, 30, tmp_path, {})


@pytest.mark.timeout(420)
def test_real_process_readback_after_producer_root_and_wrapper_deleted(tmp_path: Path) -> None:
    import json
    import os
    import platform
    import shutil
    import subprocess

    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.project.public_acceptance_auxiliary_supervision import complete_auxiliary_observation
    from infrastructure.project.public_acceptance_auxiliary_validation import _supervision_diagnostic
    from infrastructure.reporting.readiness_receipts import source_fingerprint

    source = Path.cwd()
    producer = tmp_path / "producer"
    producer.mkdir()
    shutil.copytree(
        source / "infrastructure", producer / "infrastructure", ignore=shutil.ignore_patterns("__pycache__")
    )
    for kind in ("storybook", "newspaper"):
        original = source / f"projects/templates/template_{kind}"
        destination = producer / f"projects/templates/template_{kind}"
        for part in ("src", "content"):
            shutil.copytree(original / part, destination / part, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(original / "pyproject.toml", destination / "pyproject.toml")
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(source / name, producer / name)
    prepared = Path(sys.prefix).resolve()
    environment = producer / ".venv"
    (environment / "bin").mkdir(parents=True)
    interpreter = environment / "bin/python"
    interpreter.symlink_to(Path(sys.executable))
    shutil.copyfile(prepared / "pyvenv.cfg", environment / "pyvenv.cfg")
    library = environment / f"lib/python{sys.version_info.major}.{sys.version_info.minor}"
    library.mkdir(parents=True)
    # Complete genuine installed RECORD files need regular held directories.
    # Reuse owned regular inodes when permitted; copy foreign-owned runtime
    # files with their metadata. The producer never writes prepared files.
    shutil.copytree(
        prepared / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages",
        library / "site-packages",
        copy_function=_copy_prepared_runtime_file,
    )
    shutil.copytree(prepared / "share", environment / "share", copy_function=_copy_prepared_runtime_file)
    for entrypoint in (prepared / "bin").iterdir():
        if entrypoint.is_file() and not entrypoint.is_symlink() and entrypoint.name != "python":
            _copy_prepared_runtime_file(str(entrypoint), str(environment / "bin" / entrypoint.name))
    directory = producer / "output/readiness/portable"
    gate = "root:roster"
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    # This control claims complete source-roster metadata and process
    # portability, not execution of each exemplar's algorithms.
    for scope in PUBLIC_PROJECT_NAMES:
        project = producer / "projects" / scope
        (project / "src").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / "projects" / scope / "pyproject.toml", project / "pyproject.toml")
    refused_directory = producer / "output/readiness/unsupported-print"
    refused_spec = write_json(
        producer,
        refused_directory / "spec.json",
        {"gate": "root:macos:rendering", "budget": 180, "raw_path": "output/readiness/unsupported-print/raw.json"},
    )
    from infrastructure.project.public_acceptance_auxiliary_bootstrap import WORKER, prepare_audited_auxiliary_command

    refused_command, refused_payload = prepare_audited_auxiliary_command(
        interpreter, producer, WORKER, ("--spec", str(producer / refused_spec["path"])), refused_directory / "execution"
    )
    refused = supervise(
        refused_command,
        producer,
        refused_directory / "execution",
        time.monotonic() + 180,
        bootstrap_payload=refused_payload,
    )
    actual_refusal = json.loads((refused_directory / "raw.json").read_text())
    assert refused["timed_out"] is False
    assert not actual_refusal.get("details", {}).get("print_witness_artifact")
    darwin_tools = all(shutil.which(name) for name in ("pandoc", "pdftoppm", "pdffonts"))
    if platform.system() == "Darwin" and darwin_tools:
        # A standalone Darwin print witness runs its tools and writes its witness
        # DATA, then its own validation needs externally admitted source and
        # original launch custody for every native tool receipt. Without that
        # authority it fails closed: the raw result references no witness, and
        # the retained file is only unadmitted DATA for the controls below.
        refusal_code, refusal_status = 1, "fail"
        assert actual_refusal["failure_class"] == "ProjectionSourceUnsupported"
        assert UNADMITTED in actual_refusal["diagnostic"]
        assert list(refused_directory.rglob("print-witness.json")) == [
            refused_directory / "print-witness/print-witness.json"
        ]
        print_controls = "retained-witness"
    else:
        refusal_code, refusal_status = 75, "blocked"
        assert ("actual Darwin host" if platform.system() != "Darwin" else "unavailable") in actual_refusal[
            "diagnostic"
        ]
        assert not list(refused_directory.rglob("print-witness.json"))
        print_controls = "no-witness"
    assert refused["exit_code"] == actual_refusal["exit_code"] == refusal_code
    assert actual_refusal["status"] == refusal_status
    fingerprint = source_fingerprint(producer)
    spec = write_json(
        producer,
        directory / "spec.json",
        {"gate": gate, "budget": 180, "raw_path": "output/readiness/portable/raw.json"},
    )
    command, payload = prepare_audited_auxiliary_command(
        interpreter, producer, WORKER, ("--spec", str(producer / spec["path"])), directory / "execution"
    )
    process = supervise(command, producer, directory / "execution", time.monotonic() + 180, bootstrap_payload=payload)
    assert process["exit_code"] == 0, (directory / "raw.json").read_text()
    complete = complete_auxiliary_observation(process)
    assert complete, _supervision_diagnostic(process)
    raw_binding = {
        "path": "output/readiness/portable/raw.json",
        "sha256": __import__("hashlib").sha256((directory / "raw.json").read_bytes()).hexdigest(),
    }
    raw = json.loads((directory / "raw.json").read_text())
    assert source_fingerprint(producer) == fingerprint
    process.update(
        gate=gate,
        source_fingerprint=fingerprint,
        source_before=fingerprint,
        source_after=fingerprint,
        spec_artifact=spec,
        raw_artifact=raw_binding,
    )
    binding = write_json(producer, directory / "process.json", process)
    details = {
        **raw["details"],
        "command": command,
        "execution_exit_code": 0,
        "process_artifact": binding,
        "raw_artifact": raw_binding,
    }
    write_json(producer, directory / "details.json", details)
    reader_root = tmp_path / "reader"
    shutil.copytree(producer, reader_root, ignore=shutil.ignore_patterns(".venv"))
    shutil.rmtree(producer)
    assert not interpreter.exists()
    assert source_fingerprint(reader_root) == fingerprint
    minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    # Retain the actual already-prepared interpreter distribution at a
    # distinct reader location; preserve its ABI without another install.
    prefix = Path(sys.base_prefix).resolve()
    binary = Path(sys.executable).resolve()
    assert binary.is_relative_to(prefix)
    members = list(prefix.rglob("*"))
    assert len(members) <= 100_000
    assert sum(item.lstat().st_size for item in members if item.is_file() and not item.is_symlink()) <= 2 * 1024**3
    reader_runtime = tmp_path / "reader-python"
    # A fresh reader must not add links to the shared interpreter distribution.
    # Retain exact ABI bytes in independent files and keep its original metadata.
    metadata_fields = ("st_dev", "st_ino", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
    originals = {
        item.relative_to(prefix): tuple(getattr(item.stat(), field) for field in metadata_fields)
        for item in members
        if item.is_file() and not item.is_symlink()
    }
    shutil.copytree(prefix, reader_runtime, copy_function=shutil.copy2, symlinks=True)
    for relative, expected in originals.items():
        original = prefix / relative
        copied = reader_runtime / relative
        assert tuple(getattr(original.stat(), field) for field in metadata_fields) == expected
        assert (copied.stat().st_dev, copied.stat().st_ino) != (expected[0], expected[1])
        assert copied.stat().st_nlink == 1
    alternate = reader_runtime / binary.relative_to(prefix)
    assert alternate.is_file() and alternate.resolve() != Path(sys.executable).resolve()
    script = r"""
import sys,json,pathlib,hashlib
sys.path[:0]=sys.argv[1:3]
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.project.public_acceptance_auxiliary_validation import validate_auxiliary_process
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import source_fingerprint
root=pathlib.Path(sys.argv[1])
details=json.loads((root/'output/readiness/portable/details.json').read_text())
gate,refusal_code,refusal_status,print_controls=sys.argv[4],int(sys.argv[5]),sys.argv[6],sys.argv[7]
assert source_fingerprint(root)==sys.argv[3]
validate_auxiliary_process(gate,sys.argv[3],details,SnapshotReader(root))
process_path=root/details['process_artifact']['path'];original_process=process_path.read_bytes()
original_process_binding=dict(details['process_artifact'])
for field in ('accepted','cleanup','private-malformed'):
    changed=json.loads(original_process)
    if field=='accepted':changed[field]=False
    elif field=='cleanup':changed['cleanup']['verified']=False
    else:
        # Invented private/oversize DATA must never be rendered into failure logs.
        private='invented-private-diagnostic-marker'
        changed.update(accepted={'TOKEN':private},pid=private,exit_code=2**256,
                       timed_out=[private],output_limit_exceeded={'TOKEN':private})
        changed['cleanup']={'verified':False,'environment':{'TOKEN':private},
                            'guardian_armed':{'TOKEN':private},'diagnostics':[private*10000],
                            'final_census_error':{'type':[private],'cause':private*10000,'errno':True,
                                'procfs':{'pid':private,'uid_real':2**256,'caller_euid':True,
                                          'comm':private*10000,'probe_status':[private],
                                          'environment':{'TOKEN':private}}}}
    body=(json.dumps(changed,indent=2,sort_keys=True)+'\n').encode()
    process_path.write_bytes(body)
    details['process_artifact']['sha256']=hashlib.sha256(body).hexdigest()
    try:validate_auxiliary_process(gate,sys.argv[3],details,SnapshotReader(root))
    except ValueError as error:
        if field=='private-malformed':
            assert private not in str(error) and len(str(error))<=2200
    else:raise AssertionError('unverified process cleanup admitted')
    finally:
        process_path.write_bytes(original_process)
        details['process_artifact']=dict(original_process_binding)
validate_auxiliary_process(gate,sys.argv[3],details,SnapshotReader(root))
observations=details['source_roster_observations']
assert details['projects']==list(PUBLIC_PROJECT_NAMES)
assert [item['scope'] for item in observations]==list(PUBLIC_PROJECT_NAMES)
metadata=root/observations[0]['metadata_artifact']['path'];original_metadata=metadata.read_bytes()
metadata.write_bytes(original_metadata+b'\n# changed after actual roster producer\n')
try:validate_auxiliary_process(gate,sys.argv[3],details,SnapshotReader(root))
except ValueError:pass
else:raise AssertionError('changed current roster metadata admitted')
finally:metadata.write_bytes(original_metadata)
sdk=root/'infrastructure/core/execution_boundary.py';original_sdk=sdk.read_bytes()
sdk.write_bytes(original_sdk+b'\n# changed current source after portable producer\n')
current=source_fingerprint(root);assert current!=sys.argv[3]
try:
    validate_auxiliary_process(gate,current,details,SnapshotReader(root))
except ValueError:pass
else:raise AssertionError('changed current SDK source fingerprint admitted')
finally:sdk.write_bytes(original_sdk)
assert source_fingerprint(root)==sys.argv[3]
validate_auxiliary_process(gate,sys.argv[3],details,SnapshotReader(root))
refusal=json.loads((root/'output/readiness/unsupported-print/raw.json').read_text())
assert refusal['exit_code']==refusal_code and refusal['status']==refusal_status
assert not refusal.get('details',{}).get('print_witness_artifact')
report={'role':'actual-portable-roster-controls','projects':len(observations),
        'unsupported_print_original_exit':refusal_code,'source_and_metadata_controls':2}
if print_controls=='retained-witness':
    # Call the production witness validator directly on the retained DATA of the
    # refused Darwin print run, after the producer root has been deleted.
    import copy,hashlib
    from infrastructure.reporting.native_print_witness_validation import validate_print_witness
    from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
    from infrastructure.reporting.required_acceptance_aggregate import _evidence_closure
    relative='output/readiness/unsupported-print/print-witness/print-witness.json'
    path=root/relative;original=path.read_bytes();witness=json.loads(original)
    closure=_evidence_closure(SnapshotReader(root),relative)
    assert sum(map(len,closure.values()))<64*1024*1024
    assert all(item['path'] in closure for item in witness['raster_artifacts'])
    def refused(binding):
        try:validate_print_witness(binding,SnapshotReader(root),expected_pid=refusal['pid'],expected_runtime=refusal['runtime'])
        except ValueError as error:return [isinstance(error,ProjectionSourceUnsupported),str(error)]
        raise AssertionError('retained print witness admitted without original launch custody')
    controls={'untampered':refused({'path':relative,'sha256':hashlib.sha256(original).hexdigest()})}
    for fault in ('worker','source','font-roles','font-before-after','font-private-path','library-files','tool'):
        changed=copy.deepcopy(witness);tool_path=None
        if fault=='worker':changed['pid']+=1
        elif fault=='source':changed['source_after']['infrastructure'][1][-1]='0'*64
        elif fault=='font-roles':changed['fonts_before']['storybook']['roles'].pop()
        elif fault=='font-before-after':changed['fonts_after']['storybook']['roles'][0]['resource']['sha256']='0'*64
        elif fault=='font-private-path':
            for key in ('fonts_before','fonts_after'):
                changed[key]['storybook']['roles'][0]['resource']['path']='/private/unsupported/font.ttf'
        elif fault=='library-files':changed['library_before']['distributions'][0]['files'].pop()
        elif fault=='tool':
            # Version receipts are read in retained order; only the first is reached before custody.
            name=next(iter(changed['versions']))
            tool_path=root/changed['versions'][name]['path'];saved_tool=tool_path.read_bytes()
            tool=json.loads(saved_tool);tool['original_exit_code']=1
            tool_path.write_text(json.dumps(tool));changed['versions'][name]['sha256']=hashlib.sha256(tool_path.read_bytes()).hexdigest()
        path.write_text(json.dumps(changed))
        try:controls[fault]=refused({'path':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        finally:
            path.write_bytes(original)
            if tool_path is not None:tool_path.write_bytes(saved_tool)
    report['print_witness']={'controls':controls,'closure_files':len(closure),'closure_bytes':sum(map(len,closure.values()))}
print(json.dumps(report))
"""
    result = subprocess.run(
        [
            str(alternate),
            "-I",
            "-c",
            script,
            str(reader_root),
            str(prepared / f"lib/python{minor}/site-packages"),
            fingerprint,
            gate,
            str(refusal_code),
            refusal_status,
            print_controls,
        ],
        cwd=reader_root,
        capture_output=True,
        text=True,
        timeout=180,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    (tmp_path / "portable-observation.json").write_text(result.stdout)
    observation = json.loads(result.stdout.strip().splitlines()[-1])
    if print_controls == "retained-witness":
        controls = observation["print_witness"]["controls"]
        # Unchanged retained witness DATA fails closed at the custody gate.
        custody_refusal, message = controls.pop("untampered")
        assert custody_refusal and UNADMITTED in message, message
        # Each fault reached before custody is refused for its own reason.
        assert set(controls) == set(PRINT_WITNESS_FAULTS)
        for fault, reason in PRINT_WITNESS_FAULTS.items():
            custody_refusal, message = controls[fault]
            assert not custody_refusal and reason in message, (fault, message)
    else:
        assert "print_witness" not in observation


@pytest.fixture(scope="module")
def print_candidate_data(tmp_path_factory: pytest.TempPathFactory) -> tuple[list[dict], list[dict]]:
    """Actual bounded Pandoc/XeTeX/PDF raster DATA; no complete print witness claim.

    A finite invented two-page manuscript exercises the shared PDF inventory and full raster closure predicates
    on every platform, independently of Darwin-only print witness admission.
    """
    from infrastructure.reporting.native_format_acceptance_checks import (
        audit_pdf_raster,
        native_tool_record,
        parse_native_bytes,
    )
    from infrastructure.reporting.native_format_acceptance_contracts import native_environment
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    root = tmp_path_factory.mktemp("actual-print-candidate")
    directory = root / "output/readiness/candidate"
    directory.mkdir(mode=0o700, parents=True)
    deadline = time.monotonic() + 60
    env = native_environment(Path(__file__).resolve().parents[3], Path(sys.executable), directory)
    rows = []
    closure = []
    for ordinal, kind in enumerate(("storybook", "newspaper")):
        work = directory / kind
        work.mkdir(mode=0o700)
        pdf = work / "candidate.pdf"
        source = work / "source.md"
        source.write_text(
            f"# Invented {kind} candidate\n\nFinite first source page.\n\n\\newpage\n\nFinite second source page.\n"
        )
        tool = native_tool_record(
            root,
            work,
            "pandoc",
            [str(source), "--from=markdown+raw_tex", "--standalone", "--pdf-engine=xelatex", "--output", str(pdf)],
            env=env,
            deadline=deadline,
            run_id="d" * 32,
            purpose="actual-print-candidate-source",
        )
        assert tool["exit_code"] == tool["original_exit_code"] == 0
        snapshot = SnapshotReader(root).read(pdf.relative_to(root).as_posix())
        observed = parse_native_bytes("pdf", snapshot.content)
        assert observed["pages"] == 2
        raster = audit_pdf_raster(
            root,
            work,
            snapshot,
            observed,
            env=env,
            deadline=deadline,
            run_id="d" * 32,
            ordinal=ordinal,
        )
        assert len(raster["rasters"]) == 2
        row = {"kind": kind, "observation": observed, "raster": raster, "source": {}}
        groups = [raster]
        if kind == "newspaper":
            source_raster = audit_pdf_raster(
                root,
                work,
                snapshot,
                observed,
                env=env,
                deadline=deadline,
                run_id="d" * 32,
                ordinal=3,
            )
            row["source"]["raster"] = source_raster
            groups.append(source_raster)
        for group in groups:
            for page in group["rasters"]:
                retained = SnapshotReader(root).read(page["path"])
                assert retained.sha256 == page["sha256"]
                closure.append({"path": retained.relative, "sha256": retained.sha256})
        # Reparse retained native bytes rather than trusting the recorded outcome.
        row["independent_observation"] = parse_native_bytes("pdf", SnapshotReader(root).read(snapshot.relative).content)
        rows.append(row)
    return rows, closure


@pytest.mark.parametrize("fault", ["pages", "closure"])
def test_print_witness_page_and_closure_tamper_needs_original_launch_custody(
    fault: str, print_candidate_data: tuple[list[dict], list[dict]]
) -> None:
    """Shared candidate DATA predicates reject genuine retained observation tampering.

    No Source/Original capability is created. Complete witness custody refusal
    remains separately asserted by the actual portable auxiliary worker test.
    """
    import copy
    from infrastructure.reporting.native_print_witness_validation import (
        _validate_print_candidate_page_inventory,
        _validate_print_candidate_raster_closure,
    )
    from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported

    rows, closure = print_candidate_data
    assert len(closure) == 6
    assert _validate_print_candidate_raster_closure(closure, rows) == closure
    for row in rows:
        _validate_print_candidate_page_inventory(row["observation"], row["independent_observation"])
    if fault == "pages":
        changed = copy.deepcopy(rows[0]["observation"])
        changed["pages"] += 1
        with pytest.raises(ValueError, match="page inventory differs from actual PDF bytes") as refused:
            _validate_print_candidate_page_inventory(changed, rows[0]["independent_observation"])
    else:
        changed = copy.deepcopy(closure)
        changed.pop()
        with pytest.raises(ValueError, match="page artifact closure is missing or changed") as refused:
            _validate_print_candidate_raster_closure(changed, rows)
    assert not isinstance(refused.value, ProjectionSourceUnsupported)


def test_mandatory_raw_custody_rejects_bare_success_flags(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_validation import (
        validate_auxiliary_process,
        validate_sandbox_transfer,
    )
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    with pytest.raises(ValueError, match="exact artifact binding"):
        validate_auxiliary_process("root:docs_lint", "a" * 64, {"execution_exit_code": 0}, SnapshotReader(tmp_path))
    with pytest.raises(ValueError, match="exact artifact bindings"):
        validate_sandbox_transfer({"destination_kind": "sandbox", "remote_verified": True}, SnapshotReader(tmp_path))


def test_transfer_rejects_unscoped_identity_before_export_or_remote_io(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary import run_sandbox_transfer

    with pytest.raises(ValueError, match="exact repository"):
        run_sandbox_transfer(
            tmp_path,
            export_receipt=tmp_path / "missing.json",
            upload_outputs=tmp_path / "missing-outputs.json",
            downloaded_directory=tmp_path / "output/readiness/download",
            repository="unselected",
            run_id="0",
            source_commit="branch-name",
            evidence_dir=tmp_path / "output/readiness/transfer",
        )
    assert not (tmp_path / "output").exists()


def test_roster_executes_actual_source_admission_and_rejects_missing_roots(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_worker import execute

    with pytest.raises(ValueError, match="canonical public source root"):
        execute(tmp_path, "root:roster", 10)


@pytest.mark.parametrize(
    "name",
    [
        "template_textbook",
        "template_code_project",
        "template_gold_refinement",
        "template_registered_report",
        "template_template",
        "template_sia",
        "template_experiment_tree",
        "template_madlib",
        "template_prose_project",
        "template_search_project",
        "template_literature_meta_analysis",
        "template_advanced_literature_review",
        "template_autoresearch_project",
    ],
)
def test_actual_deterministic_domains_reject_corrupt_measurements(name: str) -> None:
    import copy
    import tempfile

    from infrastructure.project.public_acceptance_auxiliary_domains import (
        domain_negative,
        execute_domain,
        validate_domain,
    )
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    root = Path.cwd()
    base = root / "output/readiness"
    base.mkdir(parents=True, exist_ok=True)
    scope = f"templates/{name}"
    with tempfile.TemporaryDirectory(prefix="domain-control-", dir=base) as temporary:
        result = execute_domain(root, scope, Path(temporary), 120)
        assert result is not None
        validate_domain(result, SnapshotReader(root))
        assert domain_negative(root, scope) == 23
        corrupt = copy.deepcopy(result)
        measured = corrupt["measurements"]
        if name == "template_textbook":
            measured["logistic_growth"]["N"][0] += 1
        elif name == "template_code_project":
            next(iter(measured["runs"].values()))["objective_value"] += 1
        elif name == "template_gold_refinement":
            measured["purities"][-1] = -1
        elif name == "template_registered_report":
            measured["frozen"]["registration_hash"] = "0" * 64
        elif name == "template_template":
            measured["receipt"]["public_exemplar_count"] = 0
        elif name == "template_sia":
            measured["score"] = 0
        elif name == "template_experiment_tree":
            measured["summary"]["total_nodes"] = 0
        elif name == "template_madlib":
            measured["field_counts"] = {}
        elif name == "template_prose_project":
            measured["total_words"] = 0
        elif name == "template_search_project":
            measured["invariants"][0]["actual"] += 1
        elif name == "template_literature_meta_analysis":
            measured["statistics"]["total"] = 0
        elif name == "template_advanced_literature_review":
            measured["phase_corpora"]["combined_corpus.jsonl"] = []
        elif name == "template_autoresearch_project":
            measured["result"]["baseline"]["test_accuracy"] = 0
        with pytest.raises(ValueError):
            validate_domain(corrupt, SnapshotReader(root))


def test_portable_pipeline_rejects_bare_success_before_compilation(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_pipeline import SCHEMA, validate_portable_pipeline
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    with pytest.raises(ValueError, match="original artifact binding"):
        validate_portable_pipeline(
            "templates/template_madlib", {"pipeline_schema": SCHEMA, "mode": "core"}, SnapshotReader(tmp_path)
        )
    assert negative_control(Path.cwd(), "templates/template_madlib:pipeline") == 23


def test_explicit_supervision_rejects_protected_environment_names_before_reading_values(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="protected credential names"):
        supervise(
            [sys.executable, "-c", "raise SystemExit(0)"],
            tmp_path,
            tmp_path / "output/readiness/forbidden",
            time.monotonic() + 5,
            environment={"EXAMPLE_API_KEY": "invalid-control"},
        )
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("budget", [600, 600.0])
def test_portable_logical_plan_preserves_original_budget_serialization(budget: float) -> None:
    from infrastructure.project.public_acceptance_auxiliary_pipeline import _read_logical_plan

    root = Path(__file__).resolve().parents[3]
    plan = _read_logical_plan(root, "templates/template_madlib", budget, "1760000000")["plan"]
    assert type(plan["run_timeout_seconds"]) is type(budget)
    assert plan["run_timeout_seconds"] == budget


@pytest.mark.skipif(sys.platform != "darwin", reason="actual Darwin print worker control")
@pytest.mark.parametrize("control", ["missing-tools", "caller-timer", "deadline"])
def test_print_worker_retains_real_preflight_and_guard_failures(tmp_path: Path, control: str) -> None:
    import json
    import subprocess
    import uuid

    from infrastructure.project.public_acceptance_evidence import write_json

    root = Path.cwd()
    directory = root / "output/readiness" / ("worker-failure-" + uuid.uuid4().hex + "-" + control)
    spec = write_json(
        root,
        directory / "spec.json",
        {
            "gate": "root:macos:rendering",
            "budget": 1 if control == "deadline" else 30,
            "raw_path": (directory / "raw.json").relative_to(root).as_posix(),
        },
    )
    script = (
        "import pathlib,signal,sys; "
        + ("signal.setitimer(signal.ITIMER_REAL,60); " if control == "caller-timer" else "")
        + "from infrastructure.project.public_acceptance_auxiliary_worker import main; "
        + "sys.argv=['worker','--spec',sys.argv[1]]; raise SystemExit(main())"
    )
    from infrastructure.core.execution_boundary import build_bounded_env

    env = build_bounded_env()
    if control == "missing-tools":
        env["PATH"] = str(tmp_path / "empty-path")
    result = subprocess.run(
        [sys.executable, "-c", script, str(root / spec["path"])],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    raw = json.loads((directory / "raw.json").read_text())
    if control == "missing-tools":
        assert result.returncode == raw["exit_code"] == 75
        assert raw["status"] == "blocked"
        assert "unavailable" in raw["diagnostic"]
    else:
        assert result.returncode == raw["exit_code"] == (124 if control == "deadline" else 1), result.stderr
        assert raw["status"] == ("timeout" if control == "deadline" else "fail")
        expected = "NativeDeadlineExpired" if control == "deadline" else "NativeDeadlineUnavailable"
        assert raw["failure_class"] == expected
        assert "deadline" in raw["diagnostic"] or "timer" in raw["diagnostic"]

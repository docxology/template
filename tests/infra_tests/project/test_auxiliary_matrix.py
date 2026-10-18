"""Complete Source partition and adversarial DATA controls, never hosted authority."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from infrastructure.project.auxiliary_matrix_hosted import AuxiliaryMatrixOriginal, _jobs, _producer
from infrastructure.project.auxiliary_matrix_plan import (
    DARWIN_GATES,
    KINDS,
    TRANSFER_GATE,
    matrix_plan,
    selection,
    validate_cell,
)
from infrastructure.project.auxiliary_matrix_validation import _authenticate_graph, authenticate_matrix
from infrastructure.project.public_hosted_origin import HostedReadbackContext
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.original_job_outcome import evaluate_original_outcome
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.required_acceptance_aggregate import auxiliary_owned_projection


@pytest.fixture(scope="module")
def requirements():
    root = Path(__file__).resolve().parents[3]
    result, faults = required_profile(root, SnapshotReader(root), source_fingerprint(root))
    assert not faults
    return result


def _report(requirements, cell):
    return dict(
        schema_version=SCHEMA_VERSION,
        source_fingerprint="a" * 64,
        roster=list(PUBLIC_PROJECT_NAMES),
        gates={gate: {"status": "pass"} for gate in matrix_plan(requirements)[cell]},
        auxiliary_selection=selection(requirements, cell),
        auxiliary_workers=1,
        source_current=True,
        deadline_exhausted=False,
        exit_code=0,
    )


def test_every_project_and_linux_gate_has_one_complete_serial_owner(requirements):
    plan = matrix_plan(requirements)
    assert set(plan) == {"root", *(Path(scope).name for scope in PUBLIC_PROJECT_NAMES)}
    actual = [gate for gates in plan.values() for gate in gates]
    expected = {row.id for row in requirements if row.kind in KINDS} - DARWIN_GATES - {TRANSFER_GATE}
    assert set(actual) == expected and len(actual) == len(expected)
    assert all(selection(requirements, cell)["timeout_seconds"] == 1800 for cell in plan)
    assert all(selection(requirements, cell)["workers"] == 1 for cell in plan)
    values = {cell: _report(requirements, cell) for cell in plan}
    values["darwin"] = dict(
        gates={gate: {"status": "pass"} for gate in DARWIN_GATES},
        source_current=True,
        deadline_exhausted=False,
        exit_code=0,
    )
    projected = auxiliary_owned_projection(values, requirements)
    assert sum(len(value["gates"]) for value in projected) == len(expected | DARWIN_GATES)
    assert TRANSFER_GATE not in {gate for value in projected for gate in value["gates"]}
    for cell in plan:
        outcome = evaluate_original_outcome("auxiliary", values[cell], requirements, fingerprint="a" * 64)
        assert outcome["exit_code"] == 0 and outcome["release_acceptance_granted"] is False


@pytest.mark.parametrize("mutation", ["omit", "foreign", "clock", "workers", "owner", "missing-selection"])
def test_cell_cannot_narrow_or_reassign_original_scope(requirements, mutation):
    report = _report(requirements, "root")
    if mutation == "omit":
        report["gates"].pop(next(iter(report["gates"])))
    elif mutation == "foreign":
        report["gates"][next(iter(DARWIN_GATES))] = {"status": "pass"}
    elif mutation == "clock":
        report["auxiliary_selection"]["timeout_seconds"] = 3600
    elif mutation == "workers":
        report["auxiliary_workers"] = 3
    elif mutation == "owner":
        report["auxiliary_selection"]["cell"] = "template_code_project"
    else:
        report.pop("auxiliary_selection")
    with pytest.raises(ValueError):
        validate_cell(report, requirements, "root")


@pytest.mark.parametrize("fault", ["missing", "duplicate-gate", "duplicate-scope", "foreign-scope"])
def test_partition_refuses_incomplete_or_overlapping_source(requirements, fault):
    rows = list(requirements)
    if fault == "missing":
        rows = [row for row in rows if row.scope != PUBLIC_PROJECT_NAMES[0]]
    elif fault == "duplicate-gate":
        rows.append(next(row for row in rows if row.kind in KINDS))
    else:
        from dataclasses import replace

        row = next(row for row in rows if row.kind in KINDS and row.scope != "root")
        rows.append(replace(row, id=row.id + ":extra", scope="foreign" if fault == "foreign-scope" else "root"))
        if fault == "duplicate-scope":
            # Same gate may never acquire a second Source owner.
            rows[-1] = replace(rows[-1], id=row.id)
    with pytest.raises(ValueError):
        matrix_plan(rows)


@pytest.mark.parametrize("fault", ["missing-cell", "darwin-overlap", "failed-operation", "expired-operation"])
def test_aggregate_cannot_choose_successful_subset(requirements, fault):
    values = {cell: _report(requirements, cell) for cell in matrix_plan(requirements)}
    values["darwin"] = dict(
        gates={gate: {"status": "pass"} for gate in DARWIN_GATES},
        source_current=True,
        deadline_exhausted=False,
        exit_code=0,
    )
    if fault == "missing-cell":
        values.pop(next(cell for cell in values if cell != "darwin"))
    elif fault == "darwin-overlap":
        values["darwin"]["gates"]["root:roster"] = {"status": "pass"}
    elif fault == "failed-operation":
        values["root"]["exit_code"] = 1
    else:
        values["root"]["deadline_exhausted"] = True
    with pytest.raises(ValueError):
        auxiliary_owned_projection(values, requirements)


def _api_data():
    run = dict(id=11, head_sha="b" * 40, run_attempt=2, repository={"id": 22})
    job = dict(
        id=33,
        name="auxiliary-original (root)",
        run_id=11,
        head_sha="b" * 40,
        run_attempt=2,
        status="completed",
        conclusion="success",
        started_at="2026-10-18T01:00:00Z",
        completed_at="2026-10-18T01:02:00Z",
        steps=[dict(name="Retain original auxiliary audit", conclusion="success")],
    )
    artifact = dict(
        id=44,
        name="required-source-auxiliary-linux-root",
        expired=False,
        created_at="2026-10-18T01:01:00Z",
        workflow_run=dict(id=11, head_sha="b" * 40, repository_id=22, head_repository_id=22),
    )
    return run, job, artifact


@pytest.mark.parametrize(
    "fault", ["none", "attempt", "head", "foreign", "expired", "duplicate-job", "duplicate-artifact", "step", "time"]
)
def test_api_metadata_predicates_reject_stale_or_ambiguous_data_without_minting_authority(fault):
    run, job, artifact = _api_data()
    jobs, artifacts = [job], [artifact]
    if fault == "attempt":
        job["run_attempt"] = 1
    elif fault == "head":
        job["head_sha"] = "c" * 40
    elif fault == "foreign":
        artifact["workflow_run"]["repository_id"] = 99
    elif fault == "expired":
        artifact["expired"] = True
    elif fault == "duplicate-job":
        jobs.append(copy.deepcopy(job))
    elif fault == "duplicate-artifact":
        artifacts.append(copy.deepcopy(artifact))
    elif fault == "step":
        job["steps"][0]["conclusion"] = "skipped"
    elif fault == "time":
        artifact["created_at"] = "2026-10-18T00:01:00Z"
    if fault == "none":
        assert _producer("root", artifacts, jobs, run) is artifact
    else:
        with pytest.raises(ValueError):
            _producer("root", artifacts, jobs, run)


@pytest.mark.parametrize("fault", ["missing", "repeated", "changing-count"])
def test_job_pagination_requires_exact_unique_originals(fault):
    _, job, _ = _api_data()
    pages = [dict(total_count=1, jobs=[job])]
    if fault == "missing":
        pages[0]["total_count"] = 2
    elif fault == "repeated":
        pages = [dict(total_count=2, jobs=[job, job])]
    else:
        pages.append(dict(total_count=2, jobs=[]))
    with pytest.raises(ValueError):
        _jobs(pages)


def test_transported_metadata_cannot_construct_live_matrix_original(tmp_path):
    with pytest.raises(ValueError, match="actual live fixed collector"):
        AuxiliaryMatrixOriginal(object(), tmp_path, "docxology/template", 11, "b" * 40, {}, {}, {}, 1.0)
    reader = SnapshotReader(tmp_path, hosted_origin=HostedReadbackContext({}, "docxology/template", 11, "b" * 40))
    with pytest.raises(ValueError, match="genuinely collected"):
        authenticate_matrix(reader, {}, [])


@pytest.mark.parametrize("fault", ["none", "changed", "foreign", "missing"])
def test_original_graph_is_confined_to_actual_project_archive(tmp_path, fault):
    import time

    prefix = Path("output/readiness/auxiliary-linux/root")
    target = tmp_path / prefix / "original.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(b'{"actual":true}')
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    members = {str(prefix / "original.json"): digest}
    reference = dict(path=str(prefix / "original.json"), sha256=digest)
    if fault == "changed":
        target.write_bytes(b'{"actual":false}')
    elif fault == "foreign":
        reference["path"] = "output/readiness/auxiliary-linux/foreign/original.json"
    elif fault == "missing":
        members = {}
    if fault == "none":
        _authenticate_graph(SnapshotReader(tmp_path), reference, prefix, members, time.monotonic() + 5)
    else:
        with pytest.raises(ValueError):
            _authenticate_graph(SnapshotReader(tmp_path), reference, prefix, members, time.monotonic() + 5)


@pytest.mark.parametrize("declaration", ["lean/lakefile.lean", "formal/lean/lakefile.lean"])
def test_portable_source_inventory_excludes_only_declared_lean_runtime(tmp_path, declaration):
    import os
    from infrastructure.project.public_acceptance_auxiliary_pipeline_environment import _source_records

    root = tmp_path.resolve()
    scope = "templates/template_code_project"
    project = root / "projects" / scope
    for directory in (root / "infrastructure", root / "scripts", project):
        directory.mkdir(parents=True, exist_ok=True)
    for name in ("pyproject.toml", "uv.lock", ".python-version", "pipeline.yaml"):
        (root / name).write_text("Source declaration\n")
    (project / "pipeline.yaml").write_text("stages: []\n")
    lake = project / declaration
    lake.parent.mkdir(parents=True, exist_ok=True)
    lake.write_text("import Lake\n")
    runtime = lake.parent / ".lake/generated"
    runtime.parent.mkdir()
    runtime.write_text("first")
    authored = project / "src/data/.lake/authored"
    authored.parent.mkdir(parents=True)
    authored.write_text("first")
    before = _source_records(root, scope)
    runtime.write_text("other")
    assert _source_records(root, scope) == before
    prior = authored.stat()
    authored.write_text("other")
    os.utime(authored, ns=(prior.st_atime_ns, prior.st_mtime_ns))
    assert _source_records(root, scope) != before


@pytest.mark.parametrize("fault", ["none", "repeated-identity", "omitted", "changed"])
def test_retained_archive_bytes_cover_each_live_original_identity_once(tmp_path, fault):
    from infrastructure.project.auxiliary_matrix_validation import _authenticate_archives

    directory = Path("output/readiness/owned-matrix")
    (tmp_path / directory).mkdir(parents=True)
    cells, archives = {}, []
    for identity in (11, 22):
        content = str(identity).encode()
        digest = hashlib.sha256(content).hexdigest()
        path = directory / f"{identity}.zip"
        (tmp_path / path).write_bytes(content)
        cells[str(identity)] = dict(artifact_id=identity, archive_sha256=digest)
        archives.append(dict(path=str(path), sha256=digest))
    if fault == "repeated-identity":
        alternate = directory / "elsewhere/11.zip"
        (tmp_path / alternate).parent.mkdir()
        (tmp_path / alternate).write_bytes(b"11")
        archives[-1] = dict(path=str(alternate), sha256=archives[0]["sha256"])
    elif fault == "omitted":
        archives.pop()
    elif fault == "changed":
        (tmp_path / archives[0]["path"]).write_bytes(b"xx")
    if fault == "none":
        _authenticate_archives(SnapshotReader(tmp_path), archives, cells, directory)
    else:
        with pytest.raises(ValueError):
            _authenticate_archives(SnapshotReader(tmp_path), archives, cells, directory)


@pytest.mark.parametrize("fault", ["none", "omitted", "changed", "duplicate", "page-gap"])
def test_retained_api_observation_bindings_have_complete_integrity_only(tmp_path, fault):
    from infrastructure.project.auxiliary_matrix_validation import _authenticate_observations

    directory = Path("output/readiness/owned-matrix")
    (tmp_path / directory).mkdir(parents=True)
    cells = {"root": dict(artifact_id=11)}
    observations = []
    for name in ("run", "workflow", "metadata-11", "artifact-11", "listing-1", "jobs-1"):
        path = directory / (name + "-process.json")
        (tmp_path / path).write_bytes(b"{}")
        observations.append(dict(path=str(path), sha256=hashlib.sha256(b"{}").hexdigest()))
    if fault == "omitted":
        observations.pop(0)
    elif fault == "changed":
        (tmp_path / observations[0]["path"]).write_bytes(b'{"changed":true}')
    elif fault == "duplicate":
        observations.append(dict(observations[0]))
    elif fault == "page-gap":
        path = directory / "listing-2-process.json"
        (tmp_path / path).write_bytes(b"{}")
        observations[-2] = dict(path=str(path), sha256=hashlib.sha256(b"{}").hexdigest())
    if fault == "none":
        _authenticate_observations(SnapshotReader(tmp_path), observations, cells, directory)
    else:
        with pytest.raises(ValueError):
            _authenticate_observations(SnapshotReader(tmp_path), observations, cells, directory)


def test_actual_matrix_cli_derives_complete_cells_and_scoped_provider_grants():
    import json
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "-m", "infrastructure.project.public_acceptance_auxiliary_cli", "--matrix-json"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    rows = json.loads(result.stdout)["include"]
    assert len(rows) == len(PUBLIC_PROJECT_NAMES) + 1
    assert {row["cell"] for row in rows} == {"root", *(Path(scope).name for scope in PUBLIC_PROJECT_NAMES)}
    assert all(
        type(row["docker"]) is bool and type(row["model"]) is bool and type(row["formal"]) is bool for row in rows
    )
    assert {row["cell"] for row in rows if row["docker"]} == {"template_sia"}
    assert {row["cell"] for row in rows if row["formal"]} == {"template_formal", "template_active_inference"}

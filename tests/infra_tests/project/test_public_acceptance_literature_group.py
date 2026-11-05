"""Real-file group predicates do not manufacture original process/model acceptance.

Synthetic native bytes below exercise the independent file/model reader only.
A green synthetic packet must still fail complete audited-origin admission.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from infrastructure.project.public_acceptance_evidence import MissingAuxiliaryProvider, write_json
from infrastructure.project.public_acceptance_literature_group import (
    CAPABILITIES,
    CELL,
    GATES,
    ORIGIN_SCHEMA,
    SCOPE,
    LiteratureGroup,
    bound,
    create_group,
    read_origin,
    retain_origin,
    validate_originals,
    validate_projection_execution,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _packet(tmp_path: Path):
    directory = tmp_path / "output/readiness/arl/002"
    retained = directory / "literature-originals"
    retained.mkdir(parents=True)
    model = "protocol-predicate-only"
    identity = "a" * 64
    bodies = {
        "phase_0/body.bin": b"original controlled provider bytes\x00\xff",
        "model_1/request.json": json.dumps({"model": model, "prompt": "a retained source quote"}).encode(),
        "model_1/response.json": b'{"response":"unit predicate, no actual model claim","eval_count":3}',
        "model_1/model.json": json.dumps({"model": model, "model_sha256": identity}).encode(),
    }
    artifacts = {name: _digest(body) for name, body in bodies.items()}
    native = {
        "schema_version": "template/literature-unpaid-acceptance/1",
        "project": CELL,
        "execution_mode": "live-unpaid",
        "status": "passed",
        "paid_integrations": False,
        "source_unchanged": True,
        "consumed_unchanged": True,
        "loaded_implementation_verified": True,
        "capabilities": list(CAPABILITIES),
        "producer_results": {name: {"status": "passed"} for name in CAPABILITIES},
        "local_generation_calls": [{"directory": "model_1", "status": "passed", "model_sha256": identity}],
        "artifacts": artifacts,
        "consumed_artifacts": dict(artifacts),
        "source_manifest": {"predicate-only": "b" * 64},
        "runtime_environment": {"predicate-only": True},
        "implementation_custody": {"predicate-only": True},
        "declared_dependencies": {"predicate-only": True},
    }
    native["producer_results"]["local-classification"]["model_sha256"] = identity
    plan = {"directory": "output/readiness/arl", "model": model}
    return directory, retained, bodies, native, plan


def _seal(root: Path, directory: Path, retained: Path, bodies: dict, native: dict):
    for name, raw in bodies.items():
        path = retained / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    receipt = (json.dumps(native, sort_keys=True) + "\n").encode()
    (retained / "receipt.json").write_bytes(receipt)
    native_binding = write_json(root, directory / "literature-native.json", native)
    all_bodies = {**bodies, "receipt.json": receipt}
    manifest = {
        "receipt": native_binding,
        "original_receipt": {
            "path": (retained / "receipt.json").relative_to(root).as_posix(),
            "sha256": _digest(receipt),
        },
        "bytes": sum(len(raw) for raw in all_bodies.values()),
        "files": {
            name: {"path": (retained / name).relative_to(root).as_posix(), "sha256": _digest(raw), "bytes": len(raw)}
            for name, raw in all_bodies.items()
        },
        "acceptance_granted": False,
    }
    return native_binding, write_json(root, directory / "literature-originals.json", manifest), manifest


def test_complete_file_predicate_reads_exact_provider_and_model_bytes(tmp_path: Path) -> None:
    directory, retained, bodies, native, plan = _packet(tmp_path)
    native_binding, originals_binding, _ = _seal(tmp_path, directory, retained, bodies, native)
    reader = SnapshotReader(tmp_path, operation_deadline=time.monotonic() + 60)
    assert validate_originals(reader, plan, native_binding, originals_binding) == native
    assert reader.unchanged()
    (retained / "phase_0/body.bin").write_bytes(b"changed after the independent read")
    assert not reader.unchanged()
    with pytest.raises(ValueError):
        validate_originals(SnapshotReader(tmp_path), plan, native_binding, originals_binding)


@pytest.mark.parametrize(
    "defect",
    [
        "missing-capability",
        "failed-capability",
        "capability-roster",
        "consumed-hash",
        "missing-consumed",
        "selected-model",
        "model-digest",
        "model-call-status",
        "duplicate-model-json",
        "source-custody",
        "runtime-custody",
    ],
)
def test_resealed_packet_cannot_hide_a_semantic_custody_defect(tmp_path: Path, defect: str) -> None:
    directory, retained, bodies, native, plan = _packet(tmp_path)
    if defect == "missing-capability":
        del native["producer_results"]["screening"]
    elif defect == "failed-capability":
        native["producer_results"]["licensed-fulltext"]["status"] = "failed"
    elif defect == "capability-roster":
        native["capabilities"].append("invented")
    elif defect == "consumed-hash":
        native["consumed_artifacts"]["model_1/response.json"] = "0" * 64
    elif defect == "missing-consumed":
        del native["consumed_artifacts"]["model_1/request.json"]
    elif defect == "selected-model":
        plan["model"] = "another-model"
    elif defect == "model-digest":
        native["producer_results"]["local-classification"]["model_sha256"] = "0" * 64
    elif defect == "model-call-status":
        native["local_generation_calls"][0]["status"] = "incomplete"
    elif defect == "duplicate-model-json":
        name = "model_1/model.json"
        bodies[name] = b'{"model":"first","model":"second","model_sha256":"' + b"a" * 64 + b'"}'
        native["artifacts"][name] = native["consumed_artifacts"][name] = _digest(bodies[name])
    elif defect == "source-custody":
        native["source_unchanged"] = False
    elif defect == "runtime-custody":
        native["runtime_environment"] = {}
    native_binding, originals_binding, _ = _seal(tmp_path, directory, retained, bodies, native)
    with pytest.raises(ValueError):
        validate_originals(SnapshotReader(tmp_path), plan, native_binding, originals_binding)


@pytest.mark.parametrize("defect", ["missing-file", "extra-file", "size", "raw-receipt", "escape", "symlink"])
def test_original_census_and_actual_files_are_required(tmp_path: Path, defect: str) -> None:
    directory, retained, bodies, native, plan = _packet(tmp_path)
    native_binding, originals_binding, manifest = _seal(tmp_path, directory, retained, bodies, native)
    name = "model_1/response.json"
    if defect == "missing-file":
        del manifest["files"][name]
    elif defect == "extra-file":
        manifest["files"]["invented.json"] = dict(manifest["files"][name])
    elif defect == "size":
        manifest["files"][name]["bytes"] += 1
    elif defect == "raw-receipt":
        path = retained / "receipt.json"
        path.write_text('{"status":"passed"}\n')
        digest = _digest(path.read_bytes())
        manifest["files"]["receipt.json"].update(sha256=digest, bytes=path.stat().st_size)
        manifest["original_receipt"]["sha256"] = digest
        manifest["bytes"] = sum(row["bytes"] for row in manifest["files"].values())
    elif defect == "escape":
        manifest["files"][name]["path"] = "output/readiness/foreign.json"
    elif defect == "symlink":
        original = retained / name
        outside = tmp_path / "outside.json"
        outside.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(outside)
    originals_binding = write_json(tmp_path, directory / "literature-originals.json", manifest)
    with pytest.raises((ValueError, OSError)):
        validate_originals(SnapshotReader(tmp_path), plan, native_binding, originals_binding)


def test_separate_controller_invocations_have_distinct_group_identity(tmp_path: Path) -> None:
    python = tmp_path / "python"
    python.write_bytes(b"a file identity, never executed")
    selected = {
        "cell": CELL,
        "gates": [f"{SCOPE}:pipeline", f"{SCOPE}:domain", *GATES],
        "timeout_seconds": 1800,
        "workers": 1,
    }
    groups = [
        create_group(
            tmp_path,
            tmp_path / f"output/readiness/invocation-{index}",
            selected,
            python,
            "b" * 64,
            {SCOPE: {"model": "explicit"}},
            12345.0,
        )
        for index in range(2)
    ]
    plans = [bound(SnapshotReader(tmp_path), group.binding).json_object() for group in groups]
    assert plans[0]["nonce"] != plans[1]["nonce"]
    assert plans[0]["directory"] != plans[1]["directory"]
    assert all(group.origin is None for group in groups)
    for plan in plans:
        assert plan["model"] == "explicit"
        assert plan["interpreter"]["sha256"] == _digest(python.read_bytes())
        assert plan["selection"] == selected
        assert plan["operation_deadline"] == 12345.0


@pytest.mark.parametrize("status", ["blocked", "fail"])
def test_first_refused_original_is_retained_once_without_retry(tmp_path: Path, status: str) -> None:
    directory = tmp_path / "output/readiness/arl"
    binding = write_json(tmp_path, directory / "literature-group.json", {"nonce": "a" * 32})
    group = LiteratureGroup(binding)
    original = write_json(
        tmp_path,
        directory / "002/gate.json",
        {"gate": GATES[0], "source_fingerprint": "b" * 64, "status": status, "details": {}},
    )
    retain_origin(tmp_path, directory, group, GATES[0], original)
    before = (tmp_path / group.origin["path"]).read_bytes()
    with pytest.raises(ValueError, match="more than once"):
        retain_origin(tmp_path, directory, group, GATES[0], original)
    plan = {"directory": directory.relative_to(tmp_path).as_posix(), "source_fingerprint": "b" * 64}
    error = MissingAuxiliaryProvider if status == "blocked" else ValueError
    with pytest.raises(error, match="original literature producer did not pass"):
        read_origin(SnapshotReader(tmp_path), binding, group.origin, plan)
    assert (tmp_path / group.origin["path"]).read_bytes() == before
    assert not (tmp_path / "projects").exists()  # No producer/provider was launched as a fallback.


@pytest.mark.parametrize("defect", ["recursive", "foreign-group", "foreign-directory", "synthetic-success"])
def test_retained_labels_cannot_replace_complete_original_process_admission(tmp_path: Path, defect: str) -> None:
    directory = tmp_path / "output/readiness/arl"
    binding = write_json(tmp_path, directory / "literature-group.json", {"nonce": "a" * 32})
    details = {"literature_role": "original", "literature_group": binding}
    if defect == "recursive":
        details["literature_origin"] = binding
    original = write_json(
        tmp_path,
        directory / "002/gate.json",
        {"gate": GATES[0], "source_fingerprint": "b" * 64, "status": "pass", "details": details},
    )
    origin = write_json(
        tmp_path,
        directory / "literature-origin.json",
        {
            "schema_version": ORIGIN_SCHEMA,
            "group": binding if defect != "foreign-group" else {},
            "gate_artifact": original,
        },
    )
    plan = {"directory": directory.relative_to(tmp_path).as_posix(), "source_fingerprint": "b" * 64}
    if defect == "foreign-directory":
        plan["directory"] = "output/readiness/another-invocation"
    with pytest.raises(ValueError):
        read_origin(SnapshotReader(tmp_path), binding, origin, plan)


def test_generic_projection_label_cannot_widen_other_live_gates(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="only the complete ARL"):
        validate_projection_execution(
            "templates/template_search_project:live:retrieval",
            {"literature_role": "projection"},
            SnapshotReader(tmp_path),
        )


def test_each_capability_executes_its_own_real_failing_checker() -> None:
    root = Path(__file__).resolve().parents[3]
    for gate in GATES:
        script = (
            "from infrastructure.project.public_acceptance_auxiliary_worker import negative_control; from pathlib import Path; raise SystemExit(negative_control(Path.cwd(), "
            + repr(gate)
            + "))"
        )
        process = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert process.returncode == 23, process.stdout + process.stderr


@pytest.fixture(scope="module")
def canonical_group_source():
    from infrastructure.project.auxiliary_matrix_plan import selection
    from infrastructure.reporting.readiness_receipts import source_fingerprint
    from infrastructure.reporting.release_readiness_profile import required_profile

    root = Path(__file__).resolve().parents[3]
    fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, SnapshotReader(root), fingerprint)
    assert not faults
    return root, fingerprint, selection(requirements, CELL)


@pytest.fixture
def real_group(tmp_path: Path, canonical_group_source):
    import uuid
    import time

    root, fingerprint, selected = canonical_group_source
    directory = root / "output/readiness" / ("group-predicate-" + uuid.uuid4().hex)
    group = create_group(
        root,
        directory,
        selected,
        Path(sys.executable),
        fingerprint,
        {SCOPE: {"model": "refusal-control-only"}},
        time.monotonic() + 300,
    )
    assert group is not None
    return root, directory, group, fingerprint


def test_group_reader_rederives_the_complete_selection_from_actual_source(real_group) -> None:
    from infrastructure.project.public_acceptance_literature_group import read_group

    root, directory, group, fingerprint = real_group
    reader = SnapshotReader(root)
    plan = read_group(reader, group.binding, GATES[0], fingerprint)
    assert plan["selection"]["workers"] == 1
    assert plan["selection"]["timeout_seconds"] == 1800
    assert [gate for gate in plan["selection"]["gates"] if ":live:" in gate] == list(GATES)
    assert plan["directory"] == directory.relative_to(root).as_posix()
    assert reader.unchanged()


@pytest.mark.parametrize(
    "defect", ["scope", "selection", "capability-order", "source", "directory", "deadline", "nonce", "interpreter"]
)
def test_group_reader_refuses_resealed_foreign_plan(real_group, defect: str) -> None:
    from infrastructure.project.public_acceptance_literature_group import read_group

    root, directory, group, fingerprint = real_group
    plan = bound(SnapshotReader(root), group.binding).json_object()
    if defect == "scope":
        plan["scope"] = "templates/template_search_project"
    elif defect == "selection":
        plan["selection"]["gates"].pop()
    elif defect == "capability-order":
        plan["gates"] = list(reversed(plan["gates"]))
    elif defect == "source":
        plan["source_fingerprint"] = "0" * 64
    elif defect == "directory":
        plan["directory"] = "output/readiness/foreign-invocation"
    elif defect == "deadline":
        plan["operation_deadline"] = True
    elif defect == "nonce":
        plan["nonce"] = "not-a-nonce"
    elif defect == "interpreter":
        plan["interpreter"]["path"] = "relative-python"
    altered = write_json(root, directory / "literature-group.json", plan)
    with pytest.raises(ValueError):
        read_group(SnapshotReader(root), altered, GATES[0], fingerprint)


@pytest.mark.parametrize(
    "defect",
    [
        "model",
        "interpreter",
        "interpreter-bytes",
        "spec-deadline",
        "process-deadline",
        "nonce-binding",
        "spec-directory",
    ],
)
def test_group_process_identity_predicate_rejects_foreign_observations(real_group, defect: str) -> None:
    from infrastructure.project.public_acceptance_literature_group import validate_group_process

    root, directory, group, fingerprint = real_group
    plan = bound(SnapshotReader(root), group.binding).json_object()
    details = {"literature_role": "original", "literature_group": group.binding}
    process = {
        "spec_artifact": {"path": str(directory.relative_to(root) / "002/spec.json")},
        "selected_interpreter": plan["interpreter"]["path"],
        "executable_sha256": plan["interpreter"]["sha256"],
        "original_deadline_monotonic": plan["operation_deadline"],
    }
    spec = {
        "literature_group": group.binding,
        "producer_inputs": {"model": plan["model"]},
        "operation_deadline": plan["operation_deadline"],
    }
    if defect == "model":
        spec["producer_inputs"]["model"] = "foreign-model"
    elif defect == "interpreter":
        process["selected_interpreter"] = "/foreign/python"
    elif defect == "interpreter-bytes":
        process["executable_sha256"] = "0" * 64
    elif defect == "spec-deadline":
        spec["operation_deadline"] += 1
    elif defect == "process-deadline":
        process["original_deadline_monotonic"] += 1
    elif defect == "nonce-binding":
        spec["literature_group"] = {**group.binding, "sha256": "0" * 64}
    elif defect == "spec-directory":
        process["spec_artifact"]["path"] = "output/readiness/foreign/002/spec.json"
    with pytest.raises(ValueError, match="process changed"):
        validate_group_process(GATES[0], fingerprint, details, SnapshotReader(root), process, spec)


@pytest.mark.parametrize("status", ["blocked", "fail"])
def test_actual_native_projection_entry_refuses_without_starting_another_producer(real_group, status: str) -> None:
    from infrastructure.project.public_acceptance_auxiliary_native import native_execution

    root, directory, group, fingerprint = real_group
    first = write_json(
        root,
        directory / "002/gate.json",
        {"gate": GATES[0], "source_fingerprint": fingerprint, "status": status, "details": {}},
    )
    retain_origin(root, directory, group, GATES[0], first)
    origin_before = bound(SnapshotReader(root), group.origin).content
    base = root / "projects" / SCOPE / "output/.pipeline/literature_acceptance"
    children_before = sorted(path.name for path in base.iterdir()) if base.exists() else []
    error = MissingAuxiliaryProvider if status == "blocked" else ValueError
    with pytest.raises(error, match="original literature producer did not pass"):
        native_execution(
            root,
            GATES[1],
            30,
            directory / "003",
            {"model": "refusal-control-only"},
            operation_deadline=bound(SnapshotReader(root), group.binding).json_object()["operation_deadline"],
            literature_group=group.binding,
            literature_origin=group.origin,
        )
    assert (bound(SnapshotReader(root), group.origin).content) == origin_before
    assert not (directory / "003/literature-execution.json").exists()
    assert (sorted(path.name for path in base.iterdir()) if base.exists() else []) == children_before


def test_origin_admission_cannot_omit_its_own_executed_control(real_group) -> None:
    root, directory, group, fingerprint = real_group
    execution = write_json(
        root,
        directory / "002/literature-execution.json",
        {"execution_kind": "actual", "status": "passed", "capability": "retrieval"},
    )
    details = {
        "execution_exit_code": 0,
        "capability": "retrieval",
        "paid": False,
        "execution_kind": "actual",
        "execution_artifact": execution,
        "literature_role": "original",
        "literature_group": group.binding,
        "assertions": {"predicate-only": True},
        "negative_controls": [],
    }
    first = write_json(
        root,
        directory / "002/gate.json",
        {"gate": GATES[0], "source_fingerprint": fingerprint, "status": "pass", "details": details},
    )
    retain_origin(root, directory, group, GATES[0], first)
    plan = bound(SnapshotReader(root), group.binding).json_object()
    with pytest.raises(ValueError, match="real failing negative controls"):
        read_origin(SnapshotReader(root), group.binding, group.origin, plan)


def test_enclosing_report_cannot_drop_the_group_field(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_literature_group import validate_group_report

    root = tmp_path
    gate = write_json(root, root / "output/readiness/arl/002/gate.json", {"details": {"literature_role": "projection"}})
    report = {"gates": {GATES[0]: {"artifact": gate["path"], "artifact_sha256": gate["sha256"]}}}
    with pytest.raises(ValueError, match="omitted its enclosing invocation"):
        validate_group_report(report, SnapshotReader(root), CELL)


def test_enclosing_report_refuses_a_different_first_gate_packet(real_group) -> None:
    from infrastructure.project.public_acceptance_literature_group import validate_group_report

    root, directory, group, fingerprint = real_group
    first = write_json(root, directory / "002/gate.json", {"gate": GATES[0], "status": "blocked"})
    donor = write_json(root, directory / "donor/gate.json", {"gate": GATES[0], "status": "blocked"})
    origin = write_json(
        root,
        directory / "literature-origin.json",
        {"schema_version": ORIGIN_SCHEMA, "group": group.binding, "gate_artifact": donor},
    )
    plan = bound(SnapshotReader(root), group.binding).json_object()
    report = {
        "literature_group": group.binding,
        "literature_origin": origin,
        "source_fingerprint": fingerprint,
        "auxiliary_selection": plan["selection"],
        "gates": {GATES[0]: {"artifact": first["path"], "artifact_sha256": first["sha256"]}},
    }
    with pytest.raises(ValueError, match="own first gate"):
        validate_group_report(report, SnapshotReader(root), CELL)


def test_already_expired_independent_reader_cannot_read_an_original(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_literature_group import validate_invocation

    with pytest.raises(TimeoutError, match="reader deadline exhausted"):
        validate_invocation(tmp_path, tmp_path / "output/readiness/absent.json", time.monotonic() - 1)
    directory, retained, bodies, native, plan = _packet(tmp_path)
    native_binding, originals_binding, _ = _seal(tmp_path, directory, retained, bodies, native)
    reader = SnapshotReader(tmp_path, operation_deadline=time.monotonic() - 1)
    with pytest.raises(TimeoutError, match="reader deadline exhausted"):
        validate_originals(reader, plan, native_binding, originals_binding)
    assert not reader.snapshots


@pytest.mark.parametrize(
    "defect", ["manifest-bool", "manifest-negative", "manifest-excess", "file-negative", "file-excess", "total-excess"]
)
def test_original_byte_census_refuses_malformed_or_oversized_commitments(tmp_path: Path, defect: str) -> None:
    from infrastructure.project.public_acceptance_literature_group import MAX_RETAINED_BYTES

    directory, retained, bodies, native, plan = _packet(tmp_path)
    native_binding, originals_binding, manifest = _seal(tmp_path, directory, retained, bodies, native)
    if defect == "manifest-bool":
        manifest["bytes"] = True
    elif defect == "manifest-negative":
        manifest["bytes"] = -1
    elif defect == "manifest-excess":
        manifest["bytes"] = MAX_RETAINED_BYTES + 1
    elif defect == "file-negative":
        manifest["files"]["phase_0/body.bin"]["bytes"] = -1
    elif defect == "file-excess":
        manifest["files"]["phase_0/body.bin"]["bytes"] = MAX_RETAINED_BYTES + 1
    else:
        for record in manifest["files"].values():
            record["bytes"] = MAX_RETAINED_BYTES
    originals_binding = write_json(tmp_path, directory / "literature-originals.json", manifest)
    with pytest.raises(ValueError):
        validate_originals(SnapshotReader(tmp_path), plan, native_binding, originals_binding)


@pytest.mark.parametrize(
    "changed",
    ["provider", *[f"model_{index}/{part}.json" for index in range(1, 8) for part in ("request", "response", "model")]],
)
def test_retained_original_archive_roundtrip_preserves_all_models_and_refuses_tamper(
    tmp_path: Path, changed: str
) -> None:
    # This is real archive/retained-byte validation, without original process or model authority.
    from infrastructure.reporting.native_hosted_original_producer import _zip
    from infrastructure.reporting.native_hosted_transport_archive import _archive
    from infrastructure.reporting.required_acceptance_aggregate import _evidence_closure

    producer, consumer = tmp_path / "producer", tmp_path / "consumer"
    directory, retained, bodies, native, plan = _packet(producer)
    first = dict(bodies)
    for index in range(2, 8):
        for part in ("request", "response", "model"):
            bodies[f"model_{index}/{part}.json"] = first[f"model_1/{part}.json"]
    native["local_generation_calls"] = [
        {"directory": f"model_{index}", "status": "passed", "model_sha256": "a" * 64} for index in range(1, 8)
    ]
    native["artifacts"] = {name: _digest(raw) for name, raw in bodies.items()}
    native["consumed_artifacts"] = dict(native["artifacts"])
    native_binding, originals_binding, _ = _seal(producer, directory, retained, bodies, native)
    receipt = write_json(
        producer,
        producer / "output/readiness/receipt.json",
        {"native_artifact": native_binding, "literature_originals": originals_binding},
    )
    closure = _evidence_closure(SnapshotReader(producer), receipt["path"])
    transported = _archive(_zip(closure), maximum=64 * 1024 * 1024, count=10000)
    assert set(transported) == set(closure)
    for relative, raw in transported.items():
        destination = consumer / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    assert (
        validate_originals(
            SnapshotReader(consumer, operation_deadline=time.monotonic() + 60), plan, native_binding, originals_binding
        )
        == native
    )
    name = "phase_0/body.bin" if changed == "provider" else changed
    destination = consumer / retained.relative_to(producer) / name
    destination.write_bytes(destination.read_bytes() + b"actual changed retained byte")
    with pytest.raises(ValueError, match="evidence changed"):
        validate_originals(SnapshotReader(consumer), plan, native_binding, originals_binding)

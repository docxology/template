"""Aggregate inventory admission never turns partial CI into complete acceptance."""

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION
from infrastructure.reporting.required_acceptance_aggregate import merge_receipts


def _receipt(gates):
    return {
        "schema_version": SCHEMA_VERSION,
        "platform_version": "4.0.1",
        "source_fingerprint": "a" * 64,
        "source_commit": "b" * 40,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": gates,
    }


def _merge(values):
    return merge_receipts(
        values, revision="b" * 40, fingerprint="a" * 64, version="4.0.1", required={"root:one", "root:two"}
    )


def test_partial_input_preserves_missing_inventory():
    result = _merge([_receipt({"root:one": {"status": "blocked"}})])
    assert result["gates"] == {"root:one": {"status": "blocked"}}
    assert result["source_commit"] == "b" * 40


def test_duplicate_gate_cannot_choose_successful_receipt():
    with pytest.raises(ValueError, match="duplicate"):
        _merge([_receipt({"root:one": {"status": "fail"}}), _receipt({"root:one": {"status": "pass"}})])


@pytest.mark.parametrize(
    "field,value",
    [("source_commit", "c" * 40), ("source_fingerprint", "c" * 64), ("roster", []), ("schema_version", "ordinary-ci")],
)
def test_stale_or_foreign_input_refused(field, value):
    receipt = _receipt({"root:one": {"status": "pass"}})
    receipt[field] = value
    with pytest.raises(ValueError, match="unsupported"):
        _merge([receipt])


def test_ordinary_ci_gate_is_not_release_gate():
    with pytest.raises(ValueError, match="foreign"):
        _merge([_receipt({"ordinary-infra": {"status": "pass"}})])


def test_root_owned_projection_retains_blocked_owner_and_all_six_targets():
    """Historical node ID; require every current host/minor target."""
    from types import SimpleNamespace

    from infrastructure.reporting.required_acceptance_aggregate import root_owned_projection

    requirements = [
        SimpleNamespace(id=f"root:{host}:{minor}", kind="root-case", case_platform=host, python_version=minor)
        for host in ("darwin", "linux")
        for minor in ("3.14", "3.15")
    ]
    ids = {item.id for item in requirements} | {"root:case-policy", "root:coverage"}
    values = {}
    for host in ("darwin", "linux"):
        for minor in ("3.14", "3.15"):
            gates = {key: {"status": "pass"} for key in ids}
            gates[f"root:{host}:{minor}"] = {"status": "blocked"}
            values[host, minor] = _receipt(gates)
    result = root_owned_projection(values, requirements)
    flat = {key: gate for value in result for key, gate in value["gates"].items()}
    assert set(flat) == ids
    assert all(flat[item.id]["status"] == "blocked" for item in requirements)
    assert sum(len(value["gates"]) for value in result) == len(ids)
    values.pop(("darwin", "3.15"))
    with pytest.raises(ValueError, match="all exact supported"):
        root_owned_projection(values, requirements)


def test_auxiliary_fixed_owners_retain_original_blocked_audits_and_separate_transfer():
    from types import SimpleNamespace

    from infrastructure.reporting.required_acceptance_aggregate import auxiliary_owned_projection

    requirements = [
        SimpleNamespace(id=identity, kind=kind)
        for identity, kind in (
            ("root:roster", "roster"),
            ("root:macos:process", "platform"),
            ("root:macos:rendering", "platform"),
            ("root:sandbox:transfer", "transfer"),
        )
    ]
    gates = {item.id: {"status": "blocked"} for item in requirements}
    values = {
        "linux": {**_receipt(gates), "source_current": True, "deadline_exhausted": False, "exit_code": 75},
        "darwin": {
            **_receipt({key: {"status": "pass"} for key in gates if "macos" in key}),
            "source_current": True,
            "deadline_exhausted": False,
            "exit_code": 0,
        },
    }
    projected = auxiliary_owned_projection(values, requirements)
    assert projected[0]["gates"] == {"root:roster": {"status": "blocked"}}
    assert set(projected[1]["gates"]) == {"root:macos:process", "root:macos:rendering"}
    assert values["linux"]["gates"]["root:sandbox:transfer"]["status"] == "blocked"
    values["darwin"]["gates"]["root:roster"] = {"status": "pass"}
    with pytest.raises(ValueError, match="omitted or invented"):
        auxiliary_owned_projection(values, requirements)


@pytest.mark.parametrize("host", ["linux", "darwin"])
def test_auxiliary_projection_rejects_late_operation_even_with_all_passing_gates(host):
    from types import SimpleNamespace
    from infrastructure.reporting.required_acceptance_aggregate import auxiliary_owned_projection

    kinds = {
        "root:roster": "roster",
        "root:macos:process": "platform",
        "root:macos:rendering": "platform",
        "root:sandbox:transfer": "transfer",
    }
    requirements = [SimpleNamespace(id=key, kind=kind) for key, kind in kinds.items()]
    closed = {"source_current": True, "deadline_exhausted": False, "exit_code": 0}
    values = {
        "linux": {**_receipt({key: {"status": "pass"} for key in kinds}), **closed},
        "darwin": {**_receipt({key: {"status": "pass"} for key in kinds if "macos" in key}), **closed},
    }
    assert len(auxiliary_owned_projection(values, requirements)) == 2
    values[host].update(deadline_exhausted=True, exit_code=1)
    with pytest.raises(ValueError, match="auxiliary operation did not close"):
        auxiliary_owned_projection(values, requirements)


def test_generic_merge_cannot_discard_auxiliary_deadline_failure():
    value = {
        **_receipt({"root:one": {"status": "pass"}}),
        "source_current": True,
        "deadline_exhausted": True,
        "exit_code": 1,
        "auxiliary_workers": 3,
    }
    with pytest.raises(ValueError, match="auxiliary operation did not close"):
        _merge([value])


def test_complete_archive_closure_retains_native_raster_rows_and_refuses_changed_pixels(tmp_path):
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageStat
    from infrastructure.project.installed_acceptance_artifacts import write_binary
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.required_acceptance_aggregate import _evidence_closure
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    image = Image.new("RGB", (32, 24), "white")
    ImageDraw.Draw(image).rectangle((4, 4, 18, 14), fill="navy")
    stream = BytesIO()
    image.save(stream, format="PNG")
    raster = write_binary(tmp_path, tmp_path / "output/readiness/page-1.png", stream.getvalue())
    row = {**raster, "width_px": image.width, "height_px": image.height, "variance": sum(ImageStat.Stat(image).var)}
    receipt = write_json(tmp_path, tmp_path / "output/readiness/receipt.json", {"rasters": [row]})
    closure = _evidence_closure(SnapshotReader(tmp_path), receipt["path"])
    assert set(closure) == {receipt["path"], raster["path"]}
    assert closure[raster["path"]] == stream.getvalue()
    (tmp_path / raster["path"]).write_bytes(b"changed actual native image bytes")
    with pytest.raises(ValueError, match="original reference"):
        _evidence_closure(SnapshotReader(tmp_path), receipt["path"])


def _held_census(*scopes):
    """A held native census exposing the one fact the union assertion reads."""
    from types import SimpleNamespace

    return SimpleNamespace(originals={scope: object() for scope in scopes})


def test_the_join_refuses_a_census_that_is_not_the_roster(tmp_path):
    """Collected and missing cells are both named, and the filesystem agrees.

    The audit is written before this refusal runs, exactly as the producer
    writes it, so the assertion pins the documented consequence: the audit
    exists and no canonical receipt does, and a re-run needs a fresh root.
    """
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.required_acceptance_aggregate import (
        AUDIT_PATH,
        RECEIPT_PATH,
        _require_cell_union,
    )

    collected = tuple(PUBLIC_PROJECT_NAMES[:-1])
    missing = PUBLIC_PROJECT_NAMES[-1]
    (tmp_path / AUDIT_PATH).parent.mkdir(parents=True, exist_ok=True)
    audit = write_json(tmp_path, tmp_path / AUDIT_PATH, {"candidate_state": "fail"})
    with pytest.raises(ValueError) as refusal:
        _require_cell_union(_held_census(*collected))
    message = str(refusal.value)
    assert "collected:" in message and "missing:" in message
    assert missing in message
    assert all(scope in message for scope in collected)
    assert "no canonical receipt" in message
    assert "fresh root" in message
    assert audit["path"] == AUDIT_PATH
    assert (tmp_path / AUDIT_PATH).exists()
    assert not (tmp_path / RECEIPT_PATH).exists()


def test_the_join_accepts_every_roster_scope_exactly_once():
    from infrastructure.reporting.required_acceptance_aggregate import _require_cell_union

    assert _require_cell_union(_held_census(*PUBLIC_PROJECT_NAMES)) is None


def test_the_join_refuses_an_undeclared_census():
    from infrastructure.reporting.required_acceptance_aggregate import _require_cell_union

    with pytest.raises(ValueError, match="undeclared"):
        _require_cell_union(_held_census(*PUBLIC_PROJECT_NAMES, "templates/not_a_declared_cell"))


def _produce_aggregate_body():
    """Return the real produce_aggregate function node, parsed from its source."""
    import ast
    from pathlib import Path as _Path

    from infrastructure.reporting import required_acceptance_aggregate

    tree = ast.parse(_Path(required_acceptance_aggregate.__file__).read_text())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "produce_aggregate":
            return node
    raise AssertionError("produce_aggregate is missing")


def test_the_union_assertion_is_wired_into_the_join_before_the_receipt():
    """Delete the union call from produce_aggregate and this test goes red.

    The behavioural cases above prove the assertion's contract; this case proves
    the assertion is actually reached by the join, after the state decision and
    before the canonical receipt write, and that it stays behind the packing
    guard so the unpacked path cannot reach it.
    """
    import ast

    body = _produce_aggregate_body()
    calls = [
        node
        for node in ast.walk(body)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_require_cell_union"
    ]
    assert len(calls) == 1, "produce_aggregate must assert the cell union exactly once"
    guards = [
        node
        for node in body.body
        if isinstance(node, ast.If)
        and any(
            isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == "_require_cell_union"
            for item in ast.walk(node)
        )
    ]
    assert len(guards) == 1, "the union assertion must sit behind exactly one guard"
    guard = guards[0]
    assert isinstance(guard.test, ast.Compare) and getattr(guard.test.left, "id", "") == "candidate_packing", (
        "the union assertion must be gated on candidate_packing so the unpacked path is untouched"
    )
    state = [
        node
        for node in body.body
        if isinstance(node, ast.Assign) and any(getattr(target, "id", "") == "state" for target in node.targets)
    ]
    receipt_gate = [
        node
        for node in body.body
        if isinstance(node, ast.If) and getattr(node.test, "left", None) is not None and node.test.left.id == "state"
    ]
    assert state and receipt_gate, "the state assignment and the receipt gate stay top-level"
    assert state[-1].lineno < guard.lineno < receipt_gate[-1].lineno, (
        "the union must run after the state decision and before the canonical receipt write"
    )

"""Aggregate inventory admission never turns partial CI into complete acceptance."""

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION
from infrastructure.reporting.required_acceptance_aggregate import merge_receipts


def _receipt(gates):
    return {
        "schema_version": SCHEMA_VERSION,
        "platform_version": "4.0.0",
        "source_fingerprint": "a" * 64,
        "source_commit": "b" * 40,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": gates,
    }


def _merge(values):
    return merge_receipts(
        values, revision="b" * 40, fingerprint="a" * 64, version="4.0.0", required={"root:one", "root:two"}
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
    from types import SimpleNamespace

    from infrastructure.reporting.required_acceptance_aggregate import root_owned_projection

    requirements = [
        SimpleNamespace(id=f"root:{host}:{minor}", kind="root-case", case_platform=host, python_version=minor)
        for host in ("darwin", "linux")
        for minor in ("3.12", "3.13", "3.14")
    ]
    ids = {item.id for item in requirements} | {"root:case-policy", "root:coverage"}
    values = {}
    for host in ("darwin", "linux"):
        for minor in ("3.12", "3.13", "3.14"):
            gates = {key: {"status": "pass"} for key in ids}
            gates[f"root:{host}:{minor}"] = {"status": "blocked"}
            values[host, minor] = _receipt(gates)
    result = root_owned_projection(values, requirements)
    flat = {key: gate for value in result for key, gate in value["gates"].items()}
    assert set(flat) == ids
    assert all(flat[item.id]["status"] == "blocked" for item in requirements)
    assert sum(len(value["gates"]) for value in result) == len(ids)
    values.pop(("darwin", "3.12"))
    with pytest.raises(ValueError, match="all six"):
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
        "linux": _receipt(gates),
        "darwin": _receipt({key: {"status": "pass"} for key in gates if "macos" in key}),
    }
    projected = auxiliary_owned_projection(values, requirements)
    assert projected[0]["gates"] == {"root:roster": {"status": "blocked"}}
    assert set(projected[1]["gates"]) == {"root:macos:process", "root:macos:rendering"}
    assert values["linux"]["gates"]["root:sandbox:transfer"]["status"] == "blocked"
    values["darwin"]["gates"]["root:roster"] = {"status": "pass"}
    with pytest.raises(ValueError, match="omitted or invented"):
        auxiliary_owned_projection(values, requirements)

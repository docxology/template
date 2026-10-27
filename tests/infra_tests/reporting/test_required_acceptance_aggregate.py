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

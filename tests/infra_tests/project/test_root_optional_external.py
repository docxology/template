"""Only the reviewed production catalog exception can remain unexecuted."""

from copy import deepcopy
from pathlib import Path

import pytest

from infrastructure.project.public_acceptance_case_policy import (
    CENSUS_SCHEMA,
    OPTIONAL_MONID_FAMILY,
    OPTIONAL_POLICY_SCHEMA,
    RootCasePolicy,
    compile_case_plan,
)
from infrastructure.project.public_root_case_admission import Prerequisite, RootCaseAdmission, lane_blockers
from infrastructure.project.public_root_case_units import admitted_units, optional_external_records, required_cells


def _value():
    def family(identity, lane, obligations):
        return {
            "id": identity,
            "lane": lane,
            "obligations": obligations,
            "members": [{"nodeid": identity, "parameter_id": None}],
            "source_sha256": "a" * 64,
            "metadata_sha256": "b" * 64,
        }

    return {
        "schema_version": OPTIONAL_POLICY_SCHEMA,
        "runtimes": ["3.14", "3.15"],
        "platforms": ["darwin", "linux"],
        "families": [
            family("tests/test_owned.py::test_request_parsing", "core", []),
            family(OPTIONAL_MONID_FAMILY, "optional-external", ["monid-discover"]),
        ],
        "obligations": [
            {
                "id": "monid-discover",
                "kind": "network-unverified",
                "eligibility": {
                    "provider": "monid",
                    "operation": "POST /v1/discover",
                    "billing": "unverified",
                    "public_reference": "infrastructure/config/root-monid-discover-review.json",
                    "reference_sha256": "c" * 64,
                },
            }
        ],
    }


def test_optional_catalog_retains_full_census_and_every_mandatory_target_without_pass_claim():
    policy = RootCasePolicy.parse(_value())
    census = {
        "schema_version": CENSUS_SCHEMA,
        "source_identity": "d" * 64,
        "runtime": "3.14",
        "platform": "darwin",
        "nodeids": [member.nodeid for f in policy.families for member in f.members],
        "families": [
            {
                "id": f.id,
                "members": [{"nodeid": m.nodeid, "parameter_id": m.parameter_id} for m in f.members],
                "source_sha256": f.source_sha256,
                "metadata_sha256": f.metadata_sha256,
                "markers": ["network"] if f.lane == "optional-external" else [],
                "public_closure": True,
            }
            for f in policy.families
        ],
    }
    plan = compile_case_plan(policy, census, source_identity="d" * 64)
    prerequisite = (Prerequisite("monid-discover", "network-unverified", ("MONID_API_KEY",), (), ()),)
    admission = RootCaseAdmission(policy, plan, {}, {}, prerequisite, Path.cwd())
    assert set(plan.nodeids) == {"tests/test_owned.py::test_request_parsing", OPTIONAL_MONID_FAMILY}
    assert len(required_cells(policy, prerequisite)) == 4
    assert {cell.platform for cell in required_cells(policy, prerequisite)} == {"darwin", "linux"}
    assert {cell.runtime for cell in required_cells(policy, prerequisite)} == {"3.14", "3.15"}
    assert [unit.nodeids for unit in admitted_units(admission)] == [("tests/test_owned.py::test_request_parsing",)]
    records = optional_external_records(policy)
    assert len(records) == 1 and records[0]["status"] == "unexecuted" and "passed" not in records[0]
    for mode in ("core", "live"):
        with pytest.raises(ValueError, match="exact declared"):
            lane_blockers(admission, "optional-external", mode)


@pytest.mark.parametrize("fault", ["v2", "family", "operation", "provider", "extra-member", "shared-obligation"])
def test_optional_catalog_cannot_waive_another_case_or_scope(fault):
    value = deepcopy(_value())
    optional = value["families"][1]
    if fault == "v2":
        value["schema_version"] = "template-root-case-policy-v2"
    elif fault == "family":
        optional["id"] = "tests/test_owned.py::test_required_other_provider"
        optional["members"][0]["nodeid"] = optional["id"]
    elif fault in {"operation", "provider"}:
        value["obligations"][0]["eligibility"][fault] = "unreviewed"
    elif fault == "extra-member":
        optional["members"].append({"nodeid": OPTIONAL_MONID_FAMILY + "[other]", "parameter_id": "other"})
    else:
        value["families"][0]["obligations"] = ["monid-discover"]
    with pytest.raises(ValueError, match="exact reviewed Monid"):
        RootCasePolicy.parse(value)


@pytest.mark.slow
@pytest.mark.timeout(1200)
def test_actual_v3_runtime_retains_optional_catalog_without_executing_its_body(tmp_path_factory):
    import hashlib
    import json
    import sys

    from infrastructure.project.public_acceptance import _probe_runtime
    from infrastructure.project.public_root_case_census import produce_root_census
    from infrastructure.project.public_root_case_contract import _json
    from infrastructure.project.public_root_runtime_producer import produce_runtime_cohort
    from infrastructure.project.public_root_runtime_readback import read_runtime_cohort
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
    from tests.infra_tests.project import test_root_case_lanes as controls

    root, _, _ = controls.genuine_lane.__wrapped__(tmp_path_factory)
    source = root / "tests/test_owned.py"
    source.write_text(source.read_text().split("@pytest.mark.requires_ollama")[0])
    catalog = root / OPTIONAL_MONID_FAMILY.split("::")[0]
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        "from pathlib import Path\n"
        "def test_live_discover_includes_price_when_key_present():\n"
        "    (Path.cwd()/'output/readiness/optional-production-body').write_text('executed')\n"
        "    raise AssertionError('optional production body must remain unexecuted')\n"
    )
    review_path = root / "infrastructure/config/root-monid-discover-review.json"
    review_path.write_bytes(
        (Path(__file__).parents[3] / "infrastructure/config/root-monid-discover-review.json").read_bytes()
    )
    first = controls._epoch_call(
        produce_root_census, root, root / "output/readiness/optional-authoring", timeout_seconds=180
    )
    assert first["exit_code"] == 0, first
    rows = _json(SnapshotReader(root).read(first["receipt_artifact"]["path"]))["census"]["families"]
    policy = _value()
    policy["obligations"][0]["eligibility"]["reference_sha256"] = hashlib.sha256(review_path.read_bytes()).hexdigest()
    policy["families"] = [
        {key: row[key] for key in ("id", "members", "source_sha256", "metadata_sha256")}
        | {
            "lane": "optional-external" if row["id"] == OPTIONAL_MONID_FAMILY else "core",
            "obligations": ["monid-discover"] if row["id"] == OPTIONAL_MONID_FAMILY else [],
        }
        for row in rows
    ]
    (root / "infrastructure/config/root-case-policy.json").write_text(json.dumps(policy))
    (root / "infrastructure/config/root-case-prerequisites.json").write_text(
        json.dumps(
            {
                "schema_version": "template-root-case-prerequisites-v2",
                "obligations": [
                    {
                        "id": "monid-discover",
                        "kind": "network-unverified",
                        "environment_keys": ["MONID_API_KEY"],
                        "executables": [],
                        "platforms": [],
                    }
                ],
            }
        )
    )
    project = root / "pyproject.toml"
    project.write_text(project.read_text().replace("schema_version=2", "schema_version=3"))
    probe = _probe_runtime(
        root,
        root / "output/readiness/optional-probe",
        f"{sys.version_info.major}.{sys.version_info.minor}",
        Path(sys.executable),
    )
    assert probe["status"] == "pass", probe
    produced = controls._epoch_call(
        produce_runtime_cohort,
        root,
        root / "output/readiness/optional-cohort",
        interpreter=Path(sys.executable),
        runtime_probe=probe["runtime"],
        timeout_seconds=720,
        census_timeout_seconds=180,
        test_timeout_seconds=60,
    )
    assert produced["bundle"]["exit_code"] == 0, produced
    observed = read_runtime_cohort(SnapshotReader(root), produced["bundle"])
    assert observed["passed_counts"] == {"core": 2}
    assert observed["selected_units"] == ["core"]
    assert observed["optional_external"] == optional_external_records(RootCasePolicy.parse(policy))
    assert not (root / "output/readiness/optional-production-body").exists()

"""Unverified billing keeps every target required and permanently blocks execution."""

from pathlib import Path

import pytest

from infrastructure.project.public_acceptance_case_policy import (
    CENSUS_SCHEMA,
    POLICY_SCHEMA,
    RootCasePolicy,
    compile_case_plan,
)
from infrastructure.project.public_root_case_admission import Prerequisite, RootCaseAdmission, lane_blockers
from infrastructure.project.public_root_case_units import required_cells


def _policy(lane="live-unverified"):
    family = "tests/test_owned.py::test_discover"
    return RootCasePolicy.parse(
        {
            "schema_version": POLICY_SCHEMA,
            "runtimes": ["3.12", "3.13", "3.14"],
            "platforms": ["darwin", "linux"],
            "families": [
                {
                    "id": family,
                    "lane": lane,
                    "members": [{"nodeid": family, "parameter_id": None}],
                    "obligations": ["monid-discover"],
                    "source_sha256": "a" * 64,
                    "metadata_sha256": "b" * 64,
                }
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
    )


def _census(policy):
    row = policy.families[0]
    return {
        "schema_version": CENSUS_SCHEMA,
        "source_identity": "d" * 64,
        "runtime": "3.14",
        "platform": "darwin",
        "families": [
            {
                "id": row.id,
                "members": [{"nodeid": row.id, "parameter_id": None}],
                "source_sha256": row.source_sha256,
                "metadata_sha256": row.metadata_sha256,
                "markers": ["network"],
                "public_closure": True,
            }
        ],
        "nodeids": [row.id],
    }


def test_unverified_operation_keeps_every_host_and_minor_required():
    policy = _policy()
    prerequisites = (Prerequisite("monid-discover", "network-unverified", ("MONID_API_KEY",), (), ()),)
    cells = required_cells(policy, prerequisites)
    assert {(cell.platform, cell.runtime) for cell in cells} == {
        (host, minor) for host in ("darwin", "linux") for minor in ("3.12", "3.13", "3.14")
    }
    plan = compile_case_plan(policy, _census(policy), source_identity="d" * 64)
    admission = RootCaseAdmission(policy, plan, {}, {}, prerequisites, Path.cwd())
    for mode in ("core", "live"):
        assert lane_blockers(admission, "live-unverified", mode) == [
            {"id": "live-unverified", "reason": "unpaid-operation-eligibility-unverified"}
        ]


def test_unverified_network_cannot_be_reclassified_as_core_or_verified_live():
    for lane in ("core", "live-unpaid"):
        policy = _policy(lane)
        with pytest.raises(ValueError, match="unverified"):
            compile_case_plan(policy, _census(policy), source_identity="d" * 64)

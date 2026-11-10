"""Naming contract for the bounded native/candidate transport artifacts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from infrastructure.reporting.native_hosted_transport_archive import INDEX_ARTIFACT, MAX_SHARDS, SHARD_PREFIX
from infrastructure.reporting.native_workflow_transport import transport_artifact_names


def test_transport_names_are_unchanged_without_a_cell() -> None:
    assert transport_artifact_names("native") == ("native-index.json", INDEX_ARTIFACT, SHARD_PREFIX)
    assert transport_artifact_names("candidate")[1] == "platform-required-acceptance"


def test_transport_cell_renames_only_the_artifact_names() -> None:
    filename, primary, prefix = transport_artifact_names("native", "template_code_project")
    assert filename == "native-index.json"
    assert primary == "required-source-native-cell-template_code_project"
    assert prefix == primary + "-shard-"
    assert "/" not in primary and "/" not in prefix


@pytest.mark.parametrize("kind", ["candidate", "failed-native", "failed-reader", "failed-handoff"])
def test_transport_cell_names_every_kind_not_only_native(kind: str) -> None:
    """A matrix lane runs sibling cells at once; a kind that ignored `cell` would collide.

    `actions/upload-artifact` refuses or merges a duplicate name inside one run,
    so every kind a matrix cell can upload must carry the cell in its name.
    """
    filename, primary, prefix = transport_artifact_names(kind, "template_code_project")
    assert primary.endswith("-cell-template_code_project")
    assert prefix == primary + "-shard-"
    assert "/" not in primary and "/" not in prefix
    # The producer's index filename is not a name and must not change.
    assert filename == transport_artifact_names(kind)[0]


@pytest.mark.parametrize("kind", ["native", "candidate", "failed-native", "failed-reader", "failed-handoff"])
def test_sibling_cells_never_share_an_artifact_name(kind: str) -> None:
    """The property that matters: two cells of the same kind are distinguishable."""
    first = transport_artifact_names(kind, "template_code_project")
    second = transport_artifact_names(kind, "template_sia")
    assert first[1] != second[1]
    assert first[2] != second[2]
    assert first[0] == second[0]


@pytest.mark.parametrize("cell", ["template_not_declared", "templates/template_code_project"])
@pytest.mark.parametrize("kind", ["native", "candidate", "failed-reader"])
def test_transport_cell_must_be_one_bare_declared_public_exemplar(kind: str, cell: str) -> None:
    with pytest.raises(ValueError, match="one declared public exemplar"):
        transport_artifact_names(kind, cell)


def test_checked_in_shard_uploads_match_source_transport_limit() -> None:
    action_path = Path(__file__).resolve().parents[3] / ".github/actions/upload-readiness-shards/action.yml"
    steps = yaml.safe_load(action_path.read_bytes())["runs"]["steps"]
    plan, primary = steps[:2]
    assert plan["id"] == "plan"
    upload_action = primary["uses"]
    assert re.fullmatch(r"actions/upload-artifact@[0-9a-f]{40}", upload_action)
    assert type(primary["with"]["compression-level"]) is int
    assert primary == {
        "name": "Upload exact primary index",
        "uses": upload_action,
        "with": {
            "name": "${{ steps.plan.outputs.primary_name }}",
            "path": "${{ inputs.directory }}/index/${{ steps.plan.outputs.index_filename }}",
            "if-no-files-found": "error",
            "retention-days": "${{ inputs.retention-days }}",
            "compression-level": 0,
        },
    }
    assert len(steps[2:]) == MAX_SHARDS
    for index, step in enumerate(steps[2:]):
        ordinal = f"{index:04d}"
        assert type(step["with"]["compression-level"]) is int
        assert step == {
            "name": f"Upload exact bounded shard {ordinal}",
            "if": f"fromJSON(steps.plan.outputs.shard_count) > {index}",
            "uses": upload_action,
            "with": {
                "name": "${{ steps.plan.outputs.shard_prefix }}" + ordinal,
                "path": (
                    "${{ inputs.directory }}/shard-"
                    + ordinal
                    + "/${{ steps.plan.outputs.member_prefix }}-shard-"
                    + ordinal
                    + ".zip"
                ),
                "if-no-files-found": "error",
                "retention-days": "${{ inputs.retention-days }}",
                "compression-level": 0,
            },
        }

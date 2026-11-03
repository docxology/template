"""Naming contract for the bounded native/candidate transport artifacts."""

from __future__ import annotations

import pytest

from infrastructure.reporting.native_hosted_transport_archive import INDEX_ARTIFACT, SHARD_PREFIX
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
def test_transport_cell_is_refused_outside_the_native_transport(kind: str) -> None:
    with pytest.raises(ValueError, match="only to the native transport"):
        transport_artifact_names(kind, "template_code_project")


@pytest.mark.parametrize("cell", ["template_not_declared", "templates/template_code_project"])
def test_transport_cell_must_be_one_bare_declared_public_exemplar(cell: str) -> None:
    with pytest.raises(ValueError, match="one declared public exemplar"):
        transport_artifact_names("native", cell)

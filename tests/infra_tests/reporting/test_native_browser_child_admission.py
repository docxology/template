"""Retained browser role DATA cannot construct genuine current/original custody."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_format_current_pandoc import current_pandoc_reader
from infrastructure.reporting.native_print_child_custody import (
    BasicBrowserControlReaderOperation,
    SemanticBrowserControlReaderOperation,
)
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@pytest.mark.parametrize("role", [BasicBrowserControlReaderOperation, SemanticBrowserControlReaderOperation])
def test_retained_role_fields_cannot_mint_actual_original_child_source(tmp_path: Path, role: type) -> None:
    source_data = {"schema_version": role.schema, "run_id": "0" * 32, "scope": "templates/template_code_project"}
    with pytest.raises(ValueError, match="genuine unwrapped enclosing Source"):
        role(
            source_data,
            SnapshotReader(tmp_path),
            [],
            scope="templates/template_code_project",
            run_id="0" * 32,
            deadline=time.monotonic() + 10,
        )
    assert not (tmp_path / "output").exists()


def test_fresh_parser_refuses_missing_source_before_owned_leaf_creation(tmp_path: Path) -> None:
    with pytest.raises(ProjectionSourceUnsupported, match="externally admitted source"):
        with current_pandoc_reader(
            tmp_path, SnapshotReader(tmp_path), env={}, deadline=time.monotonic() + 10, purpose="source-not-admitted"
        ):
            pytest.fail("missing genuine Source admitted a current parser")
    assert not (tmp_path / "output").exists()

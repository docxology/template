"""Tests for infrastructure.orchestration.link_sync helpers."""

from __future__ import annotations

import io
from pathlib import Path

from infrastructure.core.sidecar_linking import LinkSyncResult
from infrastructure.orchestration.link_sync import (
    print_link_sync_result,
    print_link_sync_results,
    registered_link_sync_hooks,
)


def test_print_link_sync_result_writes_summary_and_deltas() -> None:
    result = LinkSyncResult(
        created=["working/demo"],
        updated=["archive/old"],
        removed=["working/retired"],
        skipped=["working/unchanged"],
        private_root=Path("/tmp/private"),
    )
    buf = io.StringIO()
    print_link_sync_result(result, stream=buf)
    text = buf.getvalue()
    assert "link-sync @ /tmp/private" in text
    assert "+ working/demo" in text


def test_print_link_sync_results_only_reports_changed_domains() -> None:
    changed = LinkSyncResult(created=["a"], private_root=Path("/tmp/private"))
    unchanged = LinkSyncResult(skipped=["b"], private_root=Path("/tmp/private"))
    buf = io.StringIO()
    print_link_sync_results([changed, unchanged], stream=buf)
    assert buf.getvalue().count("[link-sync]") == 1


def test_registered_link_sync_hooks_cover_all_resource_trees() -> None:
    assert len(registered_link_sync_hooks()) == 4

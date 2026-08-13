"""Reachability invariants for the docs/maintenance hub.

The maintenance hub (docs/maintenance/README.md) is the folder index for
long-horizon viability guides. Every substantive guide in the folder must be
reachable from that hub so it cannot silently orphan. This test guards the
doc-reachability fix for docs/maintenance/exemplar-backlog-history.md.
"""

from __future__ import annotations

from pathlib import Path


def test_maintenance_hub_links_archived_exemplar_backlog_history() -> None:
    repo = Path(__file__).resolve().parents[3]
    hub = (repo / "docs" / "maintenance" / "README.md").read_text(encoding="utf-8")
    assert "exemplar-backlog-history.md" in hub, (
        "docs/maintenance/README.md must link docs/maintenance/exemplar-backlog-history.md "
        "so the archived completed-work evidence remains reachable."
    )


def test_maintenance_hub_links_every_markdown_guide_in_folder() -> None:
    """Every tracked .md guide in docs/maintenance/ must be linked from its hub."""
    repo = Path(__file__).resolve().parents[3]
    maint_dir = repo / "docs" / "maintenance"
    hub = (maint_dir / "README.md").read_text(encoding="utf-8")
    missing = []
    for md in sorted(maint_dir.glob("*.md")):
        if md.name in {"README.md", "AGENTS.md"}:
            continue
        if md.name not in hub:
            missing.append(md.name)
    assert missing == [], (
        "Maintenance guides not linked from docs/maintenance/README.md:\n"
        + "\n".join(missing)
    )

"""Method inventory contract for source and script documentation."""

from __future__ import annotations

from pathlib import Path

from gates.method_inventory import (
    collect_method_entries,
    render_method_inventory_markdown,
    write_method_inventory,
)


def test_method_inventory_covers_source_and_scripts(project_root: Path, tmp_path: Path) -> None:
    entries = collect_method_entries(project_root)
    entry_keys = {(entry.path, entry.qualname, entry.kind) for entry in entries}

    assert ("src/analytical/bernoulli_toy.py", "ising_mutual_information", "function") in entry_keys
    assert ("src/manuscript/sheaf/models.py", "TrackRegistry", "class") in entry_keys
    assert ("scripts/z_generate_manuscript_variables.py", "main", "function") in entry_keys
    assert len(entries) >= 500

    report_path = write_method_inventory(project_root, output_path=tmp_path / "method-inventory.md")
    report = report_path.read_text(encoding="utf-8")

    assert "Total documented definitions:" in report
    assert "src/analytical/bernoulli_toy.py" in report
    assert "scripts/z_generate_manuscript_variables.py" in report
    assert "ising_mutual_information" in report
    assert "TrackRegistry" in report


def test_method_inventory_render_groups_by_module(project_root: Path) -> None:
    report = render_method_inventory_markdown(collect_method_entries(project_root))

    analytical = report.index("## `src/analytical/bernoulli_toy.py`")
    scripts = report.index("## `scripts/z_generate_manuscript_variables.py`")

    assert analytical < scripts
    assert "| line | kind | name | documentation source | summary |" in report
    assert "`function`" in report
    assert "`class`" in report


def test_docs_signpost_method_inventory(project_root: Path) -> None:
    docs_readme = (project_root / "docs" / "README.md").read_text(encoding="utf-8")
    project_readme = (project_root / "README.md").read_text(encoding="utf-8")

    assert "method-inventory.md" in docs_readme
    assert "generate_method_inventory.py" in project_readme

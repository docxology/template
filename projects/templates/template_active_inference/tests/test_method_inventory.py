"""Method inventory contract for source and script documentation."""

from __future__ import annotations

import subprocess
import sys
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


def test_method_inventory_check_command(project_root: Path) -> None:
    # Check the committed Source before the verifier's producer can repair it.
    destination = project_root / "docs/reference/method-inventory.md"
    before = destination.read_bytes()
    result = subprocess.run(
        [sys.executable, "scripts/generate_method_inventory.py", "--check"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "method_inventory: current" in result.stdout
    write_method_inventory(project_root)
    assert destination.read_bytes() == before


def test_method_inventory_check_refuses_stale_source(tmp_path: Path, project_root: Path) -> None:
    import shutil

    for relative in ("src/gates/method_inventory.py", "scripts/generate_method_inventory.py"):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project_root / relative, destination)
    (tmp_path / "src/gates/__init__.py").write_text("")
    destination = tmp_path / "docs/reference/method-inventory.md"
    destination.parent.mkdir(parents=True)
    destination.write_text("stale authored inventory\n")
    result = subprocess.run(
        [sys.executable, "scripts/generate_method_inventory.py", "--check"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 1
    assert "method_inventory: stale" in result.stderr
    assert destination.read_text() == "stale authored inventory\n"

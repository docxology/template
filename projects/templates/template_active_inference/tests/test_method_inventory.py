"""Method inventory contract for source and script documentation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from gates.method_inventory import (
    collect_method_entries,
    write_method_inventory,
)


def test_method_inventory_covers_source_and_scripts(project_root: Path) -> None:
    entries = collect_method_entries(project_root)
    entry_keys = {(entry.path, entry.qualname, entry.kind) for entry in entries}

    assert ("src/analytical/bernoulli_toy.py", "ising_mutual_information", "function") in entry_keys
    assert ("src/manuscript/sheaf/models.py", "TrackRegistry", "class") in entry_keys
    assert ("scripts/z_generate_manuscript_variables.py", "main", "function") in entry_keys


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
    assert destination.read_bytes() == before
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
    assert destination.read_text() == "stale authored inventory\n"

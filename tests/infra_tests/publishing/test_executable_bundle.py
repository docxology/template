#!/usr/bin/env python3
"""Tests for infrastructure.publishing.executable_bundle."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.publishing.executable_bundle import bundle_project
from tests._support.projects import make_project, write_doc


def _scaffold_bundle_project(root: Path, name: str) -> None:
    project = make_project(root, name, with_manuscript=True, with_scripts=True)
    (project / "src" / "demo.py").write_text("def run() -> int:\n    return 0\n")
    (project / "manuscript" / "config.yaml").write_text(
        "publication:\n  doi: '10.5281/zenodo.12345678'\n",
        encoding="utf-8",
    )
    write_doc(root / "pyproject.toml", "[project]\nname = 'demo'\n")
    write_doc(root / "uv.lock", "# lock\n")
    pinned = root / "tests" / "regression" / "pinned_values"
    pinned.mkdir(parents=True)
    (pinned / f"{name}.json").write_text(json.dumps({"claims": []}))


def test_bundle_project_writes_manifest_and_dockerfile(tmp_path: Path) -> None:
    name = "bundle_demo"
    _scaffold_bundle_project(tmp_path, name)

    out_dir = bundle_project(tmp_path, name)

    assert out_dir == tmp_path / "output" / name / "executable_bundle"
    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "Dockerfile").is_file()
    assert (out_dir / "docker-compose.yml").is_file()
    assert (out_dir / "source" / "src" / "demo.py").is_file()
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["archival_receipts"]["zenodo_doi"] == "10.5281/zenodo.12345678"
    readme = (out_dir / "README.md").read_text(encoding="utf-8")
    assert "template repository root" in readme
    assert "No combined PDF was bundled" in readme


def test_bundle_project_copies_combined_pdf_when_present(tmp_path: Path) -> None:
    name = "bundle_pdf"
    _scaffold_bundle_project(tmp_path, name)
    pdf_dir = tmp_path / "output" / name / "pdf"
    pdf_dir.mkdir(parents=True)
    pdf_name = f"{name}_combined.pdf"
    pdf_dir.joinpath(pdf_name).write_bytes(b"%PDF-1.4 demo")

    out_dir = bundle_project(tmp_path, name)

    copied = out_dir / "artifacts" / "pdf" / pdf_name
    assert copied.is_file()
    assert copied.read_bytes() == b"%PDF-1.4 demo"
    readme = (out_dir / "README.md").read_text(encoding="utf-8")
    assert f"artifacts/pdf/{pdf_name}" in readme

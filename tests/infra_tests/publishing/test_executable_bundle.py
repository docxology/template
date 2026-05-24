#!/usr/bin/env python3
"""Tests for infrastructure.publishing.executable_bundle."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.publishing.executable_bundle import bundle_project


def _scaffold_bundle_project(root: Path, name: str) -> None:
    project = root / "projects" / name
    for sub in ("src", "scripts", "manuscript", "tests"):
        (project / sub).mkdir(parents=True)
    (project / "src" / "demo.py").write_text("def run() -> int:\n    return 0\n")
    (root / "pyproject.toml").write_text("[project]\nname = 'demo'\n")
    (root / "uv.lock").write_text("# lock\n")
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

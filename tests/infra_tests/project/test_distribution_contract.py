"""Distribution contract for the reusable Layer-1 Python package."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_root_declares_buildable_layer_one_distribution() -> None:
    payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert payload["build-system"]["build-backend"] == "hatchling.build"
    assert payload["tool"]["uv"]["package"] is True
    assert payload["project"]["scripts"]["research-template"] == "infrastructure.orchestration.cli:main"
    assert payload["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["infrastructure"]
    for extra in ("rendering", "publishing", "scientific", "steganography"):
        assert payload["project"]["optional-dependencies"][extra]


def test_default_pipeline_is_a_packaged_resource() -> None:
    pipeline = REPO_ROOT / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    assert pipeline.is_file()
    assert "stages:" in pipeline.read_text(encoding="utf-8")

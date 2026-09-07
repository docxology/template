"""Tests for infrastructure.rendering.pipeline config loading helpers.

Covers _has_generated_manuscript_ordering and _load_project_config_yaml.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.rendering.pipeline import (
    _has_generated_manuscript_ordering,
    _load_project_config_yaml,
)


# ---------------------------------------------------------------------------
# _has_generated_manuscript_ordering / _load_project_config_yaml
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("config_text", "expected"),
    [
        ("# Generated manuscript ordering\nbook:\n  title: X\n", True),
        ("book:\n  title: Plain\n", False),
    ],
)
def test_has_generated_manuscript_ordering(tmp_path: Path, config_text: str, expected: bool) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(config_text, encoding="utf-8")

    assert _has_generated_manuscript_ordering(cfg) is expected


def test_has_generated_manuscript_ordering_missing_file(tmp_path: Path) -> None:
    assert _has_generated_manuscript_ordering(tmp_path / "missing.yaml") is False


def test_load_project_config_yaml_missing_file(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    assert _load_project_config_yaml(manuscript_dir) is None


def test_load_project_config_yaml_valid_dict(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n",
        encoding="utf-8",
    )

    loaded = _load_project_config_yaml(manuscript_dir)

    assert loaded is not None
    assert loaded["render"]["formats"]["pdf"] is True


def test_load_project_config_yaml_invalid_yaml(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text("paper:\n  title: [\n  broken\n", encoding="utf-8")

    assert _load_project_config_yaml(manuscript_dir) is None


def test_load_project_config_yaml_non_mapping_root(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text("- just\n- a list\n", encoding="utf-8")

    assert _load_project_config_yaml(manuscript_dir) is None

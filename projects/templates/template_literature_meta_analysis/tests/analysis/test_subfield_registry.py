"""Tests for analysis.subfield_registry."""

from __future__ import annotations

from pathlib import Path

import analysis.subfield_registry as registry
from analysis.subfield_defaults import DEFAULT_SUBFIELDS
from analysis.subfield_registry import (
    configure_subfields,
    get_pattern_cache,
    load_subfields_from_config,
)


def test_load_subfields_from_config_uses_defaults_when_missing(tmp_path: Path) -> None:
    loaded = load_subfields_from_config(tmp_path / "missing.yaml")
    assert loaded.keys() == DEFAULT_SUBFIELDS.keys()


def test_load_subfields_from_config_reads_project_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
project_config:
  subfield_keywords:
    C1_neuroscience:
      - "neural active inference"
    B_tools:
      - "pymdp"
""".strip(),
        encoding="utf-8",
    )
    loaded = load_subfields_from_config(config_path)
    assert set(loaded) == {"C1_neuroscience", "B_tools"}
    assert loaded["C1_neuroscience"]["priority"] == 1
    assert loaded["B_tools"]["priority"] == 2


def test_load_subfields_from_config_skips_non_list_entries(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
subfield_keywords:
  A1_formal:
    keywords: ["variational"]
  bad_entry: "not-a-list"
""".strip(),
        encoding="utf-8",
    )
    loaded = load_subfields_from_config(config_path)
    assert loaded.keys() == DEFAULT_SUBFIELDS.keys()


def test_configure_subfields_rebuilds_pattern_cache(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
subfield_keywords:
  C2_robotics:
    - "robotics active inference"
""".strip(),
        encoding="utf-8",
    )
    before = len(get_pattern_cache())
    fields = configure_subfields(config_path)
    after = get_pattern_cache()
    assert len(fields) == 1
    assert "C2_robotics" in after
    assert len(after) == 1 or len(after) != before
    configure_subfields(None)
    assert len(registry.SUBFIELDS) == len(DEFAULT_SUBFIELDS)

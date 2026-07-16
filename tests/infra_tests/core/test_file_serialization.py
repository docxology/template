"""Real-I/O tests for shared JSON/YAML filesystem serialization helpers."""

from pathlib import Path

import pytest

from infrastructure.core.files.serialization import load_yaml_mapping


def test_load_yaml_mapping_accepts_mapping(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("project:\n  enabled: true\n", encoding="utf-8")

    assert load_yaml_mapping(path) == {"project": {"enabled": True}}


def test_load_yaml_mapping_normalizes_invalid_or_nonmapping_input(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.yaml"
    malformed.write_text("project: [\n", encoding="utf-8")
    sequence = tmp_path / "sequence.yaml"
    sequence.write_text("- one\n- two\n", encoding="utf-8")

    assert load_yaml_mapping(malformed) == {}
    assert load_yaml_mapping(sequence) == {}
    assert load_yaml_mapping(tmp_path / "missing.yaml") == {}


def test_load_yaml_mapping_strict_surfaces_malformed_yaml(tmp_path: Path) -> None:
    """Validation boundaries can distinguish corruption from an empty mapping."""
    import yaml

    path = tmp_path / "broken.yaml"
    path.write_text("paper: {title: 'unterminated\n", encoding="utf-8")

    with pytest.raises(yaml.YAMLError):
        load_yaml_mapping(path, strict=True)

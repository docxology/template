"""Tests for shared parsing helpers."""

from __future__ import annotations
from pathlib import Path
import pytest
from template_gold_refinement.parsing import build_timestamp, load_json_object, load_yaml_dict


def test_load_yaml_dict_reads_mapping(tmp_path: Path) -> None:
    path = tmp_path / "sample.yaml"
    path.write_text("key: value\n", encoding="utf-8")
    assert load_yaml_dict(path) == {"key": "value"}


def test_build_timestamp_honours_source_date_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    assert build_timestamp() == "1970-01-01T00:00:00Z"


def test_load_json_object_missing_returns_empty(tmp_path):
    assert load_json_object(tmp_path / "absent.json") == {}


def test_load_json_object_non_dict_returns_empty(tmp_path):
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert load_json_object(path) == {}


def test_load_json_object_reads_dict(tmp_path):
    path = tmp_path / "obj.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    assert load_json_object(path) == {"a": 1}

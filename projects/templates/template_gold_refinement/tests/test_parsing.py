"""Tests for shared parsing helpers."""

from __future__ import annotations
from pathlib import Path
import pytest
from parsing import build_timestamp, load_yaml_dict


def test_load_yaml_dict_reads_mapping(tmp_path: Path) -> None:
    path = tmp_path / "sample.yaml"
    path.write_text("key: value\n", encoding="utf-8")
    assert load_yaml_dict(path) == {"key": "value"}


def test_build_timestamp_honours_source_date_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    assert build_timestamp() == "1970-01-01T00:00:00Z"

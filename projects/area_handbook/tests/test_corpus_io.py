"""Tests for corpus loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.corpus_io import CorpusValidationError, load_corpus, load_corpus_from_dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = PROJECT_ROOT / "data" / "fixtures" / "riverbend_area.yaml"


class TestLoadFixture:
    def test_load_riverbend_yaml(self) -> None:
        c = load_corpus(FIXTURE)
        assert c.area_id == "riverbend_metro"
        assert len(c.themes) == 8
        assert len(c.evidence) >= 10

    def test_round_trip_dict(self) -> None:
        c = load_corpus(FIXTURE)
        raw = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
        c2 = load_corpus_from_dict(raw)
        assert c == c2


class TestValidationErrors:
    def test_missing_key(self) -> None:
        with pytest.raises(CorpusValidationError, match="missing keys"):
            load_corpus_from_dict({"area_id": "x", "area_label": "y"})

    def test_empty_area_id(self) -> None:
        with pytest.raises(CorpusValidationError, match="non-empty"):
            load_corpus_from_dict(
                {
                    "area_id": "  ",
                    "area_label": "L",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": [],
                }
            )

    def test_unknown_theme(self) -> None:
        with pytest.raises(CorpusValidationError, match="unknown theme"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "only", "label": "O", "description": "x"}],
                    "evidence": [
                        {
                            "id": "e1",
                            "statement": "s",
                            "theme": "missing",
                            "weight": 0.5,
                            "source_label": "src",
                            "reviewed_at": "2025-01-01",
                        }
                    ],
                }
            )

    def test_empty_theme_id(self) -> None:
        with pytest.raises(CorpusValidationError, match="empty id"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "  ", "label": "T", "description": "d"}],
                    "evidence": [],
                }
            )

    def test_empty_evidence_id(self) -> None:
        with pytest.raises(CorpusValidationError, match="empty id"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": [
                        {
                            "id": "  ",
                            "statement": "s",
                            "theme": "t",
                            "weight": 0.5,
                            "source_label": "src",
                            "reviewed_at": "2025-01-01",
                        }
                    ],
                }
            )

    def test_weight_out_of_range(self) -> None:
        with pytest.raises(CorpusValidationError, match="weight"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": [
                        {
                            "id": "e1",
                            "statement": "s",
                            "theme": "t",
                            "weight": 1.5,
                            "source_label": "src",
                            "reviewed_at": "2025-01-01",
                        }
                    ],
                }
            )

    def test_empty_themes_list(self) -> None:
        with pytest.raises(CorpusValidationError, match="non-empty list"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [],
                    "evidence": [],
                }
            )

    def test_evidence_not_list(self) -> None:
        with pytest.raises(CorpusValidationError, match="evidence must be a list"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": {},
                }
            )

    def test_root_not_mapping_yaml(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yaml"
        p.write_text("- not a dict\n", encoding="utf-8")
        with pytest.raises(CorpusValidationError, match="mapping"):
            load_corpus(p)

    def test_unsupported_suffix(self, tmp_path: Path) -> None:
        p = tmp_path / "x.txt"
        p.write_text("{}", encoding="utf-8")
        with pytest.raises(CorpusValidationError, match="unsupported"):
            load_corpus(p)

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_corpus(tmp_path / "nope.yaml")

    def test_load_json(self, tmp_path: Path) -> None:
        data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
        p = tmp_path / "c.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        c = load_corpus(p)
        assert c.area_id == "riverbend_metro"


class TestJsonCorpusRoot:
    def test_json_root_not_dict(self, tmp_path: Path) -> None:
        p = tmp_path / "x.json"
        p.write_text("[1,2,3]", encoding="utf-8")
        with pytest.raises(CorpusValidationError, match="mapping"):
            load_corpus(p)


class TestCorpusIntegrityRules:
    def test_duplicate_theme_id(self) -> None:
        with pytest.raises(CorpusValidationError, match="duplicate id"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [
                        {"id": "x", "label": "L1", "description": "d"},
                        {"id": "x", "label": "L2", "description": "d"},
                    ],
                    "evidence": [],
                }
            )

    def test_duplicate_evidence_id(self) -> None:
        with pytest.raises(CorpusValidationError, match="duplicate id"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": [
                        {
                            "id": "e1",
                            "statement": "a",
                            "theme": "t",
                            "weight": 0.1,
                            "source_label": "s",
                            "reviewed_at": "2025-01-01",
                        },
                        {
                            "id": "e1",
                            "statement": "b",
                            "theme": "t",
                            "weight": 0.2,
                            "source_label": "s",
                            "reviewed_at": "2025-01-02",
                        },
                    ],
                }
            )

    def test_empty_theme_description(self) -> None:
        with pytest.raises(CorpusValidationError, match="empty description"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "L", "description": "  "}],
                    "evidence": [],
                }
            )

    def test_empty_theme_label(self) -> None:
        with pytest.raises(CorpusValidationError, match="empty label"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "  ", "description": "d"}],
                    "evidence": [],
                }
            )

    def test_empty_evidence_statement(self) -> None:
        with pytest.raises(CorpusValidationError, match="empty statement"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": [
                        {
                            "id": "e1",
                            "statement": " ",
                            "theme": "t",
                            "weight": 0.5,
                            "source_label": "s",
                            "reviewed_at": "2025-01-01",
                        }
                    ],
                }
            )

    def test_nan_weight(self) -> None:
        with pytest.raises(CorpusValidationError, match="finite"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": [
                        {
                            "id": "e1",
                            "statement": "s",
                            "theme": "t",
                            "weight": float("nan"),
                            "source_label": "src",
                            "reviewed_at": "2025-01-01",
                        }
                    ],
                }
            )

    def test_invalid_weight_type(self) -> None:
        with pytest.raises(CorpusValidationError, match="invalid weight"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": [
                        {
                            "id": "e1",
                            "statement": "s",
                            "theme": "t",
                            "weight": "heavy",
                            "source_label": "src",
                            "reviewed_at": "2025-01-01",
                        }
                    ],
                }
            )

    def test_empty_source_label(self) -> None:
        with pytest.raises(CorpusValidationError, match="empty source_label"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": [
                        {
                            "id": "e1",
                            "statement": "s",
                            "theme": "t",
                            "weight": 0.5,
                            "source_label": " ",
                            "reviewed_at": "2025-01-01",
                        }
                    ],
                }
            )

    def test_empty_reviewed_at(self) -> None:
        with pytest.raises(CorpusValidationError, match="empty reviewed_at"):
            load_corpus_from_dict(
                {
                    "area_id": "a",
                    "area_label": "A",
                    "version": "1",
                    "themes": [{"id": "t", "label": "T", "description": "d"}],
                    "evidence": [
                        {
                            "id": "e1",
                            "statement": "s",
                            "theme": "t",
                            "weight": 0.5,
                            "source_label": "src",
                            "reviewed_at": " ",
                        }
                    ],
                }
            )

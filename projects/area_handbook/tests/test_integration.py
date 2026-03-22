"""End-to-end integration over fixture corpus."""

from __future__ import annotations

import json
from pathlib import Path

from src.corpus_io import load_corpus
from src.handbook_md import build_full_handbook_body
from src.metrics import build_metrics_report
from src.synthesis import synthesize

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = PROJECT_ROOT / "data" / "fixtures" / "riverbend_area.yaml"


def test_json_roundtrip_metrics() -> None:
    c = load_corpus(FIXTURE)
    s = synthesize(c)
    m = build_metrics_report(s)
    raw = json.dumps(m)
    back = json.loads(raw)
    assert back["corpus_version"] == c.version
    assert back["evidence_count"] == len(c.evidence)
    assert "gap_threshold" in back
    assert "evidence_count_by_theme" in back


def test_handbook_body_covers_all_sections() -> None:
    c = load_corpus(FIXTURE)
    s = synthesize(c)
    body = build_full_handbook_body(s)
    for sec in s.sections:
        assert sec.title in body or sec.section_id in body

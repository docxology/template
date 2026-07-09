"""No-mocks tests for src/diligence_audit.py."""

from __future__ import annotations

from diligence_audit import diligence_rows, slide_cites_a_fact, slide_text_blob, uncited_fact_slides


def test_slide_text_blob_concatenates_prose_fields():
    slide = {
        "title": "T",
        "bullets": ["a", "b"],
        "stat_value": "42",
        "stat_label": "label",
        "quote_text": "quote",
        "quote_attribution": "attr",
    }
    blob = slide_text_blob(slide)
    for piece in ("T", "a", "b", "42", "label", "quote", "attr"):
        assert piece in blob


def test_slide_cites_a_fact_true_when_pitch_subject_token_present():
    slide = {"title": "X", "bullets": ["{{PITCH_SUBJECT_TEST_COUNT}} tests"]}
    assert slide_cites_a_fact(slide) is True


def test_slide_cites_a_fact_true_when_exemplar_token_present():
    slide = {"title": "X", "bullets": ["one of {{EXEMPLAR_COUNT}} exemplars"]}
    assert slide_cites_a_fact(slide) is True


def test_slide_cites_a_fact_false_for_plain_prose():
    slide = {"title": "X", "bullets": ["No live-sourced numbers here."]}
    assert slide_cites_a_fact(slide) is False


def test_diligence_rows_reports_needs_and_has_citation():
    raw = {
        "slides": [
            {"title": "Fact, cited", "bullets": ["{{EXEMPLAR_COUNT}} exemplars"], "source": "some/file.py"},
            {"title": "Fact, uncited", "bullets": ["{{EXEMPLAR_COUNT}} exemplars"]},
            {"title": "No fact", "bullets": ["Just prose."]},
        ]
    }
    rows = diligence_rows(raw)
    assert rows[0] == {"index": 1, "title": "Fact, cited", "needs_citation": True, "has_citation": True}
    assert rows[1] == {"index": 2, "title": "Fact, uncited", "needs_citation": True, "has_citation": False}
    assert rows[2] == {"index": 3, "title": "No fact", "needs_citation": False, "has_citation": False}


def test_uncited_fact_slides_returns_only_the_gap():
    raw = {
        "slides": [
            {"title": "Cited", "bullets": ["{{EXEMPLAR_COUNT}}"], "source": "x.py"},
            {"title": "Uncited", "bullets": ["{{EXEMPLAR_COUNT}}"]},
        ]
    }
    gaps = uncited_fact_slides(raw)
    assert len(gaps) == 1
    assert gaps[0]["title"] == "Uncited"


def test_uncited_fact_slides_empty_when_all_covered():
    raw = {"slides": [{"title": "Cited", "bullets": ["{{EXEMPLAR_COUNT}}"], "source": "x.py"}]}
    assert uncited_fact_slides(raw) == []


def test_citation_to_nonexistent_file_is_flagged_as_uncited_when_repo_root_given(tmp_path):
    """Proof-of-detection: a citation that LOOKS present (`source` is non-empty)
    but points at a file that doesn't exist must still fail the gate — this is
    the exact "looks verified but isn't" failure mode a bare `bool(source)`
    check can't catch."""
    raw = {
        "slides": [
            {"title": "Broken citation", "bullets": ["{{EXEMPLAR_COUNT}}"], "source": "does/not/exist.py"},
        ]
    }
    gaps = uncited_fact_slides(raw, tmp_path)
    assert len(gaps) == 1
    assert gaps[0]["title"] == "Broken citation"


def test_citation_to_real_file_passes_when_repo_root_given(tmp_path):
    (tmp_path / "real.py").write_text("# real file\n", encoding="utf-8")
    raw = {"slides": [{"title": "Real citation", "bullets": ["{{EXEMPLAR_COUNT}}"], "source": "real.py"}]}
    assert uncited_fact_slides(raw, tmp_path) == []


def test_citation_existence_not_checked_when_repo_root_omitted():
    """Backward-compat: without repo_root, only non-emptiness is checked (a
    caller auditing raw content with no repo context to check against)."""
    raw = {"slides": [{"title": "X", "bullets": ["{{EXEMPLAR_COUNT}}"], "source": "does/not/exist.py"}]}
    assert uncited_fact_slides(raw) == []


def test_absolute_url_citation_always_passes_existence_check(tmp_path):
    raw = {
        "slides": [
            {"title": "Y", "bullets": ["{{EXEMPLAR_COUNT}}"], "source": "https://example.org/evidence"},
        ]
    }
    assert uncited_fact_slides(raw, tmp_path) == []

"""Tests for infrastructure.prose.analysis.quality."""

from __future__ import annotations

from infrastructure.prose.analysis.quality import (
    QualityReport,
    analyze_quality,
    detect_hedge_words,
    detect_long_sentences,
    detect_passive_sentences,
    extract_citation_keys,
)


class TestPassiveDetection:
    def test_basic_passive(self):
        sentences = detect_passive_sentences("The book was written by the author.")
        assert len(sentences) == 1

    def test_active_voice_not_flagged(self):
        sentences = detect_passive_sentences("The author writes books.")
        assert sentences == []

    def test_multiple_sentences(self):
        # Use an "-ed" past participle so the heuristic regex picks it up;
        # "caught" is irregular and the simple regex skips it (documented).
        text = "The cat ran. The mouse was captured. We escaped."
        sentences = detect_passive_sentences(text)
        # Only the middle sentence is passive.
        assert len(sentences) == 1
        assert "mouse" in sentences[0]


class TestHedgeWords:
    def test_finds_hedges(self):
        text = "We may suggest this is probably useful."
        hedges = detect_hedge_words(text)
        assert "may" in hedges
        assert "probably" in hedges

    def test_no_hedges(self):
        assert detect_hedge_words("The data show this clearly.") == []

    def test_case_insensitive(self):
        assert "may" in detect_hedge_words("May I suggest something?")


class TestCitationExtraction:
    def test_bracketed(self):
        text = "Reproducibility matters [@peng2011reproducible]."
        assert extract_citation_keys(text) == ["peng2011reproducible"]

    def test_multi_keys(self):
        text = "See [@a2020; @b2021]."
        keys = extract_citation_keys(text)
        assert "a2020" in keys
        assert "b2021" in keys

    def test_bare_at_keys(self):
        text = "As @smith2024 notes..."
        keys = extract_citation_keys(text)
        assert "smith2024" in keys

    def test_no_duplicates(self):
        text = "[@k1] and again [@k1]."
        assert extract_citation_keys(text) == ["k1"]

    def test_no_citations(self):
        assert extract_citation_keys("Just plain text.") == []

    def test_crossref_excluded_from_citations(self):
        """pandoc-crossref refs (`fig:`, `tbl:`, `eq:`, `sec:`, `lst:`) must
        not be reported as citation keys — they resolve via the crossref
        filter, not the bibliography."""
        text = (
            "See [@sec:methodology] and [@fig:convergence]; "
            "results are in [@tbl:opt_results] and [@eq:gradient]. "
            "But [@peng2011reproducible] is a real citation."
        )
        keys = extract_citation_keys(text)
        assert keys == ["peng2011reproducible"]

    def test_crossref_mixed_with_citations_in_brackets(self):
        text = "See [@sec:methodology; @peng2011reproducible]."
        keys = extract_citation_keys(text)
        assert keys == ["peng2011reproducible"]

    def test_bare_crossref_excluded(self):
        text = "As @sec:methodology shows, @peng2011 is the basis."
        keys = extract_citation_keys(text)
        assert "sec:methodology" not in keys
        assert "peng2011" in keys


class TestLongSentences:
    def test_long_sentence_flagged(self):
        words = " ".join(["word"] * 40)
        sentences = detect_long_sentences(words + ".", threshold=35)
        assert len(sentences) == 1

    def test_short_sentence_not_flagged(self):
        assert detect_long_sentences("Short sentence.") == []

    def test_threshold_respected(self):
        words = " ".join(["word"] * 20)
        text = words + "."
        assert detect_long_sentences(text, threshold=10) == [text]
        assert detect_long_sentences(text, threshold=30) == []


class TestAnalyzeQualityAggregate:
    def test_combined(self):
        text = (
            "We may argue that the result was obtained by careful analysis. "
            "Reproducibility is important [@peng2011reproducible]. "
            "The convex optimization problem can be transformed into a dual "
            "form which provides additional insights into the underlying "
            "structure of the feasible region and allows for efficient "
            "computation of optimality certificates."
        )
        # Lower threshold so the 35-word sentence is flagged.
        q = analyze_quality(text, long_sentence_threshold=20)
        assert isinstance(q, QualityReport)
        assert q.passive_count >= 1
        assert q.hedge_count >= 1
        assert q.citation_count == 1
        assert q.long_sentence_count >= 1
        assert q.citation_density_per_1000 > 0

    def test_empty(self):
        q = analyze_quality("")
        assert q.word_count == 0
        assert q.citation_density_per_1000 == 0.0

    def test_to_dict_serializable(self):
        import json
        q = analyze_quality("A simple sentence.")
        json.dumps(q.to_dict())  # must not raise

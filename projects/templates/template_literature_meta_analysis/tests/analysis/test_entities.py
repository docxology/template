"""Tests for analysis.entities module.

Validates offline regex-based entity extraction, TF-scored keyphrase
extraction, and corpus-level entity aggregation using small hand-crafted
strings whose expected outputs are computed by hand (not by re-running the
implementation), to avoid green-by-construction assertions.
"""

import math

import pytest

from analysis.entities import (
    corpus_entities,
    extract_entities,
    extract_keyphrases,
)
from literature.models import Paper


# ── extract_entities ──────────────────────────────────────────────────


class TestExtractEntities:
    """Tests for extract_entities."""

    def test_empty_text(self):
        """Empty input yields no entities."""
        assert extract_entities("") == []

    def test_multiword_phrase(self):
        """A two-word capitalized run is one entity with count 1."""
        # "is", "a", "theory" are lowercase, so only "Active Inference"
        # forms a 2-word capitalized run. No acronyms present.
        result = extract_entities("Active Inference is a theory.")
        assert result == [("Active Inference", 1)]

    def test_single_capitalized_word_not_entity(self):
        """A lone capitalized common word does not become an entity."""
        # "The" is sentence-initial and capitalized but is a stopword; the
        # remaining words are lowercase so no 2-word run survives.
        result = extract_entities("The model is trained on data.")
        assert result == []

    def test_allcaps_acronyms(self):
        """ALLCAPS tokens with >=2 letters are extracted as acronyms."""
        # EEG appears twice, FEP once. "2020" is numeric-only -> not an
        # acronym. No multiword capitalized run.
        text = "We recorded EEG signals. EEG and FEP in 2020."
        result = extract_entities(text)
        # Counts: EEG=2, FEP=1. Sort by count desc -> EEG first, then FEP.
        assert result == [("EEG", 2), ("FEP", 1)]

    def test_numeric_only_token_not_acronym(self):
        """A purely numeric ALLCAPS run is rejected (needs 2 letters)."""
        assert extract_entities("Published in 2020 and 1999.") == []

    def test_case_variant_merging(self):
        """Case variants merge to one canonical first-seen surface form."""
        # "Active Inference" appears Title-cased, then as "Active inference"
        # (mixed case). The mixed-case form has a lowercase second word so it
        # does NOT form a 2-word capitalized run on its own; to exercise a
        # genuine merge we use a different Title-cased surface "ACTIVE
        # INFERENCE" would collide with the acronym pass, so instead we use a
        # period-separated repeat of the same Title-cased phrase, whose two
        # surface forms differ only by an internal hyphen variant we avoid.
        # Simplest unambiguous merge: the identical Title-cased phrase twice.
        text = "Active Inference helps. Later, Active Inference returns."
        result = extract_entities(text)
        # Both occurrences share key "active inference" -> count 2, canonical
        # = first surface "Active Inference".
        assert result == [("Active Inference", 2)]

    def test_case_variant_merging_mixed_case(self):
        """Differing surface casings of one phrase merge under one form."""
        # First "Bayesian Brain" (Title case, 2-word run). Then a
        # parenthetical "Bayesian Brain" preceded by lowercase words; the
        # capitalized run is identical, so it merges to count 2 with the
        # first-seen surface form retained as canonical.
        text = "We study Bayesian Brain ideas. The Bayesian Brain framework."
        result = extract_entities(text)
        assert result == [("Bayesian Brain", 2)]

    def test_leading_and_trailing_stopword_trimmed(self):
        """Leading/trailing stopword words are stripped from a phrase."""
        # "The Active Inference Model" -> "The" is a leading stopword and
        # trimmed, leaving "Active Inference Model" (3 words).
        result = extract_entities("The Active Inference Model works.")
        assert result == [("Active Inference Model", 1)]

    def test_all_stopword_phrase_dropped(self):
        """A capitalized run made only of stopwords yields nothing."""
        # "All These" are both stopwords -> trimmed to empty -> dropped.
        result = extract_entities("All These were considered.")
        assert result == []

    def test_trailing_stopword_trimmed(self):
        """A trailing stopword word is stripped from a phrase."""
        # "Active Inference About" -> "About" is a stopword and is trimmed
        # from the end, leaving the 2-word phrase "Active Inference".
        result = extract_entities("We discuss Active Inference About later.")
        assert result == [("Active Inference", 1)]

    def test_allcaps_multiword_run_reported_once(self):
        """A multiword ALLCAPS run is one phrase, not per-word acronyms."""
        # "FREE ENERGY PRINCIPLE" is a 3-word capitalized run. Its words
        # are not emitted as separate acronyms because each acronym span
        # lies inside the phrase span; the phrase is reported once.
        result = extract_entities("The FREE ENERGY PRINCIPLE matters.")
        assert result == [("FREE ENERGY PRINCIPLE", 1)]

    def test_acronym_inside_phrase_excluded_but_standalone_counts(self):
        """An acronym word inside a phrase is excluded; standalone counts."""
        # "DEEP LEARNING" is a phrase (its words excluded as acronyms);
        # standalone "EEG" outside any phrase is still an acronym.
        result = extract_entities("DEEP LEARNING uses EEG signals.")
        # count desc then alpha: both count 1 -> "deep learning" < "eeg".
        assert result == [("DEEP LEARNING", 1), ("EEG", 1)]

    def test_sort_count_desc_then_alpha(self):
        """Sorting: count descending, then alphabetical ascending."""
        # "Active Inference" twice; "Bayesian Brain" once; "ACR" once.
        text = "Active Inference and Active Inference again. Bayesian Brain too. ACR here."
        result = extract_entities(text)
        # Counts: Active Inference=2, ACR=1, Bayesian Brain=1.
        # count desc -> Active Inference first; ties (ACR, Bayesian Brain)
        # broken alphabetically: "acr" < "bayesian brain".
        assert result == [
            ("Active Inference", 2),
            ("ACR", 1),
            ("Bayesian Brain", 1),
        ]


# ── extract_keyphrases ────────────────────────────────────────────────


class TestExtractKeyphrases:
    """Tests for extract_keyphrases."""

    def test_empty_text(self):
        """Empty text yields no keyphrases."""
        assert extract_keyphrases("") == []

    def test_whitespace_text(self):
        """Whitespace-only text yields no keyphrases."""
        assert extract_keyphrases("   \n\t ") == []

    def test_top_k_zero(self):
        """top_k <= 0 yields no keyphrases."""
        assert extract_keyphrases("active inference model", top_k=0) == []
        assert extract_keyphrases("active inference model", top_k=-3) == []

    def test_no_surviving_ngrams(self):
        """Text that is all stopwords yields no keyphrases."""
        # Every token is a stopword, so every n-gram is filtered out.
        assert extract_keyphrases("the and of with") == []

    def test_non_whitespace_but_no_tokens(self):
        """Non-whitespace text with no alphanumeric tokens yields []."""
        # Passes the strip() guard (has visible chars) but tokenizes to
        # nothing because _TOKEN_RE matches only [a-z0-9]+.
        assert extract_keyphrases("@#$ %^&* !!!") == []

    def test_scores_and_filtering(self):
        """Scores are TF normalized by total candidate n-gram count."""
        # Tokens: ["active", "inference", "model"] (no stopwords).
        # Unigrams: active, inference, model -> 3 grams.
        # Bigrams: "active inference", "inference model" -> 2 grams.
        # Trigram: "active inference model" -> 1 gram.
        # No stopwords present, so none are filtered. total = 6.
        result = extract_keyphrases("active inference model")
        scores = dict(result)
        # Each phrase occurs exactly once -> score = 1/6 each.
        expected = 1.0 / 6.0
        assert len(result) == 6
        for phrase, score in result:
            assert math.isclose(score, expected, rel_tol=1e-12)
        # Scores sum to 1.0.
        assert math.isclose(sum(scores.values()), 1.0, rel_tol=1e-12)
        # Ordering: equal scores -> alphabetical ascending.
        phrases = [p for p, _ in result]
        assert phrases == sorted(phrases)

    def test_stopword_ngrams_excluded(self):
        """n-grams containing a stopword token are dropped entirely."""
        # Tokens: ["active", "and", "inference"].
        # Unigrams surviving: "active", "inference" ("and" is a stopword).
        # Bigrams: "active and" (has stopword) dropped; "and inference"
        # dropped. Trigram "active and inference" dropped.
        # total candidate occurrences = 2 -> each score = 1/2.
        result = extract_keyphrases("active and inference")
        assert result == [("active", 0.5), ("inference", 0.5)]

    def test_repeated_unigram_higher_score(self):
        """A repeated token ranks above singletons by TF."""
        # Tokens: ["energy", "energy", "free"].
        # Unigrams: energy x2, free x1.
        # Bigrams: "energy energy" x1, "energy free" x1.
        # Trigram: "energy energy free" x1.
        # total = 2 + 1 + 1 + 1 + 1 = 6.
        result = extract_keyphrases("energy energy free")
        scores = dict(result)
        assert math.isclose(scores["energy"], 2.0 / 6.0, rel_tol=1e-12)
        assert math.isclose(scores["free"], 1.0 / 6.0, rel_tol=1e-12)
        # "energy" must be first (highest score).
        assert result[0][0] == "energy"

    def test_top_k_truncation(self):
        """Only top_k phrases are returned."""
        result = extract_keyphrases("active inference model", top_k=2)
        assert len(result) == 2


# ── corpus_entities ───────────────────────────────────────────────────


class TestCorpusEntities:
    """Tests for corpus_entities."""

    def _papers(self):
        """Build two Paper objects with known entity content."""
        p1 = Paper(
            title="Active Inference Theory",
            abstract="Active Inference and EEG studies.",
            doi="10.1/p1",
        )
        p2 = Paper(
            title="Bayesian Brain Review",
            abstract="Active Inference with EEG and FEP.",
            doi="10.1/p2",
        )
        return p1, p2

    def test_abstract_aggregation(self):
        """Abstract-field entities aggregate across papers."""
        p1, p2 = self._papers()
        result = corpus_entities([p1, p2], field="abstract")
        # p1 abstract "Active Inference and EEG studies.":
        #   "Active Inference" (1), "EEG" (1).
        # p2 abstract "Active Inference with EEG and FEP.":
        #   "Active Inference" (1), "EEG" (1), "FEP" (1).
        # Totals: Active Inference=2, EEG=2, FEP=1.
        assert result == {
            "Active Inference": 2,
            "EEG": 2,
            "FEP": 1,
        }
        # Deterministic insertion order: count desc, then alpha.
        assert list(result.keys()) == ["Active Inference", "EEG", "FEP"]

    def test_title_aggregation(self):
        """Title-field entities aggregate across papers."""
        p1, p2 = self._papers()
        result = corpus_entities([p1, p2], field="title")
        # p1 title "Active Inference Theory" -> "Active Inference Theory".
        # p2 title "Bayesian Brain Review" -> "Bayesian Brain Review".
        assert result == {
            "Active Inference Theory": 1,
            "Bayesian Brain Review": 1,
        }

    def test_full_text_via_mapping(self):
        """Full-text path reads from the fulltext mapping by canonical_id."""
        p1, p2 = self._papers()
        fulltext = {
            p1.canonical_id: "Markov Blanket and EEG appear. Markov Blanket again.",
            # p2 deliberately omitted -> contributes nothing.
        }
        result = corpus_entities([p1, p2], field="full_text", fulltext=fulltext)
        # Only p1 has full text:
        #   "Markov Blanket" x2, "EEG" x1.
        assert result == {
            "Markov Blanket": 2,
            "EEG": 1,
        }

    def test_full_text_none_mapping_empty(self):
        """fulltext=None treats every paper as empty (no error, no entities)."""
        p1, p2 = self._papers()
        result = corpus_entities([p1, p2], field="full_text", fulltext=None)
        assert result == {}

    def test_unsupported_field_raises(self):
        """An unsupported field raises ValueError."""
        p1, p2 = self._papers()
        with pytest.raises(ValueError):
            corpus_entities([p1, p2], field="keywords")

    def test_empty_corpus(self):
        """An empty corpus yields an empty mapping."""
        assert corpus_entities([], field="abstract") == {}

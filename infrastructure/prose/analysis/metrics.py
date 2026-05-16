"""Plain-text prose metrics: word/sentence/paragraph counts, readability.

These functions are pure and deterministic. They take a string of prose
(post-Markdown, post-front-matter) and return numeric / structured
results. No I/O, no external dependencies beyond stdlib.

The readability scores are textbook-standard formulae:

* Flesch Reading Ease (FRE)
* Flesch-Kincaid Grade Level (FKGL)
* Gunning Fog Index

Implementations use a simple Naive heuristic for syllable counting that
is good enough for editorial feedback (within ~5% of textbook values on
typical academic prose). This module is *not* trying to replace a
linguistic toolkit — it is trying to give a writer-friendly signal during
manuscript review.
"""

import re
from dataclasses import dataclass

# Sentence splitting pattern. Conservative: only break on . ! ? followed
# by whitespace + capital. Won't perfectly handle abbreviations but is
# stable.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"\(\[])")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-']*")
_VOWEL_GROUP_RE = re.compile(r"[aeiouyAEIOUY]+")


@dataclass(frozen=True)
class ProseMetrics:
    """Container for prose metrics."""

    char_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    syllable_count: int
    avg_words_per_sentence: float
    avg_syllables_per_word: float
    complex_word_count: int
    complex_word_fraction: float
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float

    def to_dict(self) -> dict[str, object]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def split_paragraphs(text: str) -> list[str]:
    """Split *text* on blank lines into non-empty paragraphs."""
    if not text:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def split_sentences(text: str) -> list[str]:
    """Split *text* into sentences using a conservative heuristic."""
    if not text:
        return []
    pieces = _SENTENCE_RE.split(text.strip())
    # The final "sentence" may not end with terminal punctuation; keep it.
    return [s.strip() for s in pieces if s.strip()]


def tokenize_words(text: str) -> list[str]:
    """Return the list of word tokens in *text*."""
    return _WORD_RE.findall(text)


def count_syllables(word: str) -> int:
    """Estimate syllables in *word* using vowel-group heuristic.

    Special rules:

    * Silent terminal "e" subtracts one (unless the word would have zero).
    * Always at least one syllable for any non-empty word.
    """
    if not word:
        return 0
    word = word.lower()
    groups = _VOWEL_GROUP_RE.findall(word)
    count = len(groups)
    if word.endswith("e") and count > 1 and not word.endswith("le"):
        count -= 1
    return max(1, count)


def is_complex_word(word: str) -> bool:
    """A "complex word" for Gunning Fog: ≥3 syllables, not proper noun,
    not a -es / -ed / -ing form."""
    if not word or word[0].isupper():
        return False
    if len(word) < 4:
        return False
    lower = word.lower()
    if lower.endswith(("es", "ed", "ing")):
        return False
    return count_syllables(word) >= 3


def compute_metrics(text: str) -> ProseMetrics:
    """Compute :class:`ProseMetrics` for *text*."""
    if not text or not text.strip():
        return ProseMetrics(
            char_count=0,
            word_count=0,
            sentence_count=0,
            paragraph_count=0,
            syllable_count=0,
            avg_words_per_sentence=0.0,
            avg_syllables_per_word=0.0,
            complex_word_count=0,
            complex_word_fraction=0.0,
            flesch_reading_ease=0.0,
            flesch_kincaid_grade=0.0,
            gunning_fog=0.0,
        )

    paragraphs = split_paragraphs(text)
    sentences = []
    for p in paragraphs:
        sentences.extend(split_sentences(p))
    words = tokenize_words(text)
    syllables = sum(count_syllables(w) for w in words)
    complex_words = [w for w in words if is_complex_word(w)]

    n_words = len(words)
    n_sentences = max(1, len(sentences))
    n_paragraphs = len(paragraphs)
    avg_wps = n_words / n_sentences
    avg_spw = (syllables / n_words) if n_words else 0.0
    cwf = (len(complex_words) / n_words) if n_words else 0.0

    # Flesch Reading Ease
    fre = 206.835 - (1.015 * avg_wps) - (84.6 * avg_spw)
    # Flesch-Kincaid Grade Level
    fkgl = (0.39 * avg_wps) + (11.8 * avg_spw) - 15.59
    # Gunning Fog Index
    fog = 0.4 * (avg_wps + 100.0 * cwf)

    return ProseMetrics(
        char_count=len(text),
        word_count=n_words,
        sentence_count=len(sentences),
        paragraph_count=n_paragraphs,
        syllable_count=syllables,
        avg_words_per_sentence=round(avg_wps, 3),
        avg_syllables_per_word=round(avg_spw, 3),
        complex_word_count=len(complex_words),
        complex_word_fraction=round(cwf, 3),
        flesch_reading_ease=round(fre, 2),
        flesch_kincaid_grade=round(fkgl, 2),
        gunning_fog=round(fog, 2),
    )

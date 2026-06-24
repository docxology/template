"""Offline entity and keyphrase extraction over paper text.

Provides deterministic, regex-based extraction of named entities
(capitalized multiword proper-noun phrases plus ALLCAPS acronyms) and
TF-scored keyphrases (1-3 gram) from titles, abstracts, and full text,
with no network access and no mandatory LLM dependency.

The extraction reuses the canonical English ``STOPWORDS`` set from
:mod:`analysis.text_processing` so stopword handling stays consistent
across the pipeline.
"""

from __future__ import annotations

import re

from analysis.text_processing import STOPWORDS

# A "word" inside a candidate proper-noun phrase: a capitalized token that
# may continue with lowercase letters and may contain internal hyphens or
# apostrophes (e.g. "Inference", "Karl-Friston", "O'Neil"). The leading
# character must be an uppercase letter so common lowercase words break the
# run.
_CAP_WORD = r"[A-Z][A-Za-z]*(?:[-'][A-Za-z]+)*"

# A run of one-or-more capitalized words separated by single spaces. We later
# require >= 2 words for a phrase to qualify, but capture the full run here so
# that bordering stopwords can be trimmed.
_CAP_RUN_RE = re.compile(rf"{_CAP_WORD}(?:\s+{_CAP_WORD})*")

# An ALLCAPS acronym: 2+ characters drawn from uppercase letters and digits,
# containing at least two letters. Bounded by non-word characters so it is a
# standalone token (e.g. "EEG", "FEP", "GPT3"). The lookarounds prevent
# matching the leading slice of a Capitalized word like "EEGish". A token whose
# span lies inside a multiword capitalized run (e.g. each word of "WORLD HEALTH
# ORGANIZATION") is excluded at extraction time so such runs are reported once as a
# phrase rather than shredded into spurious single-word acronyms.
_ACRONYM_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z0-9]{2,})(?![A-Za-z0-9])")

# Lowercase token used for keyphrase n-grams: alphabetic/numeric runs.
_TOKEN_RE = re.compile(r"[a-z0-9]+")

_VALID_FIELDS = ("title", "abstract", "full_text")


def _split_words(phrase: str) -> list[str]:
    """Split a phrase on whitespace into its component words.

    Args:
        phrase: A whitespace-joined run of capitalized words.

    Returns:
        List of non-empty word strings.
    """
    return [w for w in phrase.split() if w]


def _trim_stopwords(words: list[str]) -> list[str]:
    """Drop leading and trailing stopword words from a phrase.

    Interior stopwords are preserved (a multiword proper name such as
    "Bank Of England" keeps its lowercase-equivalent connectors only at
    the interior). Comparison is case-insensitive against ``STOPWORDS``.

    Args:
        words: Component words of a candidate phrase.

    Returns:
        The words with any stopword prefix/suffix removed. May be empty
        if every word is a stopword.
    """
    start = 0
    end = len(words)
    while start < end and words[start].lower() in STOPWORDS:
        start += 1
    while end > start and words[end - 1].lower() in STOPWORDS:
        end -= 1
    return words[start:end]


def extract_entities(text: str) -> list[tuple[str, int]]:
    """Extract proper-noun phrases and ALLCAPS acronyms from text.

    Two kinds of entity are recognized using regular expressions only:

    * Capitalized multiword proper-noun phrases (runs of 2+ capitalized
      words, e.g. ``"World Health Organization"``). Leading and trailing stopword
      words are trimmed, and a phrase whose words are all stopwords is
      dropped. Single capitalized words (including a sentence-initial
      ``"The"``) never qualify on their own.
    * ALLCAPS acronyms of length >= 2 containing at least two letters
      (e.g. ``"EEG"``, ``"FEP"``).

    Counting merges case variants: occurrences are tallied
    case-insensitively, but a single canonical surface form (the first one
    seen, scanning the text left to right) is returned per entity.

    Args:
        text: Raw input text (title, abstract, or full text).

    Returns:
        List of ``(entity, count)`` tuples sorted by count descending,
        then by entity alphabetically (case-insensitive) ascending. Empty
        if ``text`` is empty or contains no qualifying entities.
    """
    if not text:
        return []

    counts: dict[str, int] = {}
    canonical: dict[str, str] = {}

    def _record(surface: str) -> None:
        key = surface.lower()
        counts[key] = counts.get(key, 0) + 1
        if key not in canonical:
            canonical[key] = surface

    # First pass: capitalized multiword proper-noun phrases. Track the
    # character spans of qualifying (>= 2 trimmed words) phrases so the
    # acronym pass can skip ALLCAPS words that live inside such a phrase.
    phrase_spans: list[tuple[int, int]] = []
    for match in _CAP_RUN_RE.finditer(text):
        words = _split_words(match.group(0))
        trimmed = _trim_stopwords(words)
        if len(trimmed) < 2:
            # Single-word run (or all stopwords) is not a multiword phrase.
            continue
        phrase_spans.append((match.start(), match.end()))
        _record(" ".join(trimmed))

    def _inside_phrase(start: int, end: int) -> bool:
        for p_start, p_end in phrase_spans:
            if start >= p_start and end <= p_end:
                return True
        return False

    # Second pass: ALLCAPS acronyms (require at least two alphabetic
    # characters so pure numeric runs like "2020" are not treated as
    # acronyms). Skip any acronym whose span sits inside a multiword phrase
    # already counted above.
    for match in _ACRONYM_RE.finditer(text):
        token = match.group(1)
        letter_count = sum(1 for ch in token if ch.isalpha())
        if letter_count < 2:
            continue
        if _inside_phrase(match.start(), match.end()):
            continue
        _record(token)

    ordered = sorted(
        canonical.keys(),
        key=lambda key: (-counts[key], key),
    )
    return [(canonical[key], counts[key]) for key in ordered]


def extract_keyphrases(text: str, top_k: int = 20) -> list[tuple[str, float]]:
    """Extract TF-scored 1-3 gram keyphrases from text.

    Tokens are lowercased alphanumeric runs. Candidate n-grams of size 1,
    2, and 3 are generated over the token sequence; any n-gram containing
    a stopword token is discarded entirely. Each surviving n-gram surface
    is the space-joined token sequence.

    Scoring is term-frequency normalized by the total number of candidate
    (post-filter) n-gram occurrences::

        score(phrase) = occurrences(phrase) / total_candidate_occurrences

    so every score lies in ``(0, 1]`` and all scores sum to 1.0.

    Args:
        text: Raw input text.
        top_k: Maximum number of keyphrases to return. Values <= 0 yield
            an empty list.

    Returns:
        List of ``(phrase, score)`` tuples sorted by score descending,
        then phrase alphabetically ascending, truncated to ``top_k``.
        Empty if ``text`` is empty/whitespace, ``top_k <= 0``, or no
        n-gram survives stopword filtering.
    """
    if top_k <= 0:
        return []
    if not text or not text.strip():
        return []

    tokens = _TOKEN_RE.findall(text.lower())
    if not tokens:
        return []

    occurrences: dict[str, int] = {}
    total = 0
    n_tokens = len(tokens)
    for n in (1, 2, 3):
        for start in range(n_tokens - n + 1):
            gram = tokens[start : start + n]
            if any(tok in STOPWORDS for tok in gram):
                continue
            phrase = " ".join(gram)
            occurrences[phrase] = occurrences.get(phrase, 0) + 1
            total += 1

    if total == 0:
        return []

    scored = [(phrase, count / total) for phrase, count in occurrences.items()]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored[:top_k]


def corpus_entities(
    papers: list,
    field: str = "abstract",
    fulltext: dict[str, str] | None = None,
) -> dict[str, int]:
    """Aggregate :func:`extract_entities` across a corpus field.

    Args:
        papers: List of ``Paper`` objects (duck-typed: each must expose
            ``title``, ``abstract``, and ``canonical_id``).
        field: Which text to extract from. One of ``"title"``,
            ``"abstract"``, or ``"full_text"``.
        fulltext: Mapping from ``paper.canonical_id`` to full-text string,
            used only when ``field == "full_text"``. A missing key (or a
            ``None`` mapping) is treated as empty text for that paper, so
            callers can probe full-text coverage without error.

    Returns:
        Dict mapping canonical entity surface form to total count across
        the corpus, merged case-insensitively (consistent with
        :func:`extract_entities`). Insertion order is deterministic:
        descending total count, then entity alphabetically (case-
        insensitive) ascending.

    Raises:
        ValueError: If ``field`` is not one of the supported fields.
    """
    if field not in _VALID_FIELDS:
        raise ValueError(f"unsupported field {field!r}; expected one of {_VALID_FIELDS}")

    fulltext_map = fulltext if fulltext is not None else {}

    totals: dict[str, int] = {}
    canonical: dict[str, str] = {}

    for paper in papers:
        if field == "title":
            text = paper.title
        elif field == "abstract":
            text = paper.abstract
        else:  # field == "full_text"
            text = fulltext_map.get(paper.canonical_id, "")

        for surface, count in extract_entities(text or ""):
            key = surface.lower()
            totals[key] = totals.get(key, 0) + count
            if key not in canonical:
                canonical[key] = surface

    ordered = sorted(
        totals.keys(),
        key=lambda key: (-totals[key], key),
    )
    return {canonical[key]: totals[key] for key in ordered}

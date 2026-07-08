"""Editorial quality checks: passive voice, hedge words, citation density.

Lightweight stylistic analysers intended to give a writer fast,
deterministic feedback. None of these is a replacement for human
review; all are heuristics tuned for academic prose.
"""

import re
from dataclasses import dataclass, field

from infrastructure.prose.analysis.metrics import (
    split_sentences,
    tokenize_words,
)

# Common "to be" forms used to flag potential passive constructions.
_BE_FORMS = {"is", "are", "was", "were", "be", "been", "being", "am"}

# Common past-participle endings (heuristic, not exhaustive). Coupled with
# a preceding "to be" form, this gives a rough passive-voice signal.
_PP_RE = re.compile(r"\b\w+(ed|en)\b", re.IGNORECASE)

# Hedge words / weasel words common in academic writing.
_HEDGE_WORDS = {
    "may",
    "might",
    "could",
    "perhaps",
    "probably",
    "likely",
    "possibly",
    "somewhat",
    "roughly",
    "approximately",
    "essentially",
    "basically",
    "arguably",
    "generally",
    "largely",
    "nearly",
    "almost",
    "seems",
    "appears",
    "suggests",
}

# Pandoc / pandoc-citeproc citation key patterns.
_CITE_RE = re.compile(r"(?<!\w)@[A-Za-z][A-Za-z0-9_:.-]*")
_BRACKET_CITE_RE = re.compile(r"\[@[^\]]+\]")

# pandoc-crossref and COGANT formalism reference prefixes (NOT citations).
# A bracketed reference like [@sec:methodology] resolves through pandoc-crossref,
# and a reference like @def:program-graph resolves through COGANT's generated
# formalism registry, not through the bibliography. Excluded from citation_keys
# so the bibliography_consistency check does not misreport them as missing bib
# entries.
_CROSSREF_PREFIXES = (
    "fig:",
    "tbl:",
    "eq:",
    "sec:",
    "lst:",
    "def:",
    "prop:",
    "inv:",
    "conj:",
    "alg:",
    "thm:",
)


@dataclass
class QualityReport:
    """Aggregate quality flags."""

    passive_count: int = 0
    passive_sentences: list[str] = field(default_factory=list)
    hedge_count: int = 0
    hedge_words: list[str] = field(default_factory=list)
    citation_count: int = 0
    citation_keys: list[str] = field(default_factory=list)
    long_sentence_count: int = 0
    long_sentences: list[str] = field(default_factory=list)
    word_count: int = 0
    citation_density_per_1000: float = 0.0
    hedge_density_per_1000: float = 0.0
    passive_density_per_1000: float = 0.0

    def to_dict(self) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "word_count": self.word_count,
            "passive_count": self.passive_count,
            "hedge_count": self.hedge_count,
            "citation_count": self.citation_count,
            "long_sentence_count": self.long_sentence_count,
            "passive_density_per_1000": self.passive_density_per_1000,
            "hedge_density_per_1000": self.hedge_density_per_1000,
            "citation_density_per_1000": self.citation_density_per_1000,
            "citation_keys": list(self.citation_keys),
            "passive_sentences": list(self.passive_sentences),
            "hedge_words": list(self.hedge_words),
            "long_sentences": list(self.long_sentences),
        }


def detect_passive_sentences(text: str) -> list[str]:
    """Return sentences with at least one "be + past participle" pair."""
    out: list[str] = []
    for sentence in split_sentences(text):
        words = tokenize_words(sentence)
        lower_words = [w.lower() for w in words]
        for i, w in enumerate(lower_words[:-1]):
            if w in _BE_FORMS:
                next_word = words[i + 1]
                if _PP_RE.match(next_word):
                    out.append(sentence)
                    break
    return out


def detect_hedge_words(text: str) -> list[str]:
    """Return list of hedge words present in *text* (with duplicates)."""
    return [w for w in (t.lower() for t in tokenize_words(text)) if w in _HEDGE_WORDS]


def extract_citation_keys(text: str) -> list[str]:
    """Extract Pandoc-style ``@key`` citations from *text*.

    Matches both ``[@key1; @key2]`` and bare ``@key``. pandoc-crossref
    references (``fig:``, ``tbl:``, ``eq:``, ``sec:``, ``lst:`` prefixes)
    are excluded — they resolve via the cross-reference filter, not the
    bibliography.
    """
    keys: list[str] = []
    for match in _BRACKET_CITE_RE.finditer(text):
        for sub in re.findall(r"@([A-Za-z][A-Za-z0-9_:.-]*)", match.group(0)):
            if not sub.startswith(_CROSSREF_PREFIXES):
                keys.append(sub)
    for match in _CITE_RE.finditer(text):
        # _BRACKET_CITE_RE already covers the bracketed form; this picks up
        # bare @key occurrences. Deduplicate via dict.fromkeys later.
        key = match.group(0)[1:]
        if not key.startswith(_CROSSREF_PREFIXES):
            keys.append(key)
    return list(dict.fromkeys(keys))


def detect_long_sentences(text: str, *, threshold: int = 35) -> list[str]:
    """Return sentences with > *threshold* words."""
    return [s for s in split_sentences(text) if len(tokenize_words(s)) > threshold]


def analyze_quality(text: str, *, long_sentence_threshold: int = 35) -> QualityReport:
    """Run every detector over *text* and return a :class:`QualityReport`."""
    if not text or not text.strip():
        return QualityReport()

    words = tokenize_words(text)
    n = len(words)
    passive = detect_passive_sentences(text)
    hedges = detect_hedge_words(text)
    cites = extract_citation_keys(text)
    long_sents = detect_long_sentences(text, threshold=long_sentence_threshold)

    def density(count: int) -> float:
        """Return the citation density metric."""
        return round(1000.0 * count / n, 2) if n else 0.0

    return QualityReport(
        passive_count=len(passive),
        passive_sentences=passive,
        hedge_count=len(hedges),
        hedge_words=hedges,
        citation_count=len(cites),
        citation_keys=cites,
        long_sentence_count=len(long_sents),
        long_sentences=long_sents,
        word_count=n,
        citation_density_per_1000=density(len(cites)),
        hedge_density_per_1000=density(len(hedges)),
        passive_density_per_1000=density(len(passive)),
    )

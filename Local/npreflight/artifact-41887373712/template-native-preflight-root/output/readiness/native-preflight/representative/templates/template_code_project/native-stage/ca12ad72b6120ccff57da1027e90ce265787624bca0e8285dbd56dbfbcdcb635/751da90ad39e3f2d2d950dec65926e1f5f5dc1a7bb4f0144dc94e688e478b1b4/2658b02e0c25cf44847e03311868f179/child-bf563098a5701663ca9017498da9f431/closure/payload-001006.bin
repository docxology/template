"""Deterministic AI-writing-pattern and burstiness detector.

A clean-room distillation of the "writing quality check" idea from Academic
Research Skills (https://github.com/Imbad0202/academic-research-skills,
CC-BY-NC-4.0): warn when prose carries statistical fingerprints of unedited LLM
output. No ARS code is vendored; this is an original Apache-2.0 implementation
and every signal here is computed deterministically — no model, no network.

The three signals:

* **AI-typical phrasing** — frequency of stock LLM phrases ("delve into", "it is
  worth noting", "rich tapestry", ...). These are *advisory*: any one is fine in
  isolation; a high density across a manuscript is the smell.
* **Em-dash density** — LLM prose over-uses the em-dash. Reported per 1000 words.
* **Burstiness** — humans mix long and short sentences (high variance); LLM
  prose trends toward uniform sentence length (low variance). Measured as the
  coefficient of variation of sentence lengths.

This is a *warning* tool, not a gate: false positives are expected on heavily
formulaic technical prose, so callers decide whether to fail on flags.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Any

from infrastructure.validation.content.markdown_strip import strip_code_and_math

__all__ = [
    "AI_TYPICAL_TERMS",
    "AiTermHit",
    "ProseQualityReport",
    "ProseQualityThresholds",
    "analyze_prose",
]

# Curated stock LLM phrases. Lower-cased; matched on word boundaries. Kept
# academic-leaning and conservative — these are *signals*, not banned words.
AI_TYPICAL_TERMS: tuple[str, ...] = (
    "delve into",
    "delve deeper",
    "it is worth noting",
    "it's worth noting",
    "it is important to note",
    "rich tapestry",
    "a testament to",
    "plays a crucial role",
    "plays a pivotal role",
    "plays a vital role",
    "in the realm of",
    "in the ever-evolving",
    "navigating the",
    "navigate the complexities",
    "a comprehensive understanding",
    "shed light on",
    "at the forefront",
    "underscores the importance",
    "underscore the importance",
    "highlights the importance",
    "the landscape of",
    "paving the way",
    "paradigm shift",
    "unlock the potential",
    "harness the power",
    "a myriad of",
    "a multitude of",
    "seamless integration",
    "ever-changing",
    "cutting-edge",
    "game-changer",
    "first and foremost",
    "when it comes to",
    "it should be noted",
    "in today's world",
    "in conclusion",
    "moreover",
    "furthermore",
    "notably",
    "crucially",
)


@dataclass(frozen=True)
class ProseQualityThresholds:
    """Tunable thresholds; exceeding any one raises a flag."""

    em_dash_per_1k_max: float = 8.0
    ai_term_per_1k_max: float = 4.0
    burstiness_min: float = 0.45
    min_words_for_burstiness: int = 40


@dataclass(frozen=True)
class AiTermHit:
    """One AI-typical phrase and how often it appears."""

    term: str
    count: int


@dataclass
class ProseQualityReport:
    """The result of analyzing one body of prose."""

    word_count: int
    sentence_count: int
    em_dash_count: int
    em_dash_per_1k: float
    ai_term_hits: list[AiTermHit] = field(default_factory=list)
    ai_term_per_1k: float = 0.0
    mean_sentence_length: float = 0.0
    burstiness: float = 0.0
    flags: list[str] = field(default_factory=list)

    @property
    def has_flags(self) -> bool:
        """Return whether flags is present."""
        return bool(self.flags)

    @property
    def total_ai_terms(self) -> int:
        """Process total ai terms."""
        return sum(hit.count for hit in self.ai_term_hits)

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "em_dash_count": self.em_dash_count,
            "em_dash_per_1k": round(self.em_dash_per_1k, 3),
            "ai_term_per_1k": round(self.ai_term_per_1k, 3),
            "total_ai_terms": self.total_ai_terms,
            "ai_term_hits": [{"term": h.term, "count": h.count} for h in self.ai_term_hits],
            "mean_sentence_length": round(self.mean_sentence_length, 3),
            "burstiness": round(self.burstiness, 3),
            "flags": list(self.flags),
            "has_flags": self.has_flags,
        }


_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+(?:\s+|$)")
_HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")
# Unicode em-dash/horizontal-bar, plus the ASCII double-hyphen "--" in either
# spaced ("a -- b") or tight ("a--b") form, but never the "---" Markdown rule.
_EM_DASH_RE = re.compile(r"—|―|(?<!-)--(?!-)")


def _count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _split_sentences(text: str) -> list[str]:
    pieces = [piece.strip() for piece in _SENTENCE_SPLIT_RE.split(text)]
    return [piece for piece in pieces if _WORD_RE.search(piece)]


def _find_ai_terms(text_lower: str) -> list[AiTermHit]:
    hits: list[AiTermHit] = []
    for term in AI_TYPICAL_TERMS:
        pattern = r"\b" + re.escape(term) + r"\b"
        count = len(re.findall(pattern, text_lower))
        if count:
            hits.append(AiTermHit(term=term, count=count))
    hits.sort(key=lambda h: (-h.count, h.term))
    return hits


def _burstiness(sentences: list[str]) -> tuple[float, float]:
    """Return (mean_sentence_length, coefficient_of_variation)."""
    lengths = [len(_WORD_RE.findall(s)) for s in sentences]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        avg = float(lengths[0]) if lengths else 0.0
        return avg, 0.0
    avg = mean(lengths)
    if avg == 0:
        return 0.0, 0.0
    return avg, pstdev(lengths) / avg


def analyze_prose(
    text: str,
    *,
    thresholds: ProseQualityThresholds | None = None,
    strip_markdown: bool = True,
) -> ProseQualityReport:
    """Analyze *text* for AI-writing fingerprints. Deterministic, offline.

    Args:
        text: Raw prose or Markdown.
        thresholds: Flagging thresholds (defaults to :class:`ProseQualityThresholds`).
        strip_markdown: Strip code fences / inline code / math before analysis so
            literal ``---`` rules and code punctuation do not skew the signals.
    """
    thresholds = thresholds or ProseQualityThresholds()
    clean = strip_code_and_math(text) if strip_markdown else text
    # HTML comments carry figure labels and generator metadata, not prose. Strip
    # them before counting punctuation so ``<!-- ... -->`` is not mistaken for
    # an author's ASCII em dash.
    if strip_markdown:
        clean = _HTML_COMMENT_RE.sub("", clean)
    clean_lower = clean.lower()

    words = _count_words(clean)
    sentences = _split_sentences(clean)
    em_dashes = len(_EM_DASH_RE.findall(clean))
    ai_hits = _find_ai_terms(clean_lower)
    total_ai = sum(h.count for h in ai_hits)
    mean_len, burst = _burstiness(sentences)

    per_1k = (1000.0 / words) if words else 0.0
    em_per_1k = em_dashes * per_1k
    ai_per_1k = total_ai * per_1k

    flags: list[str] = []
    if em_per_1k > thresholds.em_dash_per_1k_max:
        flags.append(f"em-dash density {em_per_1k:.1f}/1k exceeds {thresholds.em_dash_per_1k_max}/1k")
    if ai_per_1k > thresholds.ai_term_per_1k_max:
        flags.append(f"AI-typical phrasing {ai_per_1k:.1f}/1k exceeds {thresholds.ai_term_per_1k_max}/1k")
    if words >= thresholds.min_words_for_burstiness and len(sentences) >= 3 and burst < thresholds.burstiness_min:
        flags.append(f"low burstiness {burst:.2f} (uniform sentence length) below {thresholds.burstiness_min}")

    return ProseQualityReport(
        word_count=words,
        sentence_count=len(sentences),
        em_dash_count=em_dashes,
        em_dash_per_1k=em_per_1k,
        ai_term_hits=ai_hits,
        ai_term_per_1k=ai_per_1k,
        mean_sentence_length=mean_len,
        burstiness=burst,
        flags=flags,
    )

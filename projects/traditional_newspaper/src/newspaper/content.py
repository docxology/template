"""Deterministic fixture copy for newspaper layout stress tests and demos."""

from __future__ import annotations

import numpy as np

# Short clauses shuffled deterministically per seed to build paragraphs.
_FIXTURE_POOL: tuple[str, ...] = (
    "The compositor holds the column measure.",
    "Pandoc pours Markdown into LaTeX.",
    "Each folio slice maps to one manuscript file.",
    "XeLaTeX prints the sheet while the pipeline logs the run.",
    "Fixture copy avoids mock interviews and network calls.",
    "The Research Project Template owns the orchestration layer.",
    "Multicolumn body text flows inside a single folio slice.",
    "Headlines and bylines stay ordinary Markdown outside raw LaTeX blocks.",
)

FIXTURE_SENTENCES: tuple[str, ...] = _FIXTURE_POOL


def fixture_paragraph(*, seed: int = 0) -> str:
    """Return one paragraph: shuffled pool clauses joined as sentences."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(_FIXTURE_POOL))
    parts = [_FIXTURE_POOL[int(i)] for i in order]
    return " ".join(parts) + "."


def fixture_copy(num_paragraphs: int, *, seed: int = 0) -> str:
    """Return ``num_paragraphs`` paragraphs separated by blank lines.

    Each paragraph uses ``fixture_paragraph(seed=seed + k)`` so length and
    diversity grow predictably with ``num_paragraphs``.
    """
    if num_paragraphs < 1:
        raise ValueError("num_paragraphs must be at least 1")
    paras = [fixture_paragraph(seed=seed + k) for k in range(num_paragraphs)]
    return "\n\n".join(paras)

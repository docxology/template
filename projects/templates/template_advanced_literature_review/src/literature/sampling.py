"""Deterministic corpus subsampling for expensive LLM stages.

The full bibliography is always complete; only the LLM-gated stages
(knowledge-graph extraction, reproducibility assessment) sample a
fraction of the corpus to keep runtime bounded.

Sampling is deterministic: the same corpus + same seed + same fraction
always produces the same subset. The sample is drawn by sorting papers
by ``canonical_id`` (stable order) and then selecting every
``1/fraction``-th paper with a seed-determined offset, so the selection
is reproducible without depending on dict iteration order or random
shuffle. This makes runs idempotent and resumable: a re-run with the
same config skips already-processed papers and processes the same new
ones.
"""

from __future__ import annotations

import random
from typing import Any

from literature.models import Paper


def load_sampling_config(config: dict[str, Any]) -> tuple[float, int]:
    """Extract sampling fraction and seed from a config dict.

    Args:
        config: The ``project_config`` dict from ``manuscript/config.yaml``.

    Returns:
        A ``(fraction, seed)`` tuple. Defaults to ``(1.0, 42)`` when no
        sampling block is present (i.e., no subsampling by default).
    """
    sampling_cfg = config.get("sampling", {}) or {}
    raw_fraction = sampling_cfg.get("fraction", 1.0)
    raw_seed = sampling_cfg.get("seed", 42)
    if isinstance(raw_fraction, bool) or not isinstance(raw_fraction, (int, float)):
        raise ValueError("sampling.fraction must be numeric")
    fraction = float(raw_fraction)
    if not 0.0 < fraction <= 1.0:
        raise ValueError("sampling.fraction must be greater than zero and at most one")
    if type(raw_seed) is not int or raw_seed < 0:
        raise ValueError("sampling.seed must be a non-negative integer")
    seed = raw_seed
    return fraction, seed


def sample_papers(papers: list[Paper], *, fraction: float, seed: int) -> list[Paper]:
    """Deterministically subsample *papers* to *fraction* of the original.

    Papers are sorted by ``canonical_id`` for stable ordering, then
    selected using a seeded RNG to pick a random starting offset and
    stride through the sorted list. This ensures:

    - **Determinism**: same input + same seed + same fraction = same output.
    - **Idempotency**: re-running with the same config produces the same
      sample, so incremental resume works correctly.
    Selection is reproducible for a fixed corpus. Adding records can change
    both the offset and stride selections; no membership-stability claim is made.

    Args:
        papers: Full list of papers to sample from.
        fraction: Fraction to keep (0.0-1.0). 1.0 = all papers.
        seed: RNG seed for deterministic offset selection.

    Returns:
        A subset of *papers* of size ``max(1, round(len(papers) * fraction))``.
        When *fraction* >= 1.0, returns all papers unchanged.
    """
    if fraction >= 1.0 or not papers:
        return list(papers)

    n = len(papers)
    target = max(1, round(n * fraction))
    if target >= n:
        return list(papers)

    # Sort by canonical_id for stable ordering across runs.
    sorted_papers = sorted(papers, key=lambda p: p.canonical_id)

    # Use a seeded RNG to pick a random starting offset, then stride.
    rng = random.Random(seed)
    offset = rng.randint(0, n - 1)

    result: list[Paper] = []
    for i in range(target):
        idx = (offset + i * (n // target)) % n
        result.append(sorted_papers[idx])

    return result

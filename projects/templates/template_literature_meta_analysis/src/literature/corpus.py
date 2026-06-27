"""Unified corpus management.

Provides a Corpus class that manages collections of Paper objects with
deduplication, merging, persistence (JSONL format), and filtering
capabilities.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from .models import Paper

logger = logging.getLogger(__name__)


def _preprint_rank(paper: Paper, *, prefer_preprints: bool) -> tuple[int, int, int, int, int, int]:
    return (
        int(paper.is_preprint if prefer_preprints else not paper.is_preprint),
        int(paper.doi is not None),
        int(paper.publication_date is not None),
        int(paper.metadata_completeness),
        int(len(paper.abstract or "")),
        int(paper.citation_count),
    )


class Corpus:
    """Manages a collection of Paper objects with dedup, merge, and persistence.

    Papers are stored internally keyed by their canonical_id, ensuring
    uniqueness. When a paper with an existing canonical_id is added,
    the version with more metadata wins.

    Attributes:
        _papers: Internal dictionary mapping canonical_id to Paper.
    """

    def __init__(self, papers: Optional[list[Paper]] = None) -> None:
        """Initialize corpus, optionally with an initial list of papers.

        Args:
            papers: Optional list of Paper objects to seed the corpus.
        """
        self._papers: dict[str, Paper] = {}
        if papers:
            for p in papers:
                self.add(p)

    def add(self, paper: Paper) -> None:
        """Add a paper to the corpus, merging with existing if same canonical_id.

        When a paper with the same canonical_id already exists, the version
        with higher metadata_completeness is kept.

        Args:
            paper: Paper object to add or merge.
        """
        cid = paper.canonical_id
        if cid in self._papers:
            existing = self._papers[cid]
            if paper.metadata_completeness > existing.metadata_completeness:
                self._papers[cid] = paper
                logger.debug("Corpus.add: updated %s (better metadata)", cid)
            else:
                logger.debug("Corpus.add: kept existing %s", cid)
        else:
            self._papers[cid] = paper
            logger.debug("Corpus.add: new paper %s", cid)

    def deduplicate_by_metadata(self, *, prefer_preprints: bool = False) -> int:
        grouped: dict[str, list[str]] = {}
        for cid, paper in self._papers.items():
            grouped.setdefault(paper.publication_signature, []).append(cid)

        removed = 0
        for ids in grouped.values():
            if len(ids) <= 1:
                continue
            winner_id = max(ids, key=lambda cid: _preprint_rank(self._papers[cid], prefer_preprints=prefer_preprints))
            winner = self._papers[winner_id]
            for cid in ids:
                if cid == winner_id:
                    continue
                self._papers.pop(cid, None)
                removed += 1
            self._papers[winner.canonical_id] = winner
        return removed

    def merge(self, other: Corpus) -> None:
        """Merge another corpus into this one.

        Each paper from the other corpus is added via the standard
        add() method, so deduplication and merge logic apply.

        Args:
            other: Another Corpus instance to merge in.
        """
        for paper in other.papers:
            self.add(paper)

    @property
    def papers(self) -> list[Paper]:
        """Return all papers as a list.

        Returns:
            List of all Paper objects in the corpus.
        """
        return list(self._papers.values())

    def get(self, canonical_id: str) -> Optional[Paper]:
        """Retrieve a paper by its canonical ID.

        Args:
            canonical_id: The canonical identifier string.

        Returns:
            Paper if found, None otherwise.
        """
        return self._papers.get(canonical_id)

    def __len__(self) -> int:
        """Return the number of papers in the corpus."""
        return len(self._papers)

    def __contains__(self, canonical_id: str) -> bool:
        """Return True if a paper with *canonical_id* is in the corpus."""
        return canonical_id in self._papers

    def remove(self, canonical_id: str) -> bool:
        """Remove a paper by its canonical ID.

        Args:
            canonical_id: The canonical identifier of the paper to remove.

        Returns:
            True if a paper was removed, False if not found.
        """
        if canonical_id in self._papers:
            del self._papers[canonical_id]
            return True
        return False

    def filter_by_year(self, start: Optional[int] = None, end: Optional[int] = None) -> Corpus:
        """Filter papers by publication year range.

        Args:
            start: Minimum year (inclusive). None means no lower bound.
            end: Maximum year (inclusive). None means no upper bound.

        Returns:
            New Corpus containing only papers within the year range.
            Papers with year=None are excluded.
        """
        if start is not None and end is not None and start > end:
            raise ValueError(f"filter_by_year: start={start} > end={end}")
        filtered: list[Paper] = []
        for paper in self._papers.values():
            if paper.year is None:
                continue
            if start is not None and paper.year < start:
                continue
            if end is not None and paper.year > end:
                continue
            filtered.append(paper)
        return Corpus(filtered)

    def filter_by_subfield(self, subfield: str) -> Corpus:
        """Filter papers by subfield domain classification.

        Uses lazy import of classify_paper from analysis.subfield_classifier
        to avoid circular dependencies at module load time.

        Args:
            subfield: Domain name to filter for (e.g., "C1_neuroscience",
                "C2_robotics", "A2_philosophy").

        Returns:
            New Corpus containing only papers classified under the domain.
        """
        from analysis.subfield_classifier import classify_paper

        filtered: list[Paper] = []
        for paper in self._papers.values():
            classification = classify_paper(paper)
            if classification == subfield:
                filtered.append(paper)
        return Corpus(filtered)

    def save(self, path: Path) -> None:
        """Save corpus as a JSONL file (one JSON object per line).

        Args:
            path: File path to write the JSONL data to.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for paper in self._papers.values():
                f.write(json.dumps(paper.to_dict(), ensure_ascii=False) + "\n")
        logger.info("Saved %d papers to %s", len(self._papers), path)

    @classmethod
    def load(cls, path: Path) -> Corpus:
        """Load corpus from a JSONL file.

        Args:
            path: File path to read JSONL data from.

        Returns:
            Corpus instance populated with papers from the file.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        papers: list[Paper] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    papers.append(Paper.from_dict(data))
        logger.info("Loaded %d papers from %s", len(papers), path)
        return cls(papers)

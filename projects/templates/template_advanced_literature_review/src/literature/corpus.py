"""Unified corpus management.

Provides a Corpus class that manages collections of Paper objects with
deduplication, merging, persistence (JSONL format), and filtering
capabilities.

Deduplication is two-tiered:

1. **Canonical-ID dedup** (``add()``): papers with the same
   ``canonical_id`` (DOI-normalized, PMID, arXiv, S2, OpenAlex, or title
   hash) are merged by keeping the version with higher
   ``metadata_completeness``. This is the primary dedup path and runs
   automatically on every ``add()``.
2. **Metadata dedup** (``deduplicate_by_metadata()``): papers with the
   same ``publication_signature`` (normalized title + first-3-author
   signature) but different ``canonical_id`` values (e.g. a preprint on
   arXiv and the published version on Crossref) are collapsed, preferring
   preprints or published versions based on the ``prefer_preprints`` flag.
   This is a secondary, opt-in pass that catches cross-engine duplicates
   that escaped canonical-ID dedup because they have different identifiers.

Persistence is atomic: ``save()`` writes to a ``.jsonl.tmp`` file first,
then renames to the final path, so an interrupted write never produces a
truncated or partially-written corpus file. This mirrors the atomic-write
convention in :mod:`reproducibility.models.append_workflow_graphs` and
:mod:`literature.fulltext_download.download_fulltext`.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .models import Paper

logger = logging.getLogger(__name__)


def _preprint_rank(paper: Paper, *, prefer_preprints: bool) -> tuple[int, int, int, int, int, int]:
    return (
        int(paper.is_preprint if prefer_preprints else not paper.is_preprint),
        int(paper.doi is not None),
        int(paper.publication_date is not None),
        int(paper.metadata_completeness),
        len(paper.abstract or ""),
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

    def __init__(self, papers: list[Paper] | None = None) -> None:
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
        """Process deduplicate by metadata."""
        grouped: dict[str, list[str]] = {}
        for cid, paper in self._papers.items():
            grouped.setdefault(paper.publication_signature, []).append(cid)

        removed = 0
        for ids in grouped.values():
            if len(ids) <= 1:
                continue
            winner_id = max(
                ids,
                key=lambda cid: _preprint_rank(self._papers[cid], prefer_preprints=prefer_preprints),
            )
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

    def get(self, canonical_id: str) -> Paper | None:
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

    def summary(self) -> dict[str, int | float]:
        """Compute a quick diagnostic summary of this corpus.

        Returns:
            A dict with counts and percentages for: total papers, papers
            with DOIs, papers with abstracts, papers with authors, papers
            with year, preprints, and mean metadata completeness. Useful
            for logging after a search run or a load.
        """
        papers = self._papers.values()
        total = len(self._papers)
        if total == 0:
            return {
                "total": 0,
                "with_doi": 0,
                "with_abstract": 0,
                "with_authors": 0,
                "with_year": 0,
                "preprints": 0,
                "mean_completeness": 0.0,
            }
        with_doi = sum(1 for p in papers if p.doi)
        with_abstract = sum(1 for p in papers if p.abstract and p.abstract.strip())
        with_authors = sum(1 for p in papers if p.authors)
        with_year = sum(1 for p in papers if p.year is not None)
        preprints = sum(1 for p in papers if p.is_preprint)
        mean_completeness = sum(p.metadata_completeness for p in papers) / total
        return {
            "total": total,
            "with_doi": with_doi,
            "with_abstract": with_abstract,
            "with_authors": with_authors,
            "with_year": with_year,
            "preprints": preprints,
            "mean_completeness": round(mean_completeness, 2),
        }

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

    def filter_by_year(self, start: int | None = None, end: int | None = None) -> Corpus:
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

        Atomic write: writes to ``<path>.tmp`` first, then renames to the
        final path. An interrupted write never leaves a truncated file —
        either the old corpus or the new one is present at *path*, never a
        partial mixture.

        Args:
            path: File path to write the JSONL data to.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            for paper in self._papers.values():
                f.write(json.dumps(paper.to_dict(), ensure_ascii=False) + "\n")
        tmp.rename(path)
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
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    papers.append(Paper.from_dict(data))
        logger.info("Loaded %d papers from %s", len(papers), path)
        return cls(papers)

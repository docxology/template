"""Local JSON corpus backend."""

from __future__ import annotations

import json
import re
from pathlib import Path

from infrastructure.search.literature.base import BackendError, SearchBackend
from infrastructure.search.literature.models import Paper, SearchQuery


class LocalBackend(SearchBackend):
    """Search a JSON corpus on disk."""

    name = "local"

    def __init__(self, corpus_path: Path | str) -> None:
        self.corpus_path = Path(corpus_path)
        self._corpus: list[Paper] | None = None

    def _load(self) -> list[Paper]:
        if self._corpus is not None:
            return self._corpus
        raw = json.loads(self.corpus_path.read_text(encoding="utf-8"))
        records = raw["papers"] if isinstance(raw, dict) and "papers" in raw else raw
        if not isinstance(records, list):
            raise BackendError(f"LocalBackend corpus {self.corpus_path} must be a list or {{'papers': [...]}}")
        self._corpus = [Paper.from_dict(r) for r in records]
        return self._corpus

    def search(self, query: SearchQuery) -> list[Paper]:
        try:
            corpus = self._load()
        except (OSError, json.JSONDecodeError) as exc:
            raise BackendError(f"Cannot load corpus {self.corpus_path}: {exc}") from exc
        terms = [t.lower() for t in re.split(r"\s+", query.text.strip()) if t]
        if not terms:
            return []
        scored: list[tuple[int, Paper]] = []
        for paper in corpus:
            if not query.matches_year(paper.year):
                continue
            haystack = " ".join(
                filter(
                    None,
                    [
                        paper.title or "",
                        paper.abstract or "",
                        " ".join(paper.keywords or []),
                        " ".join(paper.authors or []),
                    ],
                )
            ).lower()
            hits = sum(1 for term in terms if term in haystack)
            if hits == 0:
                continue
            paper_copy = Paper.from_dict({**paper.to_dict(), "source": self.name})
            paper_copy.score = hits / max(1, len(terms))
            scored.append((hits, paper_copy))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [p for _, p in scored[: query.max_results]]


__all__ = ["LocalBackend"]

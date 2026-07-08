"""PDB connector — Protein Data Bank 3-D structure entries.

Queries the RCSB PDB REST API (https://search.rcsb.org).
"""

from __future__ import annotations

import json
from typing import Any

from infrastructure.search.connectors.http import ConnectorHttpClient, ConnectorHttpError
from infrastructure.search.connectors.types import (
    ConnectorDomain,
    ConnectorError,
    ConnectorHit,
    FetchOptions,
    SearchOptions,
)

_BASE_URL = "https://search.rcsb.org"
_DATA_URL = "https://data.rcsb.org"


class PDBConnector:
    """Connector for the RCSB Protein Data Bank."""

    name: str = "pdb"
    domain: ConnectorDomain = ConnectorDomain.structure
    description: str = "RCSB PDB — 3-D structures of biological macromolecules"
    base_url: str = _BASE_URL

    def __init__(
        self,
        http_client: ConnectorHttpClient | None = None,
        base_url: str = _BASE_URL,
    ) -> None:
        self._http = http_client or ConnectorHttpClient()
        self.base_url = base_url

    def search(
        self,
        query: str,
        options: SearchOptions | None = None,
    ) -> list[ConnectorHit]:
        """Search for results matching a query."""
        opts = options or SearchOptions()
        payload: dict[str, Any] = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": query},
            },
            "return_type": "entry",
            "request_options": {
                "results_verbosity": "compact",
                "paginate": {"start": 0, "rows": min(opts.max_results, 100)},
            },
        }
        params: dict[str, str] = {"json": json.dumps(payload)}
        try:
            data = self._http.get_json(f"{self.base_url}/rcsbsearch/v2/query", params)
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc

        result_set = data.get("result_set", []) if isinstance(data, dict) else []
        hits: list[ConnectorHit] = []
        for item in result_set[: opts.max_results]:
            pdb_id = item.get("identifier", "")
            score = float(item.get("score", 0.0) or 0.0)
            hit = self._minimal_hit(pdb_id, score)
            hits.append(hit)
        return hits

    def fetch(
        self,
        record_id: str,
        options: FetchOptions | None = None,
    ) -> ConnectorHit | None:
        """Fetch a resource by identifier."""
        pdb_id = record_id.removeprefix("pdb:").upper()
        try:
            data = self._http.get_json(f"{_DATA_URL}/rest/v1/core/entry/{pdb_id}")
        except ConnectorHttpError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise ConnectorError(str(exc)) from exc
        return self._parse_entry(data)

    @staticmethod
    def _minimal_hit(pdb_id: str, score: float) -> ConnectorHit:
        return ConnectorHit(
            id=f"pdb:{pdb_id}",
            title=pdb_id,
            authors=(),
            year=None,
            doi=None,
            url=f"https://www.rcsb.org/structure/{pdb_id}",
            abstract=None,
            source="pdb",
            score=score,
            extra={"pdb_id": pdb_id},
        )

    @staticmethod
    def _parse_entry(data: dict[str, Any]) -> ConnectorHit:
        pdb_id = data.get("rcsb_id", "")
        struct = data.get("struct", {}) or {}
        title = struct.get("title") or pdb_id
        citation = (data.get("citation") or [{}])[0] if data.get("citation") else {}
        authors = citation.get("rcsb_authors") or []
        year_raw = citation.get("year")
        year: int | None = None
        if year_raw:
            try:
                year = int(year_raw)
            except (TypeError, ValueError):
                pass
        doi = citation.get("pdbx_database_id_doi") or None
        return ConnectorHit(
            id=f"pdb:{pdb_id}",
            title=title,
            authors=tuple(str(a) for a in authors),
            year=year,
            doi=doi,
            url=f"https://www.rcsb.org/structure/{pdb_id}",
            abstract=struct.get("pdbx_descriptor"),
            source="pdb",
            score=0.0,
            extra={"pdb_id": pdb_id},
        )


__all__ = ["PDBConnector"]

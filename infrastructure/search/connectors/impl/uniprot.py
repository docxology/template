"""UniProt connector — protein sequences and functional information.

Queries the UniProt REST API (https://www.uniprot.org).
"""

from __future__ import annotations

from typing import Any

from infrastructure.search.connectors.http import ConnectorHttpClient, ConnectorHttpError
from infrastructure.search.connectors.types import (
    ConnectorDomain,
    ConnectorError,
    ConnectorHit,
    FetchOptions,
    SearchOptions,
)

_BASE_URL = "https://rest.uniprot.org"
_FIELDS = "accession,id,protein_name,gene_names,organism_name,length,reviewed,sequence"


class UniProtConnector:
    """Connector for the UniProt protein database."""

    name: str = "uniprot"
    domain: ConnectorDomain = ConnectorDomain.proteomics
    description: str = "UniProt — protein sequences, function, and taxonomic data"
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
        params: dict[str, str] = {
            "query": query,
            "format": "json",
            "size": str(min(opts.max_results, 500)),
            "fields": _FIELDS,
        }
        try:
            data = self._http.get_json(f"{self.base_url}/uniprotkb/search", params)
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc

        results = data.get("results", []) if isinstance(data, dict) else []
        return [self._parse_entry(item) for item in results[: opts.max_results]]

    def fetch(
        self,
        record_id: str,
        options: FetchOptions | None = None,
    ) -> ConnectorHit | None:
        """Fetch a resource by identifier."""
        accession = record_id.removeprefix("uniprot:")
        params = {"format": "json", "fields": _FIELDS}
        try:
            data = self._http.get_json(f"{self.base_url}/uniprotkb/{accession}", params)
        except ConnectorHttpError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise ConnectorError(str(exc)) from exc
        if not isinstance(data, dict) or not data:
            return None
        return self._parse_entry(data)

    @staticmethod
    def _parse_entry(item: dict[str, Any]) -> ConnectorHit:
        accession = item.get("primaryAccession") or item.get("accession", "")
        protein_desc = item.get("proteinDescription") or {}
        rec_name = protein_desc.get("recommendedName") or {}
        full_name = rec_name.get("fullName") or {}
        title = full_name.get("value") or item.get("id", accession)
        genes = item.get("genes") or []
        gene_names = [g.get("geneName", {}).get("value", "") for g in genes if isinstance(g, dict)]
        organism = (item.get("organism") or {}).get("scientificName", "")
        abstract = f"Organism: {organism}" if organism else None
        return ConnectorHit(
            id=f"uniprot:{accession}",
            title=title,
            authors=tuple(g for g in gene_names if g),
            year=None,
            doi=None,
            url=f"https://www.uniprot.org/uniprotkb/{accession}" if accession else None,
            abstract=abstract,
            source="uniprot",
            score=1.0 if item.get("reviewed") else 0.5,
            extra={
                "accession": accession,
                "length": item.get("sequence", {}).get("length") if isinstance(item.get("sequence"), dict) else None,
                "reviewed": item.get("reviewed", False),
            },
        )


__all__ = ["UniProtConnector"]

"""Zenodo REST API client (Deposit API).

See https://developers.zenodo.org/ for the official REST surface.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import requests

    _requests_available = True
except ImportError:
    requests = None  # type: ignore[assignment]
    _requests_available = False

from infrastructure.core.credentials import make_bearer_auth_headers
from infrastructure.core.exceptions import PublishingError, UploadError

from infrastructure.publishing.http_constants import REQUEST_TIMEOUT

from .config import ZenodoConfig
from .models import DepositionResult


class ZenodoClient:
    """Client for the Zenodo Deposit REST API."""

    def __init__(self, config: ZenodoConfig) -> None:
        if not _requests_available:
            raise ImportError("requests package is required for ZenodoClient")
        self.config = config
        self.headers = make_bearer_auth_headers(config.access_token)

    def create_deposition(self, metadata: dict[str, Any] | None = None) -> DepositionResult:
        """Create a new deposition and return its id and file bucket URL."""
        url = f"{self.config.api_base_url}/deposit/depositions"
        payload: dict[str, Any] = {}
        if metadata is not None:
            payload["metadata"] = metadata

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            body = response.json()
            return DepositionResult.from_zenodo_body(body)
        except requests.exceptions.RequestException as exc:
            raise PublishingError(f"Failed to create deposition: {exc}") from exc

    def upload_file(
        self,
        bucket_url: str,
        file_path: str | Path,
        *,
        object_key: str | None = None,
    ) -> None:
        """Upload a file to the deposition bucket.

        Args:
            bucket_url: Full bucket URL from ``DepositionResult.bucket_url``.
            file_path: Local file to upload.
            object_key: Remote object name; defaults to ``file_path.name``.
        """
        file_path = Path(file_path)
        key = object_key if object_key is not None else file_path.name
        url = f"{bucket_url.rstrip('/')}/{key}"

        try:
            with file_path.open("rb") as handle:
                response = requests.put(
                    url,
                    data=handle,
                    headers=self.headers,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
        except OSError as exc:
            raise UploadError(f"File access failed: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise UploadError(f"Upload failed: {exc}") from exc

    def publish(self, deposition_id: str) -> str:
        """Publish a deposition and return the assigned DOI."""
        url = f"{self.config.api_base_url}/deposit/depositions/{deposition_id}/actions/publish"

        try:
            response = requests.post(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            body = response.json()
            doi = body.get("doi") or body.get("conceptdoi")
            if not doi:
                raise PublishingError("Publication succeeded but no DOI in response")
            return str(doi)
        except requests.exceptions.RequestException as exc:
            raise PublishingError(f"Publication failed: {exc}") from exc

    def _parse_deposition_hits(self, body: Any) -> list[Any]:
        if isinstance(body, list):
            return body
        if isinstance(body, dict):
            return body.get("hits", {}).get("hits", [])
        return []

    def _search_depositions(self, query: str, *, size: int = 1) -> list[Any]:
        url = f"{self.config.api_base_url}/deposit/depositions"
        response = requests.get(
            url,
            params={"q": query, "size": size, "sort": "mostrecent"},
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return self._parse_deposition_hits(response.json())

    def _record_concept_doi(self, record: dict[str, Any]) -> str | None:
        concept = record.get("conceptdoi")
        if not concept and isinstance(record.get("metadata"), dict):
            concept = record["metadata"].get("conceptdoi")
        return str(concept) if concept else None

    def _concept_doi_from_records(self, doi: str) -> str | None:
        """Resolve a concept DOI via the records API when deposit search misses."""
        normalized = doi.strip()
        url = f"{self.config.api_base_url}/records"
        try:
            response = requests.get(
                url,
                params={"q": f"doi:{normalized}", "size": 1},
                headers=self.headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            body = response.json()
            hits = body.get("hits", {}).get("hits", []) if isinstance(body, dict) else []
            if hits:
                return self._record_concept_doi(hits[0])

            match = re.fullmatch(r"10\.5281/zenodo\.(\d+)", normalized)
            if not match:
                return None
            record_url = f"{url}/{match.group(1)}"
            record_response = requests.get(
                record_url,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT,
            )
            record_response.raise_for_status()
            return self._record_concept_doi(record_response.json())
        except requests.exceptions.RequestException:
            return None

    def resolve_deposition_id_from_doi(self, doi: str) -> str:
        """Find the latest deposition id for a published DOI."""
        normalized = doi.strip()
        queries = [f"doi:{normalized}", f"conceptdoi:{normalized}"]
        concept_doi = self._concept_doi_from_records(normalized)
        if concept_doi and concept_doi != normalized:
            queries.append(f"conceptdoi:{concept_doi}")

        try:
            for query in queries:
                hits = self._search_depositions(query)
                if not hits:
                    continue
                deposition_id = hits[0].get("id")
                if deposition_id:
                    return str(deposition_id)
            raise PublishingError(f"No deposition found for DOI {doi}")
        except requests.exceptions.RequestException as exc:
            raise PublishingError(f"Failed to resolve deposition for DOI {doi}: {exc}") from exc

    def create_new_version(self, deposition_id: str) -> DepositionResult:
        """Create a new version of an existing deposition."""
        url = f"{self.config.api_base_url}/deposit/depositions/{deposition_id}/actions/newversion"
        try:
            response = requests.post(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            body = response.json()
            return DepositionResult.from_zenodo_body(body)
        except requests.exceptions.RequestException as exc:
            raise PublishingError(f"Failed to create new version: {exc}") from exc

    def get_deposition(self, deposition_id: str) -> dict[str, Any]:
        """Return the deposition resource, including inherited draft files."""
        url = f"{self.config.api_base_url}/deposit/depositions/{deposition_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise PublishingError(f"Unexpected deposition response for {deposition_id}")
            return body
        except requests.exceptions.RequestException as exc:
            raise PublishingError(f"Failed to load deposition {deposition_id}: {exc}") from exc

    def delete_deposition_file(self, deposition_id: str, file_id: str) -> None:
        """Delete one file from an unpublished deposition."""
        url = f"{self.config.api_base_url}/deposit/depositions/{deposition_id}/files/{file_id}"
        try:
            response = requests.delete(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise PublishingError(f"Failed to delete file {file_id} from deposition {deposition_id}: {exc}") from exc

    def clear_deposition_files(self, deposition_id: str) -> list[str]:
        """Remove all files from an unpublished deposition draft.

        New-version drafts inherit prior files; clear them before uploading
        replacement artifacts so published records do not retain stale names.
        """
        body = self.get_deposition(deposition_id)
        deleted: list[str] = []
        files = body.get("files") or []
        if not isinstance(files, list):
            return deleted
        for entry in files:
            if not isinstance(entry, dict):
                continue
            file_id = entry.get("id")
            if not file_id:
                continue
            self.delete_deposition_file(deposition_id, str(file_id))
            filename = entry.get("filename")
            deleted.append(str(filename or file_id))
        return deleted

    def update_deposition_metadata(self, deposition_id: str, metadata: dict[str, Any]) -> None:
        """Update metadata on an unpublished deposition."""
        url = f"{self.config.api_base_url}/deposit/depositions/{deposition_id}"
        try:
            response = requests.put(
                url,
                json={"metadata": metadata},
                headers=self.headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise PublishingError(f"Failed to update deposition metadata: {exc}") from exc

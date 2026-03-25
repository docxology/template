"""API clients for publishing platforms (Zenodo, arXiv, GitHub)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

from infrastructure.core.exceptions import PublishingError, UploadError
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

#: Default timeout for HTTP requests (seconds)
REQUEST_TIMEOUT = 30


@dataclass
class ZenodoConfig:
    """Configuration for Zenodo API client."""
    access_token: str
    sandbox: bool = True
    base_url: str | None = None

    @property
    def api_base_url(self) -> str:
        """Return base_url if set, else sandbox or production Zenodo API endpoint."""
        if self.base_url:
            base = self.base_url.rstrip("/")
            return base if base.endswith("/api") else f"{base}/api"
        return "https://sandbox.zenodo.org/api" if self.sandbox else "https://zenodo.org/api"


class ZenodoClient:
    """Client for Zenodo API."""

    def __init__(self, config: ZenodoConfig):
        """Initialize Zenodo client with configuration."""
        if requests is None:
            raise ImportError("ZenodoClient requires the 'requests' package: pip install requests")
        self.config = config
        self.headers = {"Authorization": f"Bearer {config.access_token}"}

    def create_deposition(self, metadata: dict[str, Any]) -> str:
        """Create a new deposition.

        Returns:
            Deposition ID
        """
        url = f"{self.config.api_base_url}/deposit/depositions"
        payload = {"metadata": metadata}

        try:
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=REQUEST_TIMEOUT
            )  # noqa: E501
            response.raise_for_status()
            return str(response.json()["id"])
        except requests.exceptions.RequestException as e:
            raise PublishingError(f"Failed to create deposition: {e}") from e

    def upload_file(self, deposition_id: str, file_path: str | Path) -> None:
        """Upload file to deposition."""
        file_path = Path(file_path)
        filename = file_path.name
        # Zenodo uploads go to the deposition "bucket" endpoint:
        #   PUT {api_base_url}/files/{bucket_id}/{filename}
        # Tests pass `deposition_id` as a bucket identifier (e.g. "bucket123").
        url = f"{self.config.api_base_url}/files/{deposition_id}/{filename}"

        try:
            with open(file_path, "rb") as f:
                response = requests.put(url, data=f, headers=self.headers, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
        except OSError as e:
            raise UploadError(f"File access failed: {e}") from e
        except requests.exceptions.RequestException as e:
            raise UploadError(f"Upload failed: {e}") from e

    def publish(self, deposition_id: str) -> str:
        """Publish deposition.

        Returns:
            DOI
        """
        url = f"{self.config.api_base_url}/deposit/depositions/{deposition_id}/actions/publish"

        try:
            response = requests.post(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()["doi"]
        except requests.exceptions.RequestException as e:
            raise PublishingError(f"Publication failed: {e}") from e

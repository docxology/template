"""API clients for publishing platforms (Zenodo, arXiv, GitHub)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from infrastructure.core.exceptions import PublishingError, UploadError
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ZenodoConfig:
    access_token: str
    sandbox: bool = True
    base_url: Optional[str] = None

    @property
    def api_base_url(self) -> str:
        """Get the Zenodo API base URL.

        Returns the configured base URL if explicitly set, otherwise returns
        the appropriate Zenodo API endpoint based on the sandbox setting.

        Returns:
            str: The base URL for API requests. Either the custom base_url if
                configured, or 'https://sandbox.zenodo.org/api' for sandbox mode,
                or 'https://zenodo.org/api' for production mode.

        Example:
            >>> config = ZenodoConfig(access_token="token", sandbox=True)
            >>> config.api_base_url
            'https://sandbox.zenodo.org/api'
            >>> config = ZenodoConfig(access_token="token", sandbox=False)
            >>> config.api_base_url
            'https://zenodo.org/api'
        """
        if self.base_url:
            return self.base_url
        return (
            "https://sandbox.zenodo.org/api"
            if self.sandbox
            else "https://zenodo.org/api"
        )


class ZenodoClient:
    """Client for Zenodo API."""

    def __init__(self, config: ZenodoConfig):
        self.config = config
        self.headers = {"Authorization": f"Bearer {config.access_token}"}

    def create_deposition(self, metadata: Dict[str, Any]) -> str:
        """Create a new deposition.

        Returns:
            Deposition ID
        """
        url = f"{self.config.api_base_url}/api/deposit/depositions"
        payload = {"metadata": metadata}

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return str(response.json()["id"])
        except requests.exceptions.RequestException as e:
            raise PublishingError(f"Failed to create deposition: {e}")

    def upload_file(self, bucket: str, file_path: str) -> None:
        """Upload file to bucket."""
        filename = Path(file_path).name
        url = f"{self.config.api_base_url}/api/files/{bucket}/{filename}"

        try:
            with open(file_path, "rb") as f:
                response = requests.put(url, data=f, headers=self.headers)
                response.raise_for_status()
        except OSError as e:
            raise UploadError(f"File access failed: {e}")
        except requests.exceptions.RequestException as e:
            raise UploadError(f"Upload failed: {e}")

    def publish(self, deposition_id: str) -> str:
        """Publish deposition.

        Returns:
            DOI
        """
        url = f"{self.config.api_base_url}/api/deposit/depositions/{deposition_id}/actions/publish"

        try:
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["doi"]
        except requests.exceptions.RequestException as e:
            raise PublishingError(f"Publication failed: {e}")

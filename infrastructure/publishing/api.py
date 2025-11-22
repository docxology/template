"""API clients for publishing platforms (Zenodo, arXiv, GitHub)."""
from __future__ import annotations

import os
import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from infrastructure.core.exceptions import PublishingError, UploadError
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ZenodoConfig:
    access_token: str
    sandbox: bool = True
    
    @property
    def base_url(self) -> str:
        return "https://sandbox.zenodo.org/api" if self.sandbox else "https://zenodo.org/api"


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
        url = f"{self.config.base_url}/deposit/depositions"
        payload = {"metadata": metadata}
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return str(response.json()["id"])
        except requests.exceptions.RequestException as e:
            raise PublishingError(f"Failed to create deposition: {e}")

    def upload_file(self, deposition_id: str, file_path: str) -> None:
        """Upload file to deposition."""
        url = f"{self.config.base_url}/deposit/depositions/{deposition_id}/files"
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(url, files=files, headers=self.headers)
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
        url = f"{self.config.base_url}/deposit/depositions/{deposition_id}/actions/publish"
        
        try:
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["doi"]
        except requests.exceptions.RequestException as e:
            raise PublishingError(f"Publication failed: {e}")


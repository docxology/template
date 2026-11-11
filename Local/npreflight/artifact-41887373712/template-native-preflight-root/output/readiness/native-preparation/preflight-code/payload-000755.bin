"""Zenodo API configuration."""

from dataclasses import dataclass


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
            return self.base_url.rstrip("/")
        return "https://sandbox.zenodo.org/api" if self.sandbox else "https://zenodo.org/api"

"""GitHub release creation via the REST API."""

from __future__ import annotations

from pathlib import Path

try:
    import requests

    _requests_available = True
except ImportError:
    requests = None  # type: ignore[assignment]
    _requests_available = False

from infrastructure.core.credentials import make_token_auth_headers
from infrastructure.core.exceptions import PublishingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.http_constants import REQUEST_TIMEOUT

logger = get_logger(__name__)


def create_github_release(
    tag_name: str,
    release_name: str,
    description: str,
    assets: list[Path],
    token: str,
    repo: str,
    *,
    base_url: str = "https://api.github.com",
    target_commitish: str = "main",
) -> str:
    """Create a GitHub release with attached assets."""
    if not _requests_available:
        raise PublishingError("requests package is required for GitHub API calls")
    headers = {
        **make_token_auth_headers(token),
        "Accept": "application/vnd.github.v3+json",
    }

    url = f"{base_url}/repos/{repo}/releases"
    payload = {
        "tag_name": tag_name,
        "target_commitish": target_commitish,
        "name": release_name,
        "body": description,
        "draft": False,
        "prerelease": False,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        release_data = response.json()
        upload_url = release_data["upload_url"].split("{")[0]
        html_url = release_data["html_url"]

        for asset in assets:
            if not asset.exists():
                logger.warning(f"Skipping non-existent asset for GitHub release: {asset}")
                continue

            name = asset.name
            with asset.open("rb") as handle:
                upload_headers = headers.copy()
                upload_headers["Content-Type"] = "application/octet-stream"
                upload_resp = requests.post(
                    f"{upload_url}?name={name}",
                    headers=upload_headers,
                    data=handle,
                    timeout=REQUEST_TIMEOUT,
                )
                upload_resp.raise_for_status()

        return html_url

    except requests.exceptions.RequestException as exc:
        raise PublishingError(f"GitHub release failed: {exc}") from exc

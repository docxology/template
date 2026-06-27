from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class SiteHosting(str, Enum):
    GITHUB_PAGES = "github_pages"
    CLOUDFLARE_PAGES = "cloudflare_pages"
    NETLIFY = "netlify"


@dataclass(frozen=True)
class SiteDeployConfig:
    """Configuration for a static-site deployment."""

    hosting: SiteHosting
    site_dir: str  # local directory containing built site
    site_id: str | None = None  # Cloudflare project name / Netlify site ID
    token: str | None = None  # API token
    branch: str = "gh-pages"  # for GitHub Pages
    repo: str | None = None  # owner/repo for GitHub Pages
    production: bool = False  # False = preview/staging deploy


@dataclass(frozen=True)
class SiteDeployResult:
    """Result of a static-site deploy attempt."""

    hosting: str
    status: str  # "ok" | "error" | "dry-run"
    url: str | None = None
    deploy_id: str | None = None
    error: str | None = None
    timestamp_utc: str | None = None
    extra: dict[str, str] = field(default_factory=dict)

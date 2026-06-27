"""Static-site hosting adapters (GitHub Pages, Cloudflare Pages, Netlify)."""

from .models import SiteDeployConfig, SiteDeployResult, SiteHosting
from .github_pages import GitHubPagesAdapter
from .cloudflare_pages import CloudflarePagesAdapter
from .netlify import NetlifyAdapter
from .registry import STATIC_SITE_ADAPTERS, get_adapter

__all__ = [
    "SiteDeployConfig",
    "SiteDeployResult",
    "SiteHosting",
    "GitHubPagesAdapter",
    "CloudflarePagesAdapter",
    "NetlifyAdapter",
    "STATIC_SITE_ADAPTERS",
    "get_adapter",
]

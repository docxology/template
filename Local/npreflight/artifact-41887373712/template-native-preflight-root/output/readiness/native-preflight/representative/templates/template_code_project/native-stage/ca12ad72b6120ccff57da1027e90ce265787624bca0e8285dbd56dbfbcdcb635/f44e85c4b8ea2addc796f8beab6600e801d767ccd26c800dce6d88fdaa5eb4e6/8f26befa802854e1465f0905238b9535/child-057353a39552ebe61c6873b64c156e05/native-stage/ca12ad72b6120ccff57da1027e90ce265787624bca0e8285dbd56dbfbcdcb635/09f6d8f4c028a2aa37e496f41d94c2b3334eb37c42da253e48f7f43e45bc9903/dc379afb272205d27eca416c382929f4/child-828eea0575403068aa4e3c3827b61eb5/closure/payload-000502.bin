"""Registry of available static-site adapters."""

from __future__ import annotations

from .cloudflare_pages import CloudflarePagesAdapter
from .github_pages import GitHubPagesAdapter
from .models import SiteDeployConfig, SiteHosting
from .netlify import NetlifyAdapter

StaticSiteAdapter = GitHubPagesAdapter | CloudflarePagesAdapter | NetlifyAdapter

STATIC_SITE_ADAPTERS: dict[SiteHosting, type[StaticSiteAdapter]] = {
    SiteHosting.GITHUB_PAGES: GitHubPagesAdapter,
    SiteHosting.CLOUDFLARE_PAGES: CloudflarePagesAdapter,
    SiteHosting.NETLIFY: NetlifyAdapter,
}


def get_adapter(
    config: SiteDeployConfig,
) -> GitHubPagesAdapter | CloudflarePagesAdapter | NetlifyAdapter:
    """Return the right adapter instance for config.hosting."""
    cls = STATIC_SITE_ADAPTERS.get(config.hosting)
    if cls is None:
        raise ValueError(f"Unknown hosting: {config.hosting!r}")
    return cls(config)

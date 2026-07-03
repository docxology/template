"""Backwards-compatible platform integration re-exports."""

from infrastructure.publishing.arxiv.submission import prepare_arxiv_submission
from infrastructure.publishing.github.release import create_github_release
from infrastructure.publishing.zenodo.publish import publish_to_zenodo
from infrastructure.publishing.pypi.adapter import PyPIAdapter
from infrastructure.publishing.pypi.build import build_dist
from infrastructure.publishing.pypi.upload import upload_dist, check_dist
from infrastructure.publishing.static_site import (
    GitHubPagesAdapter,
    CloudflarePagesAdapter,
    NetlifyAdapter,
    get_adapter as get_static_site_adapter,
    SiteDeployConfig,
    SiteDeployResult,
    SiteHosting,
)
from infrastructure.publishing.huggingface import (
    HuggingFaceHubAdapter,
    HuggingFaceConfig,
    HuggingFaceResult,
    HFRepoType,
)
from infrastructure.publishing.osf import OSFAdapter, OSFConfig, OSFResult
from infrastructure.publishing.archival import (
    archive_publication,
    load_credentials,
    ArchivalProvider,
    ArchivalReceipt,
    ArchivalRun,
)

# ── Documented ebook / retail platform names ──────────────────────────────────
# These platforms are catalogued in the PLATFORM_REGISTRY at DOCUMENTED tier.
# Adapters are not yet implemented; the names are listed here for discoverability
# via `from infrastructure.publishing.platforms import DOCUMENTED_EBOOK_PLATFORMS`.
DOCUMENTED_EBOOK_PLATFORMS: tuple[str, ...] = (
    "amazon_kdp",
    "google_play_books",
    "gumroad",
    "leanpub",
    "lulu",
    "draft2digital",
    "stripe",
    "ingramspark",
)

__all__ = [
    "create_github_release",
    "prepare_arxiv_submission",
    "publish_to_zenodo",
    "PyPIAdapter",
    "build_dist",
    "upload_dist",
    "check_dist",
    "GitHubPagesAdapter",
    "CloudflarePagesAdapter",
    "NetlifyAdapter",
    "get_static_site_adapter",
    "SiteDeployConfig",
    "SiteDeployResult",
    "SiteHosting",
    "HuggingFaceHubAdapter",
    "HuggingFaceConfig",
    "HuggingFaceResult",
    "HFRepoType",
    "OSFAdapter",
    "OSFConfig",
    "OSFResult",
    "archive_publication",
    "load_credentials",
    "ArchivalProvider",
    "ArchivalReceipt",
    "ArchivalRun",
    # Documented ebook platforms
    "DOCUMENTED_EBOOK_PLATFORMS",
]

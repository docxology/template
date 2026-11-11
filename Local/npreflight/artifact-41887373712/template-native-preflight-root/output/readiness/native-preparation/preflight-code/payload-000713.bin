"""Central registry of all publishing platform adapters.

This is the single source of truth for the publishing surface. Import from here
to discover which platforms are available (first-class vs documented), what
credentials they need, and how to instantiate their adapters.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class PublishingTier(str, Enum):
    """Data container for PublishingTier."""

    FIRST_CLASS = "first_class"  # implemented, tested, locally verifiable
    DOCUMENTED = "documented"  # documented intent, no live adapter yet


@dataclass(frozen=True)
class PlatformInfo:
    """Metadata about a publishing platform adapter."""

    name: str
    tier: PublishingTier
    description: str
    adapter_module: str  # importable module path
    adapter_class: str | None  # class name if applicable
    env_vars: tuple[str, ...] = field(default_factory=tuple)
    requires_network: bool = True
    supports_dry_run: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)


PLATFORM_REGISTRY: tuple[PlatformInfo, ...] = (
    PlatformInfo(
        name="zenodo",
        tier=PublishingTier.FIRST_CLASS,
        description="CERN-backed long-term archival with DOI assignment",
        adapter_module="infrastructure.publishing.zenodo.publish",
        adapter_class="ZenodoProvider",
        env_vars=("ZENODO_API_TOKEN",),
        tags=("archival", "doi", "academic"),
    ),
    PlatformInfo(
        name="github",
        tier=PublishingTier.FIRST_CLASS,
        description="GitHub Releases with asset upload",
        adapter_module="infrastructure.publishing.github.release",
        adapter_class=None,
        env_vars=("GITHUB_TOKEN",),
        tags=("release", "software"),
    ),
    PlatformInfo(
        name="arxiv",
        tier=PublishingTier.FIRST_CLASS,
        description="arXiv preprint submission tarball preparation",
        adapter_module="infrastructure.publishing.arxiv.submission",
        adapter_class=None,
        env_vars=(),
        requires_network=False,
        tags=("academic", "preprint"),
    ),
    PlatformInfo(
        name="pypi",
        tier=PublishingTier.FIRST_CLASS,
        description="PyPI / TestPyPI package distribution via uv + twine",
        adapter_module="infrastructure.publishing.pypi.adapter",
        adapter_class="PyPIAdapter",
        env_vars=("PYPI_TOKEN", "TESTPYPI_TOKEN"),
        tags=("package", "software"),
    ),
    PlatformInfo(
        name="ipfs_pinata",
        tier=PublishingTier.FIRST_CLASS,
        description="Content-addressed IPFS pinning via Pinata",
        adapter_module="infrastructure.publishing.archival.providers",
        adapter_class="IPFSPinataProvider",
        env_vars=("PINATA_JWT",),
        tags=("archival", "ipfs", "decentralized"),
    ),
    PlatformInfo(
        name="ipfs_web3storage",
        tier=PublishingTier.FIRST_CLASS,
        description="Content-addressed IPFS pinning via Web3.Storage",
        adapter_module="infrastructure.publishing.archival.providers",
        adapter_class="IPFSWeb3StorageProvider",
        env_vars=("WEB3_STORAGE_TOKEN",),
        tags=("archival", "ipfs", "decentralized"),
    ),
    PlatformInfo(
        name="software_heritage",
        tier=PublishingTier.FIRST_CLASS,
        description="Software Heritage save-code-now for Git repositories",
        adapter_module="infrastructure.publishing.archival.providers",
        adapter_class="SoftwareHeritageProvider",
        env_vars=(),
        tags=("archival", "source-code"),
    ),
    PlatformInfo(
        name="github_pages",
        tier=PublishingTier.FIRST_CLASS,
        description="GitHub Pages static-site deployment via gh-pages branch",
        adapter_module="infrastructure.publishing.static_site.github_pages",
        adapter_class="GitHubPagesAdapter",
        env_vars=("GITHUB_TOKEN",),
        tags=("static_site", "docs"),
    ),
    PlatformInfo(
        name="cloudflare_pages",
        tier=PublishingTier.FIRST_CLASS,
        description="Cloudflare Pages deployment via Wrangler CLI",
        adapter_module="infrastructure.publishing.static_site.cloudflare_pages",
        adapter_class="CloudflarePagesAdapter",
        env_vars=("CLOUDFLARE_API_TOKEN",),
        tags=("static_site", "hosting"),
    ),
    PlatformInfo(
        name="netlify",
        tier=PublishingTier.FIRST_CLASS,
        description="Netlify deployment via netlify CLI",
        adapter_module="infrastructure.publishing.static_site.netlify",
        adapter_class="NetlifyAdapter",
        env_vars=("NETLIFY_AUTH_TOKEN",),
        tags=("static_site", "hosting"),
    ),
    PlatformInfo(
        name="huggingface_hub",
        tier=PublishingTier.FIRST_CLASS,
        description="HuggingFace Hub dataset / model / space publishing via the Hub REST API",
        adapter_module="infrastructure.publishing.huggingface.adapter",
        adapter_class="HuggingFaceHubAdapter",
        env_vars=("HUGGINGFACE_TOKEN", "HF_TOKEN"),
        tags=("ml", "dataset"),
    ),
    PlatformInfo(
        name="osf",
        tier=PublishingTier.FIRST_CLASS,
        description="Open Science Framework node creation + file deposit via OSF API v2 / Waterbutler",
        adapter_module="infrastructure.publishing.osf.adapter",
        adapter_class="OSFAdapter",
        env_vars=("OSF_TOKEN",),
        tags=("academic", "open-science"),
    ),
    # ── DOCUMENTED tier: ebook retail + distribution channels ─────────────────
    PlatformInfo(
        name="amazon_kdp",
        tier=PublishingTier.DOCUMENTED,
        description="Amazon Kindle Direct Publishing — ebook and print-on-demand via KDP dashboard",
        adapter_module="infrastructure.publishing.ebook.amazon_kdp",
        adapter_class="AmazonKDPAdapter",
        env_vars=("AMAZON_KDP_EMAIL", "AMAZON_KDP_PASSWORD"),
        requires_network=True,
        supports_dry_run=True,
        tags=("ebook", "print", "retail", "kindle"),
    ),
    PlatformInfo(
        name="google_play_books",
        tier=PublishingTier.DOCUMENTED,
        description="Google Play Books partner content upload via the Play Books Partner API",
        adapter_module="infrastructure.publishing.ebook.google_play_books",
        adapter_class="GooglePlayBooksAdapter",
        env_vars=("GOOGLE_PLAY_BOOKS_SERVICE_ACCOUNT_JSON",),
        requires_network=True,
        supports_dry_run=True,
        tags=("ebook", "retail"),
    ),
    PlatformInfo(
        name="gumroad",
        tier=PublishingTier.DOCUMENTED,
        description="Gumroad direct-sale product creation and file upload via Gumroad API v2",
        adapter_module="infrastructure.publishing.ebook.gumroad",
        adapter_class="GumroadAdapter",
        env_vars=("GUMROAD_ACCESS_TOKEN",),
        requires_network=True,
        supports_dry_run=True,
        tags=("ebook", "direct-sale", "payment"),
    ),
    PlatformInfo(
        name="leanpub",
        tier=PublishingTier.DOCUMENTED,
        description="Leanpub book publishing and preview generation via Leanpub API",
        adapter_module="infrastructure.publishing.ebook.leanpub",
        adapter_class="LeanpubAdapter",
        env_vars=("LEANPUB_API_KEY",),
        requires_network=True,
        supports_dry_run=True,
        tags=("ebook", "self-publishing"),
    ),
    PlatformInfo(
        name="lulu",
        tier=PublishingTier.DOCUMENTED,
        description="Lulu print-on-demand book creation and order fulfilment via Lulu Direct API",
        adapter_module="infrastructure.publishing.ebook.lulu",
        adapter_class="LuluAdapter",
        env_vars=("LULU_CLIENT_KEY", "LULU_CLIENT_SECRET"),
        requires_network=True,
        supports_dry_run=True,
        tags=("print", "print-on-demand", "distribution"),
    ),
    PlatformInfo(
        name="draft2digital",
        tier=PublishingTier.DOCUMENTED,
        description="Draft2Digital ebook distribution to 40+ retailers via D2D API",
        adapter_module="infrastructure.publishing.ebook.draft2digital",
        adapter_class="Draft2DigitalAdapter",
        env_vars=("DRAFT2DIGITAL_API_TOKEN",),
        requires_network=True,
        supports_dry_run=True,
        tags=("ebook", "distribution", "aggregator"),
    ),
    PlatformInfo(
        name="stripe",
        tier=PublishingTier.DOCUMENTED,
        description="Stripe payment processing for direct ebook sales (product + price + payment link)",
        adapter_module="infrastructure.publishing.ebook.stripe_adapter",
        adapter_class="StripeAdapter",
        env_vars=("STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY"),
        requires_network=True,
        supports_dry_run=True,
        tags=("payment", "direct-sale", "e-commerce"),
    ),
    PlatformInfo(
        name="ingramspark",
        tier=PublishingTier.DOCUMENTED,
        description="IngramSpark print and ebook distribution to 40,000+ retailers and libraries",
        adapter_module="infrastructure.publishing.ebook.ingramspark",
        adapter_class="IngramSparkAdapter",
        env_vars=("INGRAMSPARK_CLIENT_ID", "INGRAMSPARK_CLIENT_SECRET"),
        requires_network=True,
        supports_dry_run=True,
        tags=("print", "ebook", "distribution", "aggregator"),
    ),
)


def list_platforms(
    *,
    tier: PublishingTier | None = None,
    tag: str | None = None,
) -> tuple[PlatformInfo, ...]:
    """Return platforms, optionally filtered by tier or tag."""
    result = PLATFORM_REGISTRY
    if tier is not None:
        result = tuple(p for p in result if p.tier == tier)
    if tag is not None:
        result = tuple(p for p in result if tag in p.tags)
    return result


def get_platform(name: str) -> PlatformInfo:
    """Return PlatformInfo by name. Raises KeyError if not found."""
    for p in PLATFORM_REGISTRY:
        if p.name == name:
            return p
    raise KeyError(f"Unknown platform: {name!r}. Available: {[p.name for p in PLATFORM_REGISTRY]}")


def first_class_platforms() -> tuple[PlatformInfo, ...]:
    """Return only first-class (implemented) platforms."""
    return list_platforms(tier=PublishingTier.FIRST_CLASS)


def documented_platforms() -> tuple[PlatformInfo, ...]:
    """Return only documented (future) platforms."""
    return list_platforms(tier=PublishingTier.DOCUMENTED)

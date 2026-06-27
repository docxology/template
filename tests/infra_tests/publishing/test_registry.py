"""Tests for infrastructure.publishing.registry.

Validates the platform registry's structure, filtering helpers, and
invariants that every entry in the registry must satisfy. No network
calls; all tests are deterministic.
"""

from __future__ import annotations

import pytest

from infrastructure.publishing.registry import (
    PLATFORM_REGISTRY,
    PlatformInfo,
    PublishingTier,
    documented_platforms,
    first_class_platforms,
    get_platform,
    list_platforms,
)


# ---------------------------------------------------------------------------
# 1. Registry completeness — expected platform names are present
# ---------------------------------------------------------------------------

_EXPECTED_PLATFORMS = {
    "zenodo",
    "github",
    "arxiv",
    "pypi",
    "ipfs_pinata",
    "ipfs_web3storage",
    "software_heritage",
    "github_pages",
    "cloudflare_pages",
    "netlify",
    "huggingface_hub",
    "osf",
}


def test_registry_has_expected_platforms() -> None:
    """list_platforms() must include every platform listed in the expected set."""
    registered_names = {p.name for p in list_platforms()}
    missing = _EXPECTED_PLATFORMS - registered_names
    assert not missing, f"Missing from registry: {missing}"


def test_registry_has_no_duplicate_names() -> None:
    """Every platform name in the registry must be unique."""
    names = [p.name for p in PLATFORM_REGISTRY]
    assert len(names) == len(set(names)), "Duplicate platform names detected"


# ---------------------------------------------------------------------------
# 2. first_class_platforms()
# ---------------------------------------------------------------------------

_FIRST_CLASS_NAMES = {
    "zenodo",
    "github",
    "arxiv",
    "pypi",
    "ipfs_pinata",
    "ipfs_web3storage",
    "software_heritage",
    "github_pages",
    "cloudflare_pages",
    "netlify",
}


def test_first_class_platforms_all_implemented() -> None:
    """Every FIRST_CLASS platform must have a non-empty adapter_module."""
    for p in first_class_platforms():
        assert p.adapter_module, f"{p.name}: adapter_module must not be empty"


def test_first_class_platforms_includes_expected() -> None:
    """first_class_platforms() must include all known first-class platforms."""
    fc_names = {p.name for p in first_class_platforms()}
    missing = _FIRST_CLASS_NAMES - fc_names
    assert not missing, f"Missing from first-class: {missing}"


def test_first_class_platforms_no_documented_entries() -> None:
    """first_class_platforms() must not include any DOCUMENTED-tier entries."""
    for p in first_class_platforms():
        assert p.tier == PublishingTier.FIRST_CLASS, (
            f"{p.name} has tier {p.tier!r}, expected FIRST_CLASS"
        )


# ---------------------------------------------------------------------------
# 3. documented_platforms()
# ---------------------------------------------------------------------------

_DOCUMENTED_NAMES = {"huggingface_hub", "osf"}


def test_documented_platforms_exist() -> None:
    """documented_platforms() must be non-empty."""
    assert len(documented_platforms()) > 0


def test_documented_platforms_are_only_documented_tier() -> None:
    """Every entry returned by documented_platforms() must be DOCUMENTED tier."""
    for p in documented_platforms():
        assert p.tier == PublishingTier.DOCUMENTED, (
            f"{p.name} has tier {p.tier!r}, expected DOCUMENTED"
        )


def test_documented_platforms_includes_expected() -> None:
    """documented_platforms() must include all known documented platforms."""
    doc_names = {p.name for p in documented_platforms()}
    missing = _DOCUMENTED_NAMES - doc_names
    assert not missing, f"Missing from documented: {missing}"


# ---------------------------------------------------------------------------
# 4. get_platform()
# ---------------------------------------------------------------------------


def test_get_platform_known_zenodo() -> None:
    """get_platform('zenodo') returns a PlatformInfo with name='zenodo'."""
    info = get_platform("zenodo")
    assert isinstance(info, PlatformInfo)
    assert info.name == "zenodo"


def test_get_platform_known_github() -> None:
    """get_platform('github') returns a FIRST_CLASS PlatformInfo."""
    info = get_platform("github")
    assert info.name == "github"
    assert info.tier == PublishingTier.FIRST_CLASS


def test_get_platform_known_arxiv() -> None:
    """get_platform('arxiv') returns a platform that does not require a network call."""
    info = get_platform("arxiv")
    assert info.requires_network is False


def test_get_platform_known_huggingface_hub() -> None:
    """get_platform('huggingface_hub') returns a DOCUMENTED platform."""
    info = get_platform("huggingface_hub")
    assert info.tier == PublishingTier.DOCUMENTED


def test_get_platform_unknown_raises_key_error() -> None:
    """get_platform with an unknown name must raise KeyError."""
    with pytest.raises(KeyError, match="nonexistent"):
        get_platform("nonexistent")


def test_get_platform_empty_string_raises_key_error() -> None:
    """get_platform with an empty string must raise KeyError."""
    with pytest.raises(KeyError):
        get_platform("")


# ---------------------------------------------------------------------------
# 5. list_platforms() filtering
# ---------------------------------------------------------------------------


def test_list_platforms_no_filter_returns_all() -> None:
    """list_platforms() with no arguments returns all registered platforms."""
    assert len(list_platforms()) == len(PLATFORM_REGISTRY)


def test_list_platforms_by_first_class_tier() -> None:
    """list_platforms(tier=FIRST_CLASS) returns only FIRST_CLASS entries."""
    result = list_platforms(tier=PublishingTier.FIRST_CLASS)
    assert len(result) > 0
    for p in result:
        assert p.tier == PublishingTier.FIRST_CLASS


def test_list_platforms_by_documented_tier() -> None:
    """list_platforms(tier=DOCUMENTED) returns only DOCUMENTED entries."""
    result = list_platforms(tier=PublishingTier.DOCUMENTED)
    assert len(result) > 0
    for p in result:
        assert p.tier == PublishingTier.DOCUMENTED


def test_list_platforms_first_class_and_documented_partition_registry() -> None:
    """FIRST_CLASS + DOCUMENTED must cover the entire registry."""
    fc = set(p.name for p in list_platforms(tier=PublishingTier.FIRST_CLASS))
    doc = set(p.name for p in list_platforms(tier=PublishingTier.DOCUMENTED))
    all_names = set(p.name for p in PLATFORM_REGISTRY)
    assert fc | doc == all_names
    assert fc & doc == set()


def test_list_platforms_by_tag_archival() -> None:
    """list_platforms(tag='archival') must include zenodo, ipfs_pinata, software_heritage."""
    result = list_platforms(tag="archival")
    names = {p.name for p in result}
    assert "zenodo" in names
    assert "ipfs_pinata" in names
    assert "software_heritage" in names


def test_list_platforms_by_tag_doi() -> None:
    """list_platforms(tag='doi') must include zenodo."""
    result = list_platforms(tag="doi")
    names = {p.name for p in result}
    assert "zenodo" in names


def test_list_platforms_by_tag_academic() -> None:
    """list_platforms(tag='academic') must include zenodo and arxiv."""
    result = list_platforms(tag="academic")
    names = {p.name for p in result}
    assert "zenodo" in names
    assert "arxiv" in names


def test_list_platforms_by_tag_software() -> None:
    """list_platforms(tag='software') must include github and pypi."""
    result = list_platforms(tag="software")
    names = {p.name for p in result}
    assert "github" in names
    assert "pypi" in names


def test_list_platforms_by_tag_static_site() -> None:
    """list_platforms(tag='static_site') must include github_pages."""
    result = list_platforms(tag="static_site")
    names = {p.name for p in result}
    assert "github_pages" in names


def test_list_platforms_by_tag_and_tier_combined() -> None:
    """Combining tag and tier filters both at once."""
    result = list_platforms(tag="archival", tier=PublishingTier.FIRST_CLASS)
    for p in result:
        assert "archival" in p.tags
        assert p.tier == PublishingTier.FIRST_CLASS


def test_list_platforms_unknown_tag_returns_empty() -> None:
    """list_platforms with a tag that no platform has returns an empty tuple."""
    result = list_platforms(tag="zzz_unknown_tag_xyz")
    assert result == ()


# ---------------------------------------------------------------------------
# 6. Registry invariants across all entries
# ---------------------------------------------------------------------------


def test_all_platforms_have_non_empty_name() -> None:
    """Every PlatformInfo must have a non-empty name field."""
    for p in PLATFORM_REGISTRY:
        assert p.name, f"Empty name found in registry entry: {p!r}"


def test_all_platforms_have_non_empty_description() -> None:
    """Every PlatformInfo must have a non-empty description field."""
    for p in PLATFORM_REGISTRY:
        assert p.description, f"{p.name}: description must not be empty"


def test_all_platforms_have_valid_tier() -> None:
    """Every platform's tier must be a valid PublishingTier enum member."""
    valid_tiers = set(PublishingTier)
    for p in PLATFORM_REGISTRY:
        assert p.tier in valid_tiers, f"{p.name}: invalid tier {p.tier!r}"


def test_all_platforms_have_non_empty_adapter_module() -> None:
    """Every PlatformInfo must have an adapter_module (even for DOCUMENTED)."""
    for p in PLATFORM_REGISTRY:
        assert p.adapter_module, f"{p.name}: adapter_module must not be empty"


def test_all_first_class_support_dry_run() -> None:
    """Every FIRST_CLASS platform must have supports_dry_run=True."""
    for p in first_class_platforms():
        assert p.supports_dry_run is True, (
            f"{p.name}: FIRST_CLASS platforms must support dry_run"
        )


def test_all_platforms_env_vars_are_tuples_of_strings() -> None:
    """env_vars must be a tuple of strings for every registry entry."""
    for p in PLATFORM_REGISTRY:
        assert isinstance(p.env_vars, tuple), f"{p.name}: env_vars must be a tuple"
        for var in p.env_vars:
            assert isinstance(var, str), (
                f"{p.name}: each env_var must be a string, got {type(var)}"
            )


def test_all_platforms_tags_are_tuples_of_strings() -> None:
    """tags must be a tuple of strings for every registry entry."""
    for p in PLATFORM_REGISTRY:
        assert isinstance(p.tags, tuple), f"{p.name}: tags must be a tuple"
        for tag in p.tags:
            assert isinstance(tag, str), (
                f"{p.name}: each tag must be a string, got {type(tag)}"
            )


def test_all_platforms_boolean_flags_are_bool() -> None:
    """requires_network and supports_dry_run must be actual booleans."""
    for p in PLATFORM_REGISTRY:
        assert isinstance(p.requires_network, bool), (
            f"{p.name}: requires_network must be bool"
        )
        assert isinstance(p.supports_dry_run, bool), (
            f"{p.name}: supports_dry_run must be bool"
        )


# ---------------------------------------------------------------------------
# 7. PlatformInfo immutability
# ---------------------------------------------------------------------------


def test_platform_info_immutable_name() -> None:
    """Attempting to mutate name on a PlatformInfo must raise an error."""
    info = get_platform("zenodo")
    with pytest.raises((AttributeError, TypeError)):
        info.name = "other"  # type: ignore[misc]


def test_platform_info_immutable_tier() -> None:
    """Attempting to mutate tier on a PlatformInfo must raise an error."""
    info = get_platform("zenodo")
    with pytest.raises((AttributeError, TypeError)):
        info.tier = PublishingTier.DOCUMENTED  # type: ignore[misc]


def test_platform_info_immutable_description() -> None:
    """Attempting to mutate description on a PlatformInfo must raise an error."""
    info = get_platform("github")
    with pytest.raises((AttributeError, TypeError)):
        info.description = "overwritten"  # type: ignore[misc]


def test_platform_info_frozen_dataclass_identity() -> None:
    """PlatformInfo instances are frozen; two reads of the same entry compare equal."""
    a = get_platform("arxiv")
    b = get_platform("arxiv")
    assert a == b


# ---------------------------------------------------------------------------
# 8. PublishingTier enum
# ---------------------------------------------------------------------------


def test_publishing_tier_has_two_values() -> None:
    """PublishingTier must define exactly FIRST_CLASS and DOCUMENTED."""
    names = {t.name for t in PublishingTier}
    assert names == {"FIRST_CLASS", "DOCUMENTED"}


def test_publishing_tier_string_values() -> None:
    """PublishingTier values must be the lowercase strings used in the registry."""
    assert PublishingTier.FIRST_CLASS.value == "first_class"
    assert PublishingTier.DOCUMENTED.value == "documented"


def test_publishing_tier_is_str_subclass() -> None:
    """PublishingTier extends str; members must compare equal to their value."""
    assert PublishingTier.FIRST_CLASS == "first_class"
    assert PublishingTier.DOCUMENTED == "documented"


# ---------------------------------------------------------------------------
# 9. Specific platform spot-checks
# ---------------------------------------------------------------------------


def test_zenodo_platform_info_fields() -> None:
    """zenodo platform must have expected env_vars and tags."""
    info = get_platform("zenodo")
    assert "ZENODO_API_TOKEN" in info.env_vars
    assert "archival" in info.tags
    assert "doi" in info.tags
    assert info.requires_network is True
    assert info.supports_dry_run is True


def test_arxiv_platform_no_network() -> None:
    """arxiv submission preparation is local; requires_network must be False."""
    info = get_platform("arxiv")
    assert info.requires_network is False
    assert "academic" in info.tags
    assert "preprint" in info.tags


def test_ipfs_pinata_platform_info() -> None:
    """ipfs_pinata must reference the archival providers module."""
    info = get_platform("ipfs_pinata")
    assert "archival" in info.adapter_module
    assert info.adapter_class == "IPFSPinataProvider"
    assert "PINATA_JWT" in info.env_vars


def test_software_heritage_no_required_env_vars() -> None:
    """software_heritage does not require credentials for public repos."""
    info = get_platform("software_heritage")
    assert info.env_vars == ()


def test_github_pages_adapter_module_set() -> None:
    """github_pages must have a non-empty adapter_module and adapter_class."""
    info = get_platform("github_pages")
    assert info.adapter_module
    assert info.adapter_class == "GitHubPagesAdapter"
    assert "static_site" in info.tags


def test_huggingface_hub_is_documented_tier() -> None:
    """huggingface_hub is a future adapter; must be DOCUMENTED tier."""
    info = get_platform("huggingface_hub")
    assert info.tier == PublishingTier.DOCUMENTED
    assert "HUGGINGFACE_TOKEN" in info.env_vars


def test_osf_is_documented_tier() -> None:
    """osf is a future adapter; must be DOCUMENTED tier."""
    info = get_platform("osf")
    assert info.tier == PublishingTier.DOCUMENTED
    assert "OSF_TOKEN" in info.env_vars

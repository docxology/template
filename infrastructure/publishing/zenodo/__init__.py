"""Zenodo REST API integration."""

from .client import REQUEST_TIMEOUT, ZenodoClient
from .config import ZenodoConfig
from .models import DepositionResult, PublishResult
from .publish import (
    deposition_metadata_dict,
    patch_deposition_description,
    publish_new_version_to_zenodo,
    publish_reserved_deposition_to_zenodo,
    publish_to_zenodo,
    reserve_zenodo_deposition,
)

__all__ = [
    "DepositionResult",
    "PublishResult",
    "REQUEST_TIMEOUT",
    "ZenodoClient",
    "ZenodoConfig",
    "deposition_metadata_dict",
    "patch_deposition_description",
    "publish_new_version_to_zenodo",
    "publish_reserved_deposition_to_zenodo",
    "publish_to_zenodo",
    "reserve_zenodo_deposition",
]

"""Receipt DATA must bind to the independently selected SDK patch version."""

from __future__ import annotations

import base64
import hashlib
import json

import pytest

from infrastructure import __version__
from infrastructure.project.installed_domain_acceptance import (
    AUTOPOIESIS_DOMAINS,
    AUTOPOIESIS_SCHEMA,
    validate_autopoiesis_observation,
)


def _observation(platform_version: str) -> dict:
    receipt = {
        "schema_version": "autopoiesis/selected-child-execution/2",
        "status": "passed",
        "mode": "core",
        "selection_scope": "one-per-selected-domain",
        "selected_count": len(AUTOPOIESIS_DOMAINS),
        "platform_version": platform_version,
    }
    body = json.dumps(receipt).encode()
    return {
        "schema_version": AUTOPOIESIS_SCHEMA,
        "receipt": {"sha256": hashlib.sha256(body).hexdigest(), "content_base64": base64.b64encode(body).decode()},
    }


def test_receipt_with_matching_version_still_requires_real_distribution_custody() -> None:
    with pytest.raises(ValueError, match="genuine fresh distribution custody"):
        validate_autopoiesis_observation(_observation(__version__))


@pytest.mark.parametrize("version", ("3.8.0", "4.999.999", "", None))
def test_other_patch_receipt_cannot_substitute_for_selected_sdk(version: str) -> None:
    assert version != __version__
    with pytest.raises(ValueError, match="omitted its required selected-child execution"):
        validate_autopoiesis_observation(_observation(version))

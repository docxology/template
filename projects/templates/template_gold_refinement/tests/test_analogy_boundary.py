"""Tests for the bounded analogy theorem and its negative control."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from analogy_boundary import analogy_boundary_theorem, validate_analogy_boundary
from domain_adapter import load_domain_profile

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_live_domain_profile_satisfies_local_boundary_theorem() -> None:
    profile = load_domain_profile(PROJECT_ROOT)
    assert analogy_boundary_theorem(profile)
    receipt = validate_analogy_boundary(profile)
    assert receipt["status"] == "pass"
    assert receipt["scope"] == "local source-owned analogy boundary"


def test_boundary_without_non_claims_cannot_pass() -> None:
    profile = load_domain_profile(PROJECT_ROOT)
    broken = replace(profile, analogy_boundary_non_claims=())
    assert not analogy_boundary_theorem(broken)
    with pytest.raises(ValueError, match="analogy boundary requires"):
        validate_analogy_boundary(broken)

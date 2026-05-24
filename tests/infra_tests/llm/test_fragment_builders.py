"""Tests for infrastructure/llm/prompts/_fragment_builders.py.

Covers: build_fragment, build_format_requirements, build_content_requirements,
build_section_structure, build_token_budget_awareness, build_validation_hints.

No mocks used -- all tests use real PromptFragmentLoader and JSON fragment files.
"""

from __future__ import annotations

import pytest

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.prompts.loader import PromptFragmentLoader
from infrastructure.llm.prompts._fragment_builders import (
    build_fragment,
    build_format_requirements,
    build_content_requirements,
    build_section_structure,
    build_token_budget_awareness,
    build_validation_hints,
)


@pytest.fixture
def loader():
    """Create a PromptFragmentLoader using the real fragment directory."""
    return PromptFragmentLoader()


class TestBuildFragment:
    """Test the build_fragment dispatch function."""

    def test_section_structure_dispatch(self, loader):
        template = {}
        result = build_fragment(
            loader, "section_structures.json#executive_summary", template, None
        )
        assert "SECTION STRUCTURE:" in result

    def test_format_requirements_dispatch(self, loader):
        template = {
            "section_config": {"headers": ["## Overview", "## Methods"]}
        }
        result = build_fragment(loader, "format_requirements", template, None)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_content_requirements_dispatch(self, loader):
        template = {}
        result = build_fragment(loader, "content_requirements", template, None)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_token_budget_dispatch(self, loader):
        template = {"section_config": {"sections": 3}}
        result = build_fragment(
            loader, "token_budget_awareness", template, 2000
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_token_budget_default_max_tokens(self, loader):
        template = {"section_config": {"sections": 2}}
        result = build_fragment(
            loader, "token_budget_awareness", template, None
        )
        assert isinstance(result, str)

    def test_validation_hints_dispatch(self, loader):
        template = {
            "variables": {
                "word_count_range": [100, 500],
                "required_elements": ["heading", "conclusion"],
            }
        }
        result = build_fragment(loader, "validation_hints", template, None)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_default_fragment_load(self, loader):
        # Loading a known fragment directly
        result = build_fragment(
            loader, "system_prompts.json#manuscript_review", {}, None
        )
        assert isinstance(result, str)


class TestBuildFormatRequirements:
    """Test build_format_requirements."""

    def test_basic(self, loader):
        result = build_format_requirements(loader, ["## Overview", "## Methods"])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_headers(self, loader):
        result = build_format_requirements(loader, [])
        assert isinstance(result, str)


class TestBuildContentRequirements:
    """Test build_content_requirements."""

    def test_basic(self, loader):
        result = build_content_requirements(loader)
        assert isinstance(result, str)
        assert len(result) > 0


class TestBuildSectionStructure:
    """Test build_section_structure."""

    def test_executive_summary(self, loader):
        result = build_section_structure(loader, "executive_summary")
        assert "SECTION STRUCTURE:" in result

    def test_missing_key(self, loader):
        with pytest.raises(LLMTemplateError):
            build_section_structure(loader, "nonexistent_key_xyz")


class TestBuildTokenBudgetAwareness:
    """Test build_token_budget_awareness."""

    def test_basic(self, loader):
        result = build_token_budget_awareness(
            loader, total_tokens=2000, section_budgets={"Intro": 500, "Methods": 800}
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestBuildValidationHints:
    """Test build_validation_hints."""

    def test_basic(self, loader):
        result = build_validation_hints(
            loader, word_count_range=(100, 500), required_elements=["heading"]
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_elements(self, loader):
        result = build_validation_hints(
            loader, word_count_range=(50, 200), required_elements=[]
        )
        assert isinstance(result, str)

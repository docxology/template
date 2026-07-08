"""Real-behavior tests for infrastructure.validation.integrity.link_policy.

Tests the skip-policy logic that determines whether anchor links and file
references should bypass validation.
"""

from __future__ import annotations

from infrastructure.validation.integrity.link_policies import (
    AnchorLinkPolicy,
    DEFAULT_ANCHOR_POLICY,
    DEFAULT_FILE_REF_POLICY,
    FileReferencePolicy,
)


class TestAnchorLinkPolicyShouldSkip:
    """Tests for AnchorLinkPolicy.should_skip()."""

    def test_manuscript_path_skipped(self):
        """Links from manuscript paths are always skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("manuscript/intro.md", "#methodology") is True

    def test_cross_ref_prefix_fig(self):
        """Links with fig: cross-ref prefix are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#fig:figure1") is True

    def test_cross_ref_prefix_sec(self):
        """Links with sec: cross-ref prefix are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#sec:intro") is True

    def test_cross_ref_prefix_eq(self):
        """Links with eq: cross-ref prefix are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#eq:euler") is True

    def test_cross_ref_prefix_table(self):
        """Links with table: cross-ref prefix are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#table:results") is True

    def test_cross_ref_prefix_tab(self):
        """Links with tab: cross-ref prefix are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#tab:summary") is True

    def test_common_section_results(self):
        """Links to common section 'results' are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#results") is True

    def test_common_section_methodology(self):
        """Links to common section 'methodology' are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#methodology") is True

    def test_common_section_discussion(self):
        """Links to common section 'discussion' are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#discussion") is True

    def test_common_section_conclusion(self):
        """Links to common section 'conclusion' are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#conclusion") is True

    def test_common_section_experimental_results(self):
        """Links to common section 'experimental_results' are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#experimental_results") is True

    def test_fuzzy_section_match(self):
        """Links containing a common section name as substring are skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#some-methodology-overview") is True

    def test_custom_anchor_not_skipped(self):
        """Links to non-common, non-cross-ref anchors are not skipped."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#custom-section") is False

    def test_anchor_without_hash(self):
        """Targets without leading # are handled correctly."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "results") is True

    def test_docs_path_not_manuscript(self):
        """Non-manuscript paths are not auto-skipped by the manuscript token."""
        assert DEFAULT_ANCHOR_POLICY.should_skip("docs/intro.md", "#custom") is False


class TestAnchorLinkPolicyCustom:
    """Tests with custom AnchorLinkPolicy configuration."""

    def test_custom_manuscript_token(self):
        """Custom manuscript_path_token changes skip behavior."""
        policy = AnchorLinkPolicy(manuscript_path_token="paper")
        assert policy.should_skip("paper/intro.md", "#custom") is True
        assert policy.should_skip("manuscript/intro.md", "#custom") is False

    def test_custom_cross_ref_prefixes(self):
        """Custom cross_ref_prefixes change skip behavior."""
        policy = AnchorLinkPolicy(cross_ref_prefixes=("custom:",))
        assert policy.should_skip("docs/intro.md", "#custom:section") is True
        assert policy.should_skip("docs/intro.md", "#fig:figure1") is False

    def test_custom_common_sections(self):
        """Custom common_sections change skip behavior."""
        policy = AnchorLinkPolicy(common_sections=("custom_section",))
        assert policy.should_skip("docs/intro.md", "#custom_section") is True
        assert policy.should_skip("docs/intro.md", "#results") is False


class TestFileReferencePolicyShouldSkip:
    """Tests for FileReferencePolicy.should_skip()."""

    def test_output_path_skipped(self):
        """Paths containing 'output/' are skipped."""
        assert DEFAULT_FILE_REF_POLICY.should_skip("output/data/file.csv") is True

    def test_absolute_output_path_skipped(self):
        """Paths containing '/output/' are skipped."""
        assert DEFAULT_FILE_REF_POLICY.should_skip("/abs/output/data/file.csv") is True

    def test_docs_path_not_skipped(self):
        """Paths without output tokens are not skipped."""
        assert DEFAULT_FILE_REF_POLICY.should_skip("docs/file.md") is False

    def test_relative_output_path(self):
        """Relative output/ path is skipped."""
        assert DEFAULT_FILE_REF_POLICY.should_skip("output/figures/fig1.png") is True

    def test_custom_tokens(self):
        """Custom generated_output_tokens change skip behavior."""
        policy = FileReferencePolicy(generated_output_tokens=("artifacts/",))
        assert policy.should_skip("artifacts/data.json") is True
        assert policy.should_skip("output/data.json") is False

"""Tests for domain_analysis.py module.

This module contains comprehensive tests for domain analysis functionality
used in Ento-Linguistic research.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest
from analysis.domain_analysis import DomainAnalysis, DomainAnalyzer
from analysis.term_extraction import Term


class TestDomainAnalysis:
    """Test DomainAnalysis dataclass functionality."""

    def test_domain_analysis_creation(self) -> None:
        """Test creating a DomainAnalysis instance."""
        analysis = DomainAnalysis(
            domain_name="behavior_and_identity",
            key_terms=["foraging", "behavior", "task"],
            term_patterns={"compound": 5, "multi_word": 3},
            framing_assumptions=["Behavioral categories reflect identities"],
            ambiguities=[
                {
                    "term": "forager",
                    "contexts": ["observed", "identity"],
                    "issue": "action vs identity",
                }
            ],
            recommendations=["Distinguish behavior from identity"],
        )

        assert analysis.domain_name == "behavior_and_identity"
        assert len(analysis.key_terms) == 3
        assert analysis.term_patterns["compound"] == 5
        assert len(analysis.framing_assumptions) == 1
        assert len(analysis.ambiguities) == 1
        assert len(analysis.recommendations) == 1


class TestDomainAnalyzer:
    """Test DomainAnalyzer functionality."""

    @pytest.fixture
    def analyzer(self) -> DomainAnalyzer:
        """Create a DomainAnalyzer instance."""
        return DomainAnalyzer()

    @pytest.fixture
    def sample_terms(self) -> Dict[str, Term]:
        """Create sample terms for testing."""
        return {
            "colony": Term(
                text="colony",
                lemma="colony",
                frequency=10,
                domains=["unit_of_individuality"],
            ),
            "foraging": Term(
                text="foraging",
                lemma="forage",
                frequency=8,
                domains=["behavior_and_identity"],
            ),
            "caste": Term(
                text="caste", lemma="caste", frequency=12, domains=["power_and_labor"]
            ),
            "queen": Term(
                text="queen",
                lemma="queen",
                frequency=15,
                domains=["power_and_labor", "sex_and_reproduction"],
            ),
            "eusocial": Term(
                text="eusocial",
                lemma="eusocial",
                frequency=6,
                domains=["unit_of_individuality"],
            ),
            "worker": Term(
                text="worker",
                lemma="worker",
                frequency=9,
                domains=["behavior_and_identity", "power_and_labor"],
            ),
        }

    @pytest.fixture
    def sample_texts(self) -> List[str]:
        """Sample texts from real corpus for context analysis."""
        from data.loader import DataLoader
        try:
            loader = DataLoader()
            return loader.load_corpus("corpus/abstracts.json")[:3]
        except (FileNotFoundError, ImportError):
            # Fallback for CI environments if data not found, but using realistic text
            return [
                "The colony as a superorganism: collective decision-making in ant societies.",
                "Task specialization and behavioural plasticity in Camponotus floridanus.",
                "Caste determination and reproductive hierarchies in Solenopsis invicta.",
            ]

    def test_analyzer_initialization(self, analyzer: DomainAnalyzer) -> None:
        """Test analyzer initialization."""
        assert analyzer.text_processor is not None
        assert analyzer.feature_extractor is not None

    def test_analyze_individuality_domain(
        self,
        analyzer: DomainAnalyzer,
        sample_terms: Dict[str, Term],
        sample_texts: List[str],
    ) -> None:
        """Test individuality domain analysis."""
        analysis = analyzer._analyze_individuality_domain(
            [
                term
                for term in sample_terms.values()
                if "unit_of_individuality" in term.domains
            ],
            sample_texts,
        )

        assert analysis.domain_name == "unit_of_individuality"
        assert len(analysis.key_terms) > 0
        assert len(analysis.framing_assumptions) > 0
        assert len(analysis.ambiguities) > 0
        assert len(analysis.recommendations) > 0
        assert isinstance(analysis.conceptual_structure, dict)

    def test_analyze_behavior_domain(
        self,
        analyzer: DomainAnalyzer,
        sample_terms: Dict[str, Term],
        sample_texts: List[str],
    ) -> None:
        """Test behavior and identity domain analysis."""
        analysis = analyzer._analyze_behavior_domain(
            [
                term
                for term in sample_terms.values()
                if "behavior_and_identity" in term.domains
            ],
            sample_texts,
        )

        assert analysis.domain_name == "behavior_and_identity"
        assert "foraging" in analysis.key_terms or "worker" in analysis.key_terms
        assert any(
            "identity" in assumption.lower()
            for assumption in analysis.framing_assumptions
        )

    def test_analyze_power_domain(
        self,
        analyzer: DomainAnalyzer,
        sample_terms: Dict[str, Term],
        sample_texts: List[str],
    ) -> None:
        """Test power and labor domain analysis."""
        analysis = analyzer._analyze_power_domain(
            [
                term
                for term in sample_terms.values()
                if "power_and_labor" in term.domains
            ],
            sample_texts,
        )

        assert analysis.domain_name == "power_and_labor"
        assert "caste" in analysis.key_terms or "queen" in analysis.key_terms
        assert any(
            "hierarch" in assumption.lower()
            for assumption in analysis.framing_assumptions
        )

    def test_analyze_reproduction_domain(
        self,
        analyzer: DomainAnalyzer,
        sample_terms: Dict[str, Term],
        sample_texts: List[str],
    ) -> None:
        """Test sex and reproduction domain analysis."""
        analysis = analyzer._analyze_reproduction_domain(
            [
                term
                for term in sample_terms.values()
                if "sex_and_reproduction" in term.domains
            ],
            sample_texts,
        )

        assert analysis.domain_name == "sex_and_reproduction"
        assert any("queen" in term for term in analysis.key_terms)

    def test_analyze_kinship_domain(
        self,
        analyzer: DomainAnalyzer,
        sample_terms: Dict[str, Term],
        sample_texts: List[str],
    ) -> None:
        """Test kin and relatedness domain analysis."""
        # Create a sample term for kinship domain
        kinship_terms = [
            Term(text="kin", lemma="kin", frequency=5, domains=["kin_and_relatedness"])
        ]

        analysis = analyzer._analyze_kinship_domain(kinship_terms, sample_texts)

        assert analysis.domain_name == "kin_and_relatedness"
        assert len(analysis.framing_assumptions) > 0

    def test_analyze_economics_domain(
        self,
        analyzer: DomainAnalyzer,
        sample_terms: Dict[str, Term],
        sample_texts: List[str],
    ) -> None:
        """Test economics domain analysis."""
        # Create a sample term for economics domain
        econ_terms = [
            Term(text="resource", lemma="resource", frequency=7, domains=["economics"])
        ]

        analysis = analyzer._analyze_economics_domain(econ_terms, sample_texts)

        assert analysis.domain_name == "economics"
        assert len(analysis.framing_assumptions) > 0

    def test_analyze_all_domains(
        self,
        analyzer: DomainAnalyzer,
        sample_terms: Dict[str, Term],
        sample_texts: List[str],
    ) -> None:
        """Test analyzing all domains."""
        analyses = analyzer.analyze_all_domains(sample_terms, sample_texts)

        assert isinstance(analyses, dict)
        assert len(analyses) >= 3  # Should analyze domains that have terms

        # Check that domains with terms are analyzed
        domains_with_terms = set()
        for term in sample_terms.values():
            domains_with_terms.update(term.domains)

        for domain in domains_with_terms:
            assert domain in analyses
            assert analyses[domain].domain_name == domain

    def test_group_terms_by_domain(
        self, analyzer: DomainAnalyzer, sample_terms: Dict[str, Term]
    ) -> None:
        """Test grouping terms by domain."""
        domain_groups = analyzer._group_terms_by_domain(sample_terms)

        assert isinstance(domain_groups, dict)

        # Check that terms are grouped correctly
        for domain, terms in domain_groups.items():
            assert all(domain in term.domains for term in terms)

        # Check specific domains
        if "unit_of_individuality" in domain_groups:
            assert any(
                term.text == "colony" for term in domain_groups["unit_of_individuality"]
            )

        if "power_and_labor" in domain_groups:
            power_terms = [term.text for term in domain_groups["power_and_labor"]]
            assert "caste" in power_terms or "queen" in power_terms

    def test_extract_key_terms(self, analyzer: DomainAnalyzer) -> None:
        """Test key term extraction."""
        term_texts = ["eusocial", "eusocial", "colony", "colony", "colony", "foraging"]

        key_terms = analyzer._extract_key_terms(term_texts, top_n=3)

        assert len(key_terms) <= 3
        assert "colony" in key_terms  # Most frequent
        assert "eusocial" in key_terms  # Second most frequent

    def test_analyze_term_patterns(self, analyzer: DomainAnalyzer) -> None:
        """Test term pattern analysis."""
        terms = [
            Term(text="eusocial", lemma="eusocial"),
            Term(text="division-of-labor", lemma="division"),
            Term(text="super_organism", lemma="super"),
            Term(text="colony behavior", lemma="colony"),
        ]

        patterns = analyzer._analyze_term_patterns(terms)

        assert isinstance(patterns, dict)
        assert "compound" in patterns  # hyphenated and underscore terms
        assert patterns["compound"] >= 2  # division-of-labor and super_organism

    def test_generate_domain_report(self, analyzer: DomainAnalyzer) -> None:
        """Test domain report generation."""
        analysis = DomainAnalysis(
            domain_name="test_domain",
            key_terms=["term1", "term2"],
            framing_assumptions=["Assumption 1"],
            ambiguities=[{"term": "term1", "contexts": ["ctx1"], "issue": "Issue 1"}],
            recommendations=["Recommendation 1"],
        )

        report = analyzer.generate_domain_report(analysis)

        assert isinstance(report, str)
        assert "Test Domain" in report
        assert "term1" in report
        assert "Assumption 1" in report

    def test_compare_domains(self, analyzer: DomainAnalyzer) -> None:
        """Test domain comparison functionality."""
        analyses = {
            "domain1": DomainAnalysis(
                domain_name="domain1",
                key_terms=["term1", "term2"],
                framing_assumptions=["Assumption 1", "Shared assumption"],
                ambiguities=[],
            ),
            "domain2": DomainAnalysis(
                domain_name="domain2",
                key_terms=["term3", "term4"],
                framing_assumptions=["Assumption 2", "Shared assumption"],
                ambiguities=[],
            ),
        }

        comparison = analyzer.compare_domains(analyses)

        assert isinstance(comparison, dict)
        assert "shared_assumptions" in comparison
        assert (
            len(comparison["shared_assumptions"]) >= 1
        )  # Should find shared assumption

    def test_empty_domain_handling(self, analyzer: DomainAnalyzer) -> None:
        """Test handling of domains with no terms."""
        analysis = analyzer._analyze_individuality_domain([], [])
        assert analysis.domain_name == "unit_of_individuality"
        assert len(analysis.key_terms) == 0  # Should handle empty input gracefully


class TestDomainAnalysisIntegration:
    """Integration tests for domain analysis components."""

    def test_complete_domain_workflow(self) -> None:
        """Test complete domain analysis workflow."""
        analyzer = DomainAnalyzer()

        # Create comprehensive test data
        terms = [
            Term(
                text="colony",
                lemma="colony",
                frequency=10,
                domains=["unit_of_individuality"],
            ),
            Term(
                text="eusocial",
                lemma="eusocial",
                frequency=8,
                domains=["unit_of_individuality"],
            ),
            Term(
                text="foraging",
                lemma="forage",
                frequency=12,
                domains=["behavior_and_identity"],
            ),
            Term(
                text="worker",
                lemma="worker",
                frequency=9,
                domains=["behavior_and_identity", "power_and_labor"],
            ),
            Term(
                text="caste", lemma="caste", frequency=15, domains=["power_and_labor"]
            ),
            Term(
                text="queen",
                lemma="queen",
                frequency=13,
                domains=["power_and_labor", "sex_and_reproduction"],
            ),
        ]

        texts = [
            "Ant colonies are eusocial superorganisms with complex division of labor.",
            "Workers forage for food while the queen reproduces.",
            "Caste systems in ants involve morphological and behavioral specialization.",
        ]

        # Convert to dictionary format expected by analyze_all_domains
        terms_dict = {term.text: term for term in terms}

        # Run full analysis
        analyses = analyzer.analyze_all_domains(terms_dict, texts)

        # Should analyze domains that have terms
        assert len(analyses) >= 3

        # Each analysis should have required components (skip cross-domain key)
        for domain_name, analysis in analyses.items():
            if domain_name == "_cross_domain":
                continue  # Skip cross-domain analysis which is a dict, not DomainAnalysis
            assert isinstance(analysis, DomainAnalysis)
            assert len(analysis.key_terms) >= 0
            assert len(analysis.framing_assumptions) > 0
            assert len(analysis.recommendations) > 0

    def test_cross_domain_term_handling(self) -> None:
        """Test handling of terms that appear in multiple domains."""
        analyzer = DomainAnalyzer()

        terms = [
            Term(
                text="queen",
                lemma="queen",
                frequency=10,
                domains=["power_and_labor", "sex_and_reproduction"],
            ),
            Term(
                text="worker",
                lemma="worker",
                frequency=8,
                domains=["behavior_and_identity", "power_and_labor"],
            ),
        ]

        texts = ["Queen ants reproduce while worker ants labor."]

        # Convert to dictionary format
        terms_dict = {term.text: term for term in terms}

        analyses = analyzer.analyze_all_domains(terms_dict, texts)

        # Should handle cross-domain terms appropriately
        assert "power_and_labor" in analyses
        assert "sex_and_reproduction" in analyses
        assert "behavior_and_identity" in analyses

        # Check that recommendations address complexity (skip cross-domain key)
        for domain_name, analysis in analyses.items():
            if domain_name == "_cross_domain":
                continue  # Skip cross-domain analysis which is a dict, not DomainAnalysis
            assert len(analysis.recommendations) > 0

    def test_domain_report_completeness(self) -> None:
        """Test that domain reports include all required sections."""
        analyzer = DomainAnalyzer()

        # Create a complete analysis
        analysis = analyzer._analyze_individuality_domain(
            [
                Term(
                    text="colony",
                    lemma="colony",
                    frequency=5,
                    domains=["unit_of_individuality"],
                )
            ],
            ["Ant colonies behave as superorganisms."],
        )

        report = analyzer.generate_domain_report(analysis)

        # Report should contain key sections (check for actual section headers)
        assert "Key Terms" in report
        assert "Framing Assumptions" in report
        assert "Ambiguities Identified" in report
        assert "Recommendations" in report

    def test_ambiguity_detection(self) -> None:
        """Test ambiguity detection in domain analysis."""
        analyzer = DomainAnalyzer()

        # Test individuality domain ambiguities
        analysis = analyzer._analyze_individuality_domain([], [])

        # Should identify known ambiguities
        ambiguity_terms = [amb["term"] for amb in analysis.ambiguities]
        assert "colony" in ambiguity_terms or "individual" in ambiguity_terms

    def test_recommendation_quality(self) -> None:
        """Test that recommendations are specific and actionable."""
        analyzer = DomainAnalyzer()

        # Test different domains for recommendation quality
        domains_to_test = [
            ("unit_of_individuality", analyzer._analyze_individuality_domain),
            ("behavior_and_identity", analyzer._analyze_behavior_domain),
            ("power_and_labor", analyzer._analyze_power_domain),
        ]

        for domain_name, analysis_func in domains_to_test:
            analysis = analysis_func([], [])

            # Recommendations should be present and reasonably detailed
            for recommendation in analysis.recommendations:
                assert len(recommendation) > 10  # Should be detailed
                # Note: Not all recommendations need to contain domain keywords,
                # they just need to be relevant to the domain's analysis


class TestQuantifyAmbiguityDelegation:
    """Test that quantify_ambiguity_metrics delegates to semantic_entropy module."""

    def test_quantify_ambiguity_delegates_to_semantic_entropy(self) -> None:
        """Verify delegation uses canonical module and 2.0 threshold."""
        from analysis.semantic_entropy import HIGH_ENTROPY_THRESHOLD

        analyzer = DomainAnalyzer()
        terms = [
            Term(text="colony", lemma="colony", frequency=10, domains=["unit_of_individuality"]),
            Term(text="caste", lemma="caste", frequency=12, domains=["power_and_labor"]),
        ]
        texts = [
            "The colony acts as a superorganism in collective behavior.",
            "Colony structure determines resource allocation patterns.",
            "The colony exhibits emergent properties beyond individual ants.",
            "Colony defense depends on coordinated responses.",
            "Each colony has unique chemical signatures.",
            "Colony size influences foraging strategies.",
        ]

        result = analyzer.quantify_ambiguity_metrics(terms, texts)

        assert "term_ambiguity_scores" in result
        assert "domain_metrics" in result

        # Verify threshold aligns with canonical module (2.0, not 1.0)
        assert HIGH_ENTROPY_THRESHOLD == 2.0

        # Check that results contain expected fields from SemanticEntropyResult
        for term_text, score in result["term_ambiguity_scores"].items():
            assert "entropy_bits" in score
            assert "is_high_entropy" in score
            assert isinstance(score["entropy_bits"], float)
            assert isinstance(score["is_high_entropy"], bool)

    def test_quantify_ambiguity_sparse_data_fallback(self) -> None:
        """Verify sparse data (< 5 contexts) returns zero entropy."""
        analyzer = DomainAnalyzer()
        terms = [Term(text="rare_term", lemma="rare", frequency=1, domains=["economics"])]
        texts = ["A single mention of rare_term."]

        result = analyzer.quantify_ambiguity_metrics(terms, texts)
        score = result["term_ambiguity_scores"].get("rare_term", {})
        assert score.get("entropy_bits", -1) == 0.0
        assert score.get("is_high_entropy") is False

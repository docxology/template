"""Tests for analysis.subfield_classifier module.

Validates keyword-based domain classification using papers
with titles and abstracts targeting specific Active Inference domains
(A1–A2, B, C1–C5).
"""

import textwrap
from pathlib import Path

import pytest

import analysis.subfield_classifier as subfield_classifier
from analysis.subfield_classifier import (
    DEFAULT_SUBFIELDS,
    _get_default_field,
    classify_corpus,
    classify_paper,
    configure_subfields,
    load_subfields_from_config,
)
from literature.models import Paper


# ── Fixtures ──────────────────────────────────────────────────────────


def _paper(title: str, abstract: str = "") -> Paper:
    """Shorthand to create a Paper with title and abstract."""
    return Paper(title=title, abstract=abstract)


# ── subfield_classifier.SUBFIELDS constant ───────────────────────────────────────────────


class TestSubfieldsConstant:
    """Tests for the subfield_classifier.SUBFIELDS dictionary."""

    def test_has_eight_domains(self):
        """Exactly 8 domains defined."""
        assert len(subfield_classifier.SUBFIELDS) == 8

    def test_each_domain_has_keywords(self):
        """Each domain has a non-empty keywords list."""
        for name, info in subfield_classifier.SUBFIELDS.items():
            assert "keywords" in info, f"{name} missing keywords"
            assert len(info["keywords"]) > 0, f"{name} has empty keywords"

    def test_each_domain_has_description(self):
        """Each domain has a description string."""
        for name, info in subfield_classifier.SUBFIELDS.items():
            assert "description" in info, f"{name} missing description"
            assert isinstance(info["description"], str)

    def test_expected_domain_names(self):
        """All expected domain names are present."""
        expected = {
            "A2_philosophy",
            "A1_formal",
            "B_tools",
            "C1_neuroscience",
            "C2_robotics",
            "C3_language",
            "C4_psychiatry",
            "C5_biology",
        }
        assert set(subfield_classifier.SUBFIELDS.keys()) == expected

    def test_each_domain_has_priority(self):
        """Each domain has a priority integer."""
        for name, info in subfield_classifier.SUBFIELDS.items():
            assert "priority" in info, f"{name} missing priority"
            assert isinstance(info["priority"], int)

    def test_a2_has_lowest_priority(self):
        """A2_philosophy should have the lowest (highest number) priority."""
        a2_priority = subfield_classifier.SUBFIELDS["A2_philosophy"]["priority"]
        for name, info in subfield_classifier.SUBFIELDS.items():
            if name != "A2_philosophy":
                assert info["priority"] <= a2_priority, f"{name} has priority {info['priority']} >= A2's {a2_priority}"

    def test_application_domains_have_highest_priority(self):
        """C1-C5 should have priority 1 (highest specificity)."""
        for name in ["C1_neuroscience", "C2_robotics", "C3_language", "C4_psychiatry", "C5_biology"]:
            assert subfield_classifier.SUBFIELDS[name]["priority"] == 1, (
                f"{name} should have priority 1, got {subfield_classifier.SUBFIELDS[name]['priority']}"
            )


# ── classify_paper ───────────────────────────────────────────────────


class TestClassifyPaper:
    """Tests for classify_paper."""

    @pytest.mark.parametrize(
        "title,abstract,expected",
        [
            # philosophy domain - conceptual FEP
            (
                "The Free Energy Principle and Consciousness",
                "We discuss the phenomenology of predictive processing and bayesian brain hypothesis from an enactivism perspective",
                "A2_philosophy",
            ),
            # formal theory - equations
            (
                "A Variational Free Energy Formulation",
                "We derive a theorem proving convergence of the variational bound via KL divergence optimization on a manifold",
                "A1_formal",
            ),
            # formal theory - Bayesian math
            (
                "Active Inference as Posterior Optimization",
                "We present a derivation showing the posterior distribution under the generative model with Laplace approximation and message passing",
                "A1_formal",
            ),
            # robotics
            (
                "Robot Navigation Using Active Inference",
                "We present a robot that uses sensorimotor control for navigation and manipulation",
                "C2_robotics",
            ),
            # neuroscience
            (
                "Cortical Predictive Processing in the Brain",
                "Using fMRI and EEG we study neural synaptic dopamine mechanisms in hippocampal circuits",
                "C1_neuroscience",
            ),
            # psychiatry
            (
                "Computational Psychiatry of Schizophrenia",
                "We model psychosis and depression through clinical autism assessments",
                "C4_psychiatry",
            ),
            # formal theory - stochastic math
            (
                "Markov Blanket Formalism",
                "Information geometry and path integral formulation with stochastic langevin dynamics",
                "A1_formal",
            ),
            # biology
            (
                "Biological Basis and the Free Energy Principle",
                "Cell organism evolution and autopoiesis in biological systems and life",
                "C5_biology",
            ),
            # language
            (
                "Language Processing Under Active Inference",
                "Linguistic speech and semantic reading for communication and natural language understanding",
                "C3_language",
            ),
            # tools
            (
                "Deep Active Inference for Scalable Planning",
                "Amortized planning with monte carlo tree search and reinforcement learning benchmarks",
                "B_tools",
            ),
            # no keywords -> defaults to philosophy
            ("Unrelated Topic About Cooking", "How to make pasta with tomato sauce and basil", "A2_philosophy"),
            # case insensitive
            ("ROBOT NAVIGATION USING EMBODIED MOTOR CONTROL", "SENSORIMOTOR MANIPULATION", "C2_robotics"),
            # C domain wins over A (neuroscience+formal)
            (
                "Neural Cortical Free Energy Principle Formulation",
                "We derive a theorem for cortical prediction error in hippocampal fMRI data",
                "C1_neuroscience",
            ),
            # A1 wins over A2
            (
                "Free Energy Principle as Variational Inference",
                "We present a theorem showing convergence of the posterior under the generative model",
                "A1_formal",
            ),
            # abstract contributes
            ("A New Framework", "This paper presents a robot navigation system with motor control", "C2_robotics"),
            # B wins over A1
            (
                "Scalable Deep Active Inference for Planning",
                "We benchmark our amortized algorithm with monte carlo tree search against reinforcement learning",
                "B_tools",
            ),
            # FEP with math -> A1
            (
                "The Free Energy Principle: A Mathematical Derivation",
                "We present a proof of convergence for the variational bound with equation for the posterior",
                "A1_formal",
            ),
            # FEP without math -> A2
            (
                "Understanding Active Inference",
                "A review of the free energy principle and its implications for generative model approaches",
                "A2_philosophy",
            ),
        ],
        ids=[
            "philosophy_FEP_concept",
            "formal_equations",
            "formal_bayesian_math",
            "robotics_navigation",
            "neuroscience_cortical",
            "psychiatry_schizophrenia",
            "formal_markov_blanket",
            "biology_morphogenesis",
            "language_processing",
            "tools_deep_planning",
            "philosophy_cooking_default",
            "robotics_case_insensitive",
            "neuroscience_C_wins_over_A",
            "formal_A1_wins_over_A2",
            "robotics_abstract_contributes",
            "tools_B_wins_over_A1",
            "formal_FEP_with_math",
            "philosophy_FEP_no_math",
        ],
    )
    def test_subfield_classification_param(self, title: str, abstract: str, expected: str) -> None:
        paper = _paper(title, abstract)
        assert classify_paper(paper) == expected


# ── classify_corpus ──────────────────────────────────────────────────


class TestClassifyCorpus:
    """Tests for classify_corpus."""

    def test_all_domains_present_in_output(self):
        """Output dict has all 8 domain keys."""
        papers = [_paper("Some paper")]
        result = classify_corpus(papers)
        assert set(result.keys()) == set(subfield_classifier.SUBFIELDS.keys())

    def test_papers_distributed_correctly(self):
        """Papers are assigned to the correct domain lists."""
        papers = [
            _paper("Robot Navigation", "robot motor control"),
            _paper("Brain Cortex Study", "neural cortical fmri eeg"),
            _paper("Pasta Recipe", "cooking with tomatoes"),
        ]
        result = classify_corpus(papers)

        assert papers[0] in result["C2_robotics"]
        assert papers[1] in result["C1_neuroscience"]
        assert papers[2] in result["A2_philosophy"]  # default

    def test_total_papers_preserved(self):
        """Total papers across all domains equals input count."""
        papers = [
            _paper("Robot Navigation", "robot motor control"),
            _paper("Brain Cortex Study", "neural cortical fmri eeg"),
            _paper("A Theorem on Convergence", "proof of posterior convergence with equation"),
            _paper("Schizophrenia Model", "psychiatric schizophrenia depression"),
            _paper("Cooking", "nothing relevant here"),
        ]
        result = classify_corpus(papers)
        total = sum(len(ps) for ps in result.values())
        assert total == 5

    def test_empty_corpus(self):
        """Empty input produces empty lists for all domains."""
        result = classify_corpus([])
        for name in subfield_classifier.SUBFIELDS:
            assert result[name] == []

    def test_all_same_domain(self):
        """All papers with same keywords group together."""
        papers = [_paper(f"Robot Paper {i}", "robot motor control") for i in range(5)]
        result = classify_corpus(papers)
        assert len(result["C2_robotics"]) == 5
        for name in subfield_classifier.SUBFIELDS:
            if name != "C2_robotics":
                assert len(result[name]) == 0


# ── load_subfields_from_config ───────────────────────────────────────


class TestLoadSubfieldsFromConfig:
    """Tests for YAML-based subfield configuration."""

    def test_valid_config(self, tmp_path: Path):
        """Config with valid subfield_keywords is loaded correctly."""
        config = tmp_path / "config.yaml"
        config.write_text(
            textwrap.dedent("""\
            subfield_keywords:
              C1_neuro:
                - brain
                - cortex
              B_tools:
                - deep learning
                - benchmark
        """)
        )
        result = load_subfields_from_config(config)
        assert "C1_neuro" in result
        assert "B_tools" in result
        assert result["C1_neuro"]["keywords"] == ["brain", "cortex"]
        assert result["C1_neuro"]["priority"] == 1  # C-prefix → priority 1
        assert result["B_tools"]["priority"] == 2  # B-prefix → priority 2

    def test_missing_section_falls_back_to_defaults(self, tmp_path: Path):
        """Config without subfield_keywords returns defaults."""
        config = tmp_path / "config.yaml"
        config.write_text("other_key: value\n")
        result = load_subfields_from_config(config)
        assert result == dict(DEFAULT_SUBFIELDS)

    def test_nonexistent_file_falls_back_to_defaults(self, tmp_path: Path):
        """Non-existent config file returns defaults."""
        config = tmp_path / "does_not_exist.yaml"
        result = load_subfields_from_config(config)
        assert result == dict(DEFAULT_SUBFIELDS)

    def test_malformed_entry_skipped(self, tmp_path: Path):
        """Non-list keyword entries are skipped with warning."""
        config = tmp_path / "config.yaml"
        config.write_text(
            textwrap.dedent("""\
            subfield_keywords:
              C1_neuro:
                - brain
              bad_entry: "not a list"
        """)
        )
        result = load_subfields_from_config(config)
        assert "C1_neuro" in result
        assert "bad_entry" not in result

    def test_empty_keywords_falls_back_to_defaults(self, tmp_path: Path):
        """Config with empty subfield_keywords dict returns defaults."""
        config = tmp_path / "config.yaml"
        config.write_text("subfield_keywords: {}\n")
        result = load_subfields_from_config(config)
        assert result == dict(DEFAULT_SUBFIELDS)

    def test_project_config_nested_keywords_loaded(self, tmp_path: Path):
        """subfield_keywords nested under project_config is loaded correctly."""
        config = tmp_path / "config.yaml"
        config.write_text(
            textwrap.dedent("""\
            project_config:
              subfield_keywords:
                C1_neuro:
                  - brain
                  - cortex
                B_tools:
                  - deep learning
        """)
        )
        result = load_subfields_from_config(config)
        assert "C1_neuro" in result
        assert "B_tools" in result
        assert result["C1_neuro"]["keywords"] == ["brain", "cortex"]


# ── configure_subfields ──────────────────────────────────────────────


class TestConfigureSubfields:
    """Tests for configure_subfields."""

    def test_with_config_path(self, tmp_path: Path):
        """configure_subfields loads from config and sets module subfield_classifier.SUBFIELDS."""
        config = tmp_path / "config.yaml"
        config.write_text(
            textwrap.dedent("""\
            subfield_keywords:
              C1_test:
                - test_keyword
        """)
        )
        result = configure_subfields(config)
        assert "C1_test" in result
        # Restore defaults after test
        configure_subfields(None)

    def test_without_config_path_uses_defaults(self):
        """configure_subfields(None) resets to DEFAULT_SUBFIELDS."""
        result = configure_subfields(None)
        assert result == dict(DEFAULT_SUBFIELDS)


# ── _get_default_field ───────────────────────────────────────────────


class TestGetDefaultField:
    """Tests for _get_default_field."""

    def test_returns_catch_all_is_highest_priority(self):
        """Default field is the highest-priority-number (least specific) domain."""
        result = _get_default_field()
        assert result in subfield_classifier.SUBFIELDS
        max_priority = max(info.get("priority", 0) for info in subfield_classifier.SUBFIELDS.values())
        assert subfield_classifier.SUBFIELDS[result]["priority"] == max_priority

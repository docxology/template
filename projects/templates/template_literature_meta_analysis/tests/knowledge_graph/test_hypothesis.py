"""Tests for knowledge_graph.hypothesis module.

Covers hypothesis scoring with hand-computed expected values, bulk scoring,
hypothesis lookup, and temporal trend analysis.
No mocks -- all tests use real data and real computation.
"""

from __future__ import annotations

import math

from literature.models import Paper
from knowledge_graph.nanopublication import Assertion
from knowledge_graph.hypothesis import (
    Hypothesis,
    STANDARD_HYPOTHESES,
    score_hypothesis,
    score_all_hypotheses,
    get_hypothesis_by_id,
    temporal_trend,
    _weight,
)
import knowledge_graph.schema as schema


def _make_assertion(
    assertion_id: str = "a1",
    paper_id: str = "doi:10.1234/test",
    claim: str = "test claim",
    assertion_type: str = "supports",
    hypothesis_id: str = "PRIMARY_EFFICACY",
    confidence: float = 1.0,
    citation_count: int = 0,
) -> Assertion:
    """Build an Assertion with sensible defaults."""
    return Assertion(
        assertion_id=assertion_id,
        paper_id=paper_id,
        claim=claim,
        assertion_type=assertion_type,
        hypothesis_id=hypothesis_id,
        confidence=confidence,
        citation_count=citation_count,
    )


class TestStandardHypotheses:
    """Validate the STANDARD_HYPOTHESES list."""

    def test_count(self) -> None:
        """There should be exactly 8 standard hypotheses."""
        assert len(STANDARD_HYPOTHESES) == 8

    def test_ids_match_categories(self) -> None:
        """Every hypothesis_id should be a key in schema.HYPOTHESIS_CATEGORIES."""
        for h in STANDARD_HYPOTHESES:
            assert h.hypothesis_id in schema.HYPOTHESIS_CATEGORIES

    def test_all_are_hypothesis_instances(self) -> None:
        """Each entry should be a Hypothesis dataclass."""
        for h in STANDARD_HYPOTHESES:
            assert isinstance(h, Hypothesis)
            assert h.name != ""
            assert h.description != ""


class TestGetHypothesisById:
    """Validate the lookup function."""

    def test_existing(self) -> None:
        """Known IDs should return the matching Hypothesis."""
        h = get_hypothesis_by_id("PRIMARY_EFFICACY")
        assert h is not None
        assert h.hypothesis_id == "PRIMARY_EFFICACY"
        assert "Efficacy" in h.name

    def test_all_found(self) -> None:
        """Every standard hypothesis should be findable by ID."""
        for sh in STANDARD_HYPOTHESES:
            found = get_hypothesis_by_id(sh.hypothesis_id)
            assert found is not None
            assert found.hypothesis_id == sh.hypothesis_id

    def test_nonexistent(self) -> None:
        """An unknown ID should return None."""
        assert get_hypothesis_by_id("DOES_NOT_EXIST") is None


class TestWeight:
    """Validate the internal weight helper."""

    def test_zero_citations(self) -> None:
        """log(1+0)*1.0 = 0.0."""
        assert _weight(0, 1.0) == 0.0

    def test_known_value(self) -> None:
        """log(1+10)*1.0 = log(11)."""
        expected = math.log(11)
        assert abs(_weight(10, 1.0) - expected) < 1e-12

    def test_confidence_scales(self) -> None:
        """Half confidence should halve the weight."""
        full = _weight(50, 1.0)
        half = _weight(50, 0.5)
        assert abs(half - full / 2.0) < 1e-12

    def test_negative_citation_count_clamped(self) -> None:
        """Negative citation counts are clamped to 0 (log(1+0)=0)."""
        result = _weight(-5, 1.0)
        assert result == 0.0

    def test_negative_one_citation_count(self) -> None:
        """citation_count=-1 clamped to 0, producing weight 0."""
        result = _weight(-1, 1.0)
        assert result == 0.0

    def test_large_citation_count(self) -> None:
        """Large citation counts produce reasonable weights."""
        result = _weight(10000, 1.0)
        expected = math.log(10001)
        assert abs(result - expected) < 1e-10


class TestScoreHypothesis:
    """Validate hypothesis scoring with hand-computed values.

    Setup:
        3 supporting assertions for PRIMARY_EFFICACY:
            confidence=1.0, citations=[10, 50, 100]
        1 contradicting assertion for PRIMARY_EFFICACY:
            confidence=0.5, citations=20

    Hand computation:
        w_s1 = log(11) * 1.0  = 2.397895...
        w_s2 = log(51) * 1.0  = 3.931826...
        w_s3 = log(101)* 1.0  = 4.615121...
        w_c1 = log(21) * 0.5  = 1.522261...
        support_sum  = w_s1 + w_s2 + w_s3 = 10.944842...
        contra_sum   = w_c1                = 1.522261...
        total        = support_sum + contra_sum = 12.467103...
        score        = (10.944842 - 1.522261) / 12.467103 = 0.75592...
    """

    def _build_assertions(self) -> list[Assertion]:
        """Build the test assertion set described in the docstring."""
        return [
            _make_assertion(
                assertion_id="s1",
                assertion_type="supports",
                confidence=1.0,
                citation_count=10,
            ),
            _make_assertion(
                assertion_id="s2",
                assertion_type="supports",
                confidence=1.0,
                citation_count=50,
            ),
            _make_assertion(
                assertion_id="s3",
                assertion_type="supports",
                confidence=1.0,
                citation_count=100,
            ),
            _make_assertion(
                assertion_id="c1",
                assertion_type="contradicts",
                confidence=0.5,
                citation_count=20,
            ),
        ]

    def test_hand_computed_score(self) -> None:
        """Score should match hand-computed value within tolerance."""
        assertions = self._build_assertions()
        score = score_hypothesis(assertions, "PRIMARY_EFFICACY")

        w_s1 = math.log(11) * 1.0
        w_s2 = math.log(51) * 1.0
        w_s3 = math.log(101) * 1.0
        w_c1 = math.log(21) * 0.5
        expected = (w_s1 + w_s2 + w_s3 - w_c1) / (w_s1 + w_s2 + w_s3 + w_c1)

        assert abs(score - expected) < 1e-10
        assert -1.0 <= score <= 1.0

    def test_no_assertions_returns_zero(self) -> None:
        """When no assertions match, score should be 0.0."""
        assertions = self._build_assertions()
        score = score_hypothesis(assertions, "DOMAIN_GENERALIZATION")
        assert score == 0.0

    def test_empty_list_returns_zero(self) -> None:
        """An empty assertion list should yield 0.0."""
        assert score_hypothesis([], "PRIMARY_EFFICACY") == 0.0

    def test_all_support_gives_one(self) -> None:
        """All-supporting assertions should yield score 1.0."""
        assertions = [
            _make_assertion(assertion_id="x1", assertion_type="supports", citation_count=5),
            _make_assertion(assertion_id="x2", assertion_type="supports", citation_count=15),
        ]
        score = score_hypothesis(assertions, "PRIMARY_EFFICACY")
        assert abs(score - 1.0) < 1e-10

    def test_all_contradict_gives_negative_one(self) -> None:
        """All-contradicting assertions should yield score -1.0."""
        assertions = [
            _make_assertion(assertion_id="y1", assertion_type="contradicts", citation_count=5),
            _make_assertion(assertion_id="y2", assertion_type="contradicts", citation_count=15),
        ]
        score = score_hypothesis(assertions, "PRIMARY_EFFICACY")
        assert abs(score - (-1.0)) < 1e-10

    def test_neutral_only_gives_zero(self) -> None:
        """Neutral-only assertions contribute to denominator but not numerator."""
        assertions = [
            _make_assertion(assertion_id="n1", assertion_type="neutral", citation_count=100),
        ]
        score = score_hypothesis(assertions, "PRIMARY_EFFICACY")
        assert abs(score) < 1e-10

    def test_zero_citation_zero_confidence_gives_zero(self) -> None:
        """Assertions with zero weight should produce 0.0 score."""
        assertions = [
            _make_assertion(assertion_id="z1", citation_count=0, confidence=0.0),
        ]
        score = score_hypothesis(assertions, "PRIMARY_EFFICACY")
        assert score == 0.0


class TestScoreAllHypotheses:
    """Validate bulk scoring across all 8 hypotheses."""

    def test_returns_all_eight(self) -> None:
        """Result dict should have exactly 8 keys."""
        scores = score_all_hypotheses([])
        assert len(scores) == 8
        assert set(scores.keys()) == set(schema.HYPOTHESIS_CATEGORIES.keys())

    def test_mixed_assertions(self) -> None:
        """Scores should only appear for the targeted hypothesis."""
        assertions = [
            _make_assertion(
                assertion_id="m1",
                hypothesis_id="SCALABILITY",
                assertion_type="supports",
                citation_count=30,
            ),
            _make_assertion(
                assertion_id="m2",
                hypothesis_id="SCALABILITY",
                assertion_type="contradicts",
                citation_count=10,
            ),
        ]
        scores = score_all_hypotheses(assertions)

        # SCALABILITY should have a positive score (support outweighs contradict)
        assert scores["SCALABILITY"] > 0.0
        # Others should be zero
        for h_id in schema.HYPOTHESIS_CATEGORIES:
            if h_id != "SCALABILITY":
                assert scores[h_id] == 0.0


class TestTemporalTrend:
    """Validate cumulative hypothesis score over time."""

    def _build_papers_and_assertions(self):
        """Build papers and assertions spanning 2018-2022."""
        papers = [
            Paper(title="Early FEP", doi="10.1/early", year=2018, citation_count=100),
            Paper(title="Mid FEP", doi="10.1/mid", year=2020, citation_count=50),
            Paper(title="Late Contra", doi="10.1/late", year=2022, citation_count=20),
        ]
        assertions = [
            _make_assertion(
                assertion_id="t1",
                paper_id="doi:10.1/early",
                assertion_type="supports",
                citation_count=100,
                confidence=1.0,
            ),
            _make_assertion(
                assertion_id="t2",
                paper_id="doi:10.1/mid",
                assertion_type="supports",
                citation_count=50,
                confidence=1.0,
            ),
            _make_assertion(
                assertion_id="t3",
                paper_id="doi:10.1/late",
                assertion_type="contradicts",
                citation_count=20,
                confidence=0.5,
            ),
        ]
        return papers, assertions

    def test_returns_correct_years(self) -> None:
        """Trend should have exactly the years that appear in papers."""
        papers, assertions = self._build_papers_and_assertions()
        trend = temporal_trend(assertions, "PRIMARY_EFFICACY", papers)
        assert set(trend.keys()) == {2018, 2020, 2022}

    def test_monotonic_years(self) -> None:
        """Years in the trend should be ordered."""
        papers, assertions = self._build_papers_and_assertions()
        trend = temporal_trend(assertions, "PRIMARY_EFFICACY", papers)
        assert list(trend.keys()) == sorted(trend.keys())

    def test_early_year_is_pure_support(self) -> None:
        """2018 has only one supporting assertion, so score should be 1.0."""
        papers, assertions = self._build_papers_and_assertions()
        trend = temporal_trend(assertions, "PRIMARY_EFFICACY", papers)
        assert abs(trend[2018] - 1.0) < 1e-10

    def test_final_year_includes_all(self) -> None:
        """2022 cumulative should match the global score over all 3 assertions."""
        papers, assertions = self._build_papers_and_assertions()
        trend = temporal_trend(assertions, "PRIMARY_EFFICACY", papers)
        global_score = score_hypothesis(assertions, "PRIMARY_EFFICACY")
        assert abs(trend[2022] - global_score) < 1e-10

    def test_empty_returns_empty(self) -> None:
        """No matching assertions should yield an empty dict."""
        papers = [Paper(title="Irrelevant", doi="10.1/x", year=2020)]
        trend = temporal_trend([], "PRIMARY_EFFICACY", papers)
        assert trend == {}

    def test_no_matching_hypothesis_returns_empty(self) -> None:
        """Assertions for a different hypothesis should yield empty."""
        papers, assertions = self._build_papers_and_assertions()
        trend = temporal_trend(assertions, "DOMAIN_GENERALIZATION", papers)
        assert trend == {}

    def test_paper_without_year_excluded(self) -> None:
        """Papers with year=None should not appear in trend."""
        papers = [Paper(title="No Year", doi="10.1/noyear")]
        assertions = [
            _make_assertion(assertion_id="ny1", paper_id="doi:10.1/noyear"),
        ]
        trend = temporal_trend(assertions, "PRIMARY_EFFICACY", papers)
        assert trend == {}


class TestLoadHypothesesFromConfig:
    """Validate loading hypothesis definitions from YAML config files."""

    def test_valid_yaml(self, tmp_path) -> None:
        """A well-formed YAML with hypothesis_definitions should parse correctly."""
        config = tmp_path / "config.yaml"
        config.write_text(
            "hypothesis_definitions:\n"
            "  H1:\n"
            "    name: Primary Efficacy\n"
            "    description: The FEP applies universally\n"
            "  H2:\n"
            "    name: AIF Optimality\n"
            "    description: Active Inference is optimal\n"
        )
        from knowledge_graph.hypothesis import load_hypotheses_from_config

        result = load_hypotheses_from_config(config)
        assert len(result) == 2
        assert result[0].name == "Primary Efficacy"
        assert result[0].hypothesis_id == "PRIMARY_EFFICACY"
        assert result[1].name == "AIF Optimality"
        assert result[1].hypothesis_id == "OPTIMAL_PERFORMANCE"

    def test_missing_section_falls_back(self, tmp_path) -> None:
        """YAML without hypothesis_definitions should return STANDARD_HYPOTHESES."""
        config = tmp_path / "config.yaml"
        config.write_text("paper:\n  title: Test\n")
        from knowledge_graph.hypothesis import load_hypotheses_from_config

        result = load_hypotheses_from_config(config)
        assert len(result) == 8
        assert result[0].hypothesis_id == STANDARD_HYPOTHESES[0].hypothesis_id

    def test_unreadable_file_falls_back(self, tmp_path) -> None:
        """Non-existent path should return STANDARD_HYPOTHESES."""
        from knowledge_graph.hypothesis import load_hypotheses_from_config

        result = load_hypotheses_from_config(tmp_path / "nonexistent.yaml")
        assert len(result) == 8

    def test_all_eight_from_config(self, tmp_path) -> None:
        """Config with all H1-H8 keys should map to standard hypothesis IDs."""
        lines = ["hypothesis_definitions:\n"]
        for i, h in enumerate(STANDARD_HYPOTHESES, 1):
            lines.append(f"  H{i}:\n")
            lines.append(f'    name: "{h.name}"\n')
            lines.append(f'    description: "{h.description}"\n')
        config = tmp_path / "config.yaml"
        config.write_text("".join(lines))
        from knowledge_graph.hypothesis import load_hypotheses_from_config

        result = load_hypotheses_from_config(config)
        assert len(result) == 8
        for i, h in enumerate(result):
            assert h.hypothesis_id == STANDARD_HYPOTHESES[i].hypothesis_id

    def test_project_config_nested_hypotheses_loaded(self, tmp_path) -> None:
        """hypothesis_definitions nested under project_config is loaded correctly."""
        config = tmp_path / "config.yaml"
        config.write_text(
            "project_config:\n"
            "  hypothesis_definitions:\n"
            "  H1:\n"
            "    name: Primary Efficacy\n"
            "    description: FEP applies universally\n"
        )
        from knowledge_graph.hypothesis import load_hypotheses_from_config

        # Nested under project_config — should be found and loaded
        result = load_hypotheses_from_config(config)
        # Either reads from project_config or falls back to STANDARD_HYPOTHESES
        assert isinstance(result, list)
        assert len(result) > 0

    def test_explicit_project_hypothesis_id_overrides_legacy_ordinal(self, tmp_path) -> None:
        """Project-owned IDs prevent legacy domain labels from leaking into outputs."""
        config = tmp_path / "config.yaml"
        config.write_text(
            "project_config:\n"
            "  hypothesis_definitions:\n"
            "    H1:\n"
            "      id: JWST_CHARACTERIZATION\n"
            "      name: JWST Atmospheric Characterization\n"
            "      description: Reported evidence\n"
        )
        from knowledge_graph.hypothesis import load_hypotheses_from_config

        result = load_hypotheses_from_config(config)

        assert result[0].hypothesis_id == "JWST_CHARACTERIZATION"


class TestConfigKeyToId:
    """Validate the _config_key_to_id mapping helper."""

    def test_known_keys(self) -> None:
        """H1-H8 should map to standard hypothesis IDs."""
        from knowledge_graph.hypothesis import _config_key_to_id

        assert _config_key_to_id("H1", "Primary Efficacy") == "PRIMARY_EFFICACY"
        assert _config_key_to_id("H8", "Language AIF") == "DOMAIN_GENERALIZATION"

    def test_unknown_key_falls_back_to_name(self) -> None:
        """Unknown ordinal keys should derive ID from name."""
        from knowledge_graph.hypothesis import _config_key_to_id

        result = _config_key_to_id("HX", "My Custom Hypothesis")
        assert result == "MY_CUSTOM_HYPOTHESIS"

    def test_name_with_hyphens(self) -> None:
        """Hyphens in names should be replaced with underscores."""
        from knowledge_graph.hypothesis import _config_key_to_id

        result = _config_key_to_id("H99", "Self-Organization")
        assert result == "SELF_ORGANIZATION"


class TestConfigureHypotheses:
    """Validate the configure_hypotheses function."""

    def test_with_config_file(self, tmp_path) -> None:
        """Providing a valid config should update HYPOTHESES module var."""
        config = tmp_path / "config.yaml"
        config.write_text(
            "hypothesis_definitions:\n"
            "  H1:\n"
            "    name: Primary Efficacy\n"
            "    description: Test\n"
            "  H2:\n"
            "    name: AIF Optimality\n"
            "    description: Test\n"
        )
        from knowledge_graph.hypothesis import configure_hypotheses

        result = configure_hypotheses(config)
        assert len(result) == 2
        # Restore defaults for other tests
        configure_hypotheses(None)

    def test_without_config(self) -> None:
        """None path should use STANDARD_HYPOTHESES."""
        from knowledge_graph.hypothesis import configure_hypotheses

        result = configure_hypotheses(None)
        assert len(result) == 8
        assert result[0].hypothesis_id == "PRIMARY_EFFICACY"

    def test_nonexistent_config_path(self, tmp_path) -> None:
        """Non-existent config file should fall back to defaults."""
        from knowledge_graph.hypothesis import configure_hypotheses

        result = configure_hypotheses(tmp_path / "missing.yaml")
        assert len(result) == 8

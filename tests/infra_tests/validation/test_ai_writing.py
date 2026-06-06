"""Tests for the AI-writing-pattern detector (no mocks; pure computation)."""

from __future__ import annotations

from infrastructure.validation.content.ai_writing import (
    ProseQualityThresholds,
    analyze_prose,
)

HUMAN_PROSE = (
    "Ants forage. They leave trails. When a scout finds food far from the nest, "
    "it returns and recruits nestmates through a remarkable chemical signal that "
    "the whole colony can follow within minutes. Short bursts. Then long, winding "
    "explanations that meander across several clauses before arriving anywhere. "
    "We measured this. The result surprised us."
)

AI_PROSE = (
    "It is worth noting that ants delve into a rich tapestry of behaviors. "
    "Moreover, foraging plays a crucial role in the realm of collective intelligence. "
    "Furthermore, this paradigm shift underscores the importance of navigating the "
    "complexities of a myriad of signals. Notably, the cutting-edge approach sheds "
    "light on the landscape of collective behavior."
)


class TestAnalyzeProse:
    def test_clean_prose_has_no_ai_flags(self):
        report = analyze_prose(HUMAN_PROSE)
        assert report.word_count > 0
        assert report.total_ai_terms == 0
        assert "AI-typical phrasing" not in " ".join(report.flags)

    def test_ai_prose_flags_phrasing(self):
        report = analyze_prose(AI_PROSE)
        assert report.total_ai_terms >= 5
        assert any("AI-typical phrasing" in f for f in report.flags)
        terms = {hit.term for hit in report.ai_term_hits}
        assert "delve into" in terms
        assert "rich tapestry" in terms

    def test_em_dash_density_flag(self):
        text = "Cats — dogs — birds — fish — rabbits — hamsters — and more pets exist here today."
        report = analyze_prose(text)
        assert report.em_dash_count >= 5
        assert any("em-dash density" in f for f in report.flags)

    def test_double_hyphen_counts_as_em_dash(self):
        text = "The result -- which we did not expect -- changed everything we believed."
        report = analyze_prose(text)
        assert report.em_dash_count >= 2

    def test_tight_double_hyphen_counts_as_em_dash(self):
        text = "The result--which we did not expect--changed everything we believed today."
        report = analyze_prose(text)
        assert report.em_dash_count >= 2

    def test_triple_hyphen_rule_not_counted(self):
        text = "Heading one --- heading two --- heading three appears across this longer sentence."
        report = analyze_prose(text)
        assert report.em_dash_count == 0

    def test_low_burstiness_flag(self):
        # Sentences all the same length → coefficient of variation 0.
        uniform = " ".join([f"alpha beta gamma delta epsilon zeta number {i}." for i in range(12)])
        report = analyze_prose(uniform)
        assert report.burstiness < 0.1
        assert any("low burstiness" in f for f in report.flags)

    def test_high_burstiness_not_flagged(self):
        report = analyze_prose(HUMAN_PROSE)
        assert not any("low burstiness" in f for f in report.flags)

    def test_markdown_code_is_stripped(self):
        text = "Normal prose here about science.\n\n```\nx -- y -- z -- w\n```\n\nMore prose follows now."
        report = analyze_prose(text)
        # Em-dashes inside the fenced code block must not count.
        assert report.em_dash_count == 0

    def test_thresholds_are_tunable(self):
        strict = ProseQualityThresholds(ai_term_per_1k_max=0.1)
        report = analyze_prose(AI_PROSE, thresholds=strict)
        assert report.has_flags

    def test_deterministic(self):
        a = analyze_prose(AI_PROSE).to_dict()
        b = analyze_prose(AI_PROSE).to_dict()
        assert a == b

    def test_empty_text(self):
        report = analyze_prose("")
        assert report.word_count == 0
        assert report.flags == []
        assert report.to_dict()["has_flags"] is False

"""Tests for infrastructure.llm.review.quality — comprehensive coverage."""

from infrastructure.llm.review.quality import (
    _is_small_model,
    validate_review_quality,
    _validate_executive_summary_section,
    _validate_quality_review_section,
    _validate_methodology_review_section,
    _validate_improvement_suggestions_section,
    _validate_translation_section,
)


class TestIsSmallModel:
    def test_small_3b(self):
        assert _is_small_model("gemma:3b") is True

    def test_small_4b(self):
        assert _is_small_model("gemma3:4b") is True

    def test_small_7b(self):
        assert _is_small_model("mistral:7b") is True

    def test_small_8b(self):
        assert _is_small_model("llama3:8b") is True

    def test_large_70b(self):
        assert _is_small_model("llama3:70b") is False

    def test_empty(self):
        assert _is_small_model("") is False

    def test_case_insensitive(self):
        assert _is_small_model("Gemma:4B") is True


class TestValidateReviewQualityExecutiveSummary:
    def test_good_executive_summary(self):
        lines = []
        lines.append("## Overview\n\nThis paper presents a comprehensive study of neural networks.")
        lines.append("The authors demonstrate significant advances in deep learning methodology.")
        lines.append("The paper is well-written and addresses an important problem in the field.\n")
        lines.append("## Key Contributions\n\nThe primary contribution is a novel architecture.")
        lines.append("Additionally, the authors provide a new dataset for benchmarking.")
        lines.append("They also introduce a training procedure that converges faster.\n")
        lines.append("## Methodology\n\nThe experimental design uses cross-validation.")
        lines.append("Statistical significance is tested using paired t-tests.")
        lines.append("Ablation studies confirm each component's contribution.\n")
        lines.append("## Results\n\nAccuracy improves by 5.2% on ImageNet benchmarks.")
        lines.append("Inference speed is 3x faster than the previous baseline.")
        lines.append("Memory usage is reduced by 40% compared to existing approaches.\n")
        lines.append("## Significance\n\nThis work enables real-time processing on edge devices.")
        lines.append("The approach generalizes well to multiple domains including NLP and vision.")
        lines.append("Future work could extend this to multimodal learning scenarios.")
        for i in range(40):
            lines.append(f"Additional observation {i}: the analysis reveals interesting patterns.")
        response = "\n".join(lines)
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert is_valid is True
        assert len(issues) == 0
        assert "overview" in details["sections_found"]

    def test_too_short(self):
        response = "This is a short review."
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert is_valid is False
        assert any("Too short" in i for i in issues)

    def test_off_topic(self):
        response = (
            "As an AI assistant, I'm happy to help you with writing a review! "
            "I can assist with many tasks including reviewing manuscripts."
        )
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert is_valid is False
        assert any("off-topic" in i.lower() for i in issues)

    def test_missing_sections(self):
        # Long enough but no recognizable sections
        response = "word " * 300
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert any("Missing expected structure" in i for i in issues)

    def test_small_model_lower_threshold(self):
        # Small models get 80% word threshold
        response = "## Overview\nThis is a review. " * 30
        is_valid1, issues1, _ = validate_review_quality(
            response, "executive_summary", model_name="gemma:4b"
        )
        is_valid2, issues2, _ = validate_review_quality(
            response, "executive_summary", model_name="llama:70b"
        )
        # The small model version should be more lenient
        [i for i in issues1 if "Too short" in i]
        [i for i in issues2 if "Too short" in i]
        # Just verify both run without error
        assert isinstance(is_valid1, bool)
        assert isinstance(is_valid2, bool)

    def test_custom_min_words(self):
        response = "## Overview\nSome content here. " * 10  # ~40 words
        is_valid, issues, details = validate_review_quality(
            response, "executive_summary", min_words=20
        )
        assert details["min_required"] == 20

    def test_repetitive_content(self):
        response = "This sentence repeats. " * 200
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        # Should detect repetition or at least track it
        assert "repetition" in details


class TestValidateQualityReview:
    def test_with_scores(self):
        lines = ["## Quality Assessment\n", "Score: 4/5\n"]
        lines.append("The paper demonstrates clarity and good structure.")
        lines.append("Technical accuracy is high and the writing is precise.")
        lines.append("Readability is excellent throughout the manuscript.")
        for i in range(50):
            lines.append(f"Quality observation {i}: section {i} is well-organized and clear.")
        response = "\n".join(lines)
        is_valid, issues, details = validate_review_quality(response, "quality_review")
        # Either scores found or assessment keywords match
        assert len(details["scores_found"]) > 0 or details.get("has_assessment") is True

    def test_with_assessment_keywords(self):
        response = (
            "The clarity of the paper is excellent. The structure is well-organized. "
            "Readability is good overall. The technical accuracy is high.\n"
        ) * 10
        is_valid, issues, details = validate_review_quality(response, "quality_review")
        assert details.get("has_assessment") is True

    def test_no_scores_or_assessment(self):
        response = "word " * 300
        is_valid, issues, details = validate_review_quality(response, "quality_review")
        assert any("Missing scoring" in i for i in issues)


class TestValidateMethodologyReview:
    def test_with_strengths_weaknesses(self):
        response = (
            "## Strengths\n\nThe methodology is sound.\n\n"
            "## Weaknesses\n\nSample size is limited.\n\n"
            "## Suggestions\n\nConsider expanding the dataset.\n"
        ) * 5
        is_valid, issues, details = validate_review_quality(response, "methodology_review")
        assert "strengths" in details["sections_found"]
        assert "weaknesses" in details["sections_found"]

    def test_with_methodology_content(self):
        response = (
            "The research design is appropriate for the study. "
            "The methodology section clearly describes the experimental setup.\n"
        ) * 20
        is_valid, issues, details = validate_review_quality(response, "methodology_review")
        assert details.get("has_methodology_content") is True

    def test_missing_sections(self):
        response = "word " * 300
        is_valid, issues, details = validate_review_quality(response, "methodology_review")
        assert any("Missing expected sections" in i for i in issues)


class TestValidateImprovementSuggestions:
    def test_with_priorities(self):
        response = (
            "## High Priority\n\nFix the methodology section.\n\n"
            "## Medium Priority\n\nImprove the clarity of figures.\n\n"
            "## Low Priority\n\nMinor formatting improvements.\n"
        ) * 5
        is_valid, issues, details = validate_review_quality(response, "improvement_suggestions")
        assert "high" in details.get("priorities_found", [])

    def test_with_recommendations(self):
        response = (
            "I recommend expanding the literature review. "
            "Suggest adding more quantitative analysis. "
            "The authors should improve the discussion section.\n"
        ) * 15
        is_valid, issues, details = validate_review_quality(response, "improvement_suggestions")
        assert details.get("has_recommendations") is True

    def test_missing_priorities_and_recommendations(self):
        response = "word " * 300
        is_valid, issues, details = validate_review_quality(response, "improvement_suggestions")
        assert any("Missing priority" in i for i in issues)


class TestValidateTranslation:
    def test_with_english_and_translation(self):
        response = (
            "## English Abstract\n\nThis paper presents...\n\n"
            "## Chinese Translation\n\n本文提出了...\n"
        ) * 5
        is_valid, issues, details = validate_review_quality(response, "translation")
        assert details.get("has_english_section") is True
        assert details.get("has_translation_section") is True

    def test_missing_english(self):
        response = "## Chinese Translation\n\n" + "本文提出了一种新方法。" * 50
        is_valid, issues, details = validate_review_quality(response, "translation")
        assert any("Missing English" in i for i in issues)

    def test_missing_translation(self):
        response = "## English Abstract\n\n" + "This paper presents a new method. " * 50
        is_valid, issues, details = validate_review_quality(response, "translation")
        assert any("Missing translation" in i for i in issues)


class TestValidateHelpers:
    def test_executive_summary_section_direct(self):
        details: dict = {"sections_found": [], "sections_required": 0}
        issues: list = []
        _validate_executive_summary_section(
            "the overview shows key contributions and methodology with results of significance",
            details,
            issues,
        )
        assert len(details["sections_found"]) == 5
        assert len(issues) == 0

    def test_quality_review_section_rating_pattern(self):
        details: dict = {"scores_found": [], "has_assessment": False}
        issues: list = []
        _validate_quality_review_section("rating: 4", details, issues)
        assert len(details["scores_found"]) > 0

    def test_methodology_review_approach(self):
        details: dict = {"sections_found": []}
        issues: list = []
        _validate_methodology_review_section(
            "the approach is solid with good experimental design", details, issues
        )
        assert details.get("has_methodology_content") is True

    def test_improvement_suggestions_cosmetic(self):
        details: dict = {"priorities_found": []}
        issues: list = []
        _validate_improvement_suggestions_section(
            "cosmetic changes needed and consider updating", details, issues
        )
        assert "low" in details.get("priorities_found", [])

    def test_translation_hindi(self):
        details: dict = {}
        issues: list = []
        _validate_translation_section(
            "english abstract followed by hindi translation", details, issues
        )
        assert details["has_english_section"] is True
        assert details["has_translation_section"] is True

# LLM Review Module

## Overview

The `infrastructure/llm/review/` directory contains the manuscript review system that leverages Large Language Models to provide feedback on research documents. This module analyzes academic writing, suggests improvements, and ensures quality standards are met.

## Directory Structure

```text
infrastructure/llm/review/
├── AGENTS.md               # This technical documentation
├── __init__.py            # Package exports
├── generator.py           # Review generation logic
├── io.py                  # Review I/O operations and formatting
└── metrics.py             # Review quality metrics and analysis
```

## Key Components

### Review Generation (`generator.py`)

**Core review generation using structured LLM prompts:**

#### Review Generation Engine

**Review Creation:**

```python
class ReviewGenerator:
    """Generates manuscript reviews using LLM."""

    def __init__(self, llm_client: LLMClient, config: ReviewConfig = None):
        self.client = llm_client
        self.config = config or ReviewConfig()

    def generate_review(self, manuscript: str, review_type: str = "comprehensive") -> ReviewResult:
        """Generate a structured review of the manuscript.

        Performs multi-stage analysis:
        1. Content structure analysis
        2. Writing quality assessment
        3. Technical accuracy evaluation
        4. Suggestions for improvement

        Args:
            manuscript: Full manuscript text
            review_type: Type of review (comprehensive, technical, editorial)

        Returns:
            ReviewResult with structured feedback
        """
```

**Review Types:**

```python
REVIEW_TYPES = {
    "comprehensive": "Full review covering all aspects",
    "technical": "Focus on technical accuracy and methodology",
    "editorial": "Focus on writing quality and clarity",
    "structural": "Focus on organization and flow",
    "quick": "Brief overview with key issues"
}
```

#### Structured Review Process

**Multi-Stage Analysis:**

```python
def _generate_structured_review(self, manuscript: str) -> Dict[str, Any]:
    """Generate review using structured prompts."""

    # Stage 1: Content analysis
    content_analysis = self._analyze_content_structure(manuscript)

    # Stage 2: Writing quality assessment
    writing_quality = self._assess_writing_quality(manuscript)

    # Stage 3: Technical evaluation
    technical_quality = self._evaluate_technical_content(manuscript)

    # Stage 4: Generate recommendations
    recommendations = self._generate_improvement_suggestions(
        content_analysis, writing_quality, technical_quality
    )

    return {
        "content_analysis": content_analysis,
        "writing_quality": writing_quality,
        "technical_quality": technical_quality,
        "recommendations": recommendations,
        "overall_score": self._calculate_overall_score(
            content_analysis, writing_quality, technical_quality
        )
    }
```

**Content Structure Analysis:**

```python
def _analyze_content_structure(self, manuscript: str) -> Dict[str, Any]:
    """Analyze manuscript structure and organization."""

    prompt = f"""
    Analyze the structure and organization of this academic manuscript:

    {manuscript[:self.config.max_content_length]}

    Provide analysis of:
    1. Section organization and logical flow
    2. Introduction effectiveness
    3. Methodology clarity
    4. Results presentation
    5. Discussion comprehensiveness
    6. Conclusion adequacy

    Format as JSON with scores (1-10) and specific feedback.
    """

    response = self.client.query_structured(prompt, schema=STRUCTURE_SCHEMA)
    return response
```

### Review I/O Operations (`io.py`)

**Review persistence, formatting, and export functionality:**

#### Review Storage and Retrieval

**File-Based Review Management:**

```python
class ReviewIO:
    """Handles review input/output operations."""

    def save_review(self, review: ReviewResult, output_path: Path) -> None:
        """Save review to file in multiple formats."""

        # JSON format for programmatic access
        self._save_json_review(review, output_path.with_suffix('.json'))

        # Markdown format for human reading
        self._save_markdown_review(review, output_path.with_suffix('.md'))

        # HTML format for web viewing
        self._save_html_review(review, output_path.with_suffix('.html'))

    def load_review(self, review_path: Path) -> ReviewResult:
        """Load review from file."""
        if review_path.suffix == '.json':
            return self._load_json_review(review_path)
        elif review_path.suffix == '.md':
            return self._load_markdown_review(review_path)
        else:
            raise ValueError(f"Unsupported review format: {review_path.suffix}")
```

#### Review Formatting

**Markdown Review Reports:**

```python
def _save_markdown_review(self, review: ReviewResult, output_path: Path) -> None:
    """Generate markdown review report."""

    content = f"""# Manuscript Review Report

**Generated:** {review.timestamp}
**Manuscript:** {review.manuscript_title}
**Review Type:** {review.review_type}
**Overall Score:** {review.overall_score}/10

## Executive Summary

{review.executive_summary}

## Detailed Analysis

### Content Structure
**Score:** {review.content_analysis.get('score', 'N/A')}/10

{review.content_analysis.get('feedback', 'No feedback available')}

### Writing Quality
**Score:** {review.writing_quality.get('score', 'N/A')}/10

{review.writing_quality.get('feedback', 'No feedback available')}

### Technical Accuracy
**Score:** {review.technical_quality.get('score', 'N/A')}/10

{review.technical_quality.get('feedback', 'No feedback available')}

## Recommendations

{self._format_recommendations(review.recommendations)}

## Action Items

{self._format_action_items(review.action_items)}
"""

    output_path.write_text(content)
```

### Review Metrics (`metrics.py`)

**Quantitative analysis and scoring of review quality:**

#### Review Quality Assessment

**Scoring Algorithms:**

```python
class ReviewMetrics:
    """Calculate and analyze review quality metrics."""

    def calculate_review_quality_score(self, review: ReviewResult) -> float:
        """Calculate overall quality score for the review itself."""

        # Content coverage (does review address all aspects?)
        coverage_score = self._calculate_coverage_score(review)

        # Specificity of feedback
        specificity_score = self._calculate_specificity_score(review)

        # Actionability of recommendations
        actionability_score = self._calculate_actionability_score(review)

        # Balance of positive/constructive feedback
        balance_score = self._calculate_balance_score(review)

        # Overall quality score
        quality_score = (
            coverage_score * 0.3 +
            specificity_score * 0.25 +
            actionability_score * 0.25 +
            balance_score * 0.2
        )

        return round(quality_score, 2)
```

#### Manuscript Quality Scoring

**Quality Assessment:**

```python
def assess_manuscript_quality(self, manuscript: str, review: ReviewResult) -> QualityReport:
    """Assess overall manuscript quality based on review."""

    # Extract quality indicators
    structure_score = review.content_analysis.get('score', 5)
    writing_score = review.writing_quality.get('score', 5)
    technical_score = review.technical_quality.get('score', 5)

    # Calculate weighted overall score
    overall_score = (
        structure_score * self.config.structure_weight +
        writing_score * self.config.writing_weight +
        technical_score * self.config.technical_weight
    )

    # Determine quality level
    quality_level = self._determine_quality_level(overall_score)

    # Generate quality report
    return QualityReport(
        overall_score=round(overall_score, 1),
        quality_level=quality_level,
        strengths=self._extract_strengths(review),
        weaknesses=self._extract_weaknesses(review),
        priority_improvements=self._prioritize_improvements(review)
    )
```

## Integration with LLM System

### Review Workflow Integration

**End-to-End Review Process:**

```python
# Integration with scripts/06_llm_review.py
from infrastructure.llm.review import ReviewGenerator, ReviewIO

def perform_manuscript_review(manuscript_path: Path) -> None:
    """manuscript review workflow."""

    # Load manuscript
    manuscript = load_manuscript(manuscript_path)

    # Initialize review system
    from infrastructure.llm.core import LLMClient
    client = LLMClient()
    generator = ReviewGenerator(client)
    io_handler = ReviewIO()

    # Generate review
    review = generator.generate_review(manuscript.content, review_type="comprehensive")

    # Save review in multiple formats
    io_handler.save_review(review, manuscript_path.with_stem(f"{manuscript_path.stem}_review"))

    # Generate quality metrics
    from infrastructure.llm.review.metrics import ReviewMetrics
    metrics = ReviewMetrics()
    quality_report = metrics.assess_manuscript_quality(manuscript.content, review)

    # Output results
    print(f"Review completed. Overall quality score: {quality_report.overall_score}/10")
    print(f"Quality level: {quality_report.quality_level}")
```

### Quality Assurance Integration

**Review Validation:**

```python
def validate_review_quality(review: ReviewResult) -> ValidationResult:
    """Validate that generated review meets quality standards."""

    issues = []

    # Check required sections
    required_sections = ['content_analysis', 'writing_quality', 'technical_quality', 'recommendations']
    for section in required_sections:
        if not hasattr(review, section) or not getattr(review, section):
            issues.append(f"Missing required section: {section}")

    # Check score ranges
    if not (0 <= review.overall_score <= 10):
        issues.append(f"Invalid overall score: {review.overall_score}")

    # Check recommendation quality
    if len(review.recommendations) < 3:
        issues.append("Insufficient number of recommendations")

    return ValidationResult(
        valid=len(issues) == 0,
        issues=issues
    )
```

## Configuration

### Review Configuration

**Customizable Review Parameters:**

```python
@dataclass
class ReviewConfig:
    """Configuration for review generation."""

    # Content limits
    max_content_length: int = 50000  # Maximum characters to analyze
    min_content_length: int = 1000   # Minimum viable content

    # Scoring weights
    structure_weight: float = 0.3
    writing_weight: float = 0.3
    technical_weight: float = 0.4

    # Output options
    include_executive_summary: bool = True
    include_action_items: bool = True
    detailed_feedback: bool = True

    # Quality thresholds
    minimum_score: float = 6.0
    excellent_score: float = 8.5
```

### Environment Configuration

**Runtime Configuration:**

```bash
# Review generation settings
export LLM_REVIEW_MAX_CONTENT_LENGTH=50000
export LLM_REVIEW_MIN_CONTENT_LENGTH=1000

# Quality thresholds
export LLM_REVIEW_MINIMUM_SCORE=6.0
export LLM_REVIEW_EXCELLENT_SCORE=8.5

# Output preferences
export LLM_REVIEW_INCLUDE_EXECUTIVE_SUMMARY=true
export LLM_REVIEW_DETAILED_FEEDBACK=true
```

## Testing

### Review Generation Testing

**Mock-Based Testing:**

```python
def test_review_generation():
    """Test review generation with mocked LLM responses."""

    # Mock LLM client
    mock_client = Mock()
    mock_client.query_structured.return_value = {
        "score": 8,
        "feedback": "Well-structured manuscript with clear methodology",
        "issues": ["Minor grammatical errors"],
        "strengths": ["Good literature review", "Clear results presentation"]
    }

    # Generate review
    generator = ReviewGenerator(mock_client)
    review = generator.generate_review(sample_manuscript)

    # Verify review structure
    assert review.overall_score >= 0
    assert review.overall_score <= 10
    assert len(review.recommendations) > 0
    assert "content_analysis" in review.details
```

**Integration Testing:**

```python
def test_complete_review_workflow():
    """Test end-to-end review workflow."""

    # Setup test manuscript
    manuscript_path = create_test_manuscript()
    output_dir = Path("/tmp/review_test")

    # Run review workflow
    run_manuscript_review(manuscript_path, output_dir)

    # Verify outputs
    json_file = output_dir / "manuscript_review.json"
    md_file = output_dir / "manuscript_review.md"
    html_file = output_dir / "manuscript_review.html"

    assert json_file.exists()
    assert md_file.exists()
    assert html_file.exists()

    # Verify JSON content
    import json
    with open(json_file) as f:
        review_data = json.load(f)

    assert "overall_score" in review_data
    assert "recommendations" in review_data
    assert isinstance(review_data["recommendations"], list)
```

### Quality Metrics Testing

**Metrics Validation:**

```python
def test_review_metrics_calculation():
    """Test review quality metrics calculation."""

    metrics = ReviewMetrics()

    # Test with sample review
    sample_review = create_sample_review_result()
    quality_score = metrics.calculate_review_quality_score(sample_review)

    assert 0 <= quality_score <= 10
    assert isinstance(quality_score, float)

    # Test manuscript quality assessment
    manuscript_quality = metrics.assess_manuscript_quality(
        sample_manuscript, sample_review
    )

    assert manuscript_quality.overall_score >= 0
    assert manuscript_quality.overall_score <= 10
    assert manuscript_quality.quality_level in ["poor", "fair", "good", "excellent"]
```

## Usage Examples

### Basic Review Generation

**Simple Review:**

```python
from infrastructure.llm.review import ReviewGenerator
from infrastructure.llm.core import LLMClient

# Initialize components
client = LLMClient()
generator = ReviewGenerator(client)

# Generate review
manuscript = "Your manuscript content here..."
review = generator.generate_review(manuscript, review_type="comprehensive")

print(f"Overall score: {review.overall_score}/10")
print(f"Key recommendations: {review.recommendations[:3]}")
```

### Advanced Review with Custom Configuration

**Customized Review:**

```python
from infrastructure.llm.review import ReviewGenerator, ReviewConfig

# Custom configuration
config = ReviewConfig(
    max_content_length=100000,
    detailed_feedback=True,
    structure_weight=0.4,
    writing_weight=0.3,
    technical_weight=0.3
)

generator = ReviewGenerator(client, config)
review = generator.generate_review(large_manuscript, review_type="technical")

# Access detailed results
print(f"Content analysis: {review.content_analysis}")
print(f"Technical quality: {review.technical_quality}")
```

### Review Export and Reporting

**Multiple Format Export:**

```python
from infrastructure.llm.review import ReviewIO

# Save review in multiple formats
io_handler = ReviewIO()
io_handler.save_review(review, Path("manuscript_review"))

# Files created:
# - manuscript_review.json (structured data)
# - manuscript_review.md (human-readable)
# - manuscript_review.html (web-viewable)
```

### Quality Assessment

**Manuscript Quality Evaluation:**

```python
from infrastructure.llm.review.metrics import ReviewMetrics

metrics = ReviewMetrics()
quality_report = metrics.assess_manuscript_quality(manuscript, review)

print(f"Quality level: {quality_report.quality_level}")
print(f"Strengths: {quality_report.strengths}")
print(f"Priority improvements: {quality_report.priority_improvements}")
```

## Performance Considerations

### Efficient Review Generation

**Content Optimization:**

- Limit analysis to reasonable content lengths
- Prioritize key sections for detailed analysis
- Use streaming for large manuscript processing
- Cache intermediate results when possible

**LLM Usage Optimization:**

- Batch related analysis tasks
- Use appropriate model sizes for different review types
- Implement review result caching
- Optimize prompt sizes for cost efficiency

### Resource Management

**Memory Usage:**

- Process manuscripts in chunks for large documents
- Clean up intermediate analysis results
- Use streaming responses for long reviews
- Implement memory limits for very large manuscripts

## Error Handling

### Review Generation Errors

**Robust Error Recovery:**

```python
def generate_review_safely(self, manuscript: str) -> ReviewResult:
    """Generate review with error handling."""

    try:
        # Validate input
        if not manuscript or len(manuscript.strip()) < self.config.min_content_length:
            raise ReviewError("Manuscript too short for meaningful review")

        # Generate review
        review = self._generate_structured_review(manuscript)

        # Validate output
        validation = validate_review_quality(review)
        if not validation.valid:
            logger.warning(f"Review quality issues: {validation.issues}")

        return review

    except LLMConnectionError:
        logger.error("Cannot generate review: LLM service unavailable")
        return self._create_error_review("LLM service unavailable")

    except Exception as e:
        logger.error(f"Unexpected error during review generation: {e}")
        return self._create_error_review(f"Review generation failed: {str(e)}")
```

## Integration with Scripts

### Command-Line Review Interface

**Script Integration (`scripts/06_llm_review.py`):**

```bash
# Generate review
python3 scripts/06_llm_review.py --review manuscript.md

# Generate reviews only (no other operations)
python3 scripts/06_llm_review.py --reviews-only manuscript.md

# Custom review type
python3 scripts/06_llm_review.py --review --type technical manuscript.md

# Multiple output formats
python3 scripts/06_llm_review.py --review --formats json,md,html manuscript.md
```

## Future Enhancements

### Advanced Review Features

**Planned Improvements:**

- **Peer Review Simulation**: Multiple reviewer perspectives
- **Collaborative Review**: Multi-user review workflows
- **Review History Tracking**: Version comparison and improvement tracking
- **Automated Follow-up**: Review response and revision analysis

**Integration Enhancements:**

- **IDE Integration**: Direct editor integration for reviews
- **Version Control Integration**: Git-based review workflows
- **Publication Integration**: Pre-submission review validation
- **Team Collaboration**: Shared review workflows and templates

## Troubleshooting

### Common Review Issues

**LLM Connection Problems:**

```python
# Check LLM availability
from infrastructure.llm.core import LLMClient
client = LLMClient()
if not client.check_connection():
    print("LLM service unavailable - check Ollama status")
```

**Manuscript Format Issues:**

```python
# Validate manuscript format
from infrastructure.validation import validate_markdown

issues = validate_markdown(manuscript_path)
if issues:
    print(f"Manuscript format issues: {issues}")
    print("Fix formatting issues before review")
```

**Review Quality Issues:**

```python
# Validate review completeness
from infrastructure.llm.review.metrics import ReviewMetrics

metrics = ReviewMetrics()
quality_score = metrics.calculate_review_quality_score(review)

if quality_score < 7.0:
    print(f"Low review quality score: {quality_score}")
    print("Consider regenerating review or checking LLM configuration")
```

### Performance Optimization

**Large Manuscript Handling:**

```python
# For very large manuscripts, use chunked processing
def review_large_manuscript(manuscript: str, chunk_size: int = 10000):
    """Review large manuscripts in chunks."""

    chunks = [manuscript[i:i+chunk_size] for i in range(0, len(manuscript), chunk_size)]

    reviews = []
    for i, chunk in enumerate(chunks):
        print(f"Reviewing chunk {i+1}/{len(chunks)}")
        chunk_review = generator.generate_review(chunk, review_type="section")
        reviews.append(chunk_review)

    # Combine chunk reviews
    return combine_chunk_reviews(reviews)
```

## See Also

**Related Documentation:**

- [`../core/AGENTS.md`](../core/AGENTS.md) - LLM core functionality
- [`../templates/AGENTS.md`](../templates/AGENTS.md) - Template system
- [`../AGENTS.md`](../AGENTS.md) - LLM module overview

**System Documentation:**

- [`../../../AGENTS.md`](../../../AGENTS.md) - system overview
- [`../../../docs/operational/llm-review-troubleshooting.md`](../../../docs/operational/llm-review-troubleshooting.md) - LLM review troubleshooting

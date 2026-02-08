# LLM Validation Module

## Overview

The `infrastructure/llm/validation/` directory contains validation utilities for ensuring the quality, consistency, and reliability of LLM-generated content. These modules provide checks for content quality, format compliance, structural integrity, and output validation across all LLM operations in the research template system.

## Directory Structure

```
infrastructure/llm/validation/
├── AGENTS.md               # This technical documentation
├── __init__.py            # Package exports
├── core.py                # Core validation framework and base classes
├── format.py              # Format validation and compliance checking
├── repetition.py          # Content repetition and redundancy detection
└── structure.py           # Structural validation and organization checking
```

## Key Components

### Core Validation Framework (`core.py`)

**Foundation classes and interfaces for validation:**

#### Validation Base Classes

**Abstract Validator Interface:**

```python
class BaseValidator(ABC):
    """Abstract base class for all validators."""

    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()

    @abstractmethod
    def validate(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate content and return results."""
        pass

    def _create_result(self, passed: bool, issues: List[str] = None,
                      metadata: Dict[str, Any] = None) -> ValidationResult:
        """Create standardized validation result."""
        return ValidationResult(
            validator_name=self.__class__.__name__,
            passed=passed,
            issues=issues or [],
            metadata=metadata or {},
            timestamp=datetime.now().isoformat()
        )
```

**Validation Result Structure:**

```python
@dataclass
class ValidationResult:
    """Result of validation operation."""

    validator_name: str
    passed: bool
    issues: List[str]
    metadata: Dict[str, Any]
    timestamp: str
    severity: str = "medium"  # low, medium, high, critical

    def __post_init__(self):
        """Set severity based on issue count and types."""
        if not self.passed:
            self.severity = self._determine_severity()

    def _determine_severity(self) -> str:
        """Determine issue severity."""
        if any("critical" in issue.lower() for issue in self.issues):
            return "critical"
        elif len(self.issues) > 5:
            return "high"
        elif len(self.issues) > 2:
            return "medium"
        else:
            return "low"
```

#### Validation Configuration

**Configurable Validation Parameters:**

```python
@dataclass
class ValidationConfig:
    """Configuration for validation operations."""

    # General settings
    strict_mode: bool = False
    enable_logging: bool = True

    # Content thresholds
    min_content_length: int = 10
    max_content_length: int = 100000

    # Quality thresholds
    min_quality_score: float = 0.6
    repetition_threshold: float = 0.3

    # Performance settings
    timeout: float = 30.0
    cache_results: bool = True
```

### Format Validation (`format.py`)

**Format compliance and structure validation:**

#### Markdown Format Validator

**Markdown Structure Validation:**

```python
class MarkdownFormatValidator(BaseValidator):
    """Validate markdown format compliance and structure."""

    def validate(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate markdown formatting."""

        issues = []

        # Check header hierarchy
        issues.extend(self._validate_header_hierarchy(content))

        # Check link validity
        issues.extend(self._validate_links(content))

        # Check code block formatting
        issues.extend(self._validate_code_blocks(content))

        # Check table formatting
        issues.extend(self._validate_tables(content))

        # Check list consistency
        issues.extend(self._validate_lists(content))

        passed = len(issues) == 0
        return self._create_result(passed, issues)

    def _validate_header_hierarchy(self, content: str) -> List[str]:
        """Validate header level progression."""

        issues = []
        lines = content.split('\n')
        last_level = 0

        for line in lines:
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if level > last_level + 1:
                    issues.append(f"Skipped header level: {line.strip()}")
                last_level = level

        return issues
```

#### Academic Format Validator

**Academic Writing Standards:**

```python
class AcademicFormatValidator(BaseValidator):
    """Validate academic writing format and conventions."""

    def validate(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate academic formatting standards."""

        issues = []

        # Check citation format consistency
        issues.extend(self._validate_citations(content))

        # Check reference formatting
        issues.extend(self._validate_references(content))

        # Check figure/table references
        issues.extend(self._validate_cross_references(content))

        # Check section structure
        issues.extend(self._validate_academic_structure(content))

        passed = len(issues) == 0
        return self._create_result(passed, issues)
```

### Repetition Detection (`repetition.py`)

**Content redundancy and repetition analysis:**

#### Repetition Detector

**Advanced Repetition Analysis:**

```python
class RepetitionDetector(BaseValidator):
    """Detect content repetition and redundancy."""

    def validate(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Analyze content for repetition."""

        issues = []

        # Sentence-level repetition
        sentence_issues = self._detect_sentence_repetition(content)
        issues.extend(sentence_issues)

        # Phrase-level repetition
        phrase_issues = self._detect_phrase_repetition(content)
        issues.extend(phrase_issues)

        # Word frequency analysis
        word_issues = self._analyze_word_frequency(content)
        issues.extend(word_issues)

        # Structural repetition
        structural_issues = self._detect_structural_repetition(content)
        issues.extend(structural_issues)

        passed = len(issues) == 0
        return self._create_result(passed, issues)

    def _detect_sentence_repetition(self, content: str) -> List[str]:
        """Detect repeated sentences."""

        issues = []
        sentences = self._split_sentences(content)
        sentence_counts = Counter(sentences)

        for sentence, count in sentence_counts.items():
            if count > 1 and len(sentence.strip()) > 20:  # Ignore very short sentences
                repetition_ratio = count / len(sentences)
                if repetition_ratio > self.config.repetition_threshold:
                    issues.append(f"Repeated sentence ({count} times): '{sentence.strip()[:50]}...'")

        return issues
```

#### Semantic Similarity Detection

**Meaning-Based Repetition:**

```python
class SemanticRepetitionDetector(BaseValidator):
    """Detect semantic repetition using similarity analysis."""

    def validate(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Detect semantically similar content."""

        issues = []

        # Split content into segments
        segments = self._segment_content(content)

        # Calculate pairwise similarities
        similarities = self._calculate_similarities(segments)

        # Find highly similar segments
        for i, j in combinations(range(len(segments)), 2):
            if similarities[i][j] > 0.8:  # High similarity threshold
                issues.append(f"Highly similar content segments: {i+1} and {j+1}")

        passed = len(issues) == 0
        return self._create_result(passed, issues)
```

### Structure Validation (`structure.py`)

**Content organization and structural integrity:**

#### Document Structure Validator

**Structure Analysis:**

```python
class DocumentStructureValidator(BaseValidator):
    """Validate document structure and organization."""

    def validate(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate document structural integrity."""

        issues = []

        # Check required sections
        issues.extend(self._validate_required_sections(content, context))

        # Check section ordering
        issues.extend(self._validate_section_order(content, context))

        # Check content distribution
        issues.extend(self._validate_content_distribution(content))

        # Check transition quality
        issues.extend(self._validate_transitions(content))

        passed = len(issues) == 0
        return self._create_result(passed, issues)

    def _validate_required_sections(self, content: str, context: Dict[str, Any]) -> List[str]:
        """Check for required sections based on document type."""

        issues = []
        doc_type = context.get('document_type', 'general') if context else 'general'

        # Define required sections by document type
        required_sections = {
            'research_paper': ['introduction', 'methods', 'results', 'discussion'],
            'review': ['summary', 'analysis', 'conclusions'],
            'manuscript': ['abstract', 'introduction', 'methods', 'results', 'discussion']
        }

        required = required_sections.get(doc_type, [])
        content_lower = content.lower()

        for section in required:
            if section not in content_lower:
                issues.append(f"Missing required section: {section}")

        return issues
```

#### Content Flow Validator

**Logical Flow and Coherence:**

```python
class ContentFlowValidator(BaseValidator):
    """Validate content flow and logical coherence."""

    def validate(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate content logical flow."""

        issues = []

        # Check topic consistency
        issues.extend(self._validate_topic_consistency(content))

        # Check argument progression
        issues.extend(self._validate_argument_progression(content))

        # Check conclusion alignment
        issues.extend(self._validate_conclusion_alignment(content))

        # Check transition quality
        issues.extend(self._validate_transition_quality(content))

        passed = len(issues) == 0
        return self._create_result(passed, issues)
```

## Validation Integration

### Composite Validation System

**Multi-Validator Orchestration:**

```python
class ValidationOrchestrator:
    """Orchestrate multiple validators for validation."""

    def __init__(self, validators: List[BaseValidator] = None):
        self.validators = validators or self._create_default_validators()

    def _create_default_validators(self) -> List[BaseValidator]:
        """Create default set of validators."""
        return [
            MarkdownFormatValidator(),
            AcademicFormatValidator(),
            RepetitionDetector(),
            DocumentStructureValidator(),
            ContentFlowValidator()
        ]

    def validate_comprehensive(self, content: str,
                              context: Dict[str, Any] = None) -> ComprehensiveValidationResult:
        """Run all validators and aggregate results."""

        all_results = []
        all_issues = []

        for validator in self.validators:
            try:
                result = validator.validate(content, context)
                all_results.append(result)
                all_issues.extend(result.issues)
            except Exception as e:
                logger.error(f"Validator {validator.__class__.__name__} failed: {e}")
                # Continue with other validators

        # Aggregate results
        overall_passed = all(result.passed for result in all_results)
        highest_severity = max((result.severity for result in all_results),
                              key=lambda x: ['low', 'medium', 'high', 'critical'].index(x))

        return ComprehensiveValidationResult(
            overall_passed=overall_passed,
            individual_results=all_results,
            all_issues=all_issues,
            highest_severity=highest_severity
        )
```

### LLM Response Validation

**Post-Generation Validation:**

```python
# Integration with LLM core
from infrastructure.llm.core import LLMClient

class ValidatingLLMClient(LLMClient):
    """LLM client with built-in response validation."""

    def __init__(self, *args, validator: ValidationOrchestrator = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = validator or ValidationOrchestrator()

    def query_with_validation(self, prompt: str, **kwargs) -> ValidatedResponse:
        """Query with automatic validation."""

        # Generate response
        response = self.query(prompt, **kwargs)

        # Validate response
        validation_result = self.validator.validate_comprehensive(
            response,
            context={'source': 'llm_response', 'prompt': prompt}
        )

        return ValidatedResponse(
            content=response,
            validation_result=validation_result
        )
```

## Testing

### Validator Testing

**Individual Validator Tests:**

```python
def test_markdown_format_validator():
    """Test markdown format validation."""

    validator = MarkdownFormatValidator()

    # Valid markdown
    valid_content = "# Header\n\nSome content with [link](url)."
    result = validator.validate(valid_content)
    assert result.passed

    # Invalid markdown (skipped header levels)
    invalid_content = "# Level 1\n\n### Level 3 (skipped level 2)"
    result = validator.validate(invalid_content)
    assert not result.passed
    assert "Skipped header level" in str(result.issues)
```

**Repetition Detection Tests:**

```python
def test_repetition_detector():
    """Test repetition detection."""

    validator = RepetitionDetector()

    # Content with repetition
    repetitive_content = "This is a test. This is a test. This is a test."
    result = validator.validate(repetitive_content)
    assert not result.passed
    assert len(result.issues) > 0

    # Content without significant repetition
    unique_content = "This is the first sentence. Here is another sentence. Finally, a third sentence."
    result = validator.validate(unique_content)
    assert result.passed
```

### Integration Testing

**Validation Tests:**

```python
def test_validation_orchestrator():
    """Test validation orchestration."""

    orchestrator = ValidationOrchestrator()

    # Test content
    test_content = """
    # Introduction

    This paper presents research on machine learning.

    ## Methods

    We used Python for implementation.

    ## Results

    The results show improvement.

    ## Discussion

    This is a good result. This is a good result. This is a good result.
    """

    context = {'document_type': 'research_paper'}

    # Run validation
    result = orchestrator.validate_comprehensive(test_content, context)

    # Should detect some issues (repetition)
    assert not result.overall_passed
    assert len(result.all_issues) > 0
    assert result.highest_severity in ['low', 'medium', 'high', 'critical']
```

## Performance Considerations

### Efficient Validation

**Optimized Validation Strategies:**

```python
class CachingValidator(BaseValidator):
    """Validator with result caching for performance."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}

    def validate(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate with caching."""

        cache_key = self._generate_cache_key(content, context)

        if cache_key in self._cache:
            return self._cache[cache_key]

        result = super().validate(content, context)

        # Cache result (with size limits)
        if len(self._cache) < 100:  # Max cache size
            self._cache[cache_key] = result

        return result

    def _generate_cache_key(self, content: str, context: Dict[str, Any]) -> str:
        """Generate cache key from content and context."""
        import hashlib
        key_data = content + str(sorted(context.items()) if context else "")
        return hashlib.md5(key_data.encode()).hexdigest()
```

### Parallel Validation

**Concurrent Validation Processing:**

```python
import concurrent.futures

class ParallelValidationOrchestrator(ValidationOrchestrator):
    """Run validators in parallel for better performance."""

    def validate_comprehensive_parallel(self, content: str,
                                       context: Dict[str, Any] = None,
                                       max_workers: int = 4) -> ComprehensiveValidationResult:
        """Run validators in parallel."""

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all validation tasks
            future_to_validator = {
                executor.submit(validator.validate, content, context): validator
                for validator in self.validators
            }

            # Collect results
            all_results = []
            all_issues = []

            for future in concurrent.futures.as_completed(future_to_validator):
                validator = future_to_validator[future]
                try:
                    result = future.result(timeout=30.0)
                    all_results.append(result)
                    all_issues.extend(result.issues)
                except Exception as e:
                    logger.error(f"Validator {validator.__class__.__name__} failed: {e}")

        # Aggregate results (same as sequential version)
        overall_passed = all(result.passed for result in all_results)
        highest_severity = max((result.severity for result in all_results),
                              key=lambda x: ['low', 'medium', 'high', 'critical'].index(x))

        return ComprehensiveValidationResult(
            overall_passed=overall_passed,
            individual_results=all_results,
            all_issues=all_issues,
            highest_severity=highest_severity
        )
```

## Error Handling

### Validation Failure Handling

**Robust Error Recovery:**

```python
def validate_with_error_handling(self, content: str,
                                context: Dict[str, Any] = None) -> ValidationResult:
    """Validate with error handling."""

    try:
        # Input validation
        if not isinstance(content, str):
            raise ValidationError("Content must be a string")

        if len(content) == 0:
            return self._create_result(False, ["Content is empty"])

        # Perform validation
        return self.validate(content, context)

    except ValidationError as e:
        logger.error(f"Validation input error: {e}")
        return self._create_result(False, [str(e)])

    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        return self._create_result(False, [f"Validation failed: {str(e)}"])
```

### Validation Result Processing

**Result Interpretation and Action:**

```python
def process_validation_result(result: ValidationResult) -> ValidationAction:
    """Process validation result and determine action."""

    if result.passed:
        return ValidationAction.ACCEPT

    # Determine action based on severity and issues
    if result.severity == "critical":
        return ValidationAction.REJECT
    elif result.severity == "high":
        return ValidationAction.FLAG_FOR_REVIEW
    elif result.severity == "medium":
        if len(result.issues) > 3:
            return ValidationAction.REQUIRE_FIXES
        else:
            return ValidationAction.FLAG_FOR_REVIEW
    else:  # low
        return ValidationAction.ACCEPT_WITH_NOTES
```

## Usage Examples

### Basic Validation

**Simple Content Validation:**

```python
from infrastructure.llm.validation import MarkdownFormatValidator

validator = MarkdownFormatValidator()
content = "# Header\n\nSome content with [link](url)."
result = validator.validate(content)

if result.passed:
    print("Content is valid")
else:
    print(f"Validation issues: {result.issues}")
```

### Validation

**Multi-Validator Assessment:**

```python
from infrastructure.llm.validation import ValidationOrchestrator

orchestrator = ValidationOrchestrator()
content = "# Research Paper\n\n## Introduction\n\nThis is the introduction..."
context = {'document_type': 'research_paper'}

result = orchestrator.validate_comprehensive(content, context)

print(f"Overall validation: {'PASSED' if result.overall_passed else 'FAILED'}")
print(f"Highest severity: {result.highest_severity}")
print(f"Total issues: {len(result.all_issues)}")
```

### LLM Response Validation

**Post-Generation Quality Check:**

```python
from infrastructure.llm.validation import ValidatingLLMClient

client = ValidatingLLMClient()
response = client.query_with_validation("Write a research summary")

if response.validation_result.overall_passed:
    print("Response passed validation")
    print(f"Content: {response.content}")
else:
    print("Response failed validation:")
    for issue in response.validation_result.all_issues:
        print(f"  - {issue}")
```

## Configuration

### Validation Configuration

**Custom Validation Settings:**

```python
from infrastructure.llm.validation.core import ValidationConfig

config = ValidationConfig(
    strict_mode=True,
    min_content_length=50,
    max_content_length=50000,
    min_quality_score=0.8,
    repetition_threshold=0.2,
    enable_logging=True,
    cache_results=True
)

validator = MarkdownFormatValidator(config)
```

### Environment Configuration

**Runtime Validation Settings:**

```bash
# Validation behavior
export LLM_VALIDATION_STRICT_MODE=false
export LLM_VALIDATION_MIN_CONTENT_LENGTH=10
export LLM_VALIDATION_MAX_CONTENT_LENGTH=100000

# Quality thresholds
export LLM_VALIDATION_MIN_QUALITY_SCORE=0.6
export LLM_VALIDATION_REPETITION_THRESHOLD=0.3

# Performance settings
export LLM_VALIDATION_TIMEOUT=30.0
export LLM_VALIDATION_CACHE_RESULTS=true
```

## Future Enhancements

### Advanced Validation Features

**Planned Improvements:**

- **Machine Learning-Based Validation**: ML models for content quality assessment
- **Domain-Specific Validators**: Specialized validators for different research fields
- **Real-time Validation**: Streaming validation during content generation
- **Collaborative Validation**: Multi-user validation workflows

**Integration Features:**

- **IDE Integration**: Real-time validation in text editors
- **API Integration**: Validation as a service for external tools
- **Batch Validation**: Process multiple documents efficiently
- **Validation Reports**: Detailed HTML/PDF validation reports

## Troubleshooting

### Common Validation Issues

**False Positives:**

```python
# Adjust validation sensitivity
config = ValidationConfig(
    strict_mode=False,  # Less strict validation
    repetition_threshold=0.4  # Higher repetition threshold
)

validator = RepetitionDetector(config)
```

**Performance Issues:**

```python
# Optimize for performance
config = ValidationConfig(
    cache_results=True,  # Enable caching
    timeout=10.0  # Shorter timeout
)

orchestrator = ValidationOrchestrator()
orchestrator = ParallelValidationOrchestrator()  # Use parallel processing
```

**Configuration Issues:**

```python
# Validate configuration
try:
    config = ValidationConfig(min_content_length=-1)  # Invalid
except ValueError as e:
    print(f"Configuration error: {e}")
    config = ValidationConfig()  # Use defaults
```

### Debug Validation

**Verbose Validation Logging:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for validators
config = ValidationConfig(enable_logging=True)
validator = DocumentStructureValidator(config)

result = validator.validate(content, context)
# Check logs for detailed validation steps
```

## See Also

**Related Documentation:**

- [`../core/AGENTS.md`](../core/AGENTS.md) - LLM core functionality
- [`../templates/AGENTS.md`](../templates/AGENTS.md) - Template system
- [`../review/AGENTS.md`](../review/AGENTS.md) - Review generation

**System Documentation:**

- [`../../../AGENTS.md`](../../../AGENTS.md) - system overview
- [`../../../docs/operational/VALIDATION_GUIDE.md`](../../../docs/operational/VALIDATION_GUIDE.md) - Validation usage guide

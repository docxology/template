# LLM Templates Module

## Overview

The `infrastructure/llm/templates/` directory contains specialized template classes that provide high-level interfaces for common LLM operations. These templates combine prompt engineering, context management, and response processing into reusable components for research workflows.

## Directory Structure

```
infrastructure/llm/templates/
├── AGENTS.md               # This technical documentation
├── __init__.py            # Package exports
├── base.py                # Base template classes and interfaces
├── helpers.py             # Template utility functions and helpers
├── manuscript.py          # Manuscript-specific templates
└── research.py            # General research workflow templates
```

## Key Components

### Base Template Classes (`base.py`)

**Foundation classes for template implementation:**

#### Template Base Class

**Abstract Template Interface:**
```python
class BaseTemplate(ABC):
    """Abstract base class for LLM templates."""

    def __init__(self, llm_client: LLMClient, config: TemplateConfig = None):
        self.client = llm_client
        self.config = config or TemplateConfig()
        self._setup_template()

    @abstractmethod
    def apply(self, **kwargs) -> TemplateResult:
        """Apply the template with given parameters."""
        pass

    def _setup_template(self):
        """Setup template-specific configuration."""
        pass

    def _validate_inputs(self, **kwargs) -> None:
        """Validate template inputs."""
        pass

    def _preprocess_inputs(self, **kwargs) -> Dict[str, Any]:
        """Preprocess inputs before template application."""
        return kwargs

    def _postprocess_result(self, result: Any) -> TemplateResult:
        """Postprocess template results."""
        return TemplateResult(
            content=result,
            metadata=self._extract_metadata(result),
            template_name=self.__class__.__name__
        )
```

#### Template Configuration

**Configuration Management:**
```python
@dataclass
class TemplateConfig:
    """Configuration for template behavior."""

    # Response settings
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: float = 60.0

    # Processing options
    validate_inputs: bool = True
    preprocess_inputs: bool = True
    postprocess_results: bool = True

    # Error handling
    retry_on_failure: bool = True
    max_retries: int = 2

    # Logging
    enable_logging: bool = True
    log_level: str = "INFO"
```

### Template Helpers (`helpers.py`)

**Utility functions for template operations:**

#### Input Validation Helpers

**Content Validation:**
```python
def validate_content_length(content: str, min_length: int = 10,
                          max_length: int = 100000) -> None:
    """Validate content length constraints."""

    if len(content) < min_length:
        raise TemplateError(f"Content too short: {len(content)} < {min_length}")

    if len(content) > max_length:
        raise TemplateError(f"Content too long: {len(content)} > {max_length}")

def validate_research_content(content: str) -> List[str]:
    """Validate research content for completeness."""

    issues = []

    # Check for required elements
    if not content.strip():
        issues.append("Content is empty")

    # Check for minimum research indicators
    research_indicators = ['method', 'result', 'analysis', 'conclusion']
    content_lower = content.lower()

    found_indicators = sum(1 for indicator in research_indicators
                          if indicator in content_lower)

    if found_indicators < 2:
        issues.append("Content lacks research structure indicators")

    return issues
```

#### Response Processing Helpers

**Result Formatting:**
```python
def format_template_result(content: Any, template_name: str,
                          metadata: Dict[str, Any] = None) -> TemplateResult:
    """Format template results consistently."""

    return TemplateResult(
        content=content,
        metadata=metadata or {},
        template_name=template_name,
        timestamp=datetime.now().isoformat(),
        success=True
    )

def extract_structured_response(response: str, expected_fields: List[str]) -> Dict[str, Any]:
    """Extract structured data from LLM responses."""

    extracted = {}

    for field in expected_fields:
        # Try different extraction patterns
        patterns = [
            rf"{field}:(.*?)(?=\n\w+:|$)",  # Field: value
            rf"\*\*{field}\*\*:(.*?)(?=\n\*\*\w+\*\*:|$)",  # **Field**: value
            rf"### {field}\n(.*?)(?=\n### |\Z)"  # ### Field\ncontent
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                extracted[field] = match.group(1).strip()
                break

    return extracted
```

### Manuscript Templates (`manuscript.py`)

**Templates specialized for manuscript processing:**

#### Manuscript Review Template

**Review Generation:**
```python
class ManuscriptReviewTemplate(BaseTemplate):
    """Template for generating manuscript reviews."""

    def apply(self, manuscript: str, review_type: str = "comprehensive",
              focus_areas: List[str] = None) -> TemplateResult:
        """Generate a review of the manuscript."""

        # Validate inputs
        self._validate_inputs(manuscript=manuscript, review_type=review_type)

        # Prepare prompt
        prompt = self._build_review_prompt(manuscript, review_type, focus_areas)

        # Generate review
        response = self.client.query_structured(
            prompt,
            schema=self._get_review_schema(),
            options=GenerationOptions(max_tokens=self.config.max_tokens)
        )

        # Postprocess result
        return self._postprocess_result(response)

    def _build_review_prompt(self, manuscript: str, review_type: str,
                           focus_areas: List[str]) -> str:
        """Build the review prompt using prompt system."""

        from infrastructure.llm.prompts import PromptComposer

        composer = PromptComposer()
        variables = {
            'manuscript_content': manuscript,
            'review_type': review_type,
            'word_count': len(manuscript.split()),
            'focus_areas': ', '.join(focus_areas or [])
        }

        return composer.compose_prompt('manuscript_reviews', variables)
```

#### Manuscript Summary Template

**Executive Summary Generation:**
```python
class ManuscriptSummaryTemplate(BaseTemplate):
    """Template for generating manuscript summaries."""

    def apply(self, manuscript: str, summary_type: str = "executive",
              max_length: int = 500) -> TemplateResult:
        """Generate a summary of the manuscript."""

        # Preprocess manuscript
        processed_content = self._preprocess_manuscript(manuscript)

        # Build summary prompt
        prompt = self._build_summary_prompt(processed_content, summary_type, max_length)

        # Generate summary
        response = self.client.query(
            prompt,
            options=GenerationOptions(
                max_tokens=min(max_length // 4, 1000),  # Estimate tokens
                temperature=0.3  # Lower temperature for consistency
            )
        )

        return self._postprocess_result(response)
```

### Research Templates (`research.py`)

**General research workflow templates:**

#### Research Question Refinement Template

**Question Development and Refinement:**
```python
class ResearchQuestionTemplate(BaseTemplate):
    """Template for refining research questions."""

    def apply(self, topic: str, current_questions: List[str] = None,
              context: str = None) -> TemplateResult:
        """Refine and improve research questions."""

        variables = {
            'topic': topic,
            'current_questions': '\n'.join(current_questions or []),
            'context': context or ''
        }

        prompt = self._build_question_prompt(variables)

        response = self.client.query_structured(
            prompt,
            schema=self._get_question_schema()
        )

        return self._postprocess_result(response)
```

#### Methodology Review Template

**Methodological Evaluation:**
```python
class MethodologyReviewTemplate(BaseTemplate):
    """Template for reviewing research methodologies."""

    def apply(self, methodology_description: str,
              research_type: str = "empirical") -> TemplateResult:
        """Review and provide feedback on research methodology."""

        # Build methodology prompt
        prompt = self._build_methodology_prompt(methodology_description, research_type)

        # Get structured review
        response = self.client.query_structured(
            prompt,
            schema=self._get_methodology_schema()
        )

        return self._postprocess_result(response)
```

## Template Architecture

### Template Result Structure

**Standardized Result Format:**
```python
@dataclass
class TemplateResult:
    """Result from template application."""

    content: Any                    # Main result content
    metadata: Dict[str, Any]        # Additional metadata
    template_name: str             # Name of template used
    timestamp: str                 # ISO timestamp
    success: bool                  # Success indicator
    error_message: Optional[str] = None  # Error details if failed
    processing_time: Optional[float] = None  # Processing duration
    token_usage: Optional[Dict[str, int]] = None  # Token consumption
```

### Template Categories

**Manuscript Templates:**
- **ManuscriptReviewTemplate**: manuscript evaluation
- **ManuscriptSummaryTemplate**: Executive and technical summaries
- **ManuscriptOutlineTemplate**: Structure and organization review

**Research Templates:**
- **ResearchQuestionTemplate**: Question development and refinement
- **MethodologyReviewTemplate**: Methodological evaluation and feedback
- **LiteratureReviewTemplate**: Literature synthesis and gap analysis

## Integration with LLM System

### Template Factory Pattern

**Dynamic Template Instantiation:**
```python
class TemplateFactory:
    """Factory for creating template instances."""

    _templates = {
        'manuscript_review': ManuscriptReviewTemplate,
        'manuscript_summary': ManuscriptSummaryTemplate,
        'research_question': ResearchQuestionTemplate,
        'methodology_review': MethodologyReviewTemplate
    }

    @classmethod
    def create_template(cls, name: str, llm_client: LLMClient,
                       config: TemplateConfig = None) -> BaseTemplate:
        """Create a template instance by name."""

        template_class = cls._templates.get(name)
        if not template_class:
            raise TemplateError(f"Unknown template: {name}")

        return template_class(llm_client, config)
```

### Template Pipeline Integration

**Workflow Integration:**
```python
# Integration with scripts/06_llm_review.py
from infrastructure.llm.templates import TemplateFactory

def generate_manuscript_review(manuscript_path: Path) -> None:
    """Generate manuscript review using templates."""

    # Load manuscript
    manuscript = load_manuscript(manuscript_path)

    # Create LLM client
    from infrastructure.llm.core import LLMClient
    client = LLMClient()

    # Create review template
    template = TemplateFactory.create_template('manuscript_review', client)

    # Apply template
    result = template.apply(manuscript=manuscript.content)

    # Process result
    if result.success:
        save_review_result(result, manuscript_path)
        print(f"Review generated successfully in {result.processing_time:.2f}s")
    else:
        print(f"Review generation failed: {result.error_message}")
```

## Testing

### Template Testing Framework

**Base Template Tests:**
```python
def test_base_template_interface():
    """Test base template interface compliance."""

    # Mock LLM client
    mock_client = Mock()

    # Create template instance
    template = BaseTemplate(mock_client)

    # Test abstract method (should raise NotImplementedError)
    with pytest.raises(NotImplementedError):
        template.apply()

    # Test configuration
    assert template.config is not None
    assert template.client == mock_client
```

**Manuscript Template Tests:**
```python
def test_manuscript_review_template():
    """Test manuscript review template functionality."""

    # Mock client with structured response
    mock_client = Mock()
    mock_response = {
        'overall_assessment': 'Good manuscript with strong methodology',
        'strengths': ['Clear writing', 'Solid methods'],
        'weaknesses': ['Limited discussion of limitations'],
        'recommendations': ['Add more detail on limitations']
    }
    mock_client.query_structured.return_value = mock_response

    # Create template
    template = ManuscriptReviewTemplate(mock_client)

    # Apply template
    result = template.apply(manuscript="Sample manuscript content...")

    # Verify result
    assert result.success
    assert result.template_name == 'ManuscriptReviewTemplate'
    assert 'overall_assessment' in result.content
    assert len(result.content['recommendations']) > 0
```

### Integration Testing

**End-to-End Template Testing:**
```python
def test_template_pipeline_integration():
    """Test template pipeline."""

    # Setup test environment
    manuscript = create_test_manuscript()
    client = create_test_llm_client()

    # Test review template
    review_template = ManuscriptReviewTemplate(client)
    review_result = review_template.apply(manuscript=manuscript)

    assert review_result.success
    assert isinstance(review_result.content, dict)

    # Test summary template
    summary_template = ManuscriptSummaryTemplate(client)
    summary_result = summary_template.apply(manuscript=manuscript)

    assert summary_result.success
    assert isinstance(summary_result.content, str)
    assert len(summary_result.content) > 50
```

## Performance Considerations

### Template Optimization

**Efficient Template Execution:**
```python
def apply_with_performance_tracking(self, **kwargs) -> TemplateResult:
    """Apply template with performance monitoring."""

    start_time = time.time()

    try:
        # Apply template
        result = self.apply(**kwargs)

        # Add performance metadata
        processing_time = time.time() - start_time
        result.processing_time = processing_time

        # Log performance
        logger.info(f"Template {self.__class__.__name__} completed in {processing_time:.2f}s")

        return result

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Template {self.__class__.__name__} failed after {processing_time:.2f}s: {e}")
        raise
```

### Caching and Reuse

**Template Result Caching:**
```python
class TemplateCache:
    """Cache template results for performance."""

    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size

    def get(self, key: str) -> Optional[TemplateResult]:
        """Get cached result."""
        return self.cache.get(key)

    def put(self, key: str, result: TemplateResult) -> None:
        """Cache result."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = result
```

## Error Handling

### Template-Specific Errors

**Error Management:**
```python
class TemplateError(Exception):
    """Base exception for template errors."""
    pass

class TemplateValidationError(TemplateError):
    """Raised when template inputs are invalid."""
    pass

class TemplateExecutionError(TemplateError):
    """Raised when template execution fails."""
    pass

def apply_with_error_handling(self, **kwargs) -> TemplateResult:
    """Apply template with error handling."""

    try:
        # Validate inputs
        if self.config.validate_inputs:
            self._validate_inputs(**kwargs)

        # Apply template
        result = self.apply(**kwargs)

        return result

    except TemplateValidationError as e:
        logger.error(f"Template validation failed: {e}")
        return TemplateResult(
            content=None,
            metadata={'error_type': 'validation'},
            template_name=self.__class__.__name__,
            success=False,
            error_message=str(e)
        )

    except Exception as e:
        logger.error(f"Template execution failed: {e}")
        return TemplateResult(
            content=None,
            metadata={'error_type': 'execution'},
            template_name=self.__class__.__name__,
            success=False,
            error_message=str(e)
        )
```

## Usage Examples

### Basic Template Usage

**Manuscript Review:**
```python
from infrastructure.llm.templates import ManuscriptReviewTemplate
from infrastructure.llm.core import LLMClient

# Initialize components
client = LLMClient()
template = ManuscriptReviewTemplate(client)

# Generate review
result = template.apply(
    manuscript=manuscript_text,
    review_type="technical",
    focus_areas=["methodology", "results"]
)

print(f"Review: {result.content['overall_assessment']}")
```

### Advanced Template Configuration

**Custom Configuration:**
```python
from infrastructure.llm.templates.base import TemplateConfig

# Custom configuration
config = TemplateConfig(
    max_tokens=4096,
    temperature=0.5,
    timeout=120.0,
    validate_inputs=True,
    enable_logging=True
)

template = ManuscriptReviewTemplate(client, config)
```

### Template Factory Usage

**Dynamic Template Creation:**
```python
from infrastructure.llm.templates import TemplateFactory

# Create templates by name
review_template = TemplateFactory.create_template('manuscript_review', client)
summary_template = TemplateFactory.create_template('manuscript_summary', client)

# Apply different templates
review_result = review_template.apply(manuscript=text)
summary_result = summary_template.apply(manuscript=text)
```

## Configuration

### Template Configuration Options

**Global Template Settings:**
```bash
# Template behavior settings
export LLM_TEMPLATE_MAX_TOKENS=4096
export LLM_TEMPLATE_TEMPERATURE=0.7
export LLM_TEMPLATE_TIMEOUT=60.0

# Validation settings
export LLM_TEMPLATE_VALIDATE_INPUTS=true
export LLM_TEMPLATE_ENABLE_LOGGING=true

# Performance settings
export LLM_TEMPLATE_MAX_RETRIES=2
export LLM_TEMPLATE_CACHE_SIZE=50
```

### Template-Specific Configuration

**Manuscript Template Settings:**
```python
# Manuscript-specific configuration
manuscript_config = TemplateConfig(
    max_tokens=3000,  # Longer for detailed reviews
    temperature=0.6,  # Moderate creativity
    validate_inputs=True,
    preprocess_inputs=True  # Clean and format manuscript
)
```

## Future Enhancements

### Advanced Template Features

**Planned Improvements:**
- **Template Composition**: Combine multiple templates in workflows
- **Template Versioning**: Version management and migration
- **Template Metrics**: Performance tracking and optimization
- **Template Learning**: Adaptive template improvement

**Integration Features:**
- **IDE Integration**: Direct template application in editors
- **Batch Processing**: Process multiple documents with templates
- **Template Chains**: Sequential template application pipelines
- **Custom Template Marketplace**: User-created template sharing

## Troubleshooting

### Common Template Issues

**Input Validation Failures:**
```python
# Check input requirements
template = ManuscriptReviewTemplate(client)

try:
    result = template.apply(manuscript="")  # Empty manuscript
except TemplateValidationError as e:
    print(f"Validation failed: {e}")
    print("Ensure manuscript content is provided and meets length requirements")
```

**LLM Response Issues:**
```python
# Check LLM client configuration
client = LLMClient()

# Test basic connectivity
test_response = client.query("Hello")
if not test_response:
    print("LLM client not responding - check Ollama configuration")

# Check model availability
available_models = get_available_models()
if not available_models:
    print("No models available - install models with: ollama pull <model-name>")
```

**Performance Issues:**
```python
# Monitor template performance
import time

start_time = time.time()
result = template.apply(**kwargs)
end_time = time.time()

print(f"Template execution time: {end_time - start_time:.2f} seconds")

if result.processing_time and result.processing_time > 30:
    print("Template execution is slow - consider optimizing token limits or model selection")
```

### Debug Template Execution

**Verbose Template Logging:**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Create template with debug config
config = TemplateConfig(enable_logging=True, log_level="DEBUG")
template = ManuscriptReviewTemplate(client, config)

# Apply with detailed logging
result = template.apply(manuscript=text)
```

## See Also

**Related Documentation:**
- [`../core/AGENTS.md`](../core/AGENTS.md) - LLM core functionality
- [`../prompts/AGENTS.md`](../prompts/AGENTS.md) - Prompt engineering system
- [`../review/AGENTS.md`](../review/AGENTS.md) - Review generation

**System Documentation:**
- [`../../../../AGENTS.md`](../../../../AGENTS.md) - system overview
- [`../../../../../docs/usage/MANUSCRIPT_NUMBERING_SYSTEM.md`](../../../../../docs/usage/MANUSCRIPT_NUMBERING_SYSTEM.md) - Manuscript handling guide
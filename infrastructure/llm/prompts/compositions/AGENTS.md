# LLM Prompt Compositions

## Overview

The `infrastructure/llm/prompts/compositions/` directory contains pre-built prompt compositions that combine multiple fragments and templates for specific use cases. These compositions provide ready-to-use prompt structures for error recovery, format enforcement, and specialized review scenarios.

## Directory Structure

```text
infrastructure/llm/prompts/compositions/
├── AGENTS.md                       # This technical documentation
└── retry_prompts.json             # Error recovery and format enforcement prompts
```

## Composition Types

### Retry Prompts (`retry_prompts.json`)

**Specialized prompts for error recovery and response quality improvement:**

#### Off-Topic Reinforcement

**Content Relevance Enforcement:**

```json
{
  "off_topic_reinforcement": {
    "version": "1.0",
    "content": "IMPORTANT: You must review the ACTUAL manuscript text provided below. Do NOT generate hypothetical content, generic book descriptions, or unrelated topics. Your review must reference specific content from the manuscript.\n\n"
  }
}
```

**Purpose:** Prevents LLM from generating generic or off-topic responses by explicitly reinforcing the requirement to analyze the provided manuscript content.

**Usage Context:**

- When LLM generates hypothetical scenarios instead of analyzing provided text
- For ensuring responses are grounded in the actual manuscript content
- To maintain focus on the specific document being reviewed

#### Format Enforcement Compositions

**Executive Summary Format:**

```json
{
  "format_enforcement": {
    "executive_summary": {
      "version": "1.0",
      "content": "IMPORTANT: Your response MUST use these exact markdown headers:\n## Overview\n## Key Contributions\n## Methodology Summary\n## Principal Results\n## Significance and Impact\n\n"
    }
  }
}
```

**Purpose:** Ensures consistent structure and formatting in LLM responses by specifying required markdown headers.

**Structured Output Requirements:**

- **## Overview**: High-level summary of the content
- **## Key Contributions**: Main contributions and innovations
- **## Methodology Summary**: Approach and methods used
- **## Principal Results**: Key findings and outcomes
- **## Significance and Impact**: Importance and implications

#### Quality Review Format

**Scoring and Assessment Structure:**

```json
{
  "quality_review": {
    "version": "1.0",
    "content": "IMPORTANT: Include scoring using: **Score: [1-5]**\n\n"
  }
}
```

**Purpose:** Standardizes quality assessment format across all reviews by requiring explicit scoring.

**Scoring Guidelines:**

- **Score Range**: 1-5 scale (1 = poor, 5 = excellent)
- **Format**: Bold markdown with clear score indication
- **Consistency**: Applied uniformly across all quality dimensions

#### Methodology Review Format

**Structured Methodology Analysis:**

```json
{
  "methodology_review": {
    "version": "1.0",
    "content": "IMPORTANT: Your response MUST include all required sections with proper markdown headers.\n\n"
  }
}
```

**Purpose:** Ensures methodology evaluation with section coverage.

**Required Sections:**

- Research design and approach
- Data collection methods
- Analysis techniques
- Validation procedures
- Limitations and assumptions

#### Improvement Suggestions Format

**Structured Recommendations:**

```json
{
  "improvement_suggestions": {
    "version": "1.0",
    "content": "IMPORTANT: Each improvement must include WHAT (the issue), WHY (why it matters), and HOW (how to address it).\n\n"
  }
}
```

**Purpose:** Provides clear, actionable improvement guidance with context.

**Suggestion Structure:**

- **WHAT**: Specific issue or area needing improvement
- **WHY**: Importance and impact of addressing the issue
- **HOW**: Concrete steps or approaches to implement the improvement

## Composition Architecture

### Composition Structure

**Standard Composition Format:**

```json
{
  "composition_name": {
    "version": "1.0",
    "content": "The actual composition text...",
    "metadata": {
      "category": "retry|format|quality",
      "trigger_conditions": ["condition1", "condition2"],
      "compatibility": ["template1", "template2"],
      "priority": 1
    }
  }
}
```

### Composition Categories

**Retry Compositions:**

- **off_topic_reinforcement**: Content relevance correction
- **format_enforcement**: Structure and formatting fixes
- **quality_review**: Assessment standardization

**Enhancement Compositions:**

- **methodology_review**: Technical evaluation structure
- **improvement_suggestions**: Recommendation formatting
- **validation_enforcement**: Input validation requirements

## Integration with Prompt System

### Composition Application

**Dynamic Composition Injection:**

```python
class PromptEnhancer:
    """Applies compositions to improve prompt effectiveness."""

    def apply_composition(self, base_prompt: str, composition_name: str,
                         context: Dict[str, Any] = None) -> str:
        """Apply a composition to enhance a base prompt."""

        composition = self.load_composition(composition_name)

        # Check if composition should be applied
        if self._should_apply_composition(composition, context):
            enhanced_prompt = self._inject_composition(base_prompt, composition)
            return enhanced_prompt

        return base_prompt

    def _inject_composition(self, prompt: str, composition: Dict[str, Any]) -> str:
        """Inject composition content into prompt."""

        content = composition['content']

        # Add composition at appropriate location
        if composition.get('metadata', {}).get('position') == 'beginning':
            return content + prompt
        else:  # default to end
            return prompt + "\n\n" + content
```

### Context-Aware Application

**Conditional Composition Application:**

```python
def _should_apply_composition(self, composition: Dict[str, Any],
                             context: Dict[str, Any]) -> bool:
    """Determine if composition should be applied based on context."""

    metadata = composition.get('metadata', {})
    conditions = metadata.get('trigger_conditions', [])

    # Check trigger conditions
    for condition in conditions:
        if condition == 'low_relevance_score' and context.get('relevance_score', 1.0) < 0.7:
            return True
        elif condition == 'missing_format' and not self._has_required_format(context):
            return True
        elif condition == 'quality_below_threshold' and context.get('quality_score', 5) < 3:
            return True

    return False
```

## Usage Examples

### Error Recovery Application

**Off-Topic Response Correction:**

```python
# When LLM generates off-topic response
enhancer = PromptEnhancer()

original_prompt = "Review this manuscript about machine learning..."
off_topic_response = "Let me tell you about a great book on AI..."

# Apply composition to reinforce content focus
corrected_prompt = enhancer.apply_composition(
    original_prompt,
    'off_topic_reinforcement',
    context={'relevance_score': 0.3}
)

# Result includes reinforcement language
assert "ACTUAL manuscript text" in corrected_prompt
assert "Do NOT generate hypothetical content" in corrected_prompt
```

### Format Enforcement

**Structure Standardization:**

```python
# Ensure consistent executive summary format
base_prompt = "Summarize this research paper comprehensively..."

enhanced_prompt = enhancer.apply_composition(
    base_prompt,
    'format_enforcement.executive_summary'
)

# Result includes required headers
assert "## Overview" in enhanced_prompt
assert "## Key Contributions" in enhanced_prompt
assert "## Methodology Summary" in enhanced_prompt
```

### Quality Review Enhancement

**Scoring Standardization:**

```python
# Add scoring requirements to review prompts
review_prompt = "Evaluate the quality of this methodology..."

enhanced_prompt = enhancer.apply_composition(
    review_prompt,
    'quality_review'
)

# Result includes scoring format requirements
assert "**Score: [1-5]**" in enhanced_prompt
```

## Testing

### Composition Validation

**Structure and Content Testing:**

```python
def test_composition_loading():
    """Test composition loading and validation."""

    enhancer = PromptEnhancer()

    # Test loading existing composition
    composition = enhancer.load_composition('off_topic_reinforcement')
    assert 'version' in composition
    assert 'content' in composition
    assert isinstance(composition['content'], str)

    # Test composition content
    assert 'ACTUAL manuscript text' in composition['content']
    assert 'Do NOT generate hypothetical content' in composition['content']

def test_composition_application():
    """Test composition application to prompts."""

    enhancer = PromptEnhancer()
    base_prompt = "Review this content."

    # Apply composition
    = enhancer.apply_composition(base_prompt, 'off_topic_reinforcement')

    # Verify enhancement
    assert != base_prompt
    assert 'IMPORTANT:' in assert base_prompt in # Original content preserved
```

### Integration Testing

**End-to-End Composition Testing:**

```python
def test_composition_pipeline():
    """Test composition enhancement pipeline."""

    # Setup test scenario
    base_prompt = "Analyze this manuscript."
    context = {
        'relevance_score': 0.4,  # Low relevance triggers composition
        'quality_score': 2,      # Low quality triggers enhancement
        'has_format': False      # Missing format triggers enforcement
    }

    # Apply multiple compositions
    enhancer = PromptEnhancer()

    = enhancer.apply_composition(base_prompt, 'off_topic_reinforcement', context)
    = enhancer.apply_composition(enhanced, 'format_enforcement.executive_summary', context)
    = enhancer.apply_composition(enhanced, 'quality_review', context)

    # Verify all enhancements applied
    assert 'ACTUAL manuscript text' in assert '## Overview' in assert '**Score: [1-5]**' in assert base_prompt in ```

## Performance Considerations

### Composition Caching

**Efficient Composition Loading:**
```python
class CompositionCache:
    """Cache loaded compositions for performance."""

    def __init__(self):
        self._cache = {}

    def get_composition(self, name: str) -> Dict[str, Any]:
        """Get composition from cache or load from disk."""

        if name not in self._cache:
            self._cache[name] = self._load_composition_from_disk(name)

        return self._cache[name]

    def invalidate_cache(self):
        """Clear cache when compositions are updated."""
        self._cache.clear()
```

### Selective Application

**Performance-Optimized Application:**

```python
def apply_compositions_selectively(self, prompt: str,
                                  context: Dict[str, Any],
                                  max_compositions: int = 3) -> str:
    """Apply only the most relevant compositions."""

    # Score compositions by relevance
    scored_compositions = []
    for comp_name in self.available_compositions():
        score = self._score_composition_relevance(comp_name, context)
        scored_compositions.append((comp_name, score))

    # Sort by relevance and apply top N
    scored_compositions.sort(key=lambda x: x[1], reverse=True)

    enhanced_prompt = prompt
    applied_count = 0

    for comp_name, score in scored_compositions:
        if score > 0.5 and applied_count < max_compositions:  # Relevance threshold
            enhanced_prompt = self.apply_composition(enhanced_prompt, comp_name)
            applied_count += 1

    return enhanced_prompt
```

## Error Handling

### Composition Loading Errors

**Robust Composition Handling:**

```python
def load_composition_safely(self, name: str) -> Optional[Dict[str, Any]]:
    """Load composition with error handling."""

    try:
        return self.load_composition(name)
    except FileNotFoundError:
        logger.error(f"Composition not found: {name}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in composition {name}: {e}")
        return None
    except KeyError as e:
        logger.error(f"Composition {name} missing required field: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading composition {name}: {e}")
        return None
```

### Application Failure Handling

**Graceful Degradation:**

```python
def apply_composition_safe(self, prompt: str, composition_name: str) -> str:
    """Apply composition with fallback to original prompt."""

    try:
        return self.apply_composition(prompt, composition_name)
    except Exception as e:
        logger.warning(f"Failed to apply composition {composition_name}: {e}")
        logger.warning("Returning original prompt unchanged")
        return prompt
```

## Customization and Extension

### Adding New Compositions

**Composition Creation Workflow:**

```python
def create_composition(name: str, content: str, category: str,
                      trigger_conditions: List[str] = None) -> Dict[str, Any]:
    """Create a new prompt composition."""

    composition = {
        'name': name,
        'version': '1.0',
        'content': content,
        'metadata': {
            'category': category,
            'trigger_conditions': trigger_conditions or [],
            'compatibility': ['manuscript_reviews', 'paper_summarization'],
            'priority': 1
        }
    }

    return composition
```

### Composition Categories Extension

**Domain-Specific Compositions:**

```python
SPECIALIZED_COMPOSITIONS = {
    'clinical_trials': {
        'ethical_considerations': {
            'content': 'IMPORTANT: Address IRB approval, informed consent, and ethical considerations explicitly.',
            'trigger_conditions': ['clinical_content']
        },
        'statistical_rigor': {
            'content': 'IMPORTANT: Evaluate statistical power, p-value interpretation, and confidence intervals.',
            'trigger_conditions': ['statistical_content']
        }
    },
    'machine_learning': {
        'model_validation': {
            'content': 'IMPORTANT: Assess cross-validation, overfitting prevention, and performance metrics.',
            'trigger_conditions': ['ml_content']
        },
        'reproducibility': {
            'content': 'IMPORTANT: Evaluate code availability, random seed usage, and computational reproducibility.',
            'trigger_conditions': ['code_content']
        }
    }
}
```

## Maintenance

### Composition Updates

**Version Management:**

```python
def update_composition_version(self, name: str, new_content: str) -> None:
    """Update composition with version tracking."""

    composition = self.load_composition(name)

    # Update content
    composition['content'] = new_content

    # Increment version
    current_version = composition['version']
    composition['version'] = increment_version(current_version)

    # Update metadata
    composition['metadata']['last_modified'] = datetime.now().isoformat()

    # Save updated composition
    self.save_composition(name, composition)
```

### Composition Quality Assurance

**Regular Audits:**

```python
def audit_compositions(self) -> Dict[str, List[str]]:
    """Audit all compositions for quality and effectiveness."""

    audit_results = {}

    for comp_file in self.compositions_dir.glob('*.json'):
        name = comp_file.stem

        issues = []
        issues.extend(self.validate_composition_structure(name))
        issues.extend(self.test_composition_effectiveness(name))
        issues.extend(self.check_composition_relevance(name))

        if issues:
            audit_results[name] = issues

    return audit_results
```

## Integration Examples

### LLM Review Enhancement

**Review Quality Improvement:**

```python
# Enhance review prompts with compositions
from infrastructure.llm.review.generator import ReviewGenerator

class EnhancedReviewGenerator(ReviewGenerator):
    """Review generator with composition enhancements."""

    def __init__(self, llm_client, enhancer):
        super().__init__(llm_client)
        self.enhancer = enhancer

    def generate_review(self, manuscript: str, review_type: str = "comprehensive"):
        # Generate base prompt
        base_prompt = super()._create_review_prompt(manuscript, review_type)

        # Apply relevant compositions
        context = {'review_type': review_type, 'manuscript_length': len(manuscript)}
        enhanced_prompt = self.enhancer.apply_compositions_selectively(
            base_prompt, context
        )

        # Generate review with prompt
        return self.client.query(enhanced_prompt)
```

### Template Composition Integration

**Template Enhancement:**

```python
# Integrate compositions into template system
from infrastructure.llm.prompts.composer import PromptComposer

class EnhancedPromptComposer(PromptComposer):
    """Prompt composer with composition support."""

    def __init__(self, enhancer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enhancer = enhancer

    def compose_prompt(self, template_name: str, variables: Dict[str, Any]) -> str:
        # Compose base prompt
        base_prompt = super().compose_prompt(template_name, variables)

        # Determine context for composition application
        context = self._extract_composition_context(template_name, variables)

        # Apply relevant compositions
        enhanced_prompt = self.enhancer.apply_compositions_selectively(
            base_prompt, context
        )

        return enhanced_prompt
```

## See Also

**Related Documentation:**

- [`../AGENTS.md`](../AGENTS.md) - Prompts module overview
- [`../fragments/AGENTS.md`](../fragments/AGENTS.md) - Fragment components
- [`../templates/AGENTS.md`](../templates/AGENTS.md) - Template system

**System Documentation:**

- [`../../../../AGENTS.md`](../../../../AGENTS.md) - system overview
- [`../../../../docs/operational/LLM_REVIEW_TROUBLESHOOTING.md`](../../../../docs/operational/LLM_REVIEW_TROUBLESHOOTING.md) - LLM troubleshooting guide

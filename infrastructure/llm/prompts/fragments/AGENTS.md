# LLM Prompt Fragments

## Overview

The `infrastructure/llm/prompts/fragments/` directory contains reusable prompt components that can be assembled into prompts. These fragments provide standardized, modular pieces for consistent LLM interactions across the research template system.

## Directory Structure

```text
infrastructure/llm/prompts/fragments/
├── AGENTS.md                       # This technical documentation
├── content_requirements.json       # Quality and completeness standards
├── format_requirements.json        # Output formatting specifications
├── section_structures.json         # Document organization templates
├── system_prompts.json             # AI role and behavior definitions
├── token_budget_awareness.json     # Token usage optimization guidance
└── validation_hints.json           # Input validation and error handling
```

## Fragment Types

### System Prompts (`system_prompts.json`)

**AI role definition and behavioral guidelines:**

```json
{
  "content": "You are an expert research assistant specializing in academic writing and scientific analysis. Your responses should be:\n- Accurate and evidence-based\n- Clear and accessible to educated readers\n- Methodologically sound\n- Ethically responsible\n- Critically thoughtful\n- yet concise\n- Well-structured and logically organized"
}
```

**Usage in Templates:**

```json
{
  "parts": [
    {
      "type": "fragment",
      "content": "{{system_prompts}}"
    },
    {
      "type": "instruction",
      "content": "Analyze the following research manuscript:"
    }
  ]
}
```

### Content Requirements (`content_requirements.json`)

**Quality standards and completeness requirements:**

```json
{
  "content": "Ensure your response demonstrates:\n- Deep understanding of the subject matter\n- Clear and logical reasoning supported by evidence\n- Balanced consideration of multiple perspectives\n- Appropriate level of technical detail for the audience\n- coverage of key aspects and implications\n- Acknowledgment of limitations and uncertainties\n- Practical relevance and actionable insights"
}
```

**Application Areas:**

- Research analysis and evaluation
- Technical documentation review
- Scientific manuscript assessment
- Academic content validation

### Format Requirements (`format_requirements.json`)

**Output structure and presentation standards:**

```json
{
  "content": "Format your response using:\n- Clear, descriptive section headers\n- Hierarchical structure with appropriate heading levels\n- Bullet points for lists, features, and key items\n- Numbered steps for procedures and sequences\n- Code blocks with syntax highlighting for technical content\n- Tables for comparative data and structured information\n- Consistent terminology, notation, and citation style\n- Professional academic language and tone"
}
```

**Supported Output Formats:**

- Markdown with proper heading hierarchy
- Structured JSON for programmatic processing
- HTML for web presentation
- Plain text for simple communications

### Section Structures (`section_structures.json`)

**Document organization templates for different content types:**

```json
{
  "content": "Organize your response using this structure:\n\n## Executive Summary\nBrief overview of key findings and recommendations\n\n## Methodology\nDetailed description of approach and methods used\n\n## Results\nPresentation of findings with supporting evidence\n\n## Analysis\nInterpretation of results and implications\n\n## Recommendations\nSpecific, actionable suggestions for improvement\n\n## Conclusion\nSummary of key insights and future directions"
}
```

**Content Type Templates:**

- **Research Papers**: Abstract, Introduction, Methods, Results, Discussion, Conclusion
- **Reviews**: Summary, Strengths, Weaknesses, Recommendations
- **Technical Documentation**: Overview, Installation, Usage, API Reference, Examples
- **Reports**: Executive Summary, Background, Findings, Conclusions, Appendices

### Token Budget Awareness (`token_budget_awareness.json`)

**Token usage optimization and efficiency guidance:**

```json
{
  "content": "Optimize your response for token efficiency:\n- Prioritize the most important information first\n- Use concise, precise language without unnecessary words\n- Combine related concepts to reduce repetition\n- Use abbreviations and technical terms appropriately\n- Structure information hierarchically to maximize clarity per token\n- Focus on actionable insights rather than verbose explanations\n- Consider the response length limit and allocate tokens accordingly"
}
```

**Optimization Strategies:**

- **Prioritization**: Most important content first
- **Conciseness**: Eliminate redundancy and verbosity
- **Structure**: Hierarchical organization for efficient reading
- **Precision**: Exact terminology over circumlocution

### Validation Hints (`validation_hints.json`)

**Input validation and error handling guidance:**

```json
{
  "content": "When processing input, ensure:\n- Content is relevant to the requested task\n- Information is sufficiently for meaningful analysis\n- Data quality is adequate for the intended purpose\n- Assumptions are clearly stated when information is incomplete\n- Uncertainty is acknowledged and quantified where appropriate\n- Edge cases and special conditions are considered\n- Validation results are clearly communicated to the user"
}
```

**Validation Areas:**

- **Content Relevance**: Input matches task requirements
- **Data Completeness**: Sufficient information for analysis
- **Quality Assessment**: Reliability and accuracy of data
- **Error Handling**: Graceful degradation for invalid inputs

## Fragment Architecture

### Fragment Format

**Standard JSON Structure:**

```json
{
  "name": "fragment_name",
  "description": "Brief description of fragment purpose",
  "version": "1.0",
  "content": "The actual fragment text content...",
  "metadata": {
    "category": "system|content|format|structure|optimization|validation",
    "compatibility": ["template_type_1", "template_type_2"],
    "dependencies": ["other_fragment_1"],
    "tags": ["academic", "research", "quality"]
  }
}
```

### Fragment Categories

**System-Level Fragments:**

- Define AI behavior and role
- Set interaction context and expectations
- Establish communication standards

**Content Fragments:**

- Specify quality requirements
- Define completeness standards
- Set accuracy and relevance criteria

**Format Fragments:**

- Control output structure
- Define presentation standards
- Specify formatting conventions

**Structural Fragments:**

- Provide organizational templates
- Define section hierarchies
- Establish document frameworks

**Optimization Fragments:**

- Guide token usage efficiency
- Optimize response length and clarity
- Balance completeness with conciseness

**Validation Fragments:**

- Define input quality standards
- Guide error handling approaches
- Establish validation procedures

## Integration with Prompt Composer

### Fragment Loading

**Dynamic Fragment Loading:**

```python
def load_fragment(self, name: str) -> str:
    """Load fragment content by name."""

    fragment_path = self.fragments_dir / f"{name}.json"

    with open(fragment_path, 'r', encoding='utf-8') as f:
        fragment_data = json.load(f)

    return fragment_data['content']
```

### Fragment Substitution

**Template Variable Replacement:**

```python
def substitute_fragments(self, template_text: str) -> str:
    """Replace fragment placeholders with content."""

    # Find all fragment references {{fragment_name}}
    import re
    fragment_refs = re.findall(r'\{\{(\w+)\}\}', template_text)

    result = template_text
    for fragment_name in fragment_refs:
        fragment_content = self.load_fragment(fragment_name)
        result = result.replace(f"{{{{{fragment_name}}}}}", fragment_content)

    return result
```

## Usage Examples

### Basic Fragment Usage

**Simple Fragment Insertion:**

```python
from infrastructure.llm.prompts.composer import PromptComposer

composer = PromptComposer()

# Template with fragment references
template = """
{{system_prompts}}

Please analyze the following manuscript:

{{content}}

{{content_requirements}}
{{format_requirements}}
"""

# Compose with fragments
prompt = composer.compose_from_template(template, {'content': manuscript})
```

### Conditional Fragment Application

**Context-Aware Fragment Selection:**

```python
def select_fragments_for_task(task_type: str) -> List[str]:
    """Select appropriate fragments based on task type."""

    base_fragments = ['system_prompts', 'format_requirements']

    task_specific = {
        'review': ['content_requirements', 'validation_hints'],
        'summarize': ['token_budget_awareness'],
        'analyze': ['content_requirements', 'section_structures'],
        'generate': ['format_requirements', 'validation_hints']
    }

    return base_fragments + task_specific.get(task_type, [])
```

### Custom Fragment Creation

**Creating New Fragments:**

```python
def create_custom_fragment(name: str, content: str, category: str) -> None:
    """Create a new reusable fragment."""

    fragment_data = {
        'name': name,
        'description': f'Custom {category} fragment',
        'version': '1.0',
        'content': content,
        'metadata': {
            'category': category,
            'compatibility': ['custom'],
            'tags': ['custom', category]
        }
    }

    fragment_path = fragments_dir / f"{name}.json"
    with open(fragment_path, 'w', encoding='utf-8') as f:
        json.dump(fragment_data, f, indent=2, ensure_ascii=False)
```

## Testing

### Fragment Validation

**Content Validation Tests:**

```python
def test_fragment_content():
    """Test fragment content loading and validation."""

    composer = PromptComposer()

    # Test all standard fragments load successfully
    standard_fragments = [
        'system_prompts',
        'content_requirements',
        'format_requirements',
        'section_structures',
        'token_budget_awareness',
        'validation_hints'
    ]

    for fragment_name in standard_fragments:
        content = composer.load_fragment(fragment_name)
        assert isinstance(content, str)
        assert len(content) > 0
        assert not content.isspace()
```

**Fragment Substitution Tests:**

```python
def test_fragment_substitution():
    """Test fragment placeholder substitution."""

    template = "Start: {{system_prompts}} Middle: {{content_requirements}} End"

    result = composer.substitute_fragments(template)

    # Verify fragments were inserted
    assert 'expert research assistant' in result.lower()
    assert 'deep understanding' in result.lower()

    # Verify placeholders were removed
    assert '{{' not in result
    assert '}}' not in result
```

### Integration Testing

**End-to-End Fragment Testing:**

```python
def test_fragment_integration():
    """Test fragments work correctly in prompts."""

    # Create template using multiple fragments
    template = {
        'parts': [
            {'type': 'fragment', 'content': '{{system_prompts}}'},
            {'type': 'instruction', 'content': 'Review this content:'},
            {'type': 'context', 'content': '{content}'},
            {'type': 'fragment', 'content': '{{content_requirements}}'},
            {'type': 'fragment', 'content': '{{format_requirements}}'}
        ]
    }

    variables = {'content': 'Sample manuscript content...'}

    # Compose prompt
    prompt = composer.compose_prompt(template, variables)

    # Verify all fragments are included
    assert 'expert research assistant' in prompt.lower()
    assert 'clear and logical reasoning' in prompt.lower()
    assert 'bullet points for lists' in prompt.lower()
    assert 'Sample manuscript content' in prompt
```

## Performance Considerations

### Fragment Caching

**Efficient Fragment Loading:**

```python
class FragmentCache:
    """Cache loaded fragments for performance."""

    def __init__(self):
        self._cache = {}

    def get_fragment(self, name: str) -> str:
        """Get fragment from cache or load from disk."""

        if name not in self._cache:
            self._cache[name] = self._load_fragment_from_disk(name)

        return self._cache[name]

    def invalidate_cache(self):
        """Clear cache when fragments are updated."""
        self._cache.clear()
```

### Memory Management

**Large Fragment Handling:**

```python
def load_fragment_efficiently(self, name: str) -> str:
    """Load fragments with memory considerations."""

    # For large fragments, consider lazy loading
    # or streaming approaches if needed

    fragment_path = self.fragments_dir / f"{name}.json"

    # Check file size before loading
    if fragment_path.stat().st_size > 10_000_000:  # 10MB
        logger.warning(f"Large fragment detected: {name}")

    # Load with appropriate encoding
    with open(fragment_path, 'r', encoding='utf-8') as f:
        return f.read()
```

## Error Handling

### Fragment Loading Errors

**Robust Error Recovery:**

```python
def load_fragment_safely(self, name: str) -> str:
    """Load fragment with error handling."""

    try:
        return self.load_fragment(name)
    except FileNotFoundError:
        logger.error(f"Fragment not found: {name}")
        return f"[Fragment '{name}' not available]"
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in fragment {name}: {e}")
        return f"[Fragment '{name}' format error]"
    except KeyError:
        logger.error(f"Fragment {name} missing 'content' field")
        return f"[Fragment '{name}' invalid structure]"
    except Exception as e:
        logger.error(f"Unexpected error loading fragment {name}: {e}")
        return f"[Error loading fragment '{name}']"
```

### Fragment Content Validation

**Content Validation:**

```python
def validate_fragment(self, name: str) -> List[str]:
    """Validate fragment structure and content."""

    issues = []

    try:
        fragment_path = self.fragments_dir / f"{name}.json"
        with open(fragment_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Required fields
        if 'content' not in data:
            issues.append("Missing 'content' field")

        if not isinstance(data.get('content', ''), str):
            issues.append("'content' field must be a string")

        if len(data.get('content', '').strip()) == 0:
            issues.append("'content' field cannot be empty")

        # Metadata validation
        metadata = data.get('metadata', {})
        if not isinstance(metadata, dict):
            issues.append("'metadata' field must be a dictionary")

    except Exception as e:
        issues.append(f"Error validating fragment: {e}")

    return issues
```

## Customization and Extension

### Adding New Fragments

**Fragment Creation Workflow:**

```python
def create_fragment_template(name: str, category: str, description: str) -> dict:
    """Create a template for new fragments."""

    return {
        'name': name,
        'description': description,
        'version': '1.0',
        'content': '',  # To be filled by user
        'metadata': {
            'category': category,
            'compatibility': [],
            'dependencies': [],
            'tags': [category]
        }
    }
```

### Fragment Categories Extension

**Custom Categories:**

```python
CUSTOM_FRAGMENT_CATEGORIES = {
    'domain_specific': 'Domain-specific knowledge and terminology',
    'style_guide': 'Writing style and tone guidelines',
    'formatting': 'Specialized formatting requirements',
    'workflow': 'Process and workflow guidance',
    'quality_assurance': 'Quality control and validation'
}
```

## Maintenance

### Fragment Updates

**Version Management:**

```python
def update_fragment_version(self, name: str, new_version: str) -> None:
    """Update fragment version for change tracking."""

    fragment_path = self.fragments_dir / f"{name}.json"

    with open(fragment_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data['version'] = new_version

    with open(fragment_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

### Fragment Audit

**Regular Maintenance Checks:**

```python
def audit_fragments(self) -> Dict[str, List[str]]:
    """Audit all fragments for issues."""

    audit_results = {}

    for fragment_file in self.fragments_dir.glob('*.json'):
        name = fragment_file.stem
        issues = self.validate_fragment(name)

        if issues:
            audit_results[name] = issues

    return audit_results
```

## See Also

**Related Documentation:**

- [`../AGENTS.md`](../AGENTS.md) - Prompts module overview
- [`../composer.py`](../composer.py) - Prompt composition logic
- [`../../templates/AGENTS.md`](../../templates/AGENTS.md) - Template system

**System Documentation:**

- [`../../../../AGENTS.md`](../../../../AGENTS.md) - system overview
- [`../../../../docs/development/contributing.md`](../../../../docs/development/contributing.md) - Development guide

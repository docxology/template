# LLM Prompt Templates

## Overview

The `infrastructure/llm/prompts/templates/` directory contains, pre-built prompt templates for common research tasks. These templates combine fragments and variables to provide ready-to-use prompts for manuscript review, paper summarization, and other academic workflows.

## Directory Structure

```
infrastructure/llm/prompts/templates/
├── AGENTS.md                       # This technical documentation
├── manuscript_reviews.json         # manuscript review template
└── paper_summarization.json        # Research paper summarization template
```

## Template Architecture

### Template Format

**Standard JSON Template Structure:**

```json
{
  "name": "template_name",
  "description": "Brief description of template purpose and use cases",
  "version": "1.0",
  "variables": {
    "variable_name": {
      "type": "string|number|boolean",
      "required": true|false,
      "default": "default_value",
      "description": "What this variable controls",
      "validation": "regex or constraint description"
    }
  },
  "parts": [
    {
      "type": "instruction|context|example|fragment",
      "content": "Template content or fragment reference",
      "condition": "optional conditional logic"
    }
  ],
  "metadata": {
    "category": "review|summarization|analysis|generation",
    "complexity": "simple|intermediate|advanced",
    "estimated_tokens": 500,
    "expected_output_format": "markdown|json|text",
    "tags": ["academic", "research", "quality"]
  }
}
```

## Available Templates

### Manuscript Reviews (`manuscript_reviews.json`)

**manuscript evaluation template:**

```json
{
  "name": "manuscript_reviews",
  "description": "manuscript review template for academic papers",
  "version": "1.0",
  "variables": {
    "manuscript_content": {
      "type": "string",
      "required": true,
      "description": "Full text of the manuscript to review"
    },
    "review_type": {
      "type": "string",
      "required": false,
      "default": "comprehensive",
      "enum": ["comprehensive", "technical", "editorial", "structural"],
      "description": "Type of review to perform"
    },
    "word_count": {
      "type": "number",
      "required": false,
      "description": "Manuscript word count for context"
    },
    "focus_areas": {
      "type": "array",
      "required": false,
      "description": "Specific areas to focus the review on"
    }
  },
  "parts": [
    {
      "type": "fragment",
      "content": "{{system_prompts}}"
    },
    {
      "type": "instruction",
      "content": "You are conducting a {review_type} review of an academic manuscript."
    },
    {
      "type": "context",
      "content": "Manuscript content ({word_count} words):\n\n{manuscript_content}"
    },
    {
      "type": "instruction",
      "content": "Provide a detailed, constructive review addressing:"
    },
    {
      "type": "instruction",
      "content": "- Overall quality and scholarly contribution\n- Clarity of research question and objectives\n- Appropriateness of methodology\n- Quality and interpretation of results\n- Logic and coherence of discussion\n- Writing quality and academic style\n- Suggestions for improvement"
    },
    {
      "type": "fragment",
      "content": "{{content_requirements}}"
    },
    {
      "type": "fragment",
      "content": "{{format_requirements}}"
    },
    {
      "type": "fragment",
      "content": "{{section_structures}}"
    }
  ],
  "metadata": {
    "category": "review",
    "complexity": "advanced",
    "estimated_tokens": 2000,
    "expected_output_format": "markdown",
    "tags": ["academic", "review", "manuscript", "quality"]
  }
}
```

**Review Types Supported:**

- **Comprehensive**: Full evaluation covering all aspects
- **Technical**: Focus on methodology and technical accuracy
- **Editorial**: Emphasis on writing quality and clarity
- **Structural**: Analysis of organization and flow

### Paper Summarization (`paper_summarization.json`)

**Research paper summarization template:**

```json
{
  "name": "paper_summarization",
  "description": "Template for creating concise, accurate summaries of research papers",
  "version": "1.0",
  "variables": {
    "paper_content": {
      "type": "string",
      "required": true,
      "description": "Full text of the research paper"
    },
    "max_summary_length": {
      "type": "number",
      "required": false,
      "default": 500,
      "description": "Maximum word count for summary"
    },
    "focus_areas": {
      "type": "array",
      "required": false,
      "default": ["methodology", "findings", "implications"],
      "description": "Key areas to emphasize in summary"
    },
    "audience_level": {
      "type": "string",
      "required": false,
      "default": "expert",
      "enum": ["general", "expert", "specialist"],
      "description": "Target audience expertise level"
    }
  },
  "parts": [
    {
      "type": "fragment",
      "content": "{{system_prompts}}"
    },
    {
      "type": "instruction",
      "content": "Create a concise, summary of the following research paper for a {audience_level} audience."
    },
    {
      "type": "instruction",
      "content": "Focus on these key areas: {focus_areas}"
    },
    {
      "type": "instruction",
      "content": "Keep the summary under {max_summary_length} words while covering:"
    },
    {
      "type": "instruction",
      "content": "- Research problem and objectives\n- Methodology and approach\n- Key findings and results\n- Main conclusions and implications\n- Limitations and future work"
    },
    {
      "type": "context",
      "content": "Paper content:\n\n{paper_content}"
    },
    {
      "type": "fragment",
      "content": "{{content_requirements}}"
    },
    {
      "type": "fragment",
      "content": "{{format_requirements}}"
    },
    {
      "type": "fragment",
      "content": "{{token_budget_awareness}}"
    }
  ],
  "metadata": {
    "category": "summarization",
    "complexity": "intermediate",
    "estimated_tokens": 1500,
    "expected_output_format": "markdown",
    "tags": ["academic", "summarization", "research", "paper"]
  }
}
```

**Summarization Features:**

- **Adaptive Length**: Configurable summary length limits
- **Focus Areas**: Customizable emphasis on different aspects
- **Audience Targeting**: Adjust technical level for different readers
- **Structured Output**: Consistent summary format

## Template Usage

### Basic Template Application

**Using Manuscript Review Template:**

```python
from infrastructure.llm.prompts import PromptComposer

composer = PromptComposer()

# Prepare variables
variables = {
    'manuscript_content': full_manuscript_text,
    'review_type': 'comprehensive',
    'word_count': len(full_manuscript_text.split())
}

# Compose prompt
review_prompt = composer.compose_prompt('manuscript_reviews', variables)

# Use with LLM
from infrastructure.llm.core import LLMClient
client = LLMClient()
review_response = client.query(review_prompt)
```

### Advanced Template Configuration

**Custom Summarization:**

```python
# Advanced summarization configuration
variables = {
    'paper_content': paper_text,
    'max_summary_length': 300,
    'focus_areas': ['methodology', 'results', 'practical implications'],
    'audience_level': 'general'
}

summary_prompt = composer.compose_prompt('paper_summarization', variables)

# Generate focused summary
summary = client.query(summary_prompt, options=GenerationOptions(max_tokens=400))
```

## Template Development

### Creating New Templates

**Template Creation Workflow:**

```python
def create_research_template(name: str, description: str, variables: dict, parts: list) -> dict:
    """Create a new research prompt template."""

    template = {
        'name': name,
        'description': description,
        'version': '1.0',
        'variables': variables,
        'parts': parts,
        'metadata': {
            'category': 'research',
            'complexity': 'intermediate',
            'estimated_tokens': estimate_token_count(parts),
            'expected_output_format': 'markdown',
            'tags': ['research', 'academic']
        }
    }

    return template
```

**Template Categories:**

- **Analysis**: Code analysis, data interpretation, statistical review
- **Generation**: Content creation, documentation, examples
- **Review**: Quality assessment, peer review, evaluation
- **Summarization**: Abstract creation, literature review, synthesis
- **Translation**: Cross-language academic communication

### Template Validation

**Template Quality Checks:**

```python
def validate_template_quality(template: dict) -> List[str]:
    """Validate template structure and quality."""

    issues = []

    # Required fields
    required = ['name', 'description', 'variables', 'parts']
    for field in required:
        if field not in template:
            issues.append(f"Missing required field: {field}")

    # Variable validation
    variables = template.get('variables', {})
    for var_name, var_config in variables.items():
        if 'type' not in var_config:
            issues.append(f"Variable {var_name} missing 'type' field")
        if var_config.get('required', False) and 'default' not in var_config:
            issues.append(f"Required variable {var_name} missing default value")

    # Parts validation
    parts = template.get('parts', [])
    for i, part in enumerate(parts):
        if 'type' not in part:
            issues.append(f"Part {i} missing 'type' field")
        if 'content' not in part:
            issues.append(f"Part {i} missing 'content' field")

    return issues
```

## Integration with LLM System

### Template Discovery

**Automatic Template Loading:**

```python
def discover_available_templates(self) -> List[str]:
    """Discover all available templates."""

    template_files = list(self.templates_dir.glob('*.json'))
    template_names = [f.stem for f in template_files]

    # Validate templates
    valid_templates = []
    for name in template_names:
        try:
            self.load_template(name, validate=True)
            valid_templates.append(name)
        except Exception as e:
            logger.warning(f"Invalid template {name}: {e}")

    return valid_templates
```

### Template Metadata Management

**Template Information Retrieval:**

```python
def get_template_info(self, name: str) -> Dict[str, Any]:
    """Get template information."""

    template = self.load_template(name)

    return {
        'name': template['name'],
        'description': template['description'],
        'version': template['version'],
        'variables': template['variables'],
        'category': template.get('metadata', {}).get('category', 'general'),
        'complexity': template.get('metadata', {}).get('complexity', 'intermediate'),
        'estimated_tokens': template.get('metadata', {}).get('estimated_tokens', 1000),
        'tags': template.get('metadata', {}).get('tags', [])
    }
```

## Testing

### Template Validation Testing

**Template Tests:**

```python
def test_template_validation():
    """Test all templates load and validate correctly."""

    composer = PromptComposer()

    templates = ['manuscript_reviews', 'paper_summarization']

    for template_name in templates:
        # Load template
        template = composer.load_template(template_name)

        # Validate structure
        assert 'name' in template
        assert 'description' in template
        assert 'variables' in template
        assert 'parts' in template
        assert isinstance(template['parts'], list)

        # Validate variables
        variables = template['variables']
        assert isinstance(variables, dict)

        # Test composition
        # Use default values for required variables
        test_vars = {}
        for var_name, var_config in variables.items():
            if var_config.get('required', False) and 'default' in var_config:
                test_vars[var_name] = var_config['default']

        # Should compose without errors
        prompt = composer.compose_prompt(template_name, test_vars)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
```

### Composition Testing

**Template Composition Tests:**

```python
def test_template_composition():
    """Test template composition with various inputs."""

    composer = PromptComposer()

    # Test manuscript review template
    variables = {
        'manuscript_content': 'Sample manuscript content for testing.',
        'review_type': 'technical',
        'word_count': 50
    }

    prompt = composer.compose_prompt('manuscript_reviews', variables)

    # Verify composition
    assert 'technical review' in prompt.lower()
    assert 'Sample manuscript content' in prompt
    assert 'system_prompts' not in prompt  # Fragments should be replaced
    assert '{{' not in prompt  # All placeholders should be resolved
```

### Performance Testing

**Template Performance Benchmarks:**

```python
def benchmark_template_composition():
    """Benchmark template composition performance."""

    composer = PromptComposer()

    test_variables = {
        'manuscript_content': 'x' * 10000,  # 10KB content
        'review_type': 'comprehensive'
    }

    import time

    # Benchmark composition time
    start_time = time.time()
    for _ in range(100):
        prompt = composer.compose_prompt('manuscript_reviews', test_variables)

    end_time = time.time()

    avg_time = (end_time - start_time) / 100
    print(f"Average composition time: {avg_time:.4f} seconds")

    # Verify output quality
    assert len(prompt) > 1000  # Reasonable output length
    assert 'review' in prompt.lower()
```

## Error Handling

### Template Loading Errors

**Robust Template Loading:**

```python
def load_template_safely(self, name: str) -> Optional[Dict[str, Any]]:
    """Load template with error handling."""

    try:
        return self.load_template(name, validate=True)
    except FileNotFoundError:
        logger.error(f"Template not found: {name}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in template {name}: {e}")
        return None
    except ValidationError as e:
        logger.error(f"Template validation failed for {name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading template {name}: {e}")
        return None
```

### Variable Validation

**Input Variable Validation:**

```python
def validate_template_variables(self, template_name: str, variables: Dict[str, Any]) -> List[str]:
    """Validate provided variables against template requirements."""

    template = self.load_template(template_name)
    template_vars = template.get('variables', {})

    issues = []

    # Check required variables
    for var_name, var_config in template_vars.items():
        if var_config.get('required', False) and var_name not in variables:
            issues.append(f"Missing required variable: {var_name}")

    # Validate variable types and constraints
    for var_name, value in variables.items():
        if var_name in template_vars:
            var_config = template_vars[var_name]
            issues.extend(self._validate_variable_value(var_name, value, var_config))
        else:
            issues.append(f"Unexpected variable: {var_name}")

    return issues
```

## Customization and Extension

### Template Extension

**Adding Template Variants:**

```python
def create_template_variant(base_template: str, modifications: Dict[str, Any]) -> dict:
    """Create a variant of an existing template."""

    base = self.load_template(base_template).copy()

    # Apply modifications
    if 'variables' in modifications:
        base['variables'].update(modifications['variables'])

    if 'parts' in modifications:
        # Handle part additions/modifications
        base['parts'].extend(modifications['parts'])

    # Update metadata
    base['version'] = increment_version(base['version'])
    base['name'] = f"{base_template}_{modifications.get('suffix', 'variant')}"

    return base
```

### Domain-Specific Templates

**Specialized Research Templates:**

```python
RESEARCH_DOMAIN_TEMPLATES = {
    'machine_learning': {
        'variables': {
            'model_type': {'type': 'string', 'enum': ['supervised', 'unsupervised', 'reinforcement']},
            'dataset_size': {'type': 'number'},
            'performance_metrics': {'type': 'array'}
        },
        'special_instructions': [
            "Evaluate model architecture appropriateness",
            "Assess training methodology and validation",
            "Review performance metrics and baselines"
        ]
    },
    'clinical_trials': {
        'variables': {
            'study_design': {'type': 'string', 'enum': ['rct', 'cohort', 'case_control']},
            'sample_size': {'type': 'number'},
            'outcome_measures': {'type': 'array'}
        },
        'special_instructions': [
            "Evaluate study design and statistical power",
            "Assess ethical considerations and IRB approval",
            "Review data collection and analysis methods"
        ]
    }
}
```

## Maintenance

### Template Version Management

**Version Tracking and Updates:**

```python
def update_template_version(self, name: str, changes: Dict[str, Any]) -> None:
    """Update template with version tracking."""

    template = self.load_template(name)

    # Apply changes
    template.update(changes)

    # Increment version
    current_version = template['version']
    template['version'] = increment_version(current_version)

    # Update last modified timestamp
    template['metadata']['last_modified'] = datetime.now().isoformat()

    # Save updated template
    self.save_template(name, template)
```

### Template Quality Assurance

**Regular Template Audits:**

```python
def audit_templates(self) -> Dict[str, List[str]]:
    """Audit all templates for quality and consistency."""

    audit_results = {}

    for template_file in self.templates_dir.glob('*.json'):
        name = template_file.stem

        issues = []
        issues.extend(self.validate_template_quality(name))
        issues.extend(self.check_template_performance(name))
        issues.extend(self.verify_template_outputs(name))

        if issues:
            audit_results[name] = issues

    return audit_results
```

## See Also

**Related Documentation:**

- [`../AGENTS.md`](../AGENTS.md) - Prompts module overview
- [`../fragments/AGENTS.md`](../fragments/AGENTS.md) - Fragment components
- [`../composer.py`](../composer.py) - Composition logic

**System Documentation:**

- [`../../../../AGENTS.md`](../../../../AGENTS.md) - system overview
- [`../../../../docs/usage/MARKDOWN_TEMPLATE_GUIDE.md`](../../../../docs/usage/MARKDOWN_TEMPLATE_GUIDE.md) - Template usage guide

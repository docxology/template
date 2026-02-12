# LLM Prompts Module

## Overview

The `infrastructure/llm/prompts/` directory contains the prompt engineering system for the Large Language Model infrastructure. This module provides structured, reusable prompt templates, composition logic, and fragment management to ensure consistent, high-quality LLM interactions across the research template system.

## Directory Structure

```text
infrastructure/llm/prompts/
├── AGENTS.md               # This technical documentation
├── __init__.py            # Package exports
├── composer.py            # Prompt composition and assembly logic
├── loader.py              # Prompt loading and validation
├── compositions/          # Pre-built prompt compositions
│   └── retry_prompts.json # Error recovery prompts
├── fragments/             # Reusable prompt components
│   ├── content_requirements.json    # Content quality requirements
│   ├── format_requirements.json     # Output format specifications
│   ├── section_structures.json      # Section organization templates
│   ├── system_prompts.json         # System-level instructions
│   ├── token_budget_awareness.json  # Token usage optimization
│   └── validation_hints.json       # Input validation guidance
└── templates/             # prompt templates
    ├── manuscript_reviews.json     # Review generation templates
    └── paper_summarization.json    # Summarization templates
```

## Key Components

### Prompt Composition (`composer.py`)

**Dynamic prompt assembly from modular components:**

#### Prompt Composer Engine

**Modular Prompt Assembly:**

```python
class PromptComposer:
    """Assembles prompts from modular components."""

    def __init__(self, fragments_dir: Path = None):
        self.fragments_dir = fragments_dir or Path(__file__).parent / "fragments"
        self.templates_dir = fragments_dir.parent / "templates"
        self._fragments_cache = {}

    def compose_prompt(self, template_name: str, variables: Dict[str, Any],
                      options: CompositionOptions = None) -> str:
        """Compose a prompt from template and variables.

        Process:
        1. Load template structure
        2. Substitute variables
        3. Apply fragment insertions
        4. Validate final prompt
        5. Optimize for token usage

        Args:
            template_name: Name of template to use
            variables: Variables to substitute in template
            options: Composition options

        Returns:
            assembled prompt
        """
```

**Template Loading and Processing:**

```python
def _load_template(self, template_name: str) -> Dict[str, Any]:
    """Load template configuration from templates directory."""

    template_path = self.templates_dir / f"{template_name}.json"
    if not template_path.exists():
        raise PromptError(f"Template not found: {template_name}")

    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)

    # Validate template structure
    self._validate_template_structure(template)

    return template
```

#### Fragment Integration

**Dynamic Fragment Insertion:**

```python
def _apply_fragments(self, prompt_parts: List[str], context: Dict[str, Any]) -> List[str]:
    """Apply fragment insertions based on context."""

    enhanced_parts = []

    for part in prompt_parts:
        # Check for fragment placeholders
        if "{{" in part and "}}" in part:
            # Extract fragment references
            fragments = self._extract_fragment_references(part)

            # Load and insert fragments
            for fragment_name in fragments:
                fragment_content = self._load_fragment(fragment_name)
                part = part.replace(f"{{{{{fragment_name}}}}}", fragment_content)

        enhanced_parts.append(part)

    return enhanced_parts
```

#### Variable Substitution

**Advanced Variable Processing:**

```python
def _substitute_variables(self, template_parts: List[str],
                         variables: Dict[str, Any]) -> List[str]:
    """Substitute variables in template parts with advanced processing."""

    processed_parts = []

    for part in template_parts:
        # Standard string substitution
        processed = part.format(**variables)

        # Advanced processing for special variable types
        processed = self._process_special_variables(processed, variables)

        # Content validation
        processed = self._validate_content(processed, variables)

        processed_parts.append(processed)

    return processed_parts
```

### Prompt Loading (`loader.py`)

**Template and fragment loading with validation:**

#### Template Management

**Template Discovery and Loading:**

```python
class PromptLoader:
    """Loads and validates prompt templates and fragments."""

    def __init__(self, prompts_dir: Path = None):
        self.prompts_dir = prompts_dir or Path(__file__).parent
        self._template_cache = {}
        self._fragment_cache = {}

    def load_template(self, name: str, validate: bool = True) -> Dict[str, Any]:
        """Load template with optional validation."""

        if name in self._template_cache:
            return self._template_cache[name]

        template_path = self.prompts_dir / "templates" / f"{name}.json"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {name}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)

        if validate:
            self.validate_template(template)

        self._template_cache[name] = template
        return template

    def load_fragment(self, name: str) -> str:
        """Load reusable prompt fragment."""

        if name in self._fragment_cache:
            return self._fragment_cache[name]

        fragment_path = self.prompts_dir / "fragments" / f"{name}.json"
        if not fragment_path.exists():
            raise FileNotFoundError(f"Fragment not found: {name}")

        with open(fragment_path, 'r', encoding='utf-8') as f:
            fragment_data = json.load(f)

        # Extract content (fragments are simple content dictionaries)
        content = fragment_data.get('content', '')
        if not content:
            raise ValueError(f"Invalid fragment format: {name}")

        self._fragment_cache[name] = content
        return content
```

#### Template Validation

**Template Validation:**

```python
def validate_template(self, template: Dict[str, Any]) -> None:
    """Validate template structure and content."""

    required_fields = ['name', 'description', 'parts', 'variables']
    for field in required_fields:
        if field not in template:
            raise ValidationError(f"Missing required field: {field}")

    # Validate parts structure
    if not isinstance(template['parts'], list):
        raise ValidationError("Template parts must be a list")

    for i, part in enumerate(template['parts']):
        if not isinstance(part, dict):
            raise ValidationError(f"Part {i} must be a dictionary")

        if 'type' not in part:
            raise ValidationError(f"Part {i} missing 'type' field")

        if part['type'] not in ['instruction', 'context', 'example', 'fragment']:
            raise ValidationError(f"Invalid part type: {part['type']}")

    # Validate variables
    self._validate_variables(template.get('variables', {}))
```

### Fragment Components

#### Content Requirements (`fragments/content_requirements.json`)

**Quality and completeness requirements:**

```json
{
  "content": "Ensure your response demonstrates:\n- Deep understanding of the subject matter\n- Clear and logical reasoning\n- Evidence-based conclusions\n- Appropriate level of technical detail\n- coverage of key aspects\n- Balanced perspective on limitations and assumptions"
}
```

#### Format Requirements (`fragments/format_requirements.json`)

**Output structure and formatting standards:**

```json
{
  "content": "Format your response using:\n- Clear section headers and subheaders\n- Bullet points for lists and key items\n- Numbered steps for procedures\n- Code blocks for technical content\n- Tables for comparative data\n- Consistent terminology and notation"
}
```

#### System Prompts (`fragments/system_prompts.json`)

**Role definition and behavioral guidelines:**

```json
{
  "content": "You are an expert research assistant specializing in academic writing and scientific analysis. Your responses should be:\n- Accurate and evidence-based\n- Clear and accessible to educated readers\n- Methodologically sound\n- Ethically responsible\n- Critically thoughtful"
}
```

## Integration with LLM System

### Template-Based Review Generation

**Review Template Usage:**

```python
from infrastructure.llm.prompts import PromptComposer

# Initialize composer
composer = PromptComposer()

# Compose manuscript review prompt
variables = {
    'manuscript_content': manuscript_text,
    'word_count': len(manuscript_text.split()),
    'review_type': 'comprehensive'
}

review_prompt = composer.compose_prompt('manuscript_reviews', variables)

# Use with LLM client
from infrastructure.llm.core import LLMClient
client = LLMClient()
response = client.query_structured(review_prompt, schema=review_schema)
```

### Summarization Template Usage

**Paper Summarization:**

```python
# Compose paper summarization prompt
summarization_vars = {
    'paper_content': paper_text,
    'max_summary_length': 500,
    'focus_areas': ['methodology', 'findings', 'implications']
}

summary_prompt = composer.compose_prompt('paper_summarization', summarization_vars)

# Generate summary
summary = client.query(summary_prompt, options=GenerationOptions(max_tokens=600))
```

## Fragment System Architecture

### Fragment Types

**System-Level Fragments:**

- **system_prompts**: Define AI role and behavioral guidelines
- **content_requirements**: Quality and completeness standards
- **format_requirements**: Output structure specifications

**Task-Specific Fragments:**

- **section_structures**: Document organization templates
- **validation_hints**: Input validation guidance
- **token_budget_awareness**: Token usage optimization

### Fragment Composition Rules

**Fragment Assembly Logic:**

```python
def _compose_fragments(self, fragment_names: List[str]) -> str:
    """Compose multiple fragments with proper separation."""

    composed = []

    for name in fragment_names:
        fragment = self._load_fragment(name)

        # Add separator if not first fragment
        if composed:
            composed.append("\n\n")

        composed.append(fragment)

    return "".join(composed)
```

## Template Structure

### Template Schema

**Standard Template Format:**

```json
{
  "name": "manuscript_reviews",
  "description": "manuscript review template",
  "version": "1.0",
  "variables": {
    "manuscript_content": {
      "type": "string",
      "required": true,
      "description": "Full manuscript text to review"
    },
    "review_type": {
      "type": "string",
      "required": false,
      "default": "comprehensive",
      "enum": ["comprehensive", "technical", "editorial"]
    }
  },
  "parts": [
    {
      "type": "instruction",
      "content": "You are conducting a {{review_type}} review of an academic manuscript."
    },
    {
      "type": "fragment",
      "content": "{{system_prompts}}"
    },
    {
      "type": "context",
      "content": "Manuscript content:\n{{manuscript_content}}"
    },
    {
      "type": "instruction",
      "content": "Provide detailed feedback following these requirements:\n{{content_requirements}}"
    },
    {
      "type": "fragment",
      "content": "{{format_requirements}}"
    }
  ]
}
```

## Testing

### Template Validation Testing

**Template Structure Tests:**

```python
def test_template_validation():
    """Test template loading and validation."""

    loader = PromptLoader()

    # Test valid template
    template = loader.load_template('manuscript_reviews')
    assert template['name'] == 'manuscript_reviews'
    assert 'variables' in template
    assert 'parts' in template

    # Test invalid template
    with pytest.raises(ValidationError):
        loader.load_template('invalid_template')

def test_fragment_loading():
    """Test fragment loading functionality."""

    loader = PromptLoader()

    # Test existing fragment
    content = loader.load_fragment('system_prompts')
    assert isinstance(content, str)
    assert len(content) > 0

    # Test non-existent fragment
    with pytest.raises(FileNotFoundError):
        loader.load_fragment('nonexistent_fragment')
```

### Composition Testing

**Prompt Assembly Tests:**

```python
def test_prompt_composition():
    """Test prompt composition workflow."""

    composer = PromptComposer()

    variables = {
        'manuscript_content': 'Sample manuscript text...',
        'review_type': 'technical'
    }

    # Compose prompt
    prompt = composer.compose_prompt('manuscript_reviews', variables)

    # Verify composition
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert 'technical review' in prompt.lower()
    assert 'Sample manuscript text' in prompt

    # Verify fragment insertion
    assert 'expert research assistant' in prompt.lower()
```

**Variable Substitution Tests:**

```python
def test_variable_substitution():
    """Test variable substitution in templates."""

    composer = PromptComposer()

    # Test simple substitution
    template_parts = ["Review type: {review_type}", "Content: {content}"]
    variables = {'review_type': 'comprehensive', 'content': 'test content'}

    result = composer._substitute_variables(template_parts, variables)

    assert result[0] == "Review type:"
    assert result[1] == "Content: test content"
```

## Performance Considerations

### Template Caching

**Efficient Template Loading:**

```python
def _get_cached_template(self, name: str) -> Dict[str, Any]:
    """Get template from cache or load from disk."""

    if name not in self._template_cache:
        self._template_cache[name] = self._load_template_from_disk(name)

    return self._template_cache[name]
```

**Fragment Caching:**

```python
def _get_cached_fragment(self, name: str) -> str:
    """Get fragment from cache or load from disk."""

    if name not in self._fragment_cache:
        self._fragment_cache[name] = self._load_fragment_from_disk(name)

    return self._fragment_cache[name]
```

### Token Optimization

**Prompt Size Management:**

```python
def _optimize_prompt_size(self, prompt: str, max_tokens: int = None) -> str:
    """Optimize prompt size for token limits."""

    if not max_tokens:
        return prompt

    # Estimate token count
    estimated_tokens = self._estimate_token_count(prompt)

    if estimated_tokens <= max_tokens:
        return prompt

    # Truncate with intelligent chunking
    return self._truncate_with_context(prompt, max_tokens)
```

## Error Handling

### Template Validation Errors

**Validation:**

```python
def _validate_template_structure(self, template: Dict[str, Any]) -> None:
    """Validate template structure."""

    # Required fields
    required = ['name', 'description', 'parts', 'variables']
    missing = [field for field in required if field not in template]

    if missing:
        raise TemplateValidationError(f"Missing required fields: {missing}")

    # Parts validation
    if not isinstance(template['parts'], list):
        raise TemplateValidationError("Parts must be a list")

    for i, part in enumerate(template['parts']):
        self._validate_part(part, i)

    # Variables validation
    if not isinstance(template.get('variables', {}), dict):
        raise TemplateValidationError("Variables must be a dictionary")
```

### Fragment Loading Errors

**Robust Fragment Handling:**

```python
def _load_fragment_safely(self, name: str) -> str:
    """Load fragment with error handling."""

    try:
        return self._load_fragment_from_disk(name)
    except FileNotFoundError:
        logger.warning(f"Fragment not found: {name}")
        return f"[Fragment '{name}' not found]"
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in fragment {name}: {e}")
        return f"[Invalid fragment '{name}']"
    except Exception as e:
        logger.error(f"Error loading fragment {name}: {e}")
        return f"[Error loading fragment '{name}']"
```

## Usage Examples

### Basic Template Usage

**Simple Prompt Composition:**

```python
from infrastructure.llm.prompts import PromptComposer

composer = PromptComposer()

# Basic review prompt
variables = {
    'manuscript_content': manuscript,
    'review_focus': 'methodology'
}

prompt = composer.compose_prompt('manuscript_reviews', variables)
```

### Advanced Composition

**Custom Fragment Integration:**

```python
# Load specific fragments
composer = PromptComposer()

# Custom composition with specific fragments
variables = {
    'task_description': 'Analyze this research paper',
    'content': paper_text,
    'fragments': ['system_prompts', 'content_requirements']
}

prompt = composer.compose_prompt('custom_analysis', variables)
```

### Template Development

**Creating New Templates:**

```python
# Template creation workflow
template_data = {
    'name': 'custom_review',
    'description': 'Custom manuscript review template',
    'variables': {
        'content': {'type': 'string', 'required': True},
        'style': {'type': 'string', 'default': 'formal'}
    },
    'parts': [
        {'type': 'fragment', 'content': '{{system_prompts}}'},
        {'type': 'instruction', 'content': 'Review this content in {{style}} style'},
        {'type': 'context', 'content': '{{content}}'}
    ]
}

# Save template
import json
with open('templates/custom_review.json', 'w') as f:
    json.dump(template_data, f, indent=2)
```

## Configuration

### Directory Configuration

**Custom Prompt Directories:**

```python
# Use custom prompt directory
composer = PromptComposer(prompts_dir=Path('/custom/prompts'))

# Or set via environment
import os
os.environ['LLM_PROMPTS_DIR'] = '/custom/prompts'
```

### Template Search Paths

**Multiple Template Sources:**

```python
def _find_template_path(self, name: str) -> Path:
    """Find template in configured search paths."""

    search_paths = [
        self.templates_dir,
        Path.home() / '.llm_templates',
        Path('/usr/local/share/llm_templates')
    ]

    for path in search_paths:
        template_path = path / f"{name}.json"
        if template_path.exists():
            return template_path

    raise FileNotFoundError(f"Template not found: {name}")
```

## Future Enhancements

### Advanced Features

**Planned Improvements:**

- **Template Inheritance**: Base templates with overrides
- **Dynamic Fragment Selection**: Context-aware fragment insertion
- **Template Versioning**: Version management and migration
- **Performance Profiling**: Template composition timing analysis

**Integration Features:**

- **Hot Reloading**: Runtime template updates without restart
- **Template Marketplace**: Shared template repository
- **Collaborative Editing**: Multi-user template development
- **A/B Testing**: Template performance comparison

## Troubleshooting

### Common Template Issues

**Template Not Found:**

```python
# Check template directory
prompts_dir = Path(__file__).parent
templates_dir = prompts_dir / "templates"

print(f"Templates directory: {templates_dir}")
print(f"Contents: {list(templates_dir.glob('*.json'))}")

# Verify template exists
template_path = templates_dir / "manuscript_reviews.json"
print(f"Template exists: {template_path.exists()}")
```

**Fragment Loading Errors:**

```python
# Check fragment structure
import json

fragment_path = prompts_dir / "fragments" / "system_prompts.json"
with open(fragment_path) as f:
    fragment = json.load(f)

print(f"Fragment structure: {fragment.keys()}")
assert 'content' in fragment, "Fragment missing 'content' field"
```

**Variable Substitution Issues:**

```python
# Debug variable substitution
template_parts = ["Review: {content}", "Type: {review_type}"]
variables = {'content': 'test', 'review_type': 'full'}

try:
    result = composer._substitute_variables(template_parts, variables)
    print(f"Substitution successful: {result}")
except KeyError as e:
    print(f"Missing variable: {e}")
except Exception as e:
    print(f"Substitution error: {e}")
```

### Performance Debugging

**Composition Timing:**

```python
import time

start_time = time.time()
prompt = composer.compose_prompt('manuscript_reviews', variables)
end_time = time.time()

print(f"Composition time: {end_time - start_time:.3f} seconds")
print(f"Prompt length: {len(prompt)} characters")
```

## See Also

**Related Documentation:**

- [`../core/AGENTS.md`](../core/AGENTS.md) - LLM core functionality
- [`../templates/AGENTS.md`](../templates/AGENTS.md) - Template system
- [`../review/AGENTS.md`](../review/AGENTS.md) - Review generation

**System Documentation:**

- [`../../../AGENTS.md`](../../../AGENTS.md) - system overview
- [`../../../docs/development/contributing.md`](../../../docs/development/contributing.md) - Template development guide

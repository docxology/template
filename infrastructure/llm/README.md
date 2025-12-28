# LLM Infrastructure

Local Large Language Model (LLM) integration for research workflows, providing manuscript review, summarization, and analysis capabilities using Ollama.

## Quick Start

```bash
# Install and start Ollama
ollama serve

# Pull a model
ollama pull gemma3:4b

# Run manuscript review
python3 scripts/06_llm_review.py --review manuscript.md
```

## Features

- **Manuscript Review**: Comprehensive academic paper evaluation
- **Summarization**: Research paper and document summaries
- **Prompt Engineering**: Modular prompt templates and fragments
- **Local Processing**: Privacy-first with no external API calls
- **Multi-Format Support**: Markdown, JSON, and structured outputs

## Architecture

```
infrastructure/llm/
├── core/           # Core LLM client and configuration
├── templates/      # High-level operation templates
├── prompts/        # Prompt engineering system
├── review/         # Manuscript review functionality
├── utils/          # Ollama server utilities
├── validation/     # Response validation and quality checks
└── cli/            # Command-line interface
```

## Configuration

Set environment variables for Ollama connection:

```bash
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="gemma3:4b"
export LLM_TEMPERATURE="0.7"
export LLM_MAX_TOKENS="2048"
```

## Usage Examples

### Basic Review
```python
from infrastructure.llm.templates import ManuscriptReviewTemplate
from infrastructure.llm.core import LLMClient

client = LLMClient()
template = ManuscriptReviewTemplate(client)

result = template.apply(manuscript="Your manuscript text here")
print(result.content)
```

### Custom Prompts
```python
from infrastructure.llm.prompts import PromptComposer

composer = PromptComposer()
prompt = composer.compose_prompt('manuscript_reviews', {
    'manuscript_content': manuscript,
    'review_type': 'technical'
})
```

## Testing

```bash
# Run all LLM tests
pytest tests/infrastructure/llm/ -v

# Skip Ollama-dependent tests
pytest tests/infrastructure/llm/ -m "not requires_ollama" -v
```

## See Also

- [AGENTS.md](AGENTS.md) - Detailed technical documentation
- [core/](core/) - Core LLM client implementation
- [templates/](templates/) - Operation templates
- [prompts/](prompts/) - Prompt engineering
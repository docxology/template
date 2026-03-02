---
name: infrastructure-llm
description: Skill for the LLM infrastructure module providing local Large Language Model integration via Ollama. Covers client initialization, prompt templates, output validation, manuscript review generation, conversation context, and CLI usage. Use when querying LLMs, generating manuscript reviews, validating LLM outputs, or managing Ollama models.
---

# LLM Module

Local Large Language Model integration for research assistance via Ollama.

## Module Structure

```
llm/
├── core/       # Client, config, context management
├── templates/  # Prompt templates for research tasks
├── validation/ # Output quality validation
├── review/     # Manuscript review generation
├── prompts/    # Prompt fragment composition system
├── utils/      # Ollama server management
└── cli/        # Command-line interface
```

## LLM Client (`core/client.py`)

```python
from infrastructure.llm import LLMClient, LLMConfig, GenerationOptions, ResponseMode

# Initialize with defaults
client = LLMClient()

# Custom configuration
config = LLMConfig(model="gemma3:4b", temperature=0.7)
client = LLMClient(config)

# Generate a response
response = client.generate("Summarize this paper...", options=GenerationOptions(
    max_tokens=2000,
    temperature=0.3,
))
```

## Conversation Context (`core/context.py`)

```python
from infrastructure.llm import ConversationContext, Message

context = ConversationContext()
context.add(Message(role="user", content="What is active inference?"))
context.add(Message(role="assistant", content="Active inference is..."))
```

## Prompt Templates (`templates/`)

Pre-built research task templates:

```python
from infrastructure.llm import (
    get_template, ResearchTemplate, PaperSummarization,
    ManuscriptExecutiveSummary, ManuscriptQualityReview,
    ManuscriptMethodologyReview, ManuscriptImprovementSuggestions,
    ManuscriptTranslationAbstract,
)

# Get a template by name
template = get_template("paper_summarization")

# Use specific template classes
summary_template = ManuscriptExecutiveSummary()
prompt = summary_template.format(manuscript_text=text)
```

## Output Validation (`validation/`)

```python
from infrastructure.llm import (
    OutputValidator, detect_repetition, is_off_topic,
    check_format_compliance, validate_section_completeness,
    calculate_unique_content_ratio, deduplicate_sections,
)

validator = OutputValidator()
is_valid = validator.validate(response_text)

# Individual checks
if is_off_topic(response_text):
    logger.warning("Response appears off-topic")

ratio = calculate_unique_content_ratio(response_text)
```

## Manuscript Review Generation (`review/`)

```python
from infrastructure.llm import (
    create_review_client, check_ollama_availability, warmup_model,
    extract_manuscript_text, generate_review_with_metrics,
    generate_executive_summary, generate_quality_review,
    generate_methodology_review, generate_improvement_suggestions,
    generate_translation, save_review_outputs,
)

# Full review workflow
client = create_review_client()
warmup_model(client)
text = extract_manuscript_text(manuscript_dir)

executive = generate_executive_summary(client, text)
quality = generate_quality_review(client, text)
methodology = generate_methodology_review(client, text)
suggestions = generate_improvement_suggestions(client, text)

save_review_outputs(output_dir, executive=executive, quality=quality,
                    methodology=methodology, suggestions=suggestions)
```

## Ollama Utilities (`utils/`)

```python
from infrastructure.llm import (
    is_ollama_running, start_ollama_server, ensure_ollama_ready,
    get_available_models, get_model_names, select_best_model,
    select_small_fast_model, preload_model, check_model_loaded,
)

# Check and start Ollama
if not is_ollama_running():
    start_ollama_server()

ensure_ollama_ready()
models = get_model_names()
best = select_best_model()
```

## Prompt Composition (`prompts/`)

```python
from infrastructure.llm import PromptFragmentLoader, PromptComposer

loader = PromptFragmentLoader()
composer = PromptComposer(loader)
prompt = composer.compose(task="review", context=manuscript_text)
```

## CLI Usage

```bash
# Query the LLM
python3 -m infrastructure.llm.cli.main query "What is machine learning?"

# Check Ollama status
python3 -m infrastructure.llm.cli.main check

# List available models
python3 -m infrastructure.llm.cli.main models
```

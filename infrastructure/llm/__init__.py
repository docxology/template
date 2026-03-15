"""LLM Module.

Provides tools for interacting with Local Large Language Models (Ollama)
for research assistance tasks.

Module Structure:
- core/ - Core LLM functionality (client, config, context)
- templates/ - Prompt templates for research tasks
- validation/ - Output validation and quality checks
- review/ - Manuscript review generation system
- utils/ - Utility functions (Ollama management)
- cli/ - Command-line interface
- prompts/ - Prompt fragment system

CLI Usage:
    python3 -m infrastructure.llm.cli.main query "What is machine learning?"
    python3 -m infrastructure.llm.cli.main check
    python3 -m infrastructure.llm.cli.main models

Import directly from submodules:
    from infrastructure.llm.core.client import LLMClient
    from infrastructure.llm.core.config import OllamaClientConfig, GenerationOptions
    from infrastructure.llm.templates import get_template
    from infrastructure.llm.validation import validate_complete, is_off_topic
    from infrastructure.llm.review.generator import generate_review_with_metrics
"""

# LLM Module

LLM operations for multi-paper synthesis and paper selection.

## Components

- **operations.py**: Advanced LLM operations (literature reviews, comparisons, etc.)
- **selector.py**: Configurable paper selection and filtering

## Quick Start

```python
from infrastructure.literature.llm import (
    LiteratureLLMOperations,
    PaperSelector
)

# LLM operations
llm_ops = LiteratureLLMOperations()
result = llm_ops.generate_literature_review(papers)

# Paper selection
selector = PaperSelector.from_config("paper_selection.yaml")
selected = selector.select_papers(library_entries)
```

## Features

- Literature review generation
- Comparative analysis
- Research gap identification
- Citation network analysis
- Configurable paper filtering

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview

# LLM Module - Complete Documentation

## Purpose

The LLM module provides advanced LLM operations for multi-paper synthesis and configurable paper selection.

## Components

### LiteratureLLMOperations (operations.py)

Advanced LLM operations for synthesizing information across multiple papers.

**Key Methods:**
- `generate_literature_review()` - Generate literature review synthesis
- `generate_science_communication()` - Create accessible narratives
- `generate_comparative_analysis()` - Compare methods/findings
- `identify_research_gaps()` - Identify research gaps
- `analyze_citation_network()` - Analyze citation relationships

### PaperSelector (selector.py)

Configurable paper selection and filtering.

**Key Methods:**
- `select_papers()` - Filter papers based on criteria
- `from_config()` - Create selector from YAML config

**Selection Criteria:**
- Year range
- Venue filtering
- Keyword matching
- Citation count thresholds
- Source filtering

## Usage Examples

### LLM Operations

```python
from infrastructure.literature.llm import LiteratureLLMOperations
from infrastructure.literature.library import LibraryIndex

llm_ops = LiteratureLLMOperations()
entries = LibraryIndex(config).list_entries()

# Generate literature review
result = llm_ops.generate_literature_review(
    papers=entries[:10],
    focus="methods"
)
```

### Paper Selection

```python
from infrastructure.literature.llm import PaperSelector

selector = PaperSelector.from_config("paper_selection.yaml")
selected = selector.select_papers(library_entries)
```

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview



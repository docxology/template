# Analysis Module

Paper analysis tools for structure, domain detection, and context building.

## Components

- **paper_analyzer.py**: Paper structure and content analysis
- **domain_detector.py**: Automatic domain detection
- **context_builder.py**: Context building for LLM prompts

## Quick Start

```python
from infrastructure.literature.analysis import (
    PaperAnalyzer,
    DomainDetector,
    ContextBuilder
)

# Analyze paper structure
analyzer = PaperAnalyzer()
profile = analyzer.analyze_paper(pdf_path, search_result)

# Detect domain
detector = DomainDetector()
domain = detector.detect_domain(text=pdf_text)

# Build context
builder = ContextBuilder()
context = builder.build_context(entry, pdf_text)
```

## Features

- Paper structure analysis
- Domain detection (physics, CS, biology, etc.)
- Rich context building for LLM operations

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview



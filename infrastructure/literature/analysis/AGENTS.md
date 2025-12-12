# Analysis Module - Complete Documentation

## Purpose

The analysis module provides tools for analyzing paper structure, detecting scientific domains, and building rich context for LLM operations.

## Components

### PaperAnalyzer (paper_analyzer.py)

Analyzes paper structure and content characteristics.

**Key Methods:**
- `analyze_paper()` - Comprehensive paper analysis
- `analyze_structure()` - Analyze paper structure
- `create_content_profile()` - Create content profile

**Features:**
- Section identification
- Word/character counts
- Equation/figure/table detection
- Complexity scoring

### DomainDetector (domain_detector.py)

Automatically detects scientific domain of papers.

**Key Methods:**
- `detect_domain()` - Detect domain from text
- `get_domain_keywords()` - Get domain-specific keywords

**Supported Domains:**
- Physics
- Computer Science
- Biology
- Mathematics
- Chemistry
- Engineering
- Medicine
- Multidisciplinary

### ContextBuilder (context_builder.py)

Builds rich context for enhanced LLM prompts.

**Key Methods:**
- `build_context()` - Build comprehensive context
- `extract_key_information()` - Extract key information

**Features:**
- Domain-aware context
- Paper structure integration
- Key term extraction
- Citation context

## Usage Examples

### Paper Analysis

```python
from infrastructure.literature.analysis import PaperAnalyzer
from infrastructure.literature.sources import SearchResult

analyzer = PaperAnalyzer()
result = SearchResult(
    title="Example Paper",
    authors=["Author"],
    year=2024,
    abstract="Abstract text"
)

profile = analyzer.analyze_paper(pdf_path, result)
print(f"Domain: {profile.domain_detection.domain}")
print(f"Complexity: {profile.complexity_score}")
```

### Domain Detection

```python
from infrastructure.literature.analysis import DomainDetector

detector = DomainDetector()
result = detector.detect_domain(text=pdf_text)
print(f"Domain: {result.domain}")
print(f"Confidence: {result.confidence}")
```

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview



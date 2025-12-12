# Summarization Module

Comprehensive paper summarization system with multi-stage generation, quality validation, and context extraction.

## Architecture

### Multi-Stage Summarization

1. **PDF Text Extraction** - Extract text with section prioritization
2. **Context Extraction** - Extract and structure key sections (abstract, intro, conclusion, key terms)
3. **Draft Generation** - Generate initial summary using structured context
4. **Quality Validation** - Validate summary quality comprehensively
5. **Refinement** - Validate and refine summary based on specific issues (if needed)

### Components

- **core.py** - Main `SummarizationEngine` orchestrating the workflow
- **context_extractor.py** - Extracts and structures key sections from PDFs
- **prompt_builder.py** - Builds improved prompts with examples and enhanced requirements
- **streaming.py** - Streaming wrapper with real-time progress updates
- **multi_stage_summarizer.py** - Implements draft + refine approach
- **validator.py** - Quality validation with detailed feedback
- **pdf_processor.py** - PDF text processing with section prioritization
- **orchestrator.py** - Workflow orchestration
- **metadata.py** - Summary metadata management
- **parser.py** - Summary parsing
- **models.py** - Data models (Result, Context, ValidationResult, ProgressEvent)

## Usage

### Basic Usage

```python
from infrastructure.literature.summarization import SummarizationEngine
from infrastructure.literature.sources import SearchResult
from pathlib import Path
from infrastructure.llm import LLMClient

# Initialize LLM client
llm_client = LLMClient()

# Initialize engine (components created automatically if not provided)
engine = SummarizationEngine(llm_client)

# Summarize paper
result = engine.summarize_paper(
    result=search_result,
    pdf_path=Path("data/pdfs/paper.pdf"),
    max_retries=2
)

# Check result (summary_text is always present, even if validation failed)
if result.summary_text:
    print(f"Summary generated: {result.output_words} words")
    print(f"Quality score: {result.quality_score:.2f}")
    print(f"Validation status: {'Accepted' if result.success else 'Rejected'}")
    if result.validation_errors:
        print(f"Validation errors: {len(result.validation_errors)}")
    
    # Save summary (always saves, even if validation failed)
    summary_path = engine.save_summary(
        result=search_result,
        summary_result=result,
        output_dir=Path("data/summaries"),
        pdf_path=Path("data/pdfs/paper.pdf")
    )
    print(f"Summary saved to: {summary_path}")
    # Saved file includes validation metadata (status, score, errors)
else:
    print(f"Summarization failed: {result.error}")
```

### With Real-time Progress

```python
from infrastructure.literature.summarization import (
    SummarizationEngine,
    SummarizationProgressEvent
)

def progress_callback(event: SummarizationProgressEvent):
    """Handle progress events for real-time updates."""
    if event.status == "started":
        print(f"→ {event.stage}: {event.message}")
    elif event.status == "in_progress":
        # Handle streaming progress updates
        if event.metadata.get("streaming"):
            chars = event.metadata.get("chars_received", 0)
            words = event.metadata.get("words_received", 0)
            elapsed = event.metadata.get("elapsed_time", 0)
            print(f"↻ {event.stage}: Streaming: {chars:,} chars, {words:,} words ({elapsed:.1f}s)")
        else:
            print(f"↻ {event.stage}: {event.message}")
    elif event.status == "completed":
        print(f"✓ {event.stage} completed: {event.message}")
    elif event.status == "failed":
        print(f"✗ {event.stage} failed: {event.message}")

engine = SummarizationEngine(llm_client)

result = engine.summarize_paper(
    result=search_result,
    pdf_path=Path("data/pdfs/paper.pdf"),
    progress_callback=progress_callback
)
```

### Using with LiteratureWorkflow

```python
from infrastructure.literature import LiteratureWorkflow, LiteratureSearch
from infrastructure.literature.summarization import SummarizationEngine
from infrastructure.llm import LLMClient

# Initialize components
llm_client = LLMClient()
literature_search = LiteratureSearch()
summarizer = SummarizationEngine(llm_client)

# Create workflow
workflow = LiteratureWorkflow(literature_search)
workflow.set_summarizer(summarizer)

# Execute complete workflow
result = workflow.execute_search_and_summarize(
    keywords=["machine learning", "neural networks"],
    limit_per_keyword=10,
    max_parallel_summaries=2
)
```

### Using Orchestrator Function

```python
from infrastructure.literature.workflow import LiteratureWorkflow
from infrastructure.literature.summarization.orchestrator import run_summarize

# Create and configure workflow
workflow = LiteratureWorkflow(literature_search)
workflow.set_summarizer(summarizer)
workflow.set_progress_tracker(progress_tracker)

# Run summarization for papers with PDFs
exit_code = run_summarize(workflow)
```

## Real-time Progress Reporting

The module provides real-time progress updates during summarization:

### Progress Events

Progress events are emitted at each stage:

- `pdf_extraction` - PDF text extraction (started/completed)
- `context_extraction` - Context extraction (started/completed)
- `draft_generation` - Draft generation (started/completed)
- `validation` - Quality validation (started/completed)
- `refinement` - Summary refinement (started/completed, per attempt)

### Progress Display Format

During summarization, progress is displayed as:

```
[1/9] Processing pazem2025free...
  ✓ PDF extraction (2.3s, 116,726 chars)
  ✓ Context extraction (0.01s, abstract=1703 chars, intro=2999 chars)
  → Draft generation: Generating draft summary...
  ↻ Draft generation: Streaming: 5,234 chars, 756 words (5.2s elapsed)
  ↻ Draft generation: Streaming: 12,456 chars, 1,823 words (10.4s elapsed)
  ↻ Draft generation: Streaming: 18,923 chars, 2,756 words (15.6s elapsed)
  ✓ Draft generation: Draft generated: 2,156 words (45.2s)
  → Validation: Validating summary quality...
  ✓ Validation completed (3.1s, score: 0.85)
  → Refinement: Refining summary (attempt 1/2)...
  ↻ Refinement: Streaming: 8,234 chars, 1,156 words (5.1s elapsed)
  ↻ Refinement: Streaming: 15,678 chars, 2,234 words (10.3s elapsed)
  ✓ Refinement: Refinement completed: 2,456 words (38.5s)
  ✓ Summary accepted (score: 0.92, total: 89.1s)
```

**Streaming Progress Updates:**
- Real-time updates every 5 seconds during LLM generation
- Shows accumulated characters, words, and elapsed time
- Provides feedback during long generation times (60-80+ seconds)

### Progress Callback Interface

```python
def progress_callback(event: SummarizationProgressEvent) -> None:
    """Handle progress event.
    
    Args:
        event: Progress event with stage, status, and metadata.
    """
    # Custom progress handling
    logger.info(f"[{event.citation_key}] {event.stage}: {event.message}")
```

## Enhanced Prompt Requirements

The summarization system uses optimized, model-size-aware prompts:

### Prompt Optimization
- **~50% shorter** than original prompts (reduced from verbose instructions)
- **Model-size aware**: Shorter prompts for small models (<7B), full prompts for larger models
- **Consolidated instructions**: Removed redundant "FULL PAPER TEXT" mentions
- **Explicit anti-repetition**: Clear guidance to avoid sentence/paragraph repetition

### Quote Requirements
- **Minimum**: 8-12 direct quotes from the full paper text
- **Format**: Use "The authors state: 'exact quote'" or "According to the paper: [paraphrase]"
- **Evidence**: Every major claim should have a quote or evidence marker
- **Source**: Quotes must be extracted from the full paper text

### Length Requirements
- **Target**: 800-1200 words (adjusted for model capabilities)
- **Sections**: Must include Overview, Methodology, Results, Discussion
- **Coverage**: Methodology must include experimental details, Results must include numerical findings

### Comprehensive Coverage
- **Methodology**: Experimental setup, algorithms, procedures with quotes
- **Results**: Performance metrics, statistical findings, comparisons with evidence
- **Discussion**: Key contributions with direct quotes from the paper

## Streaming Support

The summarization system uses streaming for real-time progress updates:

### Features
- **Real-time Updates**: Progress events every 5 seconds during LLM generation
- **Chunk Tracking**: Accumulates characters, words, and chunks received
- **Time Tracking**: Shows elapsed time since streaming started
- **Progress Events**: Emits `in_progress` events with streaming metadata

### Streaming Metadata
When `status == "in_progress"` and `metadata.get("streaming") == True`:
- `chars_received`: Characters accumulated so far
- `words_received`: Words accumulated so far
- `chunks_received`: Number of chunks received
- `elapsed_time`: Time since streaming started
- `streaming`: Boolean flag indicating streaming mode

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MAX_INPUT_LENGTH` | Model-aware | Maximum PDF characters (50K for <7B, 100K for 7-13B, 200K for >13B) |
| `MAX_PARALLEL_SUMMARIES` | `1` | Maximum parallel summarization workers |
| `LITERATURE_TWO_STAGE_ENABLED` | `true` | Enable two-stage mode for large texts (>50K chars) |
| `LITERATURE_CHUNK_SIZE` | `15000` | Target chunk size for two-stage mode |
| `LITERATURE_CHUNK_OVERLAP` | Model-aware | Chunk overlap (200 for <7B, 500 for >=7B) |
| `LITERATURE_TWO_STAGE_THRESHOLD` | `50000` | Text size threshold to trigger two-stage mode |

### Engine Configuration

```python
from infrastructure.literature.summarization import SummarizationEngine
from infrastructure.literature.summarization.validator import SummaryQualityValidator
from infrastructure.literature.summarization.context_extractor import ContextExtractor
from infrastructure.literature.summarization.prompt_builder import SummarizationPromptBuilder

# Custom configuration
validator = SummaryQualityValidator(min_words=200)
extractor = ContextExtractor()
# Prompt builder automatically detects model size from LLM client
builder = SummarizationPromptBuilder(llm_client=llm_client)

engine = SummarizationEngine(
    llm_client=llm_client,
    quality_validator=validator,  # Optional: custom validator
    context_extractor=extractor,   # Optional: custom extractor
    prompt_builder=builder,        # Optional: custom builder (auto-detects model size)
    max_pdf_chars=None            # Optional: None = auto-detect from model size
)
```

**Model-Aware Configuration:**
- Temperature: 0.3 (<7B), 0.4 (7-13B), 0.5 (>13B)
- Max tokens: 2000-3000 based on model size and stage
- PDF char limit: 50K (<7B), 100K (7-13B), 200K (>13B)
- Chunk overlap: 200 (<7B), 500 (>=7B)

### Multi-Stage Summarizer Configuration

```python
from infrastructure.literature.summarization.multi_stage_summarizer import MultiStageSummarizer

summarizer = MultiStageSummarizer(
    llm_client=llm_client,
    validator=validator,
    prompt_builder=builder,
    max_refinement_attempts=2  # Maximum refinement attempts
)
```

## Key Features

- **Multi-stage generation** (draft + refine with fallback strategies)
- **Model-aware configuration** (automatic temperature/max_tokens based on model size)
- **Optimized prompts** (~50% shorter, model-size aware)
- **Always-save behavior** (summaries saved even when validation fails)
- **Validation metadata** (status, score, errors included in saved files)
- **Post-processing deduplication** (aggressive deduplication before validation)
- **Comprehensive quality validation** (pattern-based hallucination detection, repetition analysis)
- **Structured context extraction** (abstract, intro, conclusion, key terms)
- **Real-time progress reporting** (streaming updates every 5 seconds)
- **Intelligent PDF processing** (section prioritization, two-stage mode for large texts)
- **Automatic quality scoring** (0.0 to 1.0 with detailed error reporting)

## API Reference

### SummarizationEngine

**Main Methods:**

- `summarize_paper(result, pdf_path, max_retries=2, progress_callback=None)` - Generate summary for a paper
  - Returns: `SummarizationResult`
  - Parameters:
    - `result`: `SearchResult` with paper metadata
    - `pdf_path`: `Path` to PDF file
    - `max_retries`: Maximum retry attempts (default: 2)
    - `progress_callback`: Optional callback for progress events

- `save_summary(result, summary_result, output_dir, pdf_path=None)` - Save summary to file
  - Returns: `Path` to saved summary file
  - Parameters:
    - `result`: `SearchResult` with paper metadata
    - `summary_result`: `SummarizationResult` to save
    - `output_dir`: Directory for summary files
    - `pdf_path`: Optional path to PDF file (for metadata)

**Properties:**

- `quality_validator` - Quality validator instance
- `max_pdf_chars` - Maximum PDF characters to process

### SummarizationResult

**Attributes:**

- `citation_key`: Unique identifier for the paper
- `success`: Whether validation passed (score >= 0.5)
- `summary_text`: Generated summary text (always present, even if validation failed)
- `input_chars`: Number of characters in extracted PDF text
- `input_words`: Number of words in extracted PDF text
- `output_words`: Number of words in generated summary
- `generation_time`: Time taken for summarization in seconds
- `attempts`: Number of generation attempts made
- `error`: Error message if summarization failed
- `quality_score`: Quality validation score (0.0 to 1.0)
- `validation_errors`: List of quality validation issues (if any)
- `summary_path`: Path to the saved summary file (if saved)
- `skipped`: Whether this summary was skipped because it already exists

**Note:** `summary_text` is always included in the result, even when `success=False`.
This ensures summaries can be saved for review. Validation metadata is available
in `quality_score` and `validation_errors` for transparency.

**Properties:**

- `compression_ratio`: Calculate compression ratio (output/input words)
- `words_per_second`: Calculate generation speed in words per second

### SummarizationProgressEvent

**Attributes:**

- `citation_key`: Citation key for the paper
- `stage`: Stage name ("pdf_extraction", "context_extraction", "draft_generation", "validation", "refinement")
- `status`: Status ("started", "completed", "failed")
- `message`: Optional message describing the event
- `metadata`: Dictionary with additional metadata (timing, counts, etc.)
- `timestamp`: Unix timestamp of the event

## Troubleshooting

### Low Quality Scores

**Issue**: Summaries consistently score below 0.5

**Solutions**:
- Check PDF text extraction quality
- Verify context extraction is finding key sections
- Review validation errors for specific issues
- Consider adjusting refinement attempts
- Check LLM model quality and configuration

### Slow Generation

**Issue**: Summarization takes too long

**Solutions**:
- Reduce `max_pdf_chars` to process less text
- Use parallel processing for multiple papers (`max_parallel_summaries`)
- Check LLM connection and model performance
- Review progress events to identify bottlenecks
- Consider using faster LLM models

### Missing Sections

**Issue**: Important sections not included in summary

**Solutions**:
- Check PDF text extraction (may be missing sections)
- Verify context extraction is finding all sections
- Review section detection patterns
- Increase `max_pdf_chars` if truncation is occurring
- Check PDF quality and text extraction method

### Validation Errors

**Issue**: Frequent validation errors

**Solutions**:
- Review validation error messages in saved summary files
- Check for title mismatches (may indicate wrong PDF)
- Note: Term-based validation has been removed to reduce false positives
- Validation now focuses on structural quality (repetition, length, quotes)
- Summaries are always saved with validation metadata for review
- Consider adjusting validation thresholds if needed
- Review PDF text quality

### Progress Not Updating

**Issue**: Progress events not appearing

**Solutions**:
- Verify progress callback is provided
- Check that callback is being called
- Review logging configuration
- Ensure ProgressTracker is properly initialized
- Check console output settings

### LLM Connection Errors

**Issue**: LLM connection failures during generation

**Solutions**:
- Verify Ollama is running (`ollama serve`)
- Check model availability (`ollama list`)
- Verify network connectivity
- Review LLM client configuration
- Check for timeout settings

## Performance Tuning

### Character Limits

Adjust `max_pdf_chars` based on your LLM's context window:

```python
# For models with large context windows (e.g., llama3:70b)
engine = SummarizationEngine(llm_client, max_pdf_chars=500000)

# For models with smaller context windows (e.g., gemma3:4b)
engine = SummarizationEngine(llm_client, max_pdf_chars=100000)
```

### Parallel Processing

Use parallel processing for multiple papers:

```python
workflow.execute_search_and_summarize(
    keywords=["machine learning"],
    max_parallel_summaries=4  # Process 4 papers in parallel
)
```

**Note**: Parallel processing requires sufficient system resources and LLM capacity.

### Refinement Attempts

Adjust refinement attempts based on quality requirements:

```python
from infrastructure.literature.summarization.multi_stage_summarizer import MultiStageSummarizer

summarizer = MultiStageSummarizer(
    llm_client=llm_client,
    validator=validator,
    prompt_builder=builder,
    max_refinement_attempts=3  # More attempts for higher quality
)
```

## Related Documentation

- [AGENTS.md](AGENTS.md) - Complete module documentation
- [Literature Search Module](../AGENTS.md) - Paper discovery and download
- [LLM Module](../../llm/AGENTS.md) - LLM client documentation

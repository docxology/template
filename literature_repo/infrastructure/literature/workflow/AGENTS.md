# Workflow Module - Complete Documentation

## Purpose

The workflow module orchestrates multi-paper operations, tracks progress, and manages search workflows.

## Components

### LiteratureWorkflow (workflow.py)

High-level workflow orchestration for literature processing.

**Key Methods:**
- `search_and_add()` - Search and add papers to library
- `download_pdfs()` - Download PDFs for library entries
- `summarize_papers()` - Generate summaries for papers

### ProgressTracker (progress.py)

Progress tracking for resumable operations.

**Key Methods:**
- `get_progress()` - Get current progress
- `update_progress()` - Update progress for a paper
- `save_progress()` - Save progress to disk
- `load_progress()` - Load progress from disk

**Features:**
- Resumable operations
- Per-paper status tracking
- Progress persistence

### Search Orchestrator (orchestrator.py)

Functions for search workflow orchestration.

**Key Functions:**
- `run_search_only()` - Search without downloading
- `run_download_only()` - Download PDFs only
- `run_search()` - Full search workflow
- `run_cleanup()` - Library cleanup

## Usage Examples

### Workflow Operations

```python
from infrastructure.literature.workflow import LiteratureWorkflow

workflow = LiteratureWorkflow()

# Search and add
result = workflow.search_and_add(
    keywords=["active inference"],
    limit=10
)

# Download PDFs
download_result = workflow.download_pdfs()
```

### Progress Tracking

```python
from infrastructure.literature.workflow import ProgressTracker

tracker = ProgressTracker()
progress = tracker.get_progress()
print(f"Processed: {progress.completed}/{progress.total}")
```

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview



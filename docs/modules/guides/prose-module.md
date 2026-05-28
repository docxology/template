# Prose Module

> **Editorial quality analysis — readability, structure, passive voice, hedge words.**

**Location:** `infrastructure/prose/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [Manuscript Semantics](../../guides/manuscript-semantics.md) | [Code Review Checklist](../../development/code-review-checklist.md)

---

## Key Features

- **Readability metrics** — Flesch Reading Ease, Flesch-Kincaid Grade Level, Gunning Fog index.
- **Structural analysis** — heading outline, per-section word counts, depth / skipped-level detection.
- **Quality signals** — passive-voice candidates, hedge words, citation density, long sentences.
- **Manuscript aggregator** — `analyze_manuscript()` rolls per-file reports into a single `ManuscriptReport`.
- **Markdown normalisation** — `normalise_for_prose()` strips front-matter, fences, inline code, and links so analysis runs against prose only.

---

## Public API

```python
from infrastructure.prose import (
    ProseMetrics, compute_metrics,
    StructureReport, analyze_structure,
    QualityReport, analyze_quality,
    ManuscriptReport, analyze_manuscript,
    normalise_for_prose, read_manuscript_dir,
)
```

The full authoritative export list is in `infrastructure/prose/__init__.py`.

---

## Usage Pattern

```python
from pathlib import Path
from infrastructure.prose import analyze_manuscript

report = analyze_manuscript(Path("projects/templates/template_prose_project/manuscript"))
print(report.summary())
```

---

## Review Criteria Mapping

The prose module is reviewed primarily against criteria 1 (Clarity — the readability scorers must themselves be readable), 4 (Testability — heuristic detectors require numerous fixture-driven tests), and 8 (Reproducibility — same manuscript must yield identical scores). See [Code Review Checklist](../../development/code-review-checklist.md).

# src/ — area_handbook logic

## API

### `corpus_io`

- `load_corpus(path: Path) -> AreaCorpus`
- `load_corpus_from_dict(data: Mapping) -> AreaCorpus`
- `CorpusValidationError(ValueError)` — duplicates, empty strings, non-finite weights

### `corpus_stats`

- `evidence_counts_by_theme(corpus) -> dict[str, int]`
- `themes_without_evidence(corpus) -> tuple[str, ...]`
- `total_evidence_weight(corpus) -> float`

### `outline`

- `HANDBOOK_TEMPLATE: tuple[HandbookSection, ...]`
- `build_handbook_outline(corpus: AreaCorpus) -> tuple[HandbookSection, ...]`

### `synthesis`

- `DEFAULT_GAP_THRESHOLD: float` (0.35)
- `section_coverage_score(evidence: tuple[EvidenceItem, ...]) -> float`
- `synthesize(corpus, *, gap_threshold: float = DEFAULT_GAP_THRESHOLD) -> SynthesisResult`

### `handbook_md`

- `build_executive_summary_md`, `build_gap_report_md`, `build_evidence_by_theme_table_md`
- `build_toc_md`, `render_section_markdown`, `build_full_handbook_body`, `build_glossary_md`

### `metrics`

- `build_metrics_report(synth: SynthesisResult) -> dict[str, Any]` — includes `gap_threshold`, `gap_count`, theme histogram, min/mean/max section scores, `themes_without_evidence`, `total_evidence_weight`

### `handbook_plot_data`

- `section_scores_with_gap_flags(metrics: dict[str, Any]) -> tuple[list[str], list[float], list[bool], float]` — sorted section ids, scores, gap flags, threshold (for gap-status figure)

### `models`

Dataclasses: `Theme`, `EvidenceItem`, `AreaCorpus`, `HandbookSection`, `SynthesisResult` (with `gap_threshold`).

## Testing

```bash
cd /path/to/template
uv run pytest projects/area_handbook/tests/ --cov=projects/area_handbook/src --cov-fail-under=90
```

See [../docs/testing.md](../docs/testing.md).

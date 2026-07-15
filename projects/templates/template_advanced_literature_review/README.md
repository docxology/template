# Advanced Multi-Phase Literature Review Template

A systematic literature review framework that implements multi-phase search strategies with LLM-based filtering for comprehensive domain coverage.

## Overview

Traditional literature reviews often rely on single-term searches that may miss important papers or fail to capture the evolving complexity of research domains. This advanced template implements a **three-phase search strategy** that combines:

1. **Phase-based query refinement**: Sequential phases targeting different aspects of a domain
2. **Deterministic filtering**: Publication year, citation count, venue quality filters
3. **LLM-based content filtering**: Abstract classification for study type and relevance
4. **Cross-phase validation**: Citation analysis and methodological coherence checking

## Features

### Multi-Phase Search Architecture
- **Phase 1**: Foundational literature discovery with broad queries
- **Phase 2**: Technology-specific or method-specific focused search
- **Phase 3**: Detailed analysis of specific phenomena or applications
- Cross-phase deduplication with provenance tracking

### Intelligent Filtering
- **Deterministic filters**: Year ranges, citation thresholds, venue patterns
- **LLM classification**: Study type (observational/theoretical/review), content relevance
- **Quality gates**: Phase-specific minimum paper counts and citation averages

### Advanced Analytics
- Phase overlap analysis (Jaccard similarity)
- Cross-phase citation validation
- Temporal evolution tracking across phases
- Knowledge graph extraction with phase-aware hypothesis scoring

### Reproducible Pipeline
- Configuration-driven template variables
- Automated figure generation
- PDF manuscript rendering
- Complete test coverage

## Quick Start

1. **Configure your domain** in `manuscript/config.yaml`:
   ```yaml
   project_config:
     search_phases:
       phase_1_foundation:
         queries: ["your domain terms"]
         engines: {arxiv: true, openalex: true}
         deterministic_filters: {min_year: 2015}
   ```

2. **Run the multi-phase search**:
   ```bash
   python scripts/01_multi_phase_search.py
   ```

3. **Execute analysis pipeline**:
   ```bash
   python scripts/02_meta_analysis_pipeline.py
   python scripts/04_generate_figures.py
   python scripts/05_inject_variables.py
   ```

4. **Render manuscript**:
   ```bash
   python scripts/render_manuscript.py
   ```

## Configuration

The template is configured through `manuscript/config.yaml`:

### Search Phases
Each phase defines:
- **Query sets**: Multiple search terms targeting different aspects
- **Engine selection**: Which databases to query (arXiv, OpenAlex, etc.)
- **Result limits**: Papers per query and total phase limits
- **Dependencies**: Which previous phases this phase builds upon

### LLM Filters
Content-based filtering using local LLM:
- **Study type classification**: Observational vs theoretical vs review
- **Content relevance**: Domain-specific abstract analysis
- **Quality screening**: Method-specific inclusion criteria

### Analysis Configuration
- **Sampling rates**: LLM processing fraction for large corpora
- **Hypothesis definitions**: Domain-specific research questions
- **Subfield taxonomies**: Keyword-based paper classification

## Example: Exoplanet Atmospheric Composition

The default configuration demonstrates a three-phase review of exoplanet atmospheric research:

1. **Foundation Phase**: General atmospheric studies (2010+, 5+ citations)
2. **JWST Phase**: James Webb Space Telescope observations (2020+, new field)
3. **Molecular Phase**: Specific atmospheric molecule detections (2015+)

LLM filters classify papers by study type and validate JWST data usage and molecular detection focus.

## Architecture

```
template_advanced_literature_review/
├── scripts/
│   ├── 01_multi_phase_search.py     # Multi-phase search orchestrator
│   ├── 02_meta_analysis_pipeline.py # Phase-aware analysis
│   └── ...
├── src/
│   ├── literature/                  # Search engine interfaces
│   ├── analysis/                    # Bibliometric analysis
│   ├── knowledge_graph/             # LLM-based extraction
│   └── manuscript/variables/        # Template variable injection
├── manuscript/
│   ├── config.yaml                  # Complete configuration
│   ├── 00_abstract.md              # Multi-phase aware abstract
│   └── ...
└── tests/                           # Comprehensive test suite
```

## Extending the Template

### Adding New Phases
1. Define phase in `config.yaml` under `search_phases`
2. Specify queries, engines, and filters
3. Add LLM filters if needed
4. Update manuscript variables for new phase metrics

### Custom LLM Filters
```yaml
llm_filters:
  custom_filter:
    name: "Custom Classification"
    prompt: "Classify this abstract: {abstract}"
    apply_to_phases: ["phase_1"]
    keep_values: ["relevant"]
```

### Domain Adaptation
1. Replace search queries with domain terms
2. Update deterministic filters (years, venues, citations)
3. Modify hypothesis definitions
4. Adapt manuscript templates and variable extractors

## Dependencies

- Python 3.10+
- Academic database access (most are keyless)
- Local LLM server (Ollama recommended) for content filtering
- Standard scientific Python stack (pandas, matplotlib, networkx)

## Citation

```bibtex
@software{advanced_literature_review_template,
  title = {Advanced Multi-Phase Literature Review Template},
  author = {Friedman, Daniel Ari},
  year = {2026},
  url = {https://github.com/docxology/template_advanced_literature_review},
  license = {CC-BY-4.0}
}
```

## License

CC-BY-4.0 - See LICENSE file for details.
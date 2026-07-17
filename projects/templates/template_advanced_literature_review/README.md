# Reproducible Multi-Phase Literature-Review Pipeline

A public pipeline exemplar that implements multi-phase search, provenance-aware
filtering, corpus description, and optional model-backed analysis. It is a
reproducibility template, not a completed empirical domain review.

## Overview

The exemplar demonstrates a **three-phase search strategy** that combines:

1. **Phase-based query refinement**: Sequential phases targeting different aspects of a domain
2. **Deterministic filtering**: Publication year, citation count, venue quality filters
3. **LLM-based content filtering**: Abstract classification for study type and relevance
4. **Cross-phase validation**: Citation analysis and configured overlap checks

The committed default run uses a synthetic fixture corpus. Live retrieval,
full-text assessment, and optional LLM stages must be enabled explicitly and are
reported as pending when they did not run. The methods are informed by
systematic-review reporting practice, but the repository does not claim a
completed systematic review without live retrieval, a documented protocol, and
domain-expert assessment.

## When to use this template

Use this template when one review question needs distinct retrieval phases,
phase-specific filters, and explicit cross-phase provenance. For a single-term
review without phased comparison, start from `template_literature_meta_analysis`
instead. See `STANDALONE.md` for the fork checklist and template-integrity gates.

## Publication and rendering

This exemplar is an explicit public draft: its publication status and repository
identity come from `manuscript/config.yaml`, while the committed offline replay
and claim ledger provide the reproducible evidence boundary. Run it in the
[template monorepo](https://github.com/docxology/template) with:

```bash
uv run python scripts/pipeline/stage_01_test.py \
  --project templates/template_advanced_literature_review --project-only
uv run python scripts/pipeline/stage_03_render.py \
  --project templates/template_advanced_literature_review
```

Do not present a DOI or published-platform status until one is recorded in the
project config and the generated publication records are refreshed.

## Features

### Multi-Phase Search Architecture
- **Phase 1**: Foundational literature discovery with broad queries
- **Phase 2**: Technology-specific or method-specific focused search
- **Phase 3**: Detailed analysis of specific phenomena or applications
- Cross-phase deduplication with provenance tracking

### Intelligent Filtering
- **Deterministic filters**: Year ranges, citation thresholds, venue patterns
- **LLM classification**: Study type (observational/theoretical/review), content relevance
- **Quality gates**: Configured phase checks with explicit fixture/live status

### Advanced Analytics
- Phase overlap analysis (Jaccard similarity)
- Cross-phase citation validation
- Temporal evolution tracking across phases
- Knowledge graph extraction with phase-aware hypothesis scoring

### Reproducible Pipeline
- Configuration-driven template variables
- Automated figure generation
- PDF manuscript rendering
- Contract tests for phase filtering, provenance, local HTTP integration, and configuration

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
   uv run python scripts/01_multi_phase_search.py
   ```

3. **Execute analysis pipeline**:
   ```bash
   uv run python scripts/02_meta_analysis_pipeline.py
   uv run python scripts/04_generate_figures.py
   uv run python scripts/05_inject_variables.py
   ```

4. **Render manuscript** from the template repository root:
   ```bash
   uv run python scripts/pipeline/stage_03_render.py --project templates/template_advanced_literature_review
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

The default configuration demonstrates a three-phase pipeline over a synthetic
fixture corpus for exoplanet-atmosphere research:

1. **Foundation Phase**: General atmospheric studies (2010+, 5+ citations)
2. **JWST Phase**: James Webb Space Telescope observations (2020+, new field)
3. **Molecular Phase**: Specific atmospheric molecule detections (2015+)

LLM filters are configured but not implied to have executed in the fixture run;
their status is carried into the generated evidence and manuscript variables.

## Architecture

```
template_advanced_literature_review/
├── scripts/
│   ├── 01_multi_phase_search.py     # Multi-phase search orchestrator
│   ├── 02_meta_analysis_pipeline.py # Phase-aware analysis
│   └── ...
├── src/
│   ├── literature/                  # Search engine interfaces
│   ├── multi_phase/                 # Phase filtering and provenance
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
- Optional local LLM server for model-backed filtering when explicitly enabled
- Standard scientific Python stack (pandas, matplotlib, networkx)

## Citation

<!-- PUBLISHING-STATUS:START (generated by infrastructure.publishing.status_report) -->
**A Reproducible Multi-Phase Literature-Review Pipeline for Exoplanet Atmospheres** · v0.1.0 · CC-BY-4.0 · Daniel Ari Friedman

Repository: [docxology/template_advanced_literature_review](https://github.com/docxology/template_advanced_literature_review)

Publishing surface — 20 platforms, 1 published:

| Platform | Tier | Status | Reference | Credentials |
| --- | --- | --- | --- | --- |
| zenodo | first-class | ⚪ available | — | `ZENODO_API_TOKEN` |
| github | first-class | ✅ published | [docxology/template_advanced_literature_review](https://github.com/docxology/template_advanced_literature_review) | `GITHUB_TOKEN` |
| arxiv | first-class | ⚪ available | — | — |
| pypi | first-class | ⚪ available | — | `PYPI_TOKEN`, `TESTPYPI_TOKEN` |
| ipfs_pinata | first-class | ⚪ available | — | `PINATA_JWT` |
| ipfs_web3storage | first-class | ⚪ available | — | `WEB3_STORAGE_TOKEN` |
| software_heritage | first-class | ⚪ available | — | — |
| github_pages | first-class | ⚪ available | [docxology/template_advanced_literature_review](https://github.com/docxology/template_advanced_literature_review) | `GITHUB_TOKEN` |
| cloudflare_pages | first-class | ⚪ available | — | `CLOUDFLARE_API_TOKEN` |
| netlify | first-class | ⚪ available | — | `NETLIFY_AUTH_TOKEN` |
| huggingface_hub | first-class | ⚪ available | — | `HUGGINGFACE_TOKEN`, `HF_TOKEN` |
| osf | first-class | ⚪ available | — | `OSF_TOKEN` |
| amazon_kdp | documented | 🟡 planned | — | `AMAZON_KDP_EMAIL`, `AMAZON_KDP_PASSWORD` |
| google_play_books | documented | 🟡 planned | — | `GOOGLE_PLAY_BOOKS_SERVICE_ACCOUNT_JSON` |
| gumroad | documented | 🟡 planned | — | `GUMROAD_ACCESS_TOKEN` |
| leanpub | documented | 🟡 planned | — | `LEANPUB_API_KEY` |
| lulu | documented | 🟡 planned | — | `LULU_CLIENT_KEY`, `LULU_CLIENT_SECRET` |
| draft2digital | documented | 🟡 planned | — | `DRAFT2DIGITAL_API_TOKEN` |
| stripe | documented | 🟡 planned | — | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` |
| ingramspark | documented | 🟡 planned | — | `INGRAMSPARK_CLIENT_ID`, `INGRAMSPARK_CLIENT_SECRET` |

_Keywords: exoplanet atmospheres, literature review pipeline, systematic-review reporting, multi-phase search, LLM filtering, James Webb Space Telescope, atmospheric composition, transit spectroscopy, bibliometrics, cross-validation._

_Status legend: ✅ published (durable identifier recorded in `config.yaml`) · 🔵 reserved (identifier reserved but not yet registered by final publication) · ⚪ available (adapter implemented and locally verifiable) · 🟡 planned. This block is generated — edit `manuscript/config.yaml`, then regenerate with `uv run python -m infrastructure.publishing.status_report --project <path> --write`._
<!-- PUBLISHING-STATUS:END -->

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

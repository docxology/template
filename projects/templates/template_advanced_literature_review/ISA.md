---
project: template_advanced_literature_review
task: "Multi-Phase Exoplanet Atmospheric Literature Review: Advanced Search and Cross-Validation Pipeline"
effort: E6
phase: complete
progress: "public exemplar registered; standalone export, phase orchestration, offline replay, documentation, drift, and 95.57% coverage verified"
mode: algorithm
started: 2026-07-15
updated: 2026-07-15
iteration: 1
---

## Problem

Systematic literature reviews of rapidly evolving fields require more sophisticated search strategies than single-term queries. In exoplanet atmospheric science, the field has undergone distinct methodological phases: early foundational work (pre-2010), the JWST preparation era (2010-2021), and the current high-precision molecular detection period (2022+). A comprehensive review must capture papers from each phase while applying phase-appropriate filtering criteria and cross-validating findings across temporal boundaries.

## Vision

A researcher can configure a multi-phase literature review that automatically discovers, filters, and synthesizes papers across different methodological eras of a field. The system applies both deterministic (temporal, venue, citation-based) and LLM-based (abstract content analysis) filters to each phase, builds a unified knowledge graph from extracted assertions, and generates a manuscript with phase-aware statistics and cross-temporal validation of hypotheses.

## Out of Scope

- No new literature search engines beyond the existing 10 engine paths
- No live network retrieval or live LLM extraction in the default offline pipeline
- No fixed corpus, assertion, or page-count claims without tracked, regenerable evidence

## Principles

- Multi-phase architecture: Each search phase targets a distinct methodological era with appropriate temporal boundaries and filtering criteria
- Cross-phase validation: Later phases can validate, extend, or challenge findings from earlier phases
- Unified knowledge synthesis: All phases contribute to a single RDF knowledge graph with phase provenance
- Deterministic reproducibility: Default pipeline uses committed fixture data for consistent results across environments

## Constraints

- Must maintain 90% per-project coverage floor for project-specific `src/` code
- Must preserve offline determinism for the default analysis allowlist
- Must not break compatibility with existing template infrastructure
- Phase configuration must be entirely config-driven through `manuscript/config.yaml`

## Goal

A complete advanced literature review template that demonstrates multi-phase search, iterative filtering, cross-temporal validation, and phase-aware manuscript generation for the exoplanet atmospheric composition domain, with full test coverage and documentation.

## Criteria

- [x] ARL-1: Pipeline scripts 01-11 exist, remain thin, and declare their dependency order; paid/live stages are opt-in
- [x] ARL-2: Multi-phase search configuration in `manuscript/config.yaml` with 3 phases defined
- [x] ARL-3: Phase-aware retrieval preserves phase/query provenance through deterministic cross-phase de-duplication
- [x] ARL-4: Knowledge-graph and deep-research inputs use the shared typed infrastructure contracts and offline replay by default
- [x] ARL-5: Hypothesis and manuscript-variable extraction preserve cross-phase evidence without hard-coded result counts
- [x] ARL-6: Manuscript/config sources satisfy the public-draft publication and strict structural-drift contracts
- [x] ARL-7: Symlinked modules (analysis/, knowledge_graph/, reproducibility/, visualization/) preserve single-template functionality
- [x] ARL-8: Project-specific modules (manuscript/, multi_phase/, config_*) implement advanced features
- [x] ARL-9: Test suite covers multi-phase functionality with real data fixtures
- [x] ARL-10: Documentation (AGENTS.md, README.md, manuscript docs) describe advanced architecture

## Test Strategy

| ARL | Type | Check | Threshold | Tool |
|-----|------|-------|-----------|------|
| 1 | integration | stage discovery, dependency order, and thin-wrapper checks | all declared stages resolve | pytest + drift gate |
| 2-3 | unit+integration | multi-phase corpus loading, filtering, and provenance | three configured phases; deterministic outputs | pytest |
| 4-5 | unit+integration | typed offline replay, variable extraction, and hypothesis scoring | real fixture/I-O behavior passes | pytest |
| 6 | integration | public-draft metadata and manuscript structure | strict drift clean | drift gate |
| 7 | unit | symlinked modules preserve original functionality | tests pass | pytest |
| 8-9 | unit+coverage | project-specific modules and tests | ≥90% coverage | pytest --cov |
| 10 | doc | documentation completeness and accuracy | all surfaces documented | manual review |

## Features

| Name | Description | Satisfies | Depends On | Parallelizable |
|------|-------------|-----------|------------|----------------|
| multi-phase-search | Configure and execute 3-phase search with temporal boundaries | ARL-1,2,3 | none | yes (phases independent) |
| cross-phase-validation | Validate hypotheses across temporal phases | ARL-4,5 | multi-phase-search | no |
| advanced-manuscript | Generate phase-aware manuscript with cross-temporal statistics | ARL-6 | multi-phase-search, cross-phase-validation | no |
| symlink-preservation | Maintain compatibility with single-term template modules | ARL-7 | none | yes |
| comprehensive-testing | Full test coverage for multi-phase functionality | ARL-8,9 | all features | yes |
| complete-documentation | Document advanced architecture and usage | ARL-10 | all features | yes |

## Decisions

- 2026-07-15: Chose symlink architecture over code duplication for shared modules (analysis/, knowledge_graph/, reproducibility/, visualization/). Rationale: (a) reduces maintenance burden by keeping single source of truth; (b) ensures bug fixes and improvements propagate to both templates; (c) advanced template focuses on multi-phase orchestration, not reimplementing bibliometrics.

- 2026-07-15: Standalone export materializes public-exemplar symlinks as regular files while rejecting links outside the public exemplar boundary. This preserves a single source in the monorepo without producing a broken or confidentiality-unsafe exported template.

- 2026-07-15: Local full-corpus runs remain development evidence rather than committed claims. The public template records methods, provenance contracts, and real primary references, while raw provider downloads and volatile empirical counts stay out of Git until a release intentionally publishes a regenerable evidence bundle.

- 2026-07-15: Implemented phase-aware manuscript variables alongside standard template variables. Rationale: preserves compatibility with single-term template while adding advanced capabilities; allows manuscripts to present both aggregate and phase-specific statistics.

## Changelog

- **Created**: Advanced multi-phase template with an 11-stage surface, 3 configured search phases (foundation, JWST era, molecular detection), and cross-phase validation contracts.
- **Implemented**: Multi-phase search orchestration, deterministic + LLM filtering, phase-aware knowledge graph extraction, cross-temporal hypothesis scoring.
- **Hardened**: Removed untracked corpus/page-count claims from the durable contract; public evidence is now limited to regenerable tests, configuration, provenance, and draft manuscript sources.
- **Documented**: Full architecture documentation, usage guides, and test coverage for advanced multi-phase functionality.

## Verification

- ARL-1-6: Stage declarations, phase behavior, typed offline replay, manuscript variables, and draft-publication structure are verified from tracked fixtures and generated evidence.
- ARL-7: Shared monorepo symlinks preserve API compatibility; standalone export tests prove they become regular files and that outside/private links are rejected.
- ARL-8-9: `uv run pytest tests/ --cov=src --cov-branch --cov-fail-under=90` passed 54 tests at 95.57% coverage with real fixtures and no mock dependencies.
- ARL-10: Strict drift and repository documentation gates confirm the project, directory-level documentation, generated roster, ownership, CI scope, and public skill descriptor agree.

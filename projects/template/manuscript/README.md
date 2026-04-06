# `template/` Manuscript

Eighteen-file manuscript documenting the `template/` architecture, pipeline, security layer, and empirical evaluation. Long sections have been modularized into focused sub-files for clarity and maintainability.

## Chapters

1. **Abstract** (`01_abstract.md`) — Dense summary of the full system
2. **Introduction** (`02_introduction.md`) — Reproducibility crisis, related work, gap analysis, and four architectural pillars
3. **Methods** (5 files)
   - `03a_architecture.md` — Two-Layer Architecture, Standalone Project Paradigm, Thin Orchestrator
   - `03b_pipeline.md` — Eight-stage pipeline and interactive orchestrators
   - `03c_documentation.md` — Documentation Duality, agentic skills, MCP mapping
   - `03d_fair_iac.md` — FAIR4RS alignment, Infrastructure as Code
   - `03e_quality.md` — Zero-Mock testing, visualization standards
4. **Results** (`04_results.md`) — Multi-project benchmarks, module inventory, comparative feature matrix, steganographic performance
5. **Discussion** (5 files)
   - `05a_zeromock_tradeoff.md` — Zero-Mock tradeoff analysis
   - `05b_scalability.md` — From 1 to N projects
   - `05c_comparison.md` — Comparison to existing tools, FAIR4RS 2024-2026 update
   - `05d_ai_collaboration.md` — AI collaboration model, learning curve, limitations
   - `05e_future_conclusion.md` — 10 future directions and conclusion
6. **Infrastructure Modules** (`06_infrastructure_modules.md`) — All infrastructure subpackages with key exports and integration points
7. **Security & Provenance** (`07_security_provenance.md`) — Steganographic layers, threat model, tamper detection, FAIR alignment
8. **Appendices** (3 files)
   - `08a_pipeline_config.md` — Pipeline reference, configuration schema
   - `08b_directory_projects.md` — Directory tree, exemplar projects, documentation inventory
   - `08c_comparative_matrix.md` — 14-capability × 10-tool comparison matrix

## Building

```bash
./run.sh  # Select template project, then stage 3 (Render PDF)
```

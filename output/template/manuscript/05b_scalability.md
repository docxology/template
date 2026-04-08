## Scalability: From 1 to N Projects

The Standalone Project Paradigm enables horizontal scaling: adding a new project requires creating a directory with `manuscript/config.yaml` and nothing else. No infrastructure code changes, no `pyproject.toml` modifications, no CI configuration updates. The `run.sh` orchestrator automatically discovers new projects and presents them in its interactive menu.

We have validated this scaling model with three heterogeneous projects:

- **`code_project`**: Numerical optimization example paper with gradient descent, 39 tests, 90%+ coverage. Demonstrates the minimal viable project footprint: a single `src/` module, a single script, and a compact manuscript.
- **`cognitive_case_diagrams`**: Compositional approaches to linguistic case for cognitive modeling, 890 tests, 90%+ coverage, spanning enriched category theory, DisCoPy renderers, and categorical grammar diagrams. Demonstrates the template's capacity for computationally intensive, diagram-heavy research workflows with large test suites.
- **`template`**: This self-referential architectural analysis, 66 tests, 90%+ coverage. Demonstrates the system's ability to analyze and document itself—a unique stress test of the Two-Layer Architecture's reflexive capability.

These projects share no code with each other. They share only the infrastructure layer---13 modules, ~277 Python files---which provides logging, rendering, validation, steganography, and reporting services identically to each project. This validates the Two-Layer Architecture's claim that infrastructure and project concerns can be cleanly separated.

### Multi-Project Orchestration

When the `--all-projects` flag is passed to `run.sh`, the pipeline executes each discovered project sequentially, running infrastructure tests once at the start and skipping them for individual projects to avoid redundant validation. After all projects complete, a cross-project executive report aggregates metrics (test counts, coverage percentages, page counts, rendering durations) into a unified dashboard with both JSON and Markdown output formats. This executive reporting stage provides repository-level visibility without requiring any project-specific reporting code.

### Scaling Metrics

| Metric | `code_project` | `cognitive_case_diagrams` | `template` |
|--------|:--------------:|:------------------------:|:----------:|
| Source modules | 1 | ${project_cognitive_case_diagrams_src_module_count} | 4 |
| Test files | 1 | 48 | 3 |
| Test count | 39 | 890 | 66 |
| Manuscript chapters | 8 | ${project_cognitive_case_diagrams_chapter_count} | 21 |
| Analysis scripts | 3 | ${project_cognitive_case_diagrams_script_count} | 2 |
| Figures (auto-generated) | 6 | ${project_cognitive_case_diagrams_figure_count} | 4 |

The infrastructure overhead per project is constant regardless of project size: the same 13 modules, the same 8 pipeline stages, the same rendering and validation logic. This O(1) infrastructure cost is the architectural payoff of the Two-Layer separation.

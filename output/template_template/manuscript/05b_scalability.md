## Scalability: From 1 to N Projects

The Standalone Project Paradigm enables horizontal scaling: adding a new project requires creating a directory with `manuscript/config.yaml` and nothing else. No infrastructure code changes, no `pyproject.toml` modifications, no CI configuration updates. The `run.sh` orchestrator automatically discovers new projects and presents them in its interactive menu.

We have validated scaling with three canonical exemplars under `projects/`—always present for onboarding and tooling—and with this manuscript from `projects_in_progress/template` (84 tests) before promotion adds the meta-analysis tree to automated discovery menus.

Canonical trio:

- **`template_code_project`**: Numerical optimization example with gradient-descent narration, 196 tests, 90%+ coverage. Minimal footprint: compact `src/`, scripted analysis, short manuscript sections.
- **`template_prose_project`**: Prose-heavy manuscript emphasizing narrative structure and bibliography discipline, 76 tests, 90%+ coverage—tests exercise rendering and Markdown integrity without heavyweight numerics.
- **`template_autoresearch_project`**: AutoResearch readiness workflow invoking `projects/template_search_project/scripts/` to run corpus builders, scripted figures (`output/figures/`), and manifold-variable injection (the archive-only literature-search exemplar, restored on demand). Typical Stage 02 workloads include bibliography fusion, corpus JSON assembly, deep-search aggregates, and report composition.

Meta manuscript (**`projects_in_progress/template`**) analyzes the repository via `src/template/` introspection metrics; it deliberately lives outside `projects/` until promoted.

These workspaces share no project-level code—only Layer 1 (22 infrastructure subpackages, ~456 Python files)—validating insulation between domain repos and reusable services.

### Multi-Project Orchestration

When the `--all-projects` flag is passed to `run.sh`, the pipeline executes each discovered project sequentially, running infrastructure tests once at the start and skipping them for individual projects to avoid redundant validation. After all projects complete, a cross-project executive report aggregates metrics (test counts, coverage percentages, page counts, rendering durations) into a unified dashboard with both JSON and Markdown output formats. This executive reporting stage provides repository-level visibility without requiring any project-specific reporting code.

### Scaling Metrics

| Metric | `template_code_project` | `template_prose_project` | `template_autoresearch_project` |
|--------|:--------------:|:------------------------:|:----------:|
| Source modules | 25 | 5 | 53 |
| Test files | 11 | 7 | 15 |
| Test count | 196 | 76 | 151 |
| Manuscript chapters | 9 | 8 | 6 |
| Analysis scripts | 6 | 4 | 4 |
| Figures (auto-generated) | 8 | 5 | 27 |

The infrastructure overhead per project is constant regardless of project size: the same 22 modules, the same 10 pipeline stages, the same rendering and validation logic. This O(1) infrastructure cost is the architectural payoff of the Two-Layer separation.

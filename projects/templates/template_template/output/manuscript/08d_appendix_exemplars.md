\newpage

## Appendix: Exemplar Project Summary {#appendix-exemplars}

\begin{table}[h]
\caption{Three representative workspaces under \texttt{projects/templates/} illustrating heterogeneous domains while sharing Layer~1. This is a hand-picked sample, not the full roster: the complete public exemplar set (currently nine workspaces) is enumerated dynamically from \texttt{PUBLIC\_PROJECT\_NAMES} and listed below.}
\label{tab:exemplar-projects}
\end{table}

The full public exemplar roster is: `templates/template_active_inference`, `templates/template_autoresearch_project`, `templates/template_autoscientists`, `templates/template_code_project`, `templates/template_eda_notebook`, `templates/template_gold_refinement`, `templates/template_literature_meta_analysis`, `templates/template_madlib`, `templates/template_methods_paper`, `templates/template_newspaper`, `templates/template_prose_project`, `templates/template_search_project`, `templates/template_sia`, `templates/template_storybook`, `templates/template_template`, `templates/template_textbook`. The three rows below are a representative sample; a future `exemplar_summary_table` token in `build_manuscript_metrics_dict` would let this table cover every exemplar without hand-editing.

| Project slug | Purpose | Highlights | Tests | Figures (Stage 02 hint) |
|--------------|---------|------------|:-----:|:-----------------------|
| `template_code_project` | Optimization tutorial | Convex demo figures, scripted tables | 236 @ 90%+ gate | Controlled matplotlib exports |
| `template_prose_project` | Prose-heavy workflow | Validates narrative-only repos | 120 | Lightweight / optional plots |
| `template_autoresearch_project` | AutoResearch readiness | Planner + validation CLI | 296 | Readiness reports from Stage 02 |

**Meta manuscript location:** introspective study lives in `projects/templates/template_template/` beside the public exemplar set. Discovery now follows the typed `projects/` layout—`projects/templates/**` and `projects/active/**` are discovered/rendered, while `projects/working/**`, `projects/published/**`, `projects/archive/**`, and `projects/other/**` remain non-rendered—see root `CLAUDE.md` for invocation patterns (`resolve_project_root`).

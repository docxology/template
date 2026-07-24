# Architecture overview

Generated from the live public repository topology. The companion SVG
and Mermaid source provide the visual graph; this table is the
screen-reader-friendly and text-searchable representation.

| Layer | Name | Role |
| --- | --- | --- |
| Infrastructure · Python | `infrastructure/autoresearch/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/benchmark/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/core/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/doctor/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/documentation/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/fonds/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/llm/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/methods/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/orchestration/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/project/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/prose/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/provenance/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/publishing/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/reference/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/rendering/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/reporting/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/research/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/rules/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/scientific/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/search/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/sia/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/skills/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/steganography/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/tools/` | Reusable Layer 1 package |
| Infrastructure · Python | `infrastructure/validation/` | Reusable Layer 1 package |
| Infrastructure · config | `infrastructure/config/` | Shared configuration/resource directory |
| Infrastructure · config | `infrastructure/docker/` | Shared configuration/resource directory |
| Infrastructure · config | `infrastructure/logrotate.d/` | Shared configuration/resource directory |
| Projects · public CI scope | `projects/templates/template_active_inference/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_advanced_literature_review/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_autopoiesis/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_autoresearch_project/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_autoscientists/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_code_project/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_data_descriptor/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_eda_notebook/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_formal/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_gold_refinement/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_literature_meta_analysis/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_madlib/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_methods_paper/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_newspaper/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_pitch_deck/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_pools_rules_tools/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_prose_project/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_redacted_report/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_registered_report/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_search_project/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_sia/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_storybook/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_template/` | Canonical Layer 2 exemplar |
| Projects · public CI scope | `projects/templates/template_textbook/` | Canonical Layer 2 exemplar |

## Flow

`Infrastructure packages + configuration → pipeline orchestrator → public projects`

Source: `infrastructure.documentation.architecture_overview`.
Regenerate with `uv run python scripts/docgen/architecture_overview.py`.

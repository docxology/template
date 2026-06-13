# Method Inventory

Generated documentation coverage for every Python `def` and `class` under `src/` and `scripts/`. Entries marked `inventory fallback` have no inline docstring yet, but remain documented here by path, line, kind, and qualified name.

Total documented definitions: 750

## `src/analytical/bernoulli_toy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `ising_coupling` | inventory fallback | Inventory fallback for function `ising_coupling` defined at `src/analytical/bernoulli_toy.py:16`. |
| 22 | `function` | `symmetric_mean_field_prior` | inventory fallback | Inventory fallback for function `symmetric_mean_field_prior` defined at `src/analytical/bernoulli_toy.py:22`. |
| 27 | `function` | `ising_mutual_information` | inventory fallback | Inventory fallback for function `ising_mutual_information` defined at `src/analytical/bernoulli_toy.py:27`. |
| 41 | `function` | `ising_joint_posterior` | inventory fallback | Inventory fallback for function `ising_joint_posterior` defined at `src/analytical/bernoulli_toy.py:41`. |
| 48 | `function` | `empirical_mutual_information` | docstring | Mutual information recomputed independently from the joint via total correlation. |
| 61 | `function` | `lambda_sweep_values` | docstring | Backward-compatible sweep grid; delegates to ``lambda_grid`` SSOT. |

## `src/analytical/coupling.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `entangled_prior_unnormalised` | inventory fallback | Inventory fallback for function `entangled_prior_unnormalised` defined at `src/analytical/coupling.py:15`. |
| 27 | `function` | `entangled_posterior` | inventory fallback | Inventory fallback for function `entangled_posterior` defined at `src/analytical/coupling.py:27`. |
| 43 | `function` | `expected_value` | inventory fallback | Inventory fallback for function `expected_value` defined at `src/analytical/coupling.py:43`. |

## `src/analytical/decomposition.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 20 | `class` | `DecompositionTerms` | docstring | The four additive terms of the Theorem 5.1 entanglement decomposition (nats). |
| 41 | `function` | `DecompositionTerms.total` | docstring | Sum of the four decomposition terms (the RHS of the identity), in nats. |
| 51 | `function` | `sum_marginal_free_energies` | docstring | Sum over streams of the per-stream free energies, ``Σ_k F_k`` (nats). |
| 66 | `function` | `coupling_cost_term` | docstring | Precision-weighted expected coupling cost ``γλ·E_q[K_c]`` (nats). |
| 74 | `function` | `coupling_prior_term` | docstring | Prior-side coupling term ``log Z(λ) - λ·E_q[J]`` (nats). |
| 92 | `function` | `entanglement_decomposition_rhs` | docstring | Assemble the four-term RHS of the Theorem 5.1 decomposition. |
| 115 | `function` | `_marginals_g_broadcast` | inventory fallback | Inventory fallback for function `_marginals_g_broadcast` defined at `src/analytical/decomposition.py:115`. |
| 125 | `function` | `free_energy_against_entangled_prior` | docstring | Free energy of ``q`` against the fully entangled (``λ``-coupled) prior (nats). |
| 149 | `function` | `decomposition_identity_holds` | docstring | True iff the Theorem 5.1 identity holds within ``atol`` (nats). |

## `src/analytical/free_energy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `_safe_log` | inventory fallback | Inventory fallback for function `_safe_log` defined at `src/analytical/free_energy.py:17`. |
| 22 | `function` | `shannon_entropy` | docstring | Shannon entropy ``H(p) = -Σ p log p`` in nats. |
| 39 | `function` | `kl_divergence` | docstring | Kullback-Leibler divergence ``D(q‖p) = Σ q log(q/p)`` in nats. |
| 66 | `function` | `total_correlation` | docstring | Total correlation ``TC(q) = Σ_k H(q_k) - H(q)`` in nats (direct form). |
| 84 | `function` | `total_correlation_via_kl` | docstring | Total correlation as ``D(q‖∏_k q_k)`` in nats (KL form). |
| 101 | `function` | `free_energy` | docstring | Variational free energy ``F = γ·E_q[G] - E_q[log prior] - H(q)`` in nats. |
| 130 | `function` | `marginal_free_energy` | docstring | Per-stream (mean-field) free energy for factor ``k`` in nats. |

## `src/analytical/hyperparameters.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `Hyperparameters` | inventory fallback | Inventory fallback for class `Hyperparameters` defined at `src/analytical/hyperparameters.py:14`. |
| 22 | `function` | `load_hyperparameters` | inventory fallback | Inventory fallback for function `load_hyperparameters` defined at `src/analytical/hyperparameters.py:22`. |
| 26 | `function` | `lambda_grid` | inventory fallback | Inventory fallback for function `lambda_grid` defined at `src/analytical/hyperparameters.py:26`. |

## `src/analytical/invariants.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `inv_ising_mi_at_zero` | inventory fallback | Inventory fallback for function `inv_ising_mi_at_zero` defined at `src/analytical/invariants.py:21`. |
| 25 | `function` | `inv_ising_mi_saturates` | inventory fallback | Inventory fallback for function `inv_ising_mi_saturates` defined at `src/analytical/invariants.py:25`. |
| 30 | `function` | `inv_empirical_matches_closed_form` | inventory fallback | Inventory fallback for function `inv_empirical_matches_closed_form` defined at `src/analytical/invariants.py:30`. |
| 40 | `function` | `inv_decomposition_identity` | inventory fallback | Inventory fallback for function `inv_decomposition_identity` defined at `src/analytical/invariants.py:40`. |
| 58 | `function` | `inv_joint_is_pmf` | inventory fallback | Inventory fallback for function `inv_joint_is_pmf` defined at `src/analytical/invariants.py:58`. |
| 65 | `function` | `inv_mean_field_at_lambda_zero` | inventory fallback | Inventory fallback for function `inv_mean_field_at_lambda_zero` defined at `src/analytical/invariants.py:65`. |
| 82 | `function` | `run_invariants` | inventory fallback | Inventory fallback for function `run_invariants` defined at `src/analytical/invariants.py:82`. |
| 86 | `function` | `all_invariants_pass` | inventory fallback | Inventory fallback for function `all_invariants_pass` defined at `src/analytical/invariants.py:86`. |

## `src/analytical/joint_dist.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `is_pmf` | inventory fallback | Inventory fallback for function `is_pmf` defined at `src/analytical/joint_dist.py:13`. |
| 18 | `function` | `normalize` | inventory fallback | Inventory fallback for function `normalize` defined at `src/analytical/joint_dist.py:18`. |
| 26 | `function` | `mean_field_to_joint` | inventory fallback | Inventory fallback for function `mean_field_to_joint` defined at `src/analytical/joint_dist.py:26`. |
| 35 | `function` | `joint_marginal` | inventory fallback | Inventory fallback for function `joint_marginal` defined at `src/analytical/joint_dist.py:35`. |
| 43 | `function` | `joint_marginals` | inventory fallback | Inventory fallback for function `joint_marginals` defined at `src/analytical/joint_dist.py:43`. |
| 48 | `function` | `is_mean_field` | inventory fallback | Inventory fallback for function `is_mean_field` defined at `src/analytical/joint_dist.py:48`. |
| 54 | `function` | `m_projection` | inventory fallback | Inventory fallback for function `m_projection` defined at `src/analytical/joint_dist.py:54`. |

## `src/analytical/sweep_io.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `read_parameter_sweep` | docstring | Read ``parameter_sweep.csv`` rows as floats. |
| 29 | `function` | `summarize_sweep_rows` | docstring | Summarize sweep residuals and grid size from parsed rows. |
| 47 | `function` | `summarize_sweep_file` | docstring | Summarize sweep statistics from a CSV path. |

## `src/gates/claim_ledger.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `function` | `_load_structured` | inventory fallback | Inventory fallback for function `_load_structured` defined at `src/gates/claim_ledger.py:10`. |
| 20 | `function` | `_lookup_field` | inventory fallback | Inventory fallback for function `_lookup_field` defined at `src/gates/claim_ledger.py:20`. |
| 32 | `function` | `_numbers_equal` | inventory fallback | Inventory fallback for function `_numbers_equal` defined at `src/gates/claim_ledger.py:32`. |
| 40 | `function` | `_predicate_holds` | inventory fallback | Inventory fallback for function `_predicate_holds` defined at `src/gates/claim_ledger.py:40`. |
| 63 | `function` | `_set_equals` | inventory fallback | Inventory fallback for function `_set_equals` defined at `src/gates/claim_ledger.py:63`. |
| 69 | `function` | `_evidence_spec_holds` | inventory fallback | Inventory fallback for function `_evidence_spec_holds` defined at `src/gates/claim_ledger.py:69`. |
| 110 | `function` | `typed_claim_evidence_issues` | docstring | Return explicit typed-evidence failures for ``claim_ledger.yaml``. |
| 156 | `function` | `validate_typed_claim_evidence` | docstring | Validate optional typed evidence declarations in ``claim_ledger.yaml``. |
| 170 | `function` | `validate_claim_ledger` | inventory fallback | Inventory fallback for function `validate_claim_ledger` defined at `src/gates/claim_ledger.py:170`. |
| 212 | `function` | `verify_claim_bindings` | docstring | Semantic claim bindings -- tie manuscript values/adjectives to their oracles. |

## `src/gates/documentation_contract.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 73 | `class` | `DocumentationIssue` | docstring | A documentation contract violation with a stable diagnostic code. |
| 81 | `function` | `DocumentationIssue.format` | docstring | Return a compact CLI-friendly issue string. |
| 87 | `function` | `_has_skip_part` | inventory fallback | Inventory fallback for function `_has_skip_part` defined at `src/gates/documentation_contract.py:87`. |
| 95 | `function` | `_iter_files` | inventory fallback | Inventory fallback for function `_iter_files` defined at `src/gates/documentation_contract.py:95`. |
| 104 | `function` | `_line_number` | inventory fallback | Inventory fallback for function `_line_number` defined at `src/gates/documentation_contract.py:104`. |
| 108 | `function` | `_trim_link_target` | inventory fallback | Inventory fallback for function `_trim_link_target` defined at `src/gates/documentation_contract.py:108`. |
| 118 | `function` | `_split_link_target` | inventory fallback | Inventory fallback for function `_split_link_target` defined at `src/gates/documentation_contract.py:118`. |
| 126 | `function` | `_heading_anchor` | inventory fallback | Inventory fallback for function `_heading_anchor` defined at `src/gates/documentation_contract.py:126`. |
| 135 | `function` | `_markdown_anchors` | inventory fallback | Inventory fallback for function `_markdown_anchors` defined at `src/gates/documentation_contract.py:135`. |
| 150 | `function` | `_reference_label` | inventory fallback | Inventory fallback for function `_reference_label` defined at `src/gates/documentation_contract.py:150`. |
| 154 | `function` | `_reference_definitions` | inventory fallback | Inventory fallback for function `_reference_definitions` defined at `src/gates/documentation_contract.py:154`. |
| 158 | `function` | `_iter_markdown_targets` | docstring | Return inline and reference-style Markdown link targets. |
| 165 | `function` | `check_markdown_links` | docstring | Validate relative Markdown links, including generated Markdown outputs. |
| 222 | `function` | `check_hydrated_output_links` | docstring | Hydrated manuscript copies must link relative to output/manuscript/. |
| 244 | `function` | `check_readme_agents_pairs` | docstring | Require README.md and AGENTS.md to appear as a pair in source docs. |
| 265 | `function` | `check_project_local_commands` | docstring | Reject stale root-shaped commands in project-local documentation. |
| 284 | `function` | `_paragraphs` | inventory fallback | Inventory fallback for function `_paragraphs` defined at `src/gates/documentation_contract.py:284`. |
| 288 | `function` | `check_historical_test_evidence` | docstring | Keep stale suite-count evidence clearly archived and current evidence singular. |
| 325 | `function` | `check_reference_signposts` | docstring | Require canonical verification and reference signposts in reader docs. |
| 373 | `function` | `check_documentation_contract` | docstring | Run all documentation contract checks. |

## `src/gates/lean.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 20 | `function` | `lean_project_present` | docstring | True when this project ships a Lake root (``lean/lakefile.lean``). |
| 25 | `function` | `build_lean` | docstring | Build the Lean package when present; skip cleanly when absent. |
| 42 | `function` | `lean_axioms_clean` | docstring | Audit declarations with ``#print axioms``; True iff only whitelisted axioms appear. |

## `src/gates/manuscript_checks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `_duplicate_track_markers` | docstring | Composed sections in which the same sheaf-track marker appears more than once. |
| 30 | `function` | `validate_manuscript` | inventory fallback | Inventory fallback for function `validate_manuscript` defined at `src/gates/manuscript_checks.py:30`. |

## `src/gates/method_inventory.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `MethodEntry` | docstring | A documented function, method, nested helper, or class definition. |
| 25 | `function` | `_first_docstring_line` | docstring | Return a compact first docstring line when a definition has one. |
| 33 | `function` | `_fallback_summary` | docstring | Build an inventory-backed summary for a definition without a docstring. |
| 38 | `function` | `_definition_kind` | docstring | Normalize AST node types into report-friendly definition kinds. |
| 47 | `class` | `_DefinitionVisitor` | docstring | Collect definitions while preserving nested qualified names. |
| 50 | `function` | `_DefinitionVisitor.__init__` | inventory fallback | Inventory fallback for function `_DefinitionVisitor.__init__` defined at `src/gates/method_inventory.py:50`. |
| 55 | `function` | `_DefinitionVisitor.visit_ClassDef` | inventory fallback | Inventory fallback for function `_DefinitionVisitor.visit_ClassDef` defined at `src/gates/method_inventory.py:55`. |
| 61 | `function` | `_DefinitionVisitor.visit_FunctionDef` | inventory fallback | Inventory fallback for function `_DefinitionVisitor.visit_FunctionDef` defined at `src/gates/method_inventory.py:61`. |
| 67 | `function` | `_DefinitionVisitor.visit_AsyncFunctionDef` | inventory fallback | Inventory fallback for function `_DefinitionVisitor.visit_AsyncFunctionDef` defined at `src/gates/method_inventory.py:67`. |
| 73 | `function` | `_DefinitionVisitor._record` | inventory fallback | Inventory fallback for function `_DefinitionVisitor._record` defined at `src/gates/method_inventory.py:73`. |
| 89 | `function` | `_source_files` | docstring | Return Python files in the documentation inventory scope. |
| 100 | `function` | `_path_sort_key` | docstring | Sort inventory paths by declared source-root order, then by path. |
| 110 | `function` | `collect_method_entries` | docstring | Collect every class/function definition under source modules and scripts. |
| 123 | `function` | `_escape_cell` | docstring | Escape Markdown table cells without changing the underlying value. |
| 128 | `function` | `render_method_inventory_markdown` | docstring | Render method inventory entries as a grouped Markdown reference. |
| 172 | `function` | `write_method_inventory` | docstring | Write the method inventory Markdown report and return its path. |

## `src/gates/output_checks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `_figures_nonblank` | docstring | Return True only if every required figure PNG is non-trivially sized and decodable. |
| 40 | `function` | `_read_json` | inventory fallback | Inventory fallback for function `_read_json` defined at `src/gates/output_checks.py:40`. |
| 50 | `function` | `_pymdp_logging_expected` | inventory fallback | Inventory fallback for function `_pymdp_logging_expected` defined at `src/gates/output_checks.py:50`. |
| 60 | `function` | `_efe_values_explained` | inventory fallback | Inventory fallback for function `_efe_values_explained` defined at `src/gates/output_checks.py:60`. |
| 69 | `function` | `_required_output_checks` | inventory fallback | Inventory fallback for function `_required_output_checks` defined at `src/gates/output_checks.py:69`. |
| 74 | `function` | `_add_simulation_checks` | inventory fallback | Inventory fallback for function `_add_simulation_checks` defined at `src/gates/output_checks.py:74`. |
| 181 | `function` | `_add_validation_spine_checks` | inventory fallback | Inventory fallback for function `_add_validation_spine_checks` defined at `src/gates/output_checks.py:181`. |
| 302 | `function` | `_load_promoted_artifacts` | inventory fallback | Inventory fallback for function `_load_promoted_artifacts` defined at `src/gates/output_checks.py:302`. |
| 306 | `function` | `_add_toy_formal_integration_checks` | inventory fallback | Inventory fallback for function `_add_toy_formal_integration_checks` defined at `src/gates/output_checks.py:306`. |
| 432 | `function` | `_add_visualization_checks` | inventory fallback | Inventory fallback for function `_add_visualization_checks` defined at `src/gates/output_checks.py:432`. |
| 473 | `function` | `_add_canonical_sheaf_checks` | inventory fallback | Inventory fallback for function `_add_canonical_sheaf_checks` defined at `src/gates/output_checks.py:473`. |
| 583 | `function` | `_add_track_validator_checks` | inventory fallback | Inventory fallback for function `_add_track_validator_checks` defined at `src/gates/output_checks.py:583`. |
| 603 | `function` | `_add_log_check` | inventory fallback | Inventory fallback for function `_add_log_check` defined at `src/gates/output_checks.py:603`. |
| 611 | `function` | `_set_experiment_plan_metrics` | inventory fallback | Inventory fallback for function `_set_experiment_plan_metrics` defined at `src/gates/output_checks.py:611`. |
| 694 | `function` | `validate_outputs` | docstring | Validate every registered output artifact and return gate booleans by name. |

## `src/gnn/concordance.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 34 | `function` | `parity_gaps` | docstring | Report concordance gaps between GNN symbols and their ontology annotations. |
| 61 | `function` | `concordance_holds` | inventory fallback | Inventory fallback for function `concordance_holds` defined at `src/gnn/concordance.py:61`. |

## `src/gnn/model.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `GnnVariable` | inventory fallback | Inventory fallback for class `GnnVariable` defined at `src/gnn/model.py:14`. |
| 22 | `function` | `GnnVariable.size` | inventory fallback | Inventory fallback for function `GnnVariable.size` defined at `src/gnn/model.py:22`. |
| 30 | `class` | `GnnConnection` | inventory fallback | Inventory fallback for class `GnnConnection` defined at `src/gnn/model.py:30`. |
| 38 | `class` | `GnnModel` | inventory fallback | Inventory fallback for class `GnnModel` defined at `src/gnn/model.py:38`. |
| 50 | `function` | `GnnModel.variable` | inventory fallback | Inventory fallback for function `GnnModel.variable` defined at `src/gnn/model.py:50`. |
| 55 | `function` | `GnnModel.has` | inventory fallback | Inventory fallback for function `GnnModel.has` defined at `src/gnn/model.py:55`. |

## `src/gnn/parser.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 25 | `class` | `GNNParseError` | docstring | Raised on structural GNN parse failures. |
| 29 | `function` | `_split_sections` | inventory fallback | Inventory fallback for function `_split_sections` defined at `src/gnn/parser.py:29`. |
| 47 | `function` | `_section` | inventory fallback | Inventory fallback for function `_section` defined at `src/gnn/parser.py:47`. |
| 54 | `function` | `_parse_dims_and_type` | inventory fallback | Inventory fallback for function `_parse_dims_and_type` defined at `src/gnn/parser.py:54`. |
| 76 | `function` | `_parse_state_space` | inventory fallback | Inventory fallback for function `_parse_state_space` defined at `src/gnn/parser.py:76`. |
| 91 | `function` | `_parse_connections` | inventory fallback | Inventory fallback for function `_parse_connections` defined at `src/gnn/parser.py:91`. |
| 111 | `function` | `_strip_comment_lines` | inventory fallback | Inventory fallback for function `_strip_comment_lines` defined at `src/gnn/parser.py:111`. |
| 115 | `function` | `_parse_param_blocks` | inventory fallback | Inventory fallback for function `_parse_param_blocks` defined at `src/gnn/parser.py:115`. |
| 148 | `function` | `_parse_kv` | inventory fallback | Inventory fallback for function `_parse_kv` defined at `src/gnn/parser.py:148`. |
| 164 | `function` | `parse_gnn` | inventory fallback | Inventory fallback for function `parse_gnn` defined at `src/gnn/parser.py:164`. |
| 195 | `function` | `parse_gnn_file` | inventory fallback | Inventory fallback for function `parse_gnn_file` defined at `src/gnn/parser.py:195`. |

## `src/manuscript/hydrate.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `format_variables` | docstring | Stringify variable values for manuscript substitution. |
| 35 | `function` | `collect_manuscript_tokens` | docstring | Return token names referenced as {{name}} or {{name:.4f}} in markdown. |
| 40 | `function` | `collect_single_brace_tokens` | docstring | Return snake_case names in single-brace {name} form (likely typos). |
| 45 | `function` | `collect_malformed_token_names` | docstring | Return token-like names that are not valid double-brace placeholders. |
| 51 | `function` | `collect_tokens_in_directory` | inventory fallback | Inventory fallback for function `collect_tokens_in_directory` defined at `src/manuscript/hydrate.py:51`. |
| 60 | `function` | `validate_manuscript_tokens` | docstring | Return sorted unknown token names referenced under manuscript_dir. |
| 69 | `function` | `substitute_snake_case_tokens` | inventory fallback | Inventory fallback for function `substitute_snake_case_tokens` defined at `src/manuscript/hydrate.py:69`. |
| 75 | `function` | `substitute_snake_case_tokens._replace` | inventory fallback | Inventory fallback for function `substitute_snake_case_tokens._replace` defined at `src/manuscript/hydrate.py:75`. |
| 92 | `function` | `retarget_resolved_output_links` | docstring | Retarget output links for hydrated copies under output/manuscript/. |
| 97 | `function` | `write_resolved_manuscript` | docstring | Write token-substituted markdown copies to output/manuscript/. |

## `src/manuscript/invariant_counts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `load_invariant_counts` | docstring | Return passed/total invariant counts from merged reports when present. |
| 31 | `function` | `invariants_are_merged` | docstring | True when the report contains genuine *simulation* invariants by content. |

## `src/manuscript/render_helpers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `extract_preamble` | docstring | Return the LaTeX inside the ```latex fence of preamble.md (or ""). |
| 28 | `function` | `geometry_string` | docstring | Read page geometry from ``manuscript/config.yaml``; fall back to 0.5 in margins. |

## `src/manuscript/sheaf/cli.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `build_parser` | docstring | Build the sheaf composition command parser. |
| 76 | `function` | `_emit_issues` | inventory fallback | Inventory fallback for function `_emit_issues` defined at `src/manuscript/sheaf/cli.py:76`. |
| 81 | `function` | `_coverage_paths` | inventory fallback | Inventory fallback for function `_coverage_paths` defined at `src/manuscript/sheaf/cli.py:81`. |
| 88 | `function` | `_emit_coverage` | inventory fallback | Inventory fallback for function `_emit_coverage` defined at `src/manuscript/sheaf/cli.py:88`. |
| 112 | `function` | `run_compose_cli` | docstring | Run the sheaf composition CLI for ``project_root``. |

## `src/manuscript/sheaf/compose.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 24 | `function` | `issues_have_errors` | inventory fallback | Inventory fallback for function `issues_have_errors` defined at `src/manuscript/sheaf/compose.py:24`. |
| 28 | `function` | `validate_manifest` | inventory fallback | Inventory fallback for function `validate_manifest` defined at `src/manuscript/sheaf/compose.py:28`. |
| 96 | `function` | `sheaf_law_issues` | docstring | Surface sheaf-law violations as error-level manifest issues for the strict gate. |
| 105 | `function` | `_imrad_group_titles` | inventory fallback | Inventory fallback for function `_imrad_group_titles` defined at `src/manuscript/sheaf/compose.py:105`. |
| 113 | `function` | `_imrad_divider_markdown` | inventory fallback | Inventory fallback for function `_imrad_divider_markdown` defined at `src/manuscript/sheaf/compose.py:113`. |
| 123 | `function` | `compose_section` | inventory fallback | Inventory fallback for function `compose_section` defined at `src/manuscript/sheaf/compose.py:123`. |
| 156 | `function` | `compose_all_sections` | inventory fallback | Inventory fallback for function `compose_all_sections` defined at `src/manuscript/sheaf/compose.py:156`. |

## `src/manuscript/sheaf/counts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `structural_counts` | docstring | Counts derived from sheaf manifest, registry, and coverage matrix. |

## `src/manuscript/sheaf/coverage.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 24 | `class` | `SheafCoverageContext` | inventory fallback | Inventory fallback for class `SheafCoverageContext` defined at `src/manuscript/sheaf/coverage.py:24`. |
| 30 | `function` | `load_sheaf_coverage_context` | inventory fallback | Inventory fallback for function `load_sheaf_coverage_context` defined at `src/manuscript/sheaf/coverage.py:30`. |
| 46 | `function` | `classify_cell` | inventory fallback | Inventory fallback for function `classify_cell` defined at `src/manuscript/sheaf/coverage.py:46`. |
| 60 | `function` | `build_coverage_matrix` | inventory fallback | Inventory fallback for function `build_coverage_matrix` defined at `src/manuscript/sheaf/coverage.py:60`. |
| 103 | `function` | `coverage_matrix_to_dict` | inventory fallback | Inventory fallback for function `coverage_matrix_to_dict` defined at `src/manuscript/sheaf/coverage.py:103`. |
| 130 | `function` | `write_coverage_json` | inventory fallback | Inventory fallback for function `write_coverage_json` defined at `src/manuscript/sheaf/coverage.py:130`. |
| 140 | `function` | `load_coverage_json` | inventory fallback | Inventory fallback for function `load_coverage_json` defined at `src/manuscript/sheaf/coverage.py:140`. |
| 145 | `function` | `validate_coverage_strict` | inventory fallback | Inventory fallback for function `validate_coverage_strict` defined at `src/manuscript/sheaf/coverage.py:145`. |
| 158 | `function` | `gray_cell_count` | inventory fallback | Inventory fallback for function `gray_cell_count` defined at `src/manuscript/sheaf/coverage.py:158`. |
| 162 | `function` | `gray_cell_count_from_json` | inventory fallback | Inventory fallback for function `gray_cell_count_from_json` defined at `src/manuscript/sheaf/coverage.py:162`. |
| 171 | `function` | `validate_coverage_json_data` | inventory fallback | Inventory fallback for function `validate_coverage_json_data` defined at `src/manuscript/sheaf/coverage.py:171`. |
| 207 | `function` | `emit_coverage_artifacts` | docstring | Build matrix from live manifest/registry and write coverage JSON only. |

## `src/manuscript/sheaf/laws.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 67 | `class` | `SheafLaw` | docstring | The structural laws that make the coverage presheaf a sheaf. |
| 79 | `class` | `LawViolation` | docstring | A single counter-example to one sheaf law. |
| 88 | `class` | `SheafLawReport` | docstring | Structured result of verifying the sheaf laws against a manifest. |
| 95 | `function` | `SheafLawReport.ok` | inventory fallback | Inventory fallback for function `SheafLawReport.ok` defined at `src/manuscript/sheaf/laws.py:95`. |
| 98 | `function` | `SheafLawReport.for_law` | inventory fallback | Inventory fallback for function `SheafLawReport.for_law` defined at `src/manuscript/sheaf/laws.py:98`. |
| 101 | `function` | `SheafLawReport.law_ok` | inventory fallback | Inventory fallback for function `SheafLawReport.law_ok` defined at `src/manuscript/sheaf/laws.py:101`. |
| 105 | `function` | `SheafLawReport.passed_laws` | inventory fallback | Inventory fallback for function `SheafLawReport.passed_laws` defined at `src/manuscript/sheaf/laws.py:105`. |
| 109 | `function` | `SheafLawReport.summary` | inventory fallback | Inventory fallback for function `SheafLawReport.summary` defined at `src/manuscript/sheaf/laws.py:109`. |
| 115 | `function` | `_known_renderers` | inventory fallback | Inventory fallback for function `_known_renderers` defined at `src/manuscript/sheaf/laws.py:115`. |
| 120 | `function` | `_composing_sections` | inventory fallback | Inventory fallback for function `_composing_sections` defined at `src/manuscript/sheaf/laws.py:120`. |
| 124 | `function` | `_check_poset` | docstring | IMRAD blocks form a chain; compose order is monotone in block rank. |
| 168 | `function` | `_check_presheaf` | docstring | Bound tracks are registered; track order restricts the global order. |
| 224 | `function` | `_check_separation` | docstring | s ↦ output_name is injective over composing sections. |
| 253 | `function` | `_check_gluing` | docstring | Compose order is a strict linear extension; each section glues once. |
| 292 | `function` | `_check_typing` | docstring | Each binding is well-typed: renderer exists and suffix is accepted. |
| 331 | `function` | `_check_compositionality` | docstring | Every fragment file is private to one section (composition is a coproduct). |
| 362 | `function` | `verify_sheaf_laws` | docstring | Verify all sheaf laws against the live (or supplied) manifest + registry. |
| 388 | `function` | `sheaf_law_violations` | docstring | Pure law check against in-memory manifest + registry (no filesystem load). |

## `src/manuscript/sheaf/layers_report.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `render_track_registry_table` | inventory fallback | Inventory fallback for function `render_track_registry_table` defined at `src/manuscript/sheaf/layers_report.py:11`. |
| 33 | `function` | `render_binding_matrix_table` | inventory fallback | Inventory fallback for function `render_binding_matrix_table` defined at `src/manuscript/sheaf/layers_report.py:33`. |
| 69 | `function` | `render_coverage_legend` | inventory fallback | Inventory fallback for function `render_coverage_legend` defined at `src/manuscript/sheaf/layers_report.py:69`. |
| 83 | `function` | `render_evidence_crosswalk_table` | inventory fallback | Inventory fallback for function `render_evidence_crosswalk_table` defined at `src/manuscript/sheaf/layers_report.py:83`. |
| 101 | `function` | `render_artifact_producer_table` | inventory fallback | Inventory fallback for function `render_artifact_producer_table` defined at `src/manuscript/sheaf/layers_report.py:101`. |
| 125 | `function` | `render_semantic_restrictions_table` | inventory fallback | Inventory fallback for function `render_semantic_restrictions_table` defined at `src/manuscript/sheaf/layers_report.py:125`. |
| 168 | `function` | `render_track_improvement_scope_table` | inventory fallback | Inventory fallback for function `render_track_improvement_scope_table` defined at `src/manuscript/sheaf/layers_report.py:168`. |
| 191 | `function` | `render_track_lane_matrix_table` | inventory fallback | Inventory fallback for function `render_track_lane_matrix_table` defined at `src/manuscript/sheaf/layers_report.py:191`. |
| 218 | `function` | `render_section_status_table` | inventory fallback | Inventory fallback for function `render_section_status_table` defined at `src/manuscript/sheaf/layers_report.py:218`. |
| 251 | `function` | `render_track_status_table` | inventory fallback | Inventory fallback for function `render_track_status_table` defined at `src/manuscript/sheaf/layers_report.py:251`. |
| 273 | `function` | `render_sheaf_render_log_table` | inventory fallback | Inventory fallback for function `render_sheaf_render_log_table` defined at `src/manuscript/sheaf/layers_report.py:273`. |
| 294 | `function` | `render_sheaf_layers_markdown` | inventory fallback | Inventory fallback for function `render_sheaf_layers_markdown` defined at `src/manuscript/sheaf/layers_report.py:294`. |

## `src/manuscript/sheaf/manifest.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 22 | `function` | `parse_missing` | inventory fallback | Inventory fallback for function `parse_missing` defined at `src/manuscript/sheaf/manifest.py:22`. |
| 31 | `function` | `load_manifest` | inventory fallback | Inventory fallback for function `load_manifest` defined at `src/manuscript/sheaf/manifest.py:31`. |
| 101 | `function` | `default_manifest_path` | inventory fallback | Inventory fallback for function `default_manifest_path` defined at `src/manuscript/sheaf/manifest.py:101`. |

## `src/manuscript/sheaf/models.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `coverage_cell_symbol` | inventory fallback | Inventory fallback for function `coverage_cell_symbol` defined at `src/manuscript/sheaf/models.py:14`. |
| 26 | `class` | `MissingTrackPolicy` | inventory fallback | Inventory fallback for class `MissingTrackPolicy` defined at `src/manuscript/sheaf/models.py:26`. |
| 33 | `class` | `TrackSpec` | inventory fallback | Inventory fallback for class `TrackSpec` defined at `src/manuscript/sheaf/models.py:33`. |
| 44 | `class` | `SheafDefaults` | inventory fallback | Inventory fallback for class `SheafDefaults` defined at `src/manuscript/sheaf/models.py:44`. |
| 49 | `class` | `SheafSection` | inventory fallback | Inventory fallback for class `SheafSection` defined at `src/manuscript/sheaf/models.py:49`. |
| 64 | `function` | `SheafSection.should_compose` | inventory fallback | Inventory fallback for function `SheafSection.should_compose` defined at `src/manuscript/sheaf/models.py:64`. |
| 69 | `class` | `SheafManifest` | inventory fallback | Inventory fallback for class `SheafManifest` defined at `src/manuscript/sheaf/models.py:69`. |
| 76 | `class` | `ManifestIssue` | inventory fallback | Inventory fallback for class `ManifestIssue` defined at `src/manuscript/sheaf/models.py:76`. |
| 83 | `class` | `ComposeOptions` | inventory fallback | Inventory fallback for class `ComposeOptions` defined at `src/manuscript/sheaf/models.py:83`. |
| 91 | `class` | `TrackRegistry` | inventory fallback | Inventory fallback for class `TrackRegistry` defined at `src/manuscript/sheaf/models.py:91`. |
| 97 | `class` | `ComposeResult` | inventory fallback | Inventory fallback for class `ComposeResult` defined at `src/manuscript/sheaf/models.py:97`. |
| 103 | `class` | `CoverageCell` | inventory fallback | Inventory fallback for class `CoverageCell` defined at `src/manuscript/sheaf/models.py:103`. |
| 112 | `class` | `CoverageSectionRow` | inventory fallback | Inventory fallback for class `CoverageSectionRow` defined at `src/manuscript/sheaf/models.py:112`. |
| 123 | `class` | `CoverageMatrix` | inventory fallback | Inventory fallback for class `CoverageMatrix` defined at `src/manuscript/sheaf/models.py:123`. |
| 127 | `function` | `CoverageMatrix.gray_cells` | inventory fallback | Inventory fallback for function `CoverageMatrix.gray_cells` defined at `src/manuscript/sheaf/models.py:127`. |

## `src/manuscript/sheaf/registry.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `load_track_registry` | inventory fallback | Inventory fallback for function `load_track_registry` defined at `src/manuscript/sheaf/registry.py:12`. |
| 36 | `function` | `track_order_for_section` | inventory fallback | Inventory fallback for function `track_order_for_section` defined at `src/manuscript/sheaf/registry.py:36`. |
| 54 | `function` | `list_registered_tracks` | inventory fallback | Inventory fallback for function `list_registered_tracks` defined at `src/manuscript/sheaf/registry.py:54`. |

## `src/manuscript/sheaf/renderers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_render_ontology` | inventory fallback | Inventory fallback for function `_render_ontology` defined at `src/manuscript/sheaf/renderers.py:18`. |
| 35 | `function` | `_require_track_spec` | inventory fallback | Inventory fallback for function `_require_track_spec` defined at `src/manuscript/sheaf/renderers.py:35`. |
| 42 | `function` | `render_track_body` | inventory fallback | Inventory fallback for function `render_track_body` defined at `src/manuscript/sheaf/renderers.py:42`. |
| 50 | `function` | `_resolve_section_figures` | inventory fallback | Inventory fallback for function `_resolve_section_figures` defined at `src/manuscript/sheaf/renderers.py:50`. |
| 69 | `function` | `_resolve_layers_report` | inventory fallback | Inventory fallback for function `_resolve_layers_report` defined at `src/manuscript/sheaf/renderers.py:69`. |
| 89 | `function` | `resolve_track_body` | docstring | Resolve composed markdown for one bound track. |
| 104 | `function` | `validate_renderer_specs` | inventory fallback | Inventory fallback for function `validate_renderer_specs` defined at `src/manuscript/sheaf/renderers.py:104`. |

## `src/manuscript/sheaf/report.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `class` | `HeatmapConfig` | inventory fallback | Inventory fallback for class `HeatmapConfig` defined at `src/manuscript/sheaf/report.py:15`. |
| 24 | `class` | `CoverageColorConfig` | inventory fallback | Inventory fallback for class `CoverageColorConfig` defined at `src/manuscript/sheaf/report.py:24`. |
| 31 | `class` | `ReportConfig` | inventory fallback | Inventory fallback for class `ReportConfig` defined at `src/manuscript/sheaf/report.py:31`. |
| 40 | `class` | `CoverageConfig` | inventory fallback | Inventory fallback for class `CoverageConfig` defined at `src/manuscript/sheaf/report.py:40`. |
| 47 | `class` | `CoverageReport` | inventory fallback | Inventory fallback for class `CoverageReport` defined at `src/manuscript/sheaf/report.py:47`. |
| 57 | `function` | `load_coverage_config` | inventory fallback | Inventory fallback for function `load_coverage_config` defined at `src/manuscript/sheaf/report.py:57`. |
| 104 | `function` | `default_coverage_config_path` | inventory fallback | Inventory fallback for function `default_coverage_config_path` defined at `src/manuscript/sheaf/report.py:104`. |
| 108 | `function` | `build_coverage_report` | inventory fallback | Inventory fallback for function `build_coverage_report` defined at `src/manuscript/sheaf/report.py:108`. |
| 139 | `function` | `_imrad_heading` | inventory fallback | Inventory fallback for function `_imrad_heading` defined at `src/manuscript/sheaf/report.py:139`. |
| 143 | `function` | `render_report_markdown` | inventory fallback | Inventory fallback for function `render_report_markdown` defined at `src/manuscript/sheaf/report.py:143`. |
| 195 | `function` | `write_coverage_page` | inventory fallback | Inventory fallback for function `write_coverage_page` defined at `src/manuscript/sheaf/report.py:195`. |

## `src/manuscript/sheaf/semantic.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 278 | `function` | `_rel` | inventory fallback | Inventory fallback for function `_rel` defined at `src/manuscript/sheaf/semantic.py:278`. |
| 282 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/manuscript/sheaf/semantic.py:282`. |
| 289 | `function` | `_configured_analysis_scripts` | inventory fallback | Inventory fallback for function `_configured_analysis_scripts` defined at `src/manuscript/sheaf/semantic.py:289`. |
| 301 | `function` | `_claims_by_path` | inventory fallback | Inventory fallback for function `_claims_by_path` defined at `src/manuscript/sheaf/semantic.py:301`. |
| 311 | `function` | `_animation_frame_count` | inventory fallback | Inventory fallback for function `_animation_frame_count` defined at `src/manuscript/sheaf/semantic.py:311`. |
| 324 | `function` | `_lean_status` | inventory fallback | Inventory fallback for function `_lean_status` defined at `src/manuscript/sheaf/semantic.py:324`. |
| 339 | `function` | `_policy_comparison_restrictions` | inventory fallback | Inventory fallback for function `_policy_comparison_restrictions` defined at `src/manuscript/sheaf/semantic.py:339`. |
| 353 | `function` | `_policy_posterior_restrictions` | inventory fallback | Inventory fallback for function `_policy_posterior_restrictions` defined at `src/manuscript/sheaf/semantic.py:353`. |
| 363 | `function` | `_runtime_diagnostics_restrictions` | inventory fallback | Inventory fallback for function `_runtime_diagnostics_restrictions` defined at `src/manuscript/sheaf/semantic.py:363`. |
| 374 | `function` | `_restriction_class` | inventory fallback | Inventory fallback for function `_restriction_class` defined at `src/manuscript/sheaf/semantic.py:374`. |
| 386 | `function` | `_restriction_lane` | inventory fallback | Inventory fallback for function `_restriction_lane` defined at `src/manuscript/sheaf/semantic.py:386`. |
| 417 | `function` | `_restriction_lane_assignments` | inventory fallback | Inventory fallback for function `_restriction_lane_assignments` defined at `src/manuscript/sheaf/semantic.py:417`. |
| 421 | `function` | `_restriction_value_ok` | inventory fallback | Inventory fallback for function `_restriction_value_ok` defined at `src/manuscript/sheaf/semantic.py:421`. |
| 435 | `function` | `_restriction_lane_summaries` | inventory fallback | Inventory fallback for function `_restriction_lane_summaries` defined at `src/manuscript/sheaf/semantic.py:435`. |
| 451 | `function` | `_proof_obligation_rows` | inventory fallback | Inventory fallback for function `_proof_obligation_rows` defined at `src/manuscript/sheaf/semantic.py:451`. |
| 463 | `function` | `_graph_world_restrictions` | inventory fallback | Inventory fallback for function `_graph_world_restrictions` defined at `src/manuscript/sheaf/semantic.py:463`. |
| 476 | `function` | `_pymdp_hash_restrictions` | inventory fallback | Inventory fallback for function `_pymdp_hash_restrictions` defined at `src/manuscript/sheaf/semantic.py:476`. |
| 485 | `function` | `_gnn_symbols` | inventory fallback | Inventory fallback for function `_gnn_symbols` defined at `src/manuscript/sheaf/semantic.py:485`. |
| 492 | `function` | `_section_ontology_symbols` | inventory fallback | Inventory fallback for function `_section_ontology_symbols` defined at `src/manuscript/sheaf/semantic.py:492`. |
| 497 | `function` | `_expected_symbol_gaps` | inventory fallback | Inventory fallback for function `_expected_symbol_gaps` defined at `src/manuscript/sheaf/semantic.py:497`. |
| 521 | `function` | `semantic_gluing_issues` | docstring | Return semantic cross-track disagreements not covered by structural laws. |
| 646 | `function` | `_section_records` | inventory fallback | Inventory fallback for function `_section_records` defined at `src/manuscript/sheaf/semantic.py:646`. |
| 672 | `function` | `_claim_records` | inventory fallback | Inventory fallback for function `_claim_records` defined at `src/manuscript/sheaf/semantic.py:672`. |
| 694 | `function` | `build_evidence_crosswalk` | docstring | Build a claim-to-artifact crosswalk from the typed claim ledger. |
| 716 | `function` | `build_validation_dependency_graph` | docstring | Build script → artifact → manuscript/gate dependency records. |
| 723 | `function` | `validate_configured_artifact_producers` | docstring | Fail when required generated artifacts lack configured analysis producers. |
| 794 | `function` | `_semantic_artifact_sources` | inventory fallback | Inventory fallback for function `_semantic_artifact_sources` defined at `src/manuscript/sheaf/semantic.py:794`. |
| 798 | `function` | `_semantic_payloads` | inventory fallback | Inventory fallback for function `_semantic_payloads` defined at `src/manuscript/sheaf/semantic.py:798`. |
| 802 | `function` | `_semantic_track_rows` | inventory fallback | Inventory fallback for function `_semantic_track_rows` defined at `src/manuscript/sheaf/semantic.py:802`. |
| 816 | `function` | `_semantic_shared_symbols` | inventory fallback | Inventory fallback for function `_semantic_shared_symbols` defined at `src/manuscript/sheaf/semantic.py:816`. |
| 825 | `function` | `_canonical_restriction_snapshot` | inventory fallback | Inventory fallback for function `_canonical_restriction_snapshot` defined at `src/manuscript/sheaf/semantic.py:825`. |
| 834 | `function` | `build_semantic_gluing_certificate` | docstring | Build a JSON-serializable semantic certificate from live project state. |
| 995 | `function` | `write_semantic_gluing_certificate` | inventory fallback | Inventory fallback for function `write_semantic_gluing_certificate` defined at `src/manuscript/sheaf/semantic.py:995`. |
| 1020 | `function` | `_refresh_hydrated_manuscript` | docstring | Refresh composed and hydrated manuscript artifacts for semantic checks. |
| 1037 | `function` | `write_semantic_gluing_outputs` | docstring | Write semantic certificate, evidence crosswalk, and dependency graph outputs. |
| 1076 | `function` | `_stable_artifact_graph` | inventory fallback | Inventory fallback for function `_stable_artifact_graph` defined at `src/manuscript/sheaf/semantic.py:1076`. |
| 1088 | `function` | `_stable_certificate_fields` | inventory fallback | Inventory fallback for function `_stable_certificate_fields` defined at `src/manuscript/sheaf/semantic.py:1088`. |
| 1101 | `function` | `_semantic_lane_summary_issues` | inventory fallback | Inventory fallback for function `_semantic_lane_summary_issues` defined at `src/manuscript/sheaf/semantic.py:1101`. |
| 1121 | `function` | `validate_semantic_gluing` | docstring | Validate the live semantic certificate and its generated artifact. |

## `src/manuscript/sheaf/status.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_load_yaml` | inventory fallback | Inventory fallback for function `_load_yaml` defined at `src/manuscript/sheaf/status.py:18`. |
| 25 | `function` | `_claim_indexes` | inventory fallback | Inventory fallback for function `_claim_indexes` defined at `src/manuscript/sheaf/status.py:25`. |
| 52 | `function` | `_artifact_indexes` | inventory fallback | Inventory fallback for function `_artifact_indexes` defined at `src/manuscript/sheaf/status.py:52`. |
| 73 | `function` | `build_sheaf_section_status_matrix` | docstring | Build one explicit status row for every section x registered-track cell. |
| 199 | `function` | `build_sheaf_render_log` | docstring | Build a deterministic render/log summary for the sheaf manuscript layer. |
| 284 | `function` | `validate_sheaf_status_outputs` | inventory fallback | Inventory fallback for function `validate_sheaf_status_outputs` defined at `src/manuscript/sheaf/status.py:284`. |
| 330 | `function` | `write_sheaf_status_outputs` | inventory fallback | Inventory fallback for function `write_sheaf_status_outputs` defined at `src/manuscript/sheaf/status.py:330`. |

## `src/manuscript/variables.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_ising_mi_saturation_from_sweep` | docstring | Maximum closed-form MI on the measured λ grid (nats). |
| 25 | `function` | `_free_energy_argmin_lambda` | docstring | λ minimizing free energy of the entangled posterior vs the mean-field prior. |
| 52 | `function` | `_policy_goal_counts_by_mode` | docstring | Goal-reaching run counts split by inference mode from si_policy_comparison runs. |
| 66 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/manuscript/variables.py:66`. |
| 76 | `function` | `_pipeline_track_count` | docstring | Required pipeline tracks from ``tracks.yaml`` (distinct from ``sheaf_track_count``). |
| 86 | `function` | `_gnn_spec_version` | inventory fallback | Inventory fallback for function `_gnn_spec_version` defined at `src/manuscript/variables.py:86`. |
| 102 | `function` | `_efe_token_values` | docstring | Manuscript tokens for the closed-form Expected Free Energy decomposition. |
| 126 | `function` | `_precision_token_values` | docstring | Manuscript tokens for the closed-form precision (gamma) sweep. |
| 148 | `function` | `_cue_tmaze_token_values` | docstring | Manuscript tokens for the cue-then-reward T-maze epistemic-necessity result. |
| 167 | `function` | `_dirichlet_token_values` | docstring | Manuscript tokens for the deterministic Dirichlet likelihood-learning run. |
| 237 | `function` | `_load_variable_artifacts` | docstring | Load optional generated artifacts used by manuscript tokens. |
| 242 | `function` | `_core_token_values` | docstring | Return project, analytical, invariant, and structural manuscript tokens. |
| 269 | `function` | `_simulation_token_values` | docstring | Return SI, PyMDP runtime, posterior, and graph-world manuscript tokens. |
| 328 | `function` | `_validation_spine_token_values` | docstring | Return provenance, replay, and counterexample manuscript tokens. |
| 352 | `function` | `_toy_formal_token_values` | docstring | Return promoted toy-sweep, formal-interop, and animation manuscript tokens. |
| 389 | `function` | `_semantic_visualization_token_values` | docstring | Return semantic, visualization, staleness, and cross-track manuscript tokens. |
| 463 | `function` | `_canonical_sheaf_token_values` | docstring | Return canonical sheaf-track, release, proof, and scholarship tokens. |
| 552 | `function` | `generate_variables` | docstring | Generate manuscript tokens from live configuration and output artifacts. |

## `src/ontology/bindings.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 27 | `function` | `load_section_ontology` | inventory fallback | Inventory fallback for function `load_section_ontology` defined at `src/ontology/bindings.py:27`. |
| 43 | `function` | `validate_gnn_ontology` | inventory fallback | Inventory fallback for function `validate_gnn_ontology` defined at `src/ontology/bindings.py:43`. |
| 57 | `function` | `_validate_section_ontology_exact` | inventory fallback | Inventory fallback for function `_validate_section_ontology_exact` defined at `src/ontology/bindings.py:57`. |
| 74 | `function` | `validate_all_gnn_ontology` | docstring | Validate every project GNN model against its model-specific ontology map. |

## `src/orchestration/analysis.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `write_parameter_sweep` | inventory fallback | Inventory fallback for function `write_parameter_sweep` defined at `src/orchestration/analysis.py:18`. |
| 39 | `function` | `write_invariants_report` | inventory fallback | Inventory fallback for function `write_invariants_report` defined at `src/orchestration/analysis.py:39`. |
| 53 | `function` | `summarize_sweep` | inventory fallback | Inventory fallback for function `summarize_sweep` defined at `src/orchestration/analysis.py:53`. |
| 58 | `function` | `write_analysis_statistics` | inventory fallback | Inventory fallback for function `write_analysis_statistics` defined at `src/orchestration/analysis.py:58`. |
| 75 | `function` | `run_analysis` | inventory fallback | Inventory fallback for function `run_analysis` defined at `src/orchestration/analysis.py:75`. |

## `src/orchestration/coverage_pipeline.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `_coverage_input_paths` | inventory fallback | Inventory fallback for function `_coverage_input_paths` defined at `src/orchestration/coverage_pipeline.py:11`. |
| 23 | `function` | `_is_stale` | inventory fallback | Inventory fallback for function `_is_stale` defined at `src/orchestration/coverage_pipeline.py:23`. |
| 30 | `function` | `run_coverage_figures_and_page` | docstring | Render heatmap PNG and coverage page from existing coverage JSON. |
| 48 | `function` | `ensure_coverage_artifacts` | docstring | Ensure coverage JSON exists; optionally render heatmap and coverage page. |
| 90 | `function` | `run_coverage_pipeline` | docstring | Write coverage JSON, heatmap PNG, and coverage manuscript page. |

## `src/orchestration/pipeline_manifest.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `class` | `ScriptStep` | inventory fallback | Inventory fallback for class `ScriptStep` defined at `src/orchestration/pipeline_manifest.py:10`. |
| 32 | `function` | `analysis_scripts` | inventory fallback | Inventory fallback for function `analysis_scripts` defined at `src/orchestration/pipeline_manifest.py:32`. |

## `src/roadmap_tracks/figure_provenance.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `_is_deferred_source` | docstring | Pipeline-produced artifacts that do not exist at map-build time. |
| 27 | `function` | `_source_path_exists` | docstring | A listed source-code path must resolve to a real file or directory on disk. |
| 32 | `function` | `_figure_sources_mapped` | docstring | Re-derive `mapped` from the filesystem rather than trusting the hardcoded dict. |

## `src/roadmap_tracks/formal_interop.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/formal_interop.py:16`. |
| 23 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/formal_interop.py:23`. |
| 29 | `function` | `_gnn_paths` | inventory fallback | Inventory fallback for function `_gnn_paths` defined at `src/roadmap_tracks/formal_interop.py:29`. |
| 33 | `function` | `_model_to_payload` | docstring | Structured, JSON-serializable view of a parsed GNN model (sorted, deterministic). |
| 55 | `function` | `_model_payload` | inventory fallback | Inventory fallback for function `_model_payload` defined at `src/roadmap_tracks/formal_interop.py:55`. |
| 59 | `function` | `_payload_to_gnn_text` | docstring | Serialize a model payload back to GNN markdown. |
| 99 | `function` | `roundtrip_payload_lossless` | docstring | True iff serializing the STRUCTURAL payload to GNN text and re-parsing reproduces it. |
| 117 | `function` | `build_model_checking_witnesses` | inventory fallback | Inventory fallback for function `build_model_checking_witnesses` defined at `src/roadmap_tracks/formal_interop.py:117`. |
| 185 | `function` | `build_gnn_roundtrip_report` | inventory fallback | Inventory fallback for function `build_gnn_roundtrip_report` defined at `src/roadmap_tracks/formal_interop.py:185`. |
| 207 | `function` | `build_gnn_lint_report` | inventory fallback | Inventory fallback for function `build_gnn_lint_report` defined at `src/roadmap_tracks/formal_interop.py:207`. |
| 279 | `function` | `build_ontology_alias_index` | inventory fallback | Inventory fallback for function `build_ontology_alias_index` defined at `src/roadmap_tracks/formal_interop.py:279`. |
| 301 | `function` | `build_ontology_profile_matrix` | inventory fallback | Inventory fallback for function `build_ontology_profile_matrix` defined at `src/roadmap_tracks/formal_interop.py:301`. |
| 361 | `function` | `_lean_files` | inventory fallback | Inventory fallback for function `_lean_files` defined at `src/roadmap_tracks/formal_interop.py:361`. |
| 365 | `function` | `_lean_text` | inventory fallback | Inventory fallback for function `_lean_text` defined at `src/roadmap_tracks/formal_interop.py:365`. |
| 369 | `function` | `build_lean_theorem_inventory` | inventory fallback | Inventory fallback for function `build_lean_theorem_inventory` defined at `src/roadmap_tracks/formal_interop.py:369`. |
| 390 | `function` | `build_lean_graph_world_inventory` | inventory fallback | Inventory fallback for function `build_lean_graph_world_inventory` defined at `src/roadmap_tracks/formal_interop.py:390`. |
| 431 | `function` | `build_interop_roundtrip_report` | inventory fallback | Inventory fallback for function `build_interop_roundtrip_report` defined at `src/roadmap_tracks/formal_interop.py:431`. |
| 455 | `function` | `_leading_tactic` | docstring | First tactic identifier in a proof body (after ``:= by``), skipping blanks/comments. |
| 467 | `function` | `build_proof_extraction_index` | inventory fallback | Inventory fallback for function `build_proof_extraction_index` defined at `src/roadmap_tracks/formal_interop.py:467`. |
| 505 | `function` | `write_formal_interop_artifacts` | inventory fallback | Inventory fallback for function `write_formal_interop_artifacts` defined at `src/roadmap_tracks/formal_interop.py:505`. |
| 544 | `function` | `validate_formal_interop_artifacts` | inventory fallback | Inventory fallback for function `validate_formal_interop_artifacts` defined at `src/roadmap_tracks/formal_interop.py:544`. |

## `src/roadmap_tracks/integration_audit.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 100 | `function` | `write_manuscript_staleness_report` | docstring | Write the hydrated-manuscript staleness report. |
| 109 | `function` | `write_integration_audit_artifacts` | inventory fallback | Inventory fallback for function `write_integration_audit_artifacts` defined at `src/roadmap_tracks/integration_audit.py:109`. |
| 184 | `function` | `validate_integration_audit_artifacts` | inventory fallback | Inventory fallback for function `validate_integration_audit_artifacts` defined at `src/roadmap_tracks/integration_audit.py:184`. |

## `src/roadmap_tracks/integration_audit_artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 177 | `function` | `allowed_claim_lanes` | docstring | Return the stable figure/scope lane vocabulary used by validators. |
| 182 | `function` | `_lane_from_source` | inventory fallback | Inventory fallback for function `_lane_from_source` defined at `src/roadmap_tracks/integration_audit_artifacts.py:182`. |
| 190 | `function` | `_manifest_tracks_by_section` | inventory fallback | Inventory fallback for function `_manifest_tracks_by_section` defined at `src/roadmap_tracks/integration_audit_artifacts.py:190`. |
| 201 | `function` | `figure_claim_lanes` | docstring | Derive claim lanes from source artifacts, sheaf tracks, and evidence role. |
| 213 | `function` | `claim_lane_summary` | docstring | Summarize per-figure claim lanes in a validation-friendly shape. |
| 233 | `function` | `_blocked_scope_match` | inventory fallback | Inventory fallback for function `_blocked_scope_match` defined at `src/roadmap_tracks/integration_audit_artifacts.py:233`. |
| 241 | `function` | `_blocked_scope_negated` | inventory fallback | Inventory fallback for function `_blocked_scope_negated` defined at `src/roadmap_tracks/integration_audit_artifacts.py:241`. |
| 249 | `function` | `build_artifact_diffoscope` | inventory fallback | Inventory fallback for function `build_artifact_diffoscope` defined at `src/roadmap_tracks/integration_audit_artifacts.py:249`. |
| 279 | `function` | `build_artifact_license_audit` | inventory fallback | Inventory fallback for function `build_artifact_license_audit` defined at `src/roadmap_tracks/integration_audit_artifacts.py:279`. |
| 306 | `function` | `build_release_notes_evidence` | inventory fallback | Inventory fallback for function `build_release_notes_evidence` defined at `src/roadmap_tracks/integration_audit_artifacts.py:306`. |
| 343 | `function` | `build_figure_source_map` | docstring | Map rendered figures to source artifacts, section bindings, and claim lanes. |
| 453 | `function` | `build_figure_hash_manifest` | inventory fallback | Inventory fallback for function `build_figure_hash_manifest` defined at `src/roadmap_tracks/integration_audit_artifacts.py:453`. |
| 475 | `function` | `build_scope_boundary_audit` | docstring | Audit manuscript scope language against toy-only and blocked-context contracts. |
| 616 | `function` | `build_manuscript_evidence_tables` | inventory fallback | Inventory fallback for function `build_manuscript_evidence_tables` defined at `src/roadmap_tracks/integration_audit_artifacts.py:616`. |
| 760 | `function` | `build_adversarial_audit` | inventory fallback | Inventory fallback for function `build_adversarial_audit` defined at `src/roadmap_tracks/integration_audit_artifacts.py:760`. |
| 766 | `function` | `build_integration_semantic_snapshot` | inventory fallback | Inventory fallback for function `build_integration_semantic_snapshot` defined at `src/roadmap_tracks/integration_audit_artifacts.py:766`. |

## `src/roadmap_tracks/integration_audit_builders.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 28 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/integration_audit_builders.py:28`. |
| 35 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/integration_audit_builders.py:35`. |
| 41 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/integration_audit_builders.py:41`. |
| 49 | `function` | `_analysis_scripts` | inventory fallback | Inventory fallback for function `_analysis_scripts` defined at `src/roadmap_tracks/integration_audit_builders.py:49`. |
| 54 | `function` | `build_integration_dependency_graph` | inventory fallback | Inventory fallback for function `build_integration_dependency_graph` defined at `src/roadmap_tracks/integration_audit_builders.py:54`. |
| 89 | `function` | `build_producer_completeness` | inventory fallback | Inventory fallback for function `build_producer_completeness` defined at `src/roadmap_tracks/integration_audit_builders.py:89`. |
| 110 | `function` | `build_stale_artifact_report` | inventory fallback | Inventory fallback for function `build_stale_artifact_report` defined at `src/roadmap_tracks/integration_audit_builders.py:110`. |
| 136 | `function` | `build_cross_track_symbol_table` | inventory fallback | Inventory fallback for function `build_cross_track_symbol_table` defined at `src/roadmap_tracks/integration_audit_builders.py:136`. |
| 275 | `function` | `build_manuscript_token_provenance` | inventory fallback | Inventory fallback for function `build_manuscript_token_provenance` defined at `src/roadmap_tracks/integration_audit_builders.py:275`. |
| 327 | `function` | `_expected_token_value` | inventory fallback | Inventory fallback for function `_expected_token_value` defined at `src/roadmap_tracks/integration_audit_builders.py:327`. |
| 340 | `function` | `build_manuscript_staleness_report` | docstring | Compare hydrated manuscript tokens against the current generated variables. |
| 403 | `function` | `build_claim_evidence_audit` | inventory fallback | Inventory fallback for function `build_claim_evidence_audit` defined at `src/roadmap_tracks/integration_audit_builders.py:403`. |
| 445 | `function` | `build_validation_gate_index` | inventory fallback | Inventory fallback for function `build_validation_gate_index` defined at `src/roadmap_tracks/integration_audit_builders.py:445`. |
| 448 | `function` | `build_validation_gate_index.gate` | inventory fallback | Inventory fallback for function `build_validation_gate_index.gate` defined at `src/roadmap_tracks/integration_audit_builders.py:448`. |

## `src/roadmap_tracks/row_aggregates.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `rows` | docstring | Return a payload row list with a stable empty-list fallback. |
| 18 | `function` | `all_rows` | docstring | True only when the payload has rows and every row satisfies ``predicate``. |
| 24 | `function` | `all_field_present` | docstring | True iff every row has truthy values for all requested fields. |

## `src/roadmap_tracks/scholarship.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 203 | `function` | `_load_yaml` | inventory fallback | Inventory fallback for function `_load_yaml` defined at `src/roadmap_tracks/scholarship.py:203`. |
| 210 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/scholarship.py:210`. |
| 216 | `function` | `_bib_entries` | inventory fallback | Inventory fallback for function `_bib_entries` defined at `src/roadmap_tracks/scholarship.py:216`. |
| 225 | `function` | `_citation_present` | inventory fallback | Inventory fallback for function `_citation_present` defined at `src/roadmap_tracks/scholarship.py:225`. |
| 229 | `function` | `_section_id_from_path` | inventory fallback | Inventory fallback for function `_section_id_from_path` defined at `src/roadmap_tracks/scholarship.py:229`. |
| 238 | `function` | `_citation_sections` | inventory fallback | Inventory fallback for function `_citation_sections` defined at `src/roadmap_tracks/scholarship.py:238`. |
| 254 | `function` | `_registry_tracks` | inventory fallback | Inventory fallback for function `_registry_tracks` defined at `src/roadmap_tracks/scholarship.py:254`. |
| 259 | `function` | `_manifest_sections` | inventory fallback | Inventory fallback for function `_manifest_sections` defined at `src/roadmap_tracks/scholarship.py:259`. |
| 264 | `function` | `_has_locator` | inventory fallback | Inventory fallback for function `_has_locator` defined at `src/roadmap_tracks/scholarship.py:264`. |
| 269 | `function` | `_locator_kind` | inventory fallback | Inventory fallback for function `_locator_kind` defined at `src/roadmap_tracks/scholarship.py:269`. |
| 282 | `function` | `_scope_guarded` | inventory fallback | Inventory fallback for function `_scope_guarded` defined at `src/roadmap_tracks/scholarship.py:282`. |
| 288 | `function` | `_row_key` | inventory fallback | Inventory fallback for function `_row_key` defined at `src/roadmap_tracks/scholarship.py:288`. |
| 292 | `function` | `build_scholarship_source_matrix` | docstring | Build the literature-to-method traceability matrix. |
| 378 | `function` | `write_scholarship_source_matrix` | docstring | Write the source-backed scholarship matrix. |
| 386 | `function` | `validate_scholarship_source_matrix` | docstring | Validate the saved scholarship-source matrix against its row evidence. |

## `src/roadmap_tracks/sheaf_track_validation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `_all_rows` | inventory fallback | Inventory fallback for function `_all_rows` defined at `src/roadmap_tracks/sheaf_track_validation.py:12`. |
| 16 | `function` | `_all_rows_absent` | inventory fallback | Inventory fallback for function `_all_rows_absent` defined at `src/roadmap_tracks/sheaf_track_validation.py:16`. |
| 20 | `function` | `_append_schema_issue` | inventory fallback | Inventory fallback for function `_append_schema_issue` defined at `src/roadmap_tracks/sheaf_track_validation.py:20`. |
| 25 | `function` | `_append_summary_issue` | inventory fallback | Inventory fallback for function `_append_summary_issue` defined at `src/roadmap_tracks/sheaf_track_validation.py:25`. |
| 30 | `function` | `_semantic_restriction_value_ok` | inventory fallback | Inventory fallback for function `_semantic_restriction_value_ok` defined at `src/roadmap_tracks/sheaf_track_validation.py:30`. |
| 44 | `function` | `_validate_registry_contract` | inventory fallback | Inventory fallback for function `_validate_registry_contract` defined at `src/roadmap_tracks/sheaf_track_validation.py:44`. |
| 61 | `function` | `validate_sheaf_track_source_contract` | docstring | Validate source-side sheaf contracts without regenerating artifacts. |
| 83 | `function` | `_validate_saved_semantic_certificate` | inventory fallback | Inventory fallback for function `_validate_saved_semantic_certificate` defined at `src/roadmap_tracks/sheaf_track_validation.py:83`. |
| 126 | `function` | `validate_sheaf_track_artifacts` | docstring | Validate canonical sheaf-track artifacts and their semantic certificate. |

## `src/roadmap_tracks/sheaf_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 147 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/sheaf_tracks.py:147`. |
| 158 | `function` | `_parse_yaml_cached` | docstring | Parse a YAML file, memoized on (path, mtime, size). |
| 172 | `function` | `_load_yaml` | inventory fallback | Inventory fallback for function `_load_yaml` defined at `src/roadmap_tracks/sheaf_tracks.py:172`. |
| 179 | `function` | `_load_structured` | inventory fallback | Inventory fallback for function `_load_structured` defined at `src/roadmap_tracks/sheaf_tracks.py:179`. |
| 185 | `function` | `_bridge_reference_section_status` | inventory fallback | Inventory fallback for function `_bridge_reference_section_status` defined at `src/roadmap_tracks/sheaf_tracks.py:185`. |
| 195 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/sheaf_tracks.py:195`. |
| 201 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/sheaf_tracks.py:201`. |
| 211 | `function` | `_analysis_scripts` | inventory fallback | Inventory fallback for function `_analysis_scripts` defined at `src/roadmap_tracks/sheaf_tracks.py:211`. |
| 216 | `function` | `_registry_tracks` | inventory fallback | Inventory fallback for function `_registry_tracks` defined at `src/roadmap_tracks/sheaf_tracks.py:216`. |
| 222 | `function` | `_manifest_sections` | inventory fallback | Inventory fallback for function `_manifest_sections` defined at `src/roadmap_tracks/sheaf_tracks.py:222`. |
| 228 | `function` | `_bound_tracks` | inventory fallback | Inventory fallback for function `_bound_tracks` defined at `src/roadmap_tracks/sheaf_tracks.py:228`. |
| 240 | `function` | `_pipeline_tracks` | inventory fallback | Inventory fallback for function `_pipeline_tracks` defined at `src/roadmap_tracks/sheaf_tracks.py:240`. |
| 246 | `function` | `_claim_records` | inventory fallback | Inventory fallback for function `_claim_records` defined at `src/roadmap_tracks/sheaf_tracks.py:246`. |
| 252 | `function` | `_claim_ids_by_path` | inventory fallback | Inventory fallback for function `_claim_ids_by_path` defined at `src/roadmap_tracks/sheaf_tracks.py:252`. |
| 262 | `function` | `_claim_ids_by_track` | inventory fallback | Inventory fallback for function `_claim_ids_by_track` defined at `src/roadmap_tracks/sheaf_tracks.py:262`. |
| 271 | `function` | `_artifact_maps` | inventory fallback | Inventory fallback for function `_artifact_maps` defined at `src/roadmap_tracks/sheaf_tracks.py:271`. |
| 277 | `function` | `_source_commit` | inventory fallback | Inventory fallback for function `_source_commit` defined at `src/roadmap_tracks/sheaf_tracks.py:277`. |
| 291 | `function` | `_deterministic_seed` | inventory fallback | Inventory fallback for function `_deterministic_seed` defined at `src/roadmap_tracks/sheaf_tracks.py:291`. |
| 296 | `function` | `_config_digest` | inventory fallback | Inventory fallback for function `_config_digest` defined at `src/roadmap_tracks/sheaf_tracks.py:296`. |
| 319 | `class` | `_ProvenanceContext` | inventory fallback | Inventory fallback for class `_ProvenanceContext` defined at `src/roadmap_tracks/sheaf_tracks.py:319`. |
| 328 | `function` | `_provenance_context` | inventory fallback | Inventory fallback for function `_provenance_context` defined at `src/roadmap_tracks/sheaf_tracks.py:328`. |
| 338 | `function` | `_entropy` | inventory fallback | Inventory fallback for function `_entropy` defined at `src/roadmap_tracks/sheaf_tracks.py:338`. |
| 344 | `function` | `_root_output_dir` | inventory fallback | Inventory fallback for function `_root_output_dir` defined at `src/roadmap_tracks/sheaf_tracks.py:344`. |
| 352 | `function` | `_copied_parity` | inventory fallback | Inventory fallback for function `_copied_parity` defined at `src/roadmap_tracks/sheaf_tracks.py:352`. |
| 401 | `function` | `_remove_legacy_artifacts` | inventory fallback | Inventory fallback for function `_remove_legacy_artifacts` defined at `src/roadmap_tracks/sheaf_tracks.py:401`. |
| 408 | `function` | `_refresh_hydrated_manuscript` | docstring | Refresh hydrated manuscript copies so semantic staleness gates converge. |
| 424 | `function` | `_canonical_artifact_rows` | inventory fallback | Inventory fallback for function `_canonical_artifact_rows` defined at `src/roadmap_tracks/sheaf_tracks.py:424`. |
| 466 | `function` | `build_artifact_provenance` | docstring | Build canonical artifact, field-provenance, and bundle provenance rows. |
| 529 | `function` | `_artifact_bundles` | inventory fallback | Inventory fallback for function `_artifact_bundles` defined at `src/roadmap_tracks/sheaf_tracks.py:529`. |
| 610 | `function` | `build_replay_matrix` | inventory fallback | Inventory fallback for function `build_replay_matrix` defined at `src/roadmap_tracks/sheaf_tracks.py:610`. |
| 665 | `function` | `build_sensitivity_sweep` | inventory fallback | Inventory fallback for function `build_sensitivity_sweep` defined at `src/roadmap_tracks/sheaf_tracks.py:665`. |
| 739 | `function` | `build_uncertainty_summary` | inventory fallback | Inventory fallback for function `build_uncertainty_summary` defined at `src/roadmap_tracks/sheaf_tracks.py:739`. |
| 808 | `function` | `build_counterexample_matrix` | inventory fallback | Inventory fallback for function `build_counterexample_matrix` defined at `src/roadmap_tracks/sheaf_tracks.py:808`. |
| 875 | `function` | `build_model_checking_witnesses` | inventory fallback | Inventory fallback for function `build_model_checking_witnesses` defined at `src/roadmap_tracks/sheaf_tracks.py:875`. |
| 934 | `function` | `build_interop_roundtrip_report` | inventory fallback | Inventory fallback for function `build_interop_roundtrip_report` defined at `src/roadmap_tracks/sheaf_tracks.py:934`. |
| 969 | `function` | `build_adversarial_audit` | inventory fallback | Inventory fallback for function `build_adversarial_audit` defined at `src/roadmap_tracks/sheaf_tracks.py:969`. |
| 1000 | `function` | `build_blocked_scope_manifest` | docstring | Describe out-of-scope research capabilities and the artifacts needed to unblock them. |
| 1083 | `function` | `_field_value` | inventory fallback | Inventory fallback for function `_field_value` defined at `src/roadmap_tracks/sheaf_tracks.py:1083`. |
| 1093 | `function` | `build_evidence_field_index` | inventory fallback | Inventory fallback for function `build_evidence_field_index` defined at `src/roadmap_tracks/sheaf_tracks.py:1093`. |
| 1145 | `function` | `build_release_bundle_manifest` | inventory fallback | Inventory fallback for function `build_release_bundle_manifest` defined at `src/roadmap_tracks/sheaf_tracks.py:1145`. |
| 1212 | `function` | `build_theorem_traceability_matrix` | inventory fallback | Inventory fallback for function `build_theorem_traceability_matrix` defined at `src/roadmap_tracks/sheaf_tracks.py:1212`. |
| 1262 | `function` | `_track_artifact` | inventory fallback | Inventory fallback for function `_track_artifact` defined at `src/roadmap_tracks/sheaf_tracks.py:1262`. |
| 1292 | `function` | `_pipeline_sheaf_tracks` | inventory fallback | Inventory fallback for function `_pipeline_sheaf_tracks` defined at `src/roadmap_tracks/sheaf_tracks.py:1292`. |
| 1302 | `function` | `build_track_lane_matrix` | docstring | Map every pipeline track to sheaf fragments, producers, artifacts, gates, and consumers. |
| 1392 | `function` | `build_track_improvement_scope` | inventory fallback | Inventory fallback for function `build_track_improvement_scope` defined at `src/roadmap_tracks/sheaf_tracks.py:1392`. |
| 1482 | `function` | `build_validation_dependency_graph` | inventory fallback | Inventory fallback for function `build_validation_dependency_graph` defined at `src/roadmap_tracks/sheaf_tracks.py:1482`. |
| 1597 | `function` | `_canonical_restrictions` | inventory fallback | Inventory fallback for function `_canonical_restrictions` defined at `src/roadmap_tracks/sheaf_tracks.py:1597`. |
| 1785 | `function` | `_run_prerequisite_promoters` | inventory fallback | Inventory fallback for function `_run_prerequisite_promoters` defined at `src/roadmap_tracks/sheaf_tracks.py:1785`. |
| 1800 | `function` | `_record_external_artifact_paths` | inventory fallback | Inventory fallback for function `_record_external_artifact_paths` defined at `src/roadmap_tracks/sheaf_tracks.py:1800`. |
| 1809 | `function` | `_write_primary_canonical_artifacts` | inventory fallback | Inventory fallback for function `_write_primary_canonical_artifacts` defined at `src/roadmap_tracks/sheaf_tracks.py:1809`. |
| 1856 | `function` | `_write_integration_audit_phase` | inventory fallback | Inventory fallback for function `_write_integration_audit_phase` defined at `src/roadmap_tracks/sheaf_tracks.py:1856`. |
| 1866 | `function` | `_write_post_audit_canonical_artifacts` | inventory fallback | Inventory fallback for function `_write_post_audit_canonical_artifacts` defined at `src/roadmap_tracks/sheaf_tracks.py:1866`. |
| 1903 | `function` | `_write_semantic_artifacts` | inventory fallback | Inventory fallback for function `_write_semantic_artifacts` defined at `src/roadmap_tracks/sheaf_tracks.py:1903`. |
| 1916 | `function` | `_write_supplemental_phase` | inventory fallback | Inventory fallback for function `_write_supplemental_phase` defined at `src/roadmap_tracks/sheaf_tracks.py:1916`. |
| 1922 | `function` | `_write_final_canonical_pass` | inventory fallback | Inventory fallback for function `_write_final_canonical_pass` defined at `src/roadmap_tracks/sheaf_tracks.py:1922`. |
| 1951 | `function` | `write_sheaf_track_artifacts` | docstring | Write the canonical promoted sheaf artifacts in deterministic phases. |

## `src/roadmap_tracks/supplemental.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 25 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/supplemental.py:25`. |
| 35 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/supplemental.py:35`. |
| 41 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/supplemental.py:41`. |
| 51 | `function` | `_statement_symbols` | docstring | Extract stable statement identifiers from a Lean theorem statement. |
| 71 | `function` | `build_proof_dependency_graph` | docstring | Build theorem-to-source, theorem-to-symbol, and theorem-to-witness edges. |
| 123 | `function` | `_graph_world_transition_rows` | inventory fallback | Inventory fallback for function `_graph_world_transition_rows` defined at `src/roadmap_tracks/supplemental.py:123`. |
| 157 | `function` | `_tmaze_transition_rows` | inventory fallback | Inventory fallback for function `_tmaze_transition_rows` defined at `src/roadmap_tracks/supplemental.py:157`. |
| 182 | `function` | `build_state_transition_table` | docstring | Build explicit finite transition rows for graph-world topologies and T-maze actions. |
| 205 | `function` | `build_ablation_sensitivity_report` | docstring | Join causal-ablation effects to sensitivity and uncertainty source rows. |
| 251 | `function` | `build_release_attestation` | docstring | Attest release bundle, validation, license, and blocked-scope status. |
| 356 | `function` | `write_supplemental_artifacts` | docstring | Write all supplemental canonical sheaf artifacts. |
| 379 | `function` | `validate_supplemental_artifacts` | docstring | Validate supplemental artifacts from row-derived conditions. |

## `src/roadmap_tracks/toy_sweep.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 29 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/toy_sweep.py:29`. |
| 36 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/toy_sweep.py:36`. |
| 42 | `function` | `_same_state_probability` | inventory fallback | Inventory fallback for function `_same_state_probability` defined at `src/roadmap_tracks/toy_sweep.py:42`. |
| 47 | `function` | `_posterior_correlation` | inventory fallback | Inventory fallback for function `_posterior_correlation` defined at `src/roadmap_tracks/toy_sweep.py:47`. |
| 52 | `function` | `_joint_entropy` | inventory fallback | Inventory fallback for function `_joint_entropy` defined at `src/roadmap_tracks/toy_sweep.py:52`. |
| 57 | `function` | `_marginal_entropy` | inventory fallback | Inventory fallback for function `_marginal_entropy` defined at `src/roadmap_tracks/toy_sweep.py:57`. |
| 63 | `function` | `build_analytical_observable_sweep` | inventory fallback | Inventory fallback for function `build_analytical_observable_sweep` defined at `src/roadmap_tracks/toy_sweep.py:63`. |
| 119 | `function` | `build_analytical_assumption_index` | docstring | Index the finite-model assumptions behind the analytical equations. |
| 236 | `function` | `build_sensitivity_sweep` | inventory fallback | Inventory fallback for function `build_sensitivity_sweep` defined at `src/roadmap_tracks/toy_sweep.py:236`. |
| 266 | `function` | `build_uncertainty_summary` | inventory fallback | Inventory fallback for function `build_uncertainty_summary` defined at `src/roadmap_tracks/toy_sweep.py:266`. |
| 295 | `function` | `build_toy_benchmark_matrix` | inventory fallback | Inventory fallback for function `build_toy_benchmark_matrix` defined at `src/roadmap_tracks/toy_sweep.py:295`. |
| 333 | `function` | `build_policy_grid` | inventory fallback | Inventory fallback for function `build_policy_grid` defined at `src/roadmap_tracks/toy_sweep.py:333`. |
| 363 | `function` | `build_efe_terms` | inventory fallback | Inventory fallback for function `build_efe_terms` defined at `src/roadmap_tracks/toy_sweep.py:363`. |
| 402 | `function` | `_topology_trace` | inventory fallback | Inventory fallback for function `_topology_trace` defined at `src/roadmap_tracks/toy_sweep.py:402`. |
| 417 | `function` | `build_graph_world_topology_sweep` | inventory fallback | Inventory fallback for function `build_graph_world_topology_sweep` defined at `src/roadmap_tracks/toy_sweep.py:417`. |
| 440 | `function` | `build_graph_world_topology_traces` | inventory fallback | Inventory fallback for function `build_graph_world_topology_traces` defined at `src/roadmap_tracks/toy_sweep.py:440`. |
| 463 | `function` | `_graph_world_trace_invariants` | docstring | Compute the three finite invariants from an actual topology trace (not hardcoded). |
| 492 | `function` | `build_graph_world_invariants` | inventory fallback | Inventory fallback for function `build_graph_world_invariants` defined at `src/roadmap_tracks/toy_sweep.py:492`. |
| 507 | `function` | `build_state_space_catalog` | inventory fallback | Inventory fallback for function `build_state_space_catalog` defined at `src/roadmap_tracks/toy_sweep.py:507`. |
| 552 | `function` | `build_causal_ablation_matrix` | inventory fallback | Inventory fallback for function `build_causal_ablation_matrix` defined at `src/roadmap_tracks/toy_sweep.py:552`. |
| 581 | `function` | `write_toy_sweep_artifacts` | inventory fallback | Inventory fallback for function `write_toy_sweep_artifacts` defined at `src/roadmap_tracks/toy_sweep.py:581`. |
| 626 | `function` | `validate_toy_sweep_artifacts` | inventory fallback | Inventory fallback for function `validate_toy_sweep_artifacts` defined at `src/roadmap_tracks/toy_sweep.py:626`. |

## `src/roadmap_tracks/visualization_audit.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 43 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/visualization_audit.py:43`. |
| 50 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/visualization_audit.py:50`. |
| 56 | `function` | `_word_count` | inventory fallback | Inventory fallback for function `_word_count` defined at `src/roadmap_tracks/visualization_audit.py:56`. |
| 60 | `function` | `_image_metrics` | inventory fallback | Inventory fallback for function `_image_metrics` defined at `src/roadmap_tracks/visualization_audit.py:60`. |
| 75 | `function` | `_statistical_sources` | inventory fallback | Inventory fallback for function `_statistical_sources` defined at `src/roadmap_tracks/visualization_audit.py:75`. |
| 80 | `function` | `_all_sources_present` | inventory fallback | Inventory fallback for function `_all_sources_present` defined at `src/roadmap_tracks/visualization_audit.py:80`. |
| 84 | `function` | `_figure_section_bindings` | inventory fallback | Inventory fallback for function `_figure_section_bindings` defined at `src/roadmap_tracks/visualization_audit.py:84`. |
| 103 | `function` | `_section_id_from_path` | inventory fallback | Inventory fallback for function `_section_id_from_path` defined at `src/roadmap_tracks/visualization_audit.py:103`. |
| 113 | `function` | `_figure_reference_sections` | inventory fallback | Inventory fallback for function `_figure_reference_sections` defined at `src/roadmap_tracks/visualization_audit.py:113`. |
| 128 | `function` | `_manifest_section_tracks` | inventory fallback | Inventory fallback for function `_manifest_section_tracks` defined at `src/roadmap_tracks/visualization_audit.py:128`. |
| 146 | `function` | `_reference_section_status` | inventory fallback | Inventory fallback for function `_reference_section_status` defined at `src/roadmap_tracks/visualization_audit.py:146`. |
| 156 | `function` | `_figure_evidence_rows` | docstring | Derive live figure evidence rows from registry, source maps, hashes, and renders. |
| 240 | `function` | `build_visualization_quality_audit` | docstring | Build figure accessibility, source, hash, and render-readiness rows. |
| 277 | `function` | `write_visualization_quality_audit` | docstring | Write the deterministic visualization-quality audit report. |
| 286 | `function` | `build_statistical_visualization_bridge` | docstring | Build the crosswalk from statistical figure rows to scholarship and sheaf bindings. |
| 382 | `function` | `write_statistical_visualization_bridge` | docstring | Write the statistical-visualization scholarship/sheaf crosswalk. |
| 391 | `function` | `validate_visualization_quality_audit` | docstring | Validate the saved visualization-quality audit against its row evidence. |
| 537 | `function` | `validate_statistical_visualization_bridge` | docstring | Validate the saved statistical visualization crosswalk against row evidence. |

## `src/simulation/cue_tmaze_model.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 60 | `class` | `CueTMazeSpec` | docstring | Parameters of the cue-then-reward T-maze (deterministic, finite). |
| 68 | `function` | `state_index` | docstring | Joint hidden-state index for ``(position, context)``. |
| 73 | `function` | `build_cue_tmaze_generative_model` | docstring | Return ``A, B, C, D`` for the cue-then-reward T-maze (single joint factor). |
| 111 | `function` | `_context_marginal` | docstring | Marginal over the 2 reward contexts from a joint state belief. |
| 126 | `function` | `cue_information_gain` | docstring | Expected information gain ``I(context; o_cue)`` of one cue sample (nats). |
| 151 | `function` | `_expected_reward_log_pref` | docstring | Sophisticated (observation-conditioned) expected reward log-preference E[ln p(o_reward)]. |
| 188 | `class` | `CueAdvantage` | docstring | Measured epistemic advantage of cue-sampling on the cue T-maze (nats). |
| 198 | `function` | `CueAdvantage.behavioral_advantage` | docstring | How much better the cue-sampling agent's expected reward is (nats). |
| 203 | `function` | `CueAdvantage.epistemic_required` | docstring | True iff the cue carries information AND yields a behavioural advantage. |
| 208 | `function` | `CueAdvantage.flat_efe_indistinguishable` | docstring | True iff *flat* EFE cannot tell the cue and greedy policies apart. |
| 217 | `function` | `CueAdvantage.to_dict` | inventory fallback | Inventory fallback for function `CueAdvantage.to_dict` defined at `src/simulation/cue_tmaze_model.py:217`. |
| 230 | `function` | `compare_cue_vs_greedy` | docstring | Closed-form comparison proving epistemic cue-sampling is strictly necessary. |
| 251 | `function` | `cue_advantage_summary` | docstring | JSON-ready summary for the manuscript / figure / claim ledger. |

## `src/simulation/dirichlet_learning.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 45 | `class` | `DirichletLearningResult` | docstring | Trajectory of a deterministic Dirichlet likelihood-learning run. |
| 61 | `function` | `DirichletLearningResult.final_kl` | inventory fallback | Inventory fallback for function `DirichletLearningResult.final_kl` defined at `src/simulation/dirichlet_learning.py:61`. |
| 65 | `function` | `DirichletLearningResult.initial_kl` | inventory fallback | Inventory fallback for function `DirichletLearningResult.initial_kl` defined at `src/simulation/dirichlet_learning.py:65`. |
| 69 | `function` | `DirichletLearningResult.is_monotone_decreasing` | inventory fallback | Inventory fallback for function `DirichletLearningResult.is_monotone_decreasing` defined at `src/simulation/dirichlet_learning.py:69`. |
| 75 | `function` | `DirichletLearningResult.steps_to_converge` | docstring | First update step whose KL is below ``CONVERGENCE_KL_ATOL``. |
| 87 | `function` | `DirichletLearningResult.to_dict` | inventory fallback | Inventory fallback for function `DirichletLearningResult.to_dict` defined at `src/simulation/dirichlet_learning.py:87`. |
| 105 | `function` | `_true_likelihood` | docstring | Extract the (n_o, n_s) likelihood A from a (possibly list-wrapped) model. |
| 112 | `function` | `expected_likelihood` | docstring | Expected likelihood ``E[A] = pA / sum_o(pA)`` (column-normalised). |
| 119 | `function` | `_kl_columns` | docstring | ``sum_s KL(true_a[:, s] \|\| learned_a[:, s])`` in nats. |
| 135 | `function` | `learn_likelihood` | docstring | Deterministically learn ``A`` via Dirichlet concentration updates. |
| 180 | `function` | `summarize_learning` | docstring | JSON-ready summary used by figures, tokens, and the claim ledger. |

## `src/simulation/efe_decomposition.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 49 | `class` | `EFETerms` | docstring | The four EFE terms for a single policy, summed over the horizon. |
| 63 | `function` | `EFETerms.total` | docstring | Expected Free Energy G(pi) = risk + ambiguity. |
| 68 | `function` | `EFETerms.identity_residual` | docstring | ``(risk + ambiguity) + pragmatic_value + epistemic_value`` (== 0 when valid). |
| 73 | `function` | `EFETerms.identity_holds` | inventory fallback | Inventory fallback for function `EFETerms.identity_holds` defined at `src/simulation/efe_decomposition.py:73`. |
| 76 | `function` | `EFETerms.to_dict` | inventory fallback | Inventory fallback for function `EFETerms.to_dict` defined at `src/simulation/efe_decomposition.py:76`. |
| 88 | `function` | `_as_2d` | inventory fallback | Inventory fallback for function `_as_2d` defined at `src/simulation/efe_decomposition.py:88`. |
| 92 | `function` | `softmax_preference` | docstring | Preferred-outcome distribution ``p(o) = softmax(C)`` from log-preferences. |
| 100 | `function` | `_entropy` | docstring | Shannon entropy in nats, ignoring zero-probability outcomes. |
| 107 | `function` | `_kl_divergence` | docstring | KL(q \|\| p) in nats; +inf where q has support that p does not. |
| 121 | `function` | `_first_factor` | inventory fallback | Inventory fallback for function `_first_factor` defined at `src/simulation/efe_decomposition.py:121`. |
| 128 | `function` | `decompose_policy_efe` | docstring | Closed-form EFE term decomposition for one policy (action sequence). |
| 168 | `function` | `enumerate_policies` | docstring | All deterministic action sequences of length ``policy_len``. |
| 173 | `function` | `decompose_all_policies` | docstring | Decompose every length-``policy_len`` policy and summarise the result. |

## `src/simulation/graph_world.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `function` | `_graph_world_trace` | inventory fallback | Inventory fallback for function `_graph_world_trace` defined at `src/simulation/graph_world.py:10`. |
| 28 | `function` | `write_graph_world_artifacts` | docstring | Write deterministic graph-world summary and trace artifacts. |
| 53 | `function` | `write_graph_world_stub` | docstring | Backward-compatible wrapper returning the summary artifact path. |

## `src/simulation/invariants.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `_load_summary` | inventory fallback | Inventory fallback for function `_load_summary` defined at `src/simulation/invariants.py:15`. |
| 23 | `function` | `_load_trace` | inventory fallback | Inventory fallback for function `_load_trace` defined at `src/simulation/invariants.py:23`. |
| 31 | `function` | `inv_belief_entropy_finite` | inventory fallback | Inventory fallback for function `inv_belief_entropy_finite` defined at `src/simulation/invariants.py:31`. |
| 37 | `function` | `inv_actions_length_matches_steps` | inventory fallback | Inventory fallback for function `inv_actions_length_matches_steps` defined at `src/simulation/invariants.py:37`. |
| 44 | `function` | `inv_observations_in_obs_space` | inventory fallback | Inventory fallback for function `inv_observations_in_obs_space` defined at `src/simulation/invariants.py:44`. |
| 52 | `function` | `inv_policy_len_matches_config` | inventory fallback | Inventory fallback for function `inv_policy_len_matches_config` defined at `src/simulation/invariants.py:52`. |
| 59 | `function` | `inv_goal_reached` | inventory fallback | Inventory fallback for function `inv_goal_reached` defined at `src/simulation/invariants.py:59`. |
| 70 | `function` | `inv_trace_step_count_matches_summary` | inventory fallback | Inventory fallback for function `inv_trace_step_count_matches_summary` defined at `src/simulation/invariants.py:70`. |
| 86 | `function` | `run_simulation_invariants` | inventory fallback | Inventory fallback for function `run_simulation_invariants` defined at `src/simulation/invariants.py:86`. |
| 91 | `function` | `build_merged_invariants_payload` | docstring | Single SSOT for merged analytical + simulation invariant reports. |
| 121 | `function` | `write_simulation_invariants` | inventory fallback | Inventory fallback for function `write_simulation_invariants` defined at `src/simulation/invariants.py:121`. |
| 131 | `function` | `merge_simulation_into_invariants_report` | inventory fallback | Inventory fallback for function `merge_simulation_into_invariants_report` defined at `src/simulation/invariants.py:131`. |

## `src/simulation/logging_utils.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 24 | `function` | `_now_iso` | inventory fallback | Inventory fallback for function `_now_iso` defined at `src/simulation/logging_utils.py:24`. |
| 28 | `function` | `_json_default` | inventory fallback | Inventory fallback for function `_json_default` defined at `src/simulation/logging_utils.py:28`. |
| 34 | `function` | `validate_record` | inventory fallback | Inventory fallback for function `validate_record` defined at `src/simulation/logging_utils.py:34`. |
| 45 | `class` | `RunLogger` | inventory fallback | Inventory fallback for class `RunLogger` defined at `src/simulation/logging_utils.py:45`. |
| 49 | `function` | `RunLogger.__post_init__` | inventory fallback | Inventory fallback for function `RunLogger.__post_init__` defined at `src/simulation/logging_utils.py:49`. |
| 55 | `function` | `RunLogger.from_project_root` | inventory fallback | Inventory fallback for function `RunLogger.from_project_root` defined at `src/simulation/logging_utils.py:55`. |
| 66 | `function` | `RunLogger.fresh` | inventory fallback | Inventory fallback for function `RunLogger.fresh` defined at `src/simulation/logging_utils.py:66`. |
| 71 | `function` | `RunLogger.emit` | inventory fallback | Inventory fallback for function `RunLogger.emit` defined at `src/simulation/logging_utils.py:71`. |
| 80 | `function` | `RunLogger.emit_run_header` | inventory fallback | Inventory fallback for function `RunLogger.emit_run_header` defined at `src/simulation/logging_utils.py:80`. |
| 99 | `function` | `RunLogger.timed` | inventory fallback | Inventory fallback for function `RunLogger.timed` defined at `src/simulation/logging_utils.py:99`. |
| 108 | `function` | `RunLogger.records` | inventory fallback | Inventory fallback for function `RunLogger.records` defined at `src/simulation/logging_utils.py:108`. |
| 117 | `function` | `RunLogger.step_records` | inventory fallback | Inventory fallback for function `RunLogger.step_records` defined at `src/simulation/logging_utils.py:117`. |

## `src/simulation/precision_sweep.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 49 | `function` | `_softmax` | inventory fallback | Inventory fallback for function `_softmax` defined at `src/simulation/precision_sweep.py:49`. |
| 55 | `function` | `_entropy` | docstring | Shannon entropy in nats, ignoring zero-probability outcomes. |
| 63 | `class` | `PrecisionPoint` | docstring | Policy-posterior summary at one precision value. |
| 72 | `function` | `PrecisionPoint.to_dict` | inventory fallback | Inventory fallback for function `PrecisionPoint.to_dict` defined at `src/simulation/precision_sweep.py:72`. |
| 82 | `function` | `gamma_grid` | docstring | Deterministic precision grid ``[0, gamma_max]`` with ``grid_points`` samples. |
| 90 | `function` | `posterior_at_gamma` | docstring | Policy posterior ``q(pi) = softmax(-gamma * G)`` for a fixed precision. |
| 96 | `function` | `sweep_precision` | docstring | Sweep precision over the policy posterior of ``model``. |

## `src/simulation/pymdp_config.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `class` | `TMazeConfig` | inventory fallback | Inventory fallback for class `TMazeConfig` defined at `src/simulation/pymdp_config.py:17`. |
| 26 | `class` | `AgentConfig` | inventory fallback | Inventory fallback for class `AgentConfig` defined at `src/simulation/pymdp_config.py:26`. |
| 32 | `class` | `LoggingConfig` | inventory fallback | Inventory fallback for class `LoggingConfig` defined at `src/simulation/pymdp_config.py:32`. |
| 38 | `class` | `ComparisonConfig` | inventory fallback | Inventory fallback for class `ComparisonConfig` defined at `src/simulation/pymdp_config.py:38`. |
| 45 | `class` | `PymdpConfig` | inventory fallback | Inventory fallback for class `PymdpConfig` defined at `src/simulation/pymdp_config.py:45`. |
| 56 | `function` | `PymdpConfig.policy_len` | inventory fallback | Inventory fallback for function `PymdpConfig.policy_len` defined at `src/simulation/pymdp_config.py:56`. |
| 60 | `function` | `_coerce_mode` | inventory fallback | Inventory fallback for function `_coerce_mode` defined at `src/simulation/pymdp_config.py:60`. |
| 67 | `function` | `_parse_raw` | inventory fallback | Inventory fallback for function `_parse_raw` defined at `src/simulation/pymdp_config.py:67`. |
| 106 | `function` | `default_pymdp_config` | inventory fallback | Inventory fallback for function `default_pymdp_config` defined at `src/simulation/pymdp_config.py:106`. |
| 110 | `function` | `pymdp_config_path` | inventory fallback | Inventory fallback for function `pymdp_config_path` defined at `src/simulation/pymdp_config.py:110`. |
| 114 | `function` | `load_pymdp_config` | inventory fallback | Inventory fallback for function `load_pymdp_config` defined at `src/simulation/pymdp_config.py:114`. |
| 126 | `function` | `apply_pymdp_overrides` | inventory fallback | Inventory fallback for function `apply_pymdp_overrides` defined at `src/simulation/pymdp_config.py:126`. |
| 149 | `function` | `config_snapshot` | inventory fallback | Inventory fallback for function `config_snapshot` defined at `src/simulation/pymdp_config.py:149`. |
| 179 | `function` | `config_hash` | inventory fallback | Inventory fallback for function `config_hash` defined at `src/simulation/pymdp_config.py:179`. |

## `src/simulation/pymdp_runtime.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 19 | `function` | `_package_version` | inventory fallback | Inventory fallback for function `_package_version` defined at `src/simulation/pymdp_runtime.py:19`. |
| 26 | `function` | `_backend_flags` | inventory fallback | Inventory fallback for function `_backend_flags` defined at `src/simulation/pymdp_runtime.py:26`. |
| 39 | `function` | `_numpy_factors` | inventory fallback | Inventory fallback for function `_numpy_factors` defined at `src/simulation/pymdp_runtime.py:39`. |
| 43 | `function` | `_warning_record` | inventory fallback | Inventory fallback for function `_warning_record` defined at `src/simulation/pymdp_runtime.py:43`. |
| 52 | `function` | `construct_agent_with_diagnostics` | docstring | Construct ``pymdp.Agent`` while capturing the one audited JAX warning. |
| 100 | `function` | `build_runtime_diagnostics` | inventory fallback | Inventory fallback for function `build_runtime_diagnostics` defined at `src/simulation/pymdp_runtime.py:100`. |
| 190 | `function` | `write_runtime_diagnostics` | inventory fallback | Inventory fallback for function `write_runtime_diagnostics` defined at `src/simulation/pymdp_runtime.py:190`. |
| 201 | `function` | `validate_runtime_diagnostics` | inventory fallback | Inventory fallback for function `validate_runtime_diagnostics` defined at `src/simulation/pymdp_runtime.py:201`. |

## `src/simulation/si_artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `write_si_artifacts` | inventory fallback | Inventory fallback for function `write_si_artifacts` defined at `src/simulation/si_artifacts.py:21`. |
| 88 | `function` | `run_and_persist` | inventory fallback | Inventory fallback for function `run_and_persist` defined at `src/simulation/si_artifacts.py:88`. |
| 105 | `function` | `write_policy_comparison` | docstring | Write deterministic state-vs-policy comparison rows without changing main SI artifacts. |
| 223 | `function` | `write_policy_posterior_grid` | docstring | Write step-level PyMDP policy posterior normalization evidence. |

## `src/simulation/si_belief.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 8 | `function` | `marginal_state_belief` | inventory fallback | Inventory fallback for function `marginal_state_belief` defined at `src/simulation/si_belief.py:8`. |
| 19 | `function` | `belief_entropy` | inventory fallback | Inventory fallback for function `belief_entropy` defined at `src/simulation/si_belief.py:19`. |
| 24 | `function` | `qs_marginal_state1` | inventory fallback | Inventory fallback for function `qs_marginal_state1` defined at `src/simulation/si_belief.py:24`. |
| 31 | `function` | `state_inference_action` | inventory fallback | Inventory fallback for function `state_inference_action` defined at `src/simulation/si_belief.py:31`. |
| 35 | `function` | `state_inference_next_obs` | inventory fallback | Inventory fallback for function `state_inference_next_obs` defined at `src/simulation/si_belief.py:35`. |

## `src/simulation/si_loop.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 29 | `function` | `pymdp_available` | inventory fallback | Inventory fallback for function `pymdp_available` defined at `src/simulation/si_loop.py:29`. |
| 39 | `class` | `SIRunResult` | inventory fallback | Inventory fallback for class `SIRunResult` defined at `src/simulation/si_loop.py:39`. |
| 54 | `function` | `sample_next_state` | inventory fallback | Inventory fallback for function `sample_next_state` defined at `src/simulation/si_loop.py:54`. |
| 63 | `function` | `sample_observation` | inventory fallback | Inventory fallback for function `sample_observation` defined at `src/simulation/si_loop.py:63`. |
| 70 | `function` | `run_si_tmaze` | docstring | Run state or policy inference on the minimal T-maze harness. |

## `src/simulation/si_policy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `select_policy_action` | docstring | Return action, method label, selected EFE, selected policy index, and policy evidence. |

## `src/simulation/statistics.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `_adjacent_switch_count` | inventory fallback | Inventory fallback for function `_adjacent_switch_count` defined at `src/simulation/statistics.py:11`. |
| 15 | `function` | `_entropy_stats` | inventory fallback | Inventory fallback for function `_entropy_stats` defined at `src/simulation/statistics.py:15`. |
| 44 | `function` | `summarize_si_trace` | inventory fallback | Inventory fallback for function `summarize_si_trace` defined at `src/simulation/statistics.py:44`. |
| 73 | `function` | `load_si_artifacts` | inventory fallback | Inventory fallback for function `load_si_artifacts` defined at `src/simulation/statistics.py:73`. |

## `src/simulation/tmaze_model.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `TMazeSpec` | inventory fallback | Inventory fallback for class `TMazeSpec` defined at `src/simulation/tmaze_model.py:14`. |
| 24 | `function` | `spec_from_config` | inventory fallback | Inventory fallback for function `spec_from_config` defined at `src/simulation/tmaze_model.py:24`. |
| 37 | `function` | `build_tmaze_generative_model` | docstring | Return A, B, C, D for a 2-state start/goal POMDP (single factor). |

## `src/validation_spine/artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 68 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/validation_spine/artifacts.py:68`. |
| 79 | `function` | `_file_fingerprint` | inventory fallback | Inventory fallback for function `_file_fingerprint` defined at `src/validation_spine/artifacts.py:79`. |
| 92 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/validation_spine/artifacts.py:92`. |
| 99 | `function` | `_configured_analysis_scripts` | inventory fallback | Inventory fallback for function `_configured_analysis_scripts` defined at `src/validation_spine/artifacts.py:99`. |
| 109 | `function` | `_config_digest` | inventory fallback | Inventory fallback for function `_config_digest` defined at `src/validation_spine/artifacts.py:109`. |
| 121 | `function` | `_deterministic_seed` | inventory fallback | Inventory fallback for function `_deterministic_seed` defined at `src/validation_spine/artifacts.py:121`. |
| 132 | `function` | `_source_commit` | inventory fallback | Inventory fallback for function `_source_commit` defined at `src/validation_spine/artifacts.py:132`. |
| 146 | `function` | `_artifact_record` | inventory fallback | Inventory fallback for function `_artifact_record` defined at `src/validation_spine/artifacts.py:146`. |
| 170 | `function` | `_config_record` | inventory fallback | Inventory fallback for function `_config_record` defined at `src/validation_spine/artifacts.py:170`. |
| 180 | `function` | `build_artifact_provenance` | docstring | Build deterministic artifact lineage and hash records. |
| 214 | `function` | `_same_json` | inventory fallback | Inventory fallback for function `_same_json` defined at `src/validation_spine/artifacts.py:214`. |
| 220 | `function` | `_copy_replay_inputs` | inventory fallback | Inventory fallback for function `_copy_replay_inputs` defined at `src/validation_spine/artifacts.py:220`. |
| 229 | `function` | `build_reproducibility_replay` | docstring | Replay deterministic toy producers in a temporary tree and compare outputs. |
| 306 | `function` | `build_counterexample_matrix` | docstring | Document expected-failure fixtures that keep the gates falsifiable. |
| 405 | `function` | `write_validation_spine_artifacts` | docstring | Write provenance, replay, and counterexample artifacts. |
| 432 | `function` | `validate_artifact_provenance` | inventory fallback | Inventory fallback for function `validate_artifact_provenance` defined at `src/validation_spine/artifacts.py:432`. |
| 478 | `function` | `validate_reproducibility_replay` | inventory fallback | Inventory fallback for function `validate_reproducibility_replay` defined at `src/validation_spine/artifacts.py:478`. |
| 529 | `function` | `validate_counterexample_matrix` | inventory fallback | Inventory fallback for function `validate_counterexample_matrix` defined at `src/validation_spine/artifacts.py:529`. |
| 557 | `function` | `validate_validation_spine` | docstring | Return all validation-spine artifact issues. |

## `src/visualizations/animation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `_load_trace_steps` | inventory fallback | Inventory fallback for function `_load_trace_steps` defined at `src/visualizations/animation.py:14`. |
| 29 | `function` | `write_belief_trajectory_gif` | docstring | Write a deterministic multi-frame GIF from trace entropy/action state. |
| 67 | `function` | `_frame_sha256` | inventory fallback | Inventory fallback for function `_frame_sha256` defined at `src/visualizations/animation.py:67`. |
| 73 | `function` | `_perceptual_hash` | docstring | Return a deterministic 8x8 average hash for a frame. |
| 84 | `function` | `build_animation_frame_deltas` | docstring | Compute a deterministic manifest proving adjacent GIF frames change. |
| 154 | `function` | `write_animation_frame_deltas` | docstring | Write the frame-delta manifest for the deterministic animation track. |
| 163 | `function` | `validate_animation_frame_deltas` | docstring | Return frame-delta manifest issues. |

## `src/visualizations/figure_helpers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `save_styled_figure` | inventory fallback | Inventory fallback for function `save_styled_figure` defined at `src/visualizations/figure_helpers.py:16`. |
| 27 | `function` | `style_grid` | inventory fallback | Inventory fallback for function `style_grid` defined at `src/visualizations/figure_helpers.py:27`. |
| 37 | `function` | `wrap_text` | docstring | Wrap labels for compact figure panels. |
| 42 | `function` | `add_note` | docstring | Add a small source/claim note in axes coordinates. |
| 65 | `function` | `configure_axis` | docstring | Apply the common publication axis treatment. |
| 95 | `function` | `text_box` | docstring | Draw a wrapped labeled box in axes/data coordinates. |
| 125 | `function` | `draw_column_headers` | docstring | Draw aligned column headers for flow/table figures. |
| 133 | `function` | `draw_arrow` | docstring | Draw a compact left-to-right flow arrow. |
| 143 | `function` | `load_json_artifact` | docstring | Load a JSON artifact by project-relative path. |
| 152 | `function` | `add_value_labels` | docstring | Label vertical bars without changing axes limits too aggressively. |
| 169 | `function` | `styled_figure` | docstring | Load style, resolve output path, and apply matplotlib rc context. |

## `src/visualizations/figure_io.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `_normalize_rgb_extrema` | inventory fallback | Inventory fallback for function `_normalize_rgb_extrema` defined at `src/visualizations/figure_io.py:13`. |
| 22 | `function` | `image_render_metrics` | docstring | Return deterministic live PNG metrics used by render validators. |
| 55 | `function` | `save_figure_png` | docstring | Save a figure to PNG and optionally normalize to RGB for PDF pipelines. |

## `src/visualizations/figure_registry.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 19 | `class` | `FigureSpec` | inventory fallback | Inventory fallback for class `FigureSpec` defined at `src/visualizations/figure_registry.py:19`. |
| 31 | `class` | `SectionFigureRef` | inventory fallback | Inventory fallback for class `SectionFigureRef` defined at `src/visualizations/figure_registry.py:31`. |
| 38 | `function` | `_figures_yaml_path` | inventory fallback | Inventory fallback for function `_figures_yaml_path` defined at `src/visualizations/figure_registry.py:38`. |
| 42 | `function` | `_load_figures_yaml` | inventory fallback | Inventory fallback for function `_load_figures_yaml` defined at `src/visualizations/figure_registry.py:42`. |
| 49 | `function` | `load_figure_registry` | inventory fallback | Inventory fallback for function `load_figure_registry` defined at `src/visualizations/figure_registry.py:49`. |
| 73 | `function` | `load_section_figures` | inventory fallback | Inventory fallback for function `load_section_figures` defined at `src/visualizations/figure_registry.py:73`. |
| 97 | `function` | `figure_output_path` | inventory fallback | Inventory fallback for function `figure_output_path` defined at `src/visualizations/figure_registry.py:97`. |
| 102 | `function` | `render_figure_markdown` | inventory fallback | Inventory fallback for function `render_figure_markdown` defined at `src/visualizations/figure_registry.py:102`. |
| 138 | `function` | `render_section_figures` | inventory fallback | Inventory fallback for function `render_section_figures` defined at `src/visualizations/figure_registry.py:138`. |
| 161 | `function` | `build_figure_registry_payload` | docstring | Build validator-facing registry JSON keyed by ``fig:{id}`` labels. |
| 182 | `function` | `write_figure_registry_json` | docstring | Write ``output/figures/figure_registry.json`` from ``figures.yaml``. |

## `src/visualizations/figure_style.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 30 | `class` | `FigureStyleConfig` | inventory fallback | Inventory fallback for class `FigureStyleConfig` defined at `src/visualizations/figure_style.py:30`. |
| 37 | `function` | `FigureStyleConfig.color` | inventory fallback | Inventory fallback for function `FigureStyleConfig.color` defined at `src/visualizations/figure_style.py:37`. |
| 40 | `function` | `FigureStyleConfig.rc_params` | inventory fallback | Inventory fallback for function `FigureStyleConfig.rc_params` defined at `src/visualizations/figure_style.py:40`. |
| 60 | `function` | `active_style` | inventory fallback | Inventory fallback for function `active_style` defined at `src/visualizations/figure_style.py:60`. |
| 64 | `function` | `load_figure_style` | inventory fallback | Inventory fallback for function `load_figure_style` defined at `src/visualizations/figure_style.py:64`. |
| 81 | `function` | `apply_style` | inventory fallback | Inventory fallback for function `apply_style` defined at `src/visualizations/figure_style.py:81`. |

## `src/visualizations/figures.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 42 | `function` | `_read_sweep` | inventory fallback | Inventory fallback for function `_read_sweep` defined at `src/visualizations/figures.py:42`. |
| 50 | `function` | `_style_discrete_y` | inventory fallback | Inventory fallback for function `_style_discrete_y` defined at `src/visualizations/figures.py:50`. |
| 55 | `function` | `_apply_artifact_note` | inventory fallback | Inventory fallback for function `_apply_artifact_note` defined at `src/visualizations/figures.py:55`. |
| 59 | `function` | `figure_ising_mi_curve` | inventory fallback | Inventory fallback for function `figure_ising_mi_curve` defined at `src/visualizations/figures.py:59`. |
| 113 | `function` | `figure_si_belief_entropy_curve` | inventory fallback | Inventory fallback for function `figure_si_belief_entropy_curve` defined at `src/visualizations/figures.py:113`. |
| 149 | `function` | `figure_si_obs_action_trace` | inventory fallback | Inventory fallback for function `figure_si_obs_action_trace` defined at `src/visualizations/figures.py:149`. |
| 182 | `function` | `figure_si_tmaze_actions` | inventory fallback | Inventory fallback for function `figure_si_tmaze_actions` defined at `src/visualizations/figures.py:182`. |
| 217 | `function` | `figure_si_summary` | docstring | Deprecated alias for ``figure_si_tmaze_actions``. |
| 222 | `function` | `figure_free_energy_curve` | inventory fallback | Inventory fallback for function `figure_free_energy_curve` defined at `src/visualizations/figures.py:222`. |
| 263 | `function` | `figure_semantic_gluing_graph` | inventory fallback | Inventory fallback for function `figure_semantic_gluing_graph` defined at `src/visualizations/figures.py:263`. |
| 333 | `function` | `figure_theorem_traceability_graph` | docstring | Render theorem → proof dependency → witness links from generated JSON rows. |
| 394 | `function` | `figure_causal_ablation_heatmap` | docstring | Render source-backed causal-ablation effects as topology × perturbation heatmap. |
| 445 | `function` | `figure_scholarship_source_map` | docstring | Render bibliography-to-method-source bindings from the scholarship matrix. |
| 493 | `function` | `figure_efe_decomposition` | docstring | Expected Free Energy term decomposition across T-maze policies. |
| 564 | `function` | `figure_precision_sweep` | docstring | Policy-posterior sharpening as precision (gamma) increases. |
| 631 | `function` | `figure_cue_tmaze_advantage` | docstring | Epistemic necessity in the cue-then-reward T-maze. |
| 692 | `function` | `figure_dirichlet_convergence` | docstring | KL(true A \|\| learned A) versus Dirichlet update step (log-y). |
| 769 | `function` | `run_figure` | docstring | Dispatch a registry figure id to its generator. |
| 782 | `function` | `generate_all_figures` | inventory fallback | Inventory fallback for function `generate_all_figures` defined at `src/visualizations/figures.py:782`. |

## `src/visualizations/figures_diagrams.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 34 | `function` | `_load_invariant_blocks` | inventory fallback | Inventory fallback for function `_load_invariant_blocks` defined at `src/visualizations/figures_diagrams.py:34`. |
| 47 | `function` | `figure_invariant_dashboard` | inventory fallback | Inventory fallback for function `figure_invariant_dashboard` defined at `src/visualizations/figures_diagrams.py:47`. |
| 93 | `function` | `figure_tmaze_schematic` | inventory fallback | Inventory fallback for function `figure_tmaze_schematic` defined at `src/visualizations/figures_diagrams.py:93`. |
| 159 | `function` | `_load_pipeline_track_labels` | inventory fallback | Inventory fallback for function `_load_pipeline_track_labels` defined at `src/visualizations/figures_diagrams.py:159`. |
| 166 | `function` | `_load_sheaf_track_labels` | inventory fallback | Inventory fallback for function `_load_sheaf_track_labels` defined at `src/visualizations/figures_diagrams.py:166`. |
| 174 | `function` | `figure_multi_track_architecture` | inventory fallback | Inventory fallback for function `figure_multi_track_architecture` defined at `src/visualizations/figures_diagrams.py:174`. |
| 185 | `function` | `figure_multi_track_architecture.chunks` | inventory fallback | Inventory fallback for function `figure_multi_track_architecture.chunks` defined at `src/visualizations/figures_diagrams.py:185`. |
| 188 | `function` | `figure_multi_track_architecture.draw_group_column` | inventory fallback | Inventory fallback for function `figure_multi_track_architecture.draw_group_column` defined at `src/visualizations/figures_diagrams.py:188`. |
| 237 | `function` | `figure_track_lane_promotion_map` | docstring | Render the pipeline-track promotion obligations and sheaf-lane bindings. |
| 330 | `function` | `figure_lean_boundary_status` | inventory fallback | Inventory fallback for function `figure_lean_boundary_status` defined at `src/visualizations/figures_diagrams.py:330`. |
| 361 | `function` | `figure_gnn_ontology_concordance` | inventory fallback | Inventory fallback for function `figure_gnn_ontology_concordance` defined at `src/visualizations/figures_diagrams.py:361`. |

## `src/visualizations/figures_sheaf.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 32 | `function` | `figure_sheaf_layers_overview` | inventory fallback | Inventory fallback for function `figure_sheaf_layers_overview` defined at `src/visualizations/figures_sheaf.py:32`. |
| 67 | `function` | `figure_sheaf_coverage_heatmap` | docstring | Render B/W/G sheaf coverage matrix with IMRAD row grouping. |

## `src/visualizations/figures_sheaf_draw.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `_imrad_group_label` | inventory fallback | Inventory fallback for function `_imrad_group_label` defined at `src/visualizations/figures_sheaf_draw.py:15`. |
| 19 | `function` | `_wrap_label` | inventory fallback | Inventory fallback for function `_wrap_label` defined at `src/visualizations/figures_sheaf_draw.py:19`. |
| 23 | `function` | `_draw_imrad_group_labels` | docstring | Annotate IMRAD block names on the left margin of the heatmap. |
| 60 | `function` | `draw_coverage_heatmap` | inventory fallback | Inventory fallback for function `draw_coverage_heatmap` defined at `src/visualizations/figures_sheaf_draw.py:60`. |
| 138 | `function` | `draw_track_layers_panel` | inventory fallback | Inventory fallback for function `draw_track_layers_panel` defined at `src/visualizations/figures_sheaf_draw.py:138`. |
| 200 | `function` | `layers_overview_figure_height` | docstring | Figure height (inches) for the two-panel sheaf layers overview. |

## `src/visualizations/figures_sheaf_payload.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `class` | `HeatmapPayload` | inventory fallback | Inventory fallback for class `HeatmapPayload` defined at `src/visualizations/figures_sheaf_payload.py:13`. |
| 22 | `function` | `coverage_heatmap_payload` | inventory fallback | Inventory fallback for function `coverage_heatmap_payload` defined at `src/visualizations/figures_sheaf_payload.py:22`. |

## `src/visualizations/lean_boundary.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `class` | `LeanBoundaryRow` | inventory fallback | Inventory fallback for class `LeanBoundaryRow` defined at `src/visualizations/lean_boundary.py:11`. |
| 26 | `function` | `_module_name` | inventory fallback | Inventory fallback for function `_module_name` defined at `src/visualizations/lean_boundary.py:26`. |
| 34 | `function` | `_declaration_block` | docstring | Return the declaration body from ``start`` until the next top-level def/theorem. |
| 43 | `function` | `_scan_lean_file` | inventory fallback | Inventory fallback for function `_scan_lean_file` defined at `src/visualizations/lean_boundary.py:43`. |
| 56 | `function` | `load_lean_boundary_rows` | inventory fallback | Inventory fallback for function `load_lean_boundary_rows` defined at `src/visualizations/lean_boundary.py:56`. |

## `scripts/check_documentation_contract.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `build_parser` | docstring | Return the CLI parser for documentation contract checks. |
| 27 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/check_documentation_contract.py:27`. |

## `scripts/compose_manuscript.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/compose_manuscript.py:15`. |

## `scripts/compute_statistics.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/compute_statistics.py:15`. |

## `scripts/generate_figures.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_figures.py:15`. |

## `scripts/generate_formal_interop_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_formal_interop_tracks.py:16`. |

## `scripts/generate_integration_audit.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_integration_audit.py:15`. |

## `scripts/generate_method_inventory.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `build_parser` | docstring | Return the CLI parser for method-inventory generation. |
| 32 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_method_inventory.py:32`. |

## `scripts/generate_sheaf_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_sheaf_tracks.py:15`. |

## `scripts/generate_toy_sweep_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_toy_sweep_tracks.py:15`. |

## `scripts/generate_validation_spine.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_validation_spine.py:15`. |

## `scripts/inject_variables.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/inject_variables.py:11`. |

## `scripts/render_animation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `build_parser` | inventory fallback | Inventory fallback for function `build_parser` defined at `scripts/render_animation.py:14`. |
| 26 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/render_animation.py:26`. |

## `scripts/render_pdf.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 36 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/render_pdf.py:36`. |

## `scripts/run_analytical_sweep.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/run_analytical_sweep.py:15`. |

## `scripts/simulate_si_graph_world.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/simulate_si_graph_world.py:13`. |

## `scripts/simulate_si_tmaze.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `build_parser` | inventory fallback | Inventory fallback for function `build_parser` defined at `scripts/simulate_si_tmaze.py:18`. |
| 50 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/simulate_si_tmaze.py:50`. |

## `scripts/validate_outputs.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/validate_outputs.py:16`. |

## `scripts/z_generate_manuscript_variables.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 25 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/z_generate_manuscript_variables.py:25`. |

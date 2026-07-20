# Method Inventory

Generated documentation coverage for every Python `def` and `class` under `src/` and `scripts/`. Entries marked `inventory fallback` have no inline docstring yet, but remain documented here by path, line, kind, and qualified name.

Total documented definitions: 805

## `src/analytical/bernoulli_toy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `ising_coupling` | docstring | Process ising coupling. |
| 23 | `function` | `symmetric_mean_field_prior` | docstring | Process symmetric mean field prior. |
| 29 | `function` | `ising_mutual_information` | docstring | Process ising mutual information. |
| 44 | `function` | `ising_joint_posterior` | docstring | Process ising joint posterior. |
| 52 | `function` | `empirical_mutual_information` | docstring | Mutual information recomputed independently from the joint via total correlation. |
| 65 | `function` | `lambda_sweep_values` | docstring | Backward-compatible sweep grid; delegates to ``lambda_grid`` SSOT. |

## `src/analytical/coupling.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `entangled_prior_unnormalised` | docstring | Process entangled prior unnormalised. |
| 28 | `function` | `entangled_posterior` | docstring | Process entangled posterior. |
| 45 | `function` | `expected_value` | docstring | Process expected value. |

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
| 14 | `class` | `Hyperparameters` | docstring | Data container for Hyperparameters. |
| 24 | `function` | `load_hyperparameters` | docstring | Load hyperparameters from a file. |
| 29 | `function` | `lambda_grid` | docstring | Process lambda grid. |

## `src/analytical/invariants.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `inv_ising_mi_at_zero` | docstring | Process inv ising mi at zero. |
| 26 | `function` | `inv_ising_mi_saturates` | docstring | Process inv ising mi saturates. |
| 32 | `function` | `inv_empirical_matches_closed_form` | docstring | Process inv empirical matches closed form. |
| 43 | `function` | `inv_decomposition_identity` | docstring | Process inv decomposition identity. |
| 62 | `function` | `inv_joint_is_pmf` | docstring | Process inv joint is pmf. |
| 70 | `function` | `inv_mean_field_at_lambda_zero` | docstring | Process inv mean field at lambda zero. |
| 88 | `function` | `run_invariants` | docstring | Run invariants. |
| 93 | `function` | `all_invariants_pass` | docstring | Process all invariants pass. |

## `src/analytical/joint_dist.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `is_pmf` | docstring | Check whether pmf. |
| 19 | `function` | `normalize` | docstring | Process normalize. |
| 28 | `function` | `mean_field_to_joint` | docstring | Process mean field to joint. |
| 38 | `function` | `joint_marginal` | docstring | Process joint marginal. |
| 47 | `function` | `joint_marginals` | docstring | Process joint marginals. |
| 53 | `function` | `is_mean_field` | docstring | Check whether mean field. |
| 60 | `function` | `m_projection` | docstring | Process m projection. |

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
| 110 | `function` | `_evidence_predicate_name` | inventory fallback | Inventory fallback for function `_evidence_predicate_name` defined at `src/gates/claim_ledger.py:110`. |
| 119 | `function` | `claim_evidence_status_rows` | docstring | Return row-level resolution status for every claim-ledger evidence declaration. |
| 227 | `function` | `typed_claim_evidence_issues` | docstring | Return explicit typed-evidence failures for ``claim_ledger.yaml``. |
| 273 | `function` | `validate_typed_claim_evidence` | docstring | Validate optional typed evidence declarations in ``claim_ledger.yaml``. |
| 287 | `function` | `validate_claim_ledger` | docstring | Validate claim ledger. |
| 330 | `function` | `verify_claim_bindings` | docstring | Semantic claim bindings -- tie manuscript values/adjectives to their oracles. |

## `src/gates/documentation_contract.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 80 | `class` | `DocumentationIssue` | docstring | A documentation contract violation with a stable diagnostic code. |
| 88 | `function` | `DocumentationIssue.format` | docstring | Return a compact CLI-friendly issue string. |
| 94 | `function` | `_has_skip_part` | inventory fallback | Inventory fallback for function `_has_skip_part` defined at `src/gates/documentation_contract.py:94`. |
| 102 | `function` | `_iter_files` | inventory fallback | Inventory fallback for function `_iter_files` defined at `src/gates/documentation_contract.py:102`. |
| 111 | `function` | `_read_text_if_present` | docstring | Read text while tolerating concurrent generated-output refreshes. |
| 119 | `function` | `_line_number` | inventory fallback | Inventory fallback for function `_line_number` defined at `src/gates/documentation_contract.py:119`. |
| 123 | `function` | `_trim_link_target` | inventory fallback | Inventory fallback for function `_trim_link_target` defined at `src/gates/documentation_contract.py:123`. |
| 133 | `function` | `_split_link_target` | inventory fallback | Inventory fallback for function `_split_link_target` defined at `src/gates/documentation_contract.py:133`. |
| 141 | `function` | `_heading_anchor` | inventory fallback | Inventory fallback for function `_heading_anchor` defined at `src/gates/documentation_contract.py:141`. |
| 150 | `function` | `_markdown_anchors` | inventory fallback | Inventory fallback for function `_markdown_anchors` defined at `src/gates/documentation_contract.py:150`. |
| 167 | `function` | `_reference_label` | inventory fallback | Inventory fallback for function `_reference_label` defined at `src/gates/documentation_contract.py:167`. |
| 171 | `function` | `_reference_definitions` | inventory fallback | Inventory fallback for function `_reference_definitions` defined at `src/gates/documentation_contract.py:171`. |
| 175 | `function` | `_iter_markdown_targets` | docstring | Return inline and reference-style Markdown link targets. |
| 182 | `function` | `check_markdown_links` | docstring | Validate relative Markdown links, including generated Markdown outputs. |
| 241 | `function` | `check_hydrated_output_links` | docstring | Hydrated manuscript copies must link relative to output/manuscript/. |
| 265 | `function` | `check_readme_agents_pairs` | docstring | Require README.md and AGENTS.md to appear as a pair in source docs. |
| 286 | `function` | `check_project_local_commands` | docstring | Reject stale root-shaped commands in project-local documentation. |
| 307 | `function` | `_paragraphs` | inventory fallback | Inventory fallback for function `_paragraphs` defined at `src/gates/documentation_contract.py:307`. |
| 311 | `function` | `check_historical_test_evidence` | docstring | Keep stale suite-count evidence clearly archived and current evidence singular. |
| 392 | `function` | `check_reference_signposts` | docstring | Require canonical verification and reference signposts in reader docs. |
| 442 | `function` | `check_documentation_contract` | docstring | Run all documentation contract checks. |

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
| 30 | `function` | `validate_manuscript` | docstring | Validate manuscript. |

## `src/gates/method_inventory.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `MethodEntry` | docstring | A documented function, method, nested helper, or class definition. |
| 25 | `function` | `_first_docstring_line` | docstring | Return a compact first docstring line when a definition has one. |
| 33 | `function` | `_fallback_summary` | docstring | Build an inventory-backed summary for a definition without a docstring. |
| 38 | `function` | `_definition_kind` | docstring | Normalize AST node types into report-friendly definition kinds. |
| 47 | `class` | `_DefinitionVisitor` | docstring | Collect definitions while preserving nested qualified names. |
| 50 | `function` | `_DefinitionVisitor.__init__` | inventory fallback | Inventory fallback for function `_DefinitionVisitor.__init__` defined at `src/gates/method_inventory.py:50`. |
| 55 | `function` | `_DefinitionVisitor.visit_ClassDef` | docstring | Process visit ClassDef. |
| 62 | `function` | `_DefinitionVisitor.visit_FunctionDef` | docstring | Process visit FunctionDef. |
| 69 | `function` | `_DefinitionVisitor.visit_AsyncFunctionDef` | docstring | Process visit AsyncFunctionDef. |
| 76 | `function` | `_DefinitionVisitor._record` | inventory fallback | Inventory fallback for function `_DefinitionVisitor._record` defined at `src/gates/method_inventory.py:76`. |
| 92 | `function` | `_source_files` | docstring | Return Python files in the documentation inventory scope. |
| 103 | `function` | `_path_sort_key` | docstring | Sort inventory paths by declared source-root order, then by path. |
| 113 | `function` | `collect_method_entries` | docstring | Collect every class/function definition under source modules and scripts. |
| 126 | `function` | `_escape_cell` | docstring | Escape Markdown table cells without changing the underlying value. |
| 131 | `function` | `render_method_inventory_markdown` | docstring | Render method inventory entries as a grouped Markdown reference. |
| 175 | `function` | `write_method_inventory` | docstring | Write the method inventory Markdown report and return its path. |

## `src/gates/output_checks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 23 | `function` | `_figures_nonblank` | inventory fallback | Inventory fallback for function `_figures_nonblank` defined at `src/gates/output_checks.py:23`. |
| 42 | `function` | `_required_output_checks` | inventory fallback | Inventory fallback for function `_required_output_checks` defined at `src/gates/output_checks.py:42`. |
| 46 | `function` | `validate_outputs` | docstring | Validate every registered output artifact and return gate booleans by name. |

## `src/gates/output_checks_promoted.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 9 | `function` | `load_promoted_artifacts` | docstring | Load promoted artifacts from a file. |
| 14 | `function` | `add_toy_formal_integration_checks` | docstring | Add toy formal integration checks to the collection. |
| 149 | `function` | `add_visualization_checks` | docstring | Add visualization checks to the collection. |
| 197 | `function` | `add_canonical_sheaf_checks` | docstring | Add canonical sheaf checks to the collection. |
| 331 | `function` | `add_track_validator_checks` | docstring | Add track validator checks to the collection. |
| 352 | `function` | `set_experiment_plan_metrics` | docstring | Process set experiment plan metrics. |

## `src/gates/output_checks_simulation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 8 | `function` | `pymdp_logging_expected` | docstring | Process pymdp logging expected. |
| 19 | `function` | `_efe_values_explained` | inventory fallback | Inventory fallback for function `_efe_values_explained` defined at `src/gates/output_checks_simulation.py:19`. |
| 28 | `function` | `efe_values_explained` | docstring | Process efe values explained. |
| 38 | `function` | `add_simulation_checks` | docstring | Add simulation checks to the collection. |
| 146 | `function` | `add_log_check` | docstring | Add log check to the collection. |

## `src/gates/output_checks_spine.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 6 | `function` | `add_validation_spine_checks` | docstring | Add validation spine checks to the collection. |

## `src/gnn/concordance.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 34 | `function` | `parity_gaps` | docstring | Report concordance gaps between GNN symbols and their ontology annotations. |
| 61 | `function` | `concordance_holds` | docstring | Process concordance holds. |

## `src/gnn/model.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `GnnVariable` | docstring | Data container for GnnVariable. |
| 24 | `function` | `GnnVariable.size` | docstring | Process size. |
| 33 | `class` | `GnnConnection` | docstring | Data container for GnnConnection. |
| 43 | `class` | `GnnModel` | docstring | Data container for GnnModel. |
| 57 | `function` | `GnnModel.variable` | docstring | Process variable. |
| 63 | `function` | `GnnModel.has` | docstring | Process has. |

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
| 164 | `function` | `parse_gnn` | docstring | Parse gnn. |
| 196 | `function` | `parse_gnn_file` | docstring | Parse gnn file. |

## `src/json_io.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `function` | `load_json` | docstring | Load a JSON object from ``path``; return ``{}`` when missing or invalid. |
| 21 | `function` | `load_json_strict` | docstring | Load a JSON object from ``path``, failing loudly on malformed content. |
| 39 | `function` | `read_json` | docstring | Alias for :func:`load_json`. |
| 44 | `function` | `write_json` | docstring | Write ``payload`` as sorted JSON and return ``path``. |

## `src/manuscript/hydrate.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `format_variables` | docstring | Stringify variable values for manuscript substitution. |
| 35 | `function` | `collect_manuscript_tokens` | docstring | Return token names referenced as {{name}} or {{name:.4f}} in markdown. |
| 40 | `function` | `collect_single_brace_tokens` | docstring | Return snake_case names in single-brace {name} form (likely typos). |
| 45 | `function` | `collect_malformed_token_names` | docstring | Return token-like names that are not valid double-brace placeholders. |
| 51 | `function` | `collect_tokens_in_directory` | docstring | Process collect tokens in directory. |
| 61 | `function` | `validate_manuscript_tokens` | docstring | Return sorted unknown token names referenced under manuscript_dir. |
| 70 | `function` | `substitute_snake_case_tokens` | docstring | Process substitute snake case tokens. |
| 77 | `function` | `substitute_snake_case_tokens._replace` | inventory fallback | Inventory fallback for function `substitute_snake_case_tokens._replace` defined at `src/manuscript/hydrate.py:77`. |
| 94 | `function` | `retarget_resolved_output_links` | docstring | Retarget output links for hydrated copies under output/manuscript/. |
| 99 | `function` | `write_resolved_manuscript` | docstring | Write token-substituted markdown copies to output/manuscript/. |

## `src/manuscript/invariant_counts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `load_invariant_counts` | docstring | Return passed/total invariant counts from merged reports when present. |
| 31 | `function` | `invariants_are_merged` | docstring | True when the report contains genuine *simulation* invariants by content. |

## `src/manuscript/refresh.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `class` | `ManuscriptRefreshPhase` | docstring | Data container for ManuscriptRefreshPhase. |
| 17 | `function` | `refresh_manuscript_pipeline` | docstring | Process refresh manuscript pipeline. |
| 41 | `function` | `settle_manuscript_artifacts` | docstring | Process settle manuscript artifacts. |

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
| 24 | `function` | `issues_have_errors` | docstring | Process issues have errors. |
| 29 | `function` | `validate_manifest` | docstring | Validate manifest. |
| 98 | `function` | `sheaf_law_issues` | docstring | Surface sheaf-law violations as error-level manifest issues for the strict gate. |
| 107 | `function` | `_imrad_group_titles` | inventory fallback | Inventory fallback for function `_imrad_group_titles` defined at `src/manuscript/sheaf/compose.py:107`. |
| 115 | `function` | `_imrad_divider_markdown` | inventory fallback | Inventory fallback for function `_imrad_divider_markdown` defined at `src/manuscript/sheaf/compose.py:115`. |
| 125 | `function` | `compose_section` | docstring | Process compose section. |
| 159 | `function` | `compose_all_sections` | docstring | Process compose all sections. |

## `src/manuscript/sheaf/counts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `structural_counts` | docstring | Counts derived from sheaf manifest, registry, and coverage matrix. |

## `src/manuscript/sheaf/coverage.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 24 | `class` | `SheafCoverageContext` | docstring | Data container for SheafCoverageContext. |
| 32 | `function` | `load_sheaf_coverage_context` | docstring | Load sheaf coverage context from a file. |
| 49 | `function` | `classify_cell` | docstring | Process classify cell. |
| 64 | `function` | `build_coverage_matrix` | docstring | Build coverage matrix. |
| 108 | `function` | `coverage_matrix_to_dict` | docstring | Process coverage matrix to dict. |
| 136 | `function` | `write_coverage_json` | docstring | Write coverage json to the output path. |
| 147 | `function` | `load_coverage_json` | docstring | Load coverage json from a file. |
| 153 | `function` | `validate_coverage_strict` | docstring | Validate coverage strict. |
| 167 | `function` | `gray_cell_count` | docstring | Process gray cell count. |
| 172 | `function` | `gray_cell_count_from_json` | docstring | Process gray cell count from json. |
| 182 | `function` | `validate_coverage_json_data` | docstring | Validate coverage json data. |
| 219 | `function` | `emit_coverage_artifacts` | docstring | Build matrix from live manifest/registry and write coverage JSON only. |

## `src/manuscript/sheaf/laws.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 67 | `class` | `SheafLaw` | docstring | The structural laws that make the coverage presheaf a sheaf. |
| 79 | `class` | `LawViolation` | docstring | A single counter-example to one sheaf law. |
| 88 | `class` | `SheafLawReport` | docstring | Structured result of verifying the sheaf laws against a manifest. |
| 95 | `function` | `SheafLawReport.ok` | docstring | Return True if the result is successful. |
| 99 | `function` | `SheafLawReport.for_law` | docstring | Process for law. |
| 103 | `function` | `SheafLawReport.law_ok` | docstring | Process law ok. |
| 108 | `function` | `SheafLawReport.passed_laws` | docstring | Process passed laws. |
| 113 | `function` | `SheafLawReport.summary` | docstring | Return a summary dict of counts and status. |
| 120 | `function` | `_known_renderers` | inventory fallback | Inventory fallback for function `_known_renderers` defined at `src/manuscript/sheaf/laws.py:120`. |
| 125 | `function` | `_composing_sections` | inventory fallback | Inventory fallback for function `_composing_sections` defined at `src/manuscript/sheaf/laws.py:125`. |
| 129 | `function` | `_check_poset` | docstring | IMRAD blocks form a chain; compose order is monotone in block rank. |
| 173 | `function` | `_check_presheaf` | docstring | Bound tracks are registered; track order restricts the global order. |
| 229 | `function` | `_check_separation` | docstring | s ↦ output_name is injective over composing sections. |
| 258 | `function` | `_check_gluing` | docstring | Compose order is a strict linear extension; each section glues once. |
| 297 | `function` | `_check_typing` | docstring | Each binding is well-typed: renderer exists and suffix is accepted. |
| 336 | `function` | `_check_compositionality` | docstring | Every fragment file is private to one section (composition is a coproduct). |
| 367 | `function` | `verify_sheaf_laws` | docstring | Verify all sheaf laws against the live (or supplied) manifest + registry. |
| 393 | `function` | `sheaf_law_violations` | docstring | Pure law check against in-memory manifest + registry (no filesystem load). |

## `src/manuscript/sheaf/layers_report.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `render_track_registry_table` | docstring | Render track registry table. |
| 34 | `function` | `render_binding_matrix_table` | docstring | Render binding matrix table. |
| 71 | `function` | `render_coverage_legend` | docstring | Render coverage legend. |
| 86 | `function` | `render_evidence_crosswalk_table` | docstring | Render evidence crosswalk table. |
| 105 | `function` | `render_artifact_producer_table` | docstring | Render artifact producer table. |
| 130 | `function` | `render_semantic_restrictions_table` | docstring | Render semantic restrictions table. |
| 174 | `function` | `render_track_improvement_scope_table` | docstring | Render track improvement scope table. |
| 198 | `function` | `render_track_lane_matrix_table` | docstring | Render track lane matrix table. |
| 226 | `function` | `render_section_status_table` | docstring | Render section status table. |
| 260 | `function` | `render_track_status_table` | docstring | Render track status table. |
| 283 | `function` | `render_sheaf_render_log_table` | docstring | Render sheaf render log table. |
| 305 | `function` | `render_sheaf_layers_markdown` | docstring | Render sheaf layers markdown. |

## `src/manuscript/sheaf/manifest.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 22 | `function` | `parse_missing` | docstring | Parse missing. |
| 32 | `function` | `load_manifest` | docstring | Load manifest from a file. |
| 103 | `function` | `default_manifest_path` | docstring | Process default manifest path. |

## `src/manuscript/sheaf/models.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `coverage_cell_symbol` | docstring | Process coverage cell symbol. |
| 27 | `class` | `MissingTrackPolicy` | docstring | Data container for MissingTrackPolicy. |
| 36 | `class` | `TrackSpec` | docstring | Data container for TrackSpec. |
| 49 | `class` | `SheafDefaults` | docstring | Data container for SheafDefaults. |
| 56 | `class` | `SheafSection` | docstring | Data container for SheafSection. |
| 73 | `function` | `SheafSection.should_compose` | docstring | Process should compose. |
| 79 | `class` | `SheafManifest` | docstring | Data container for SheafManifest. |
| 88 | `class` | `ManifestIssue` | docstring | Data container for ManifestIssue. |
| 97 | `class` | `ComposeOptions` | docstring | Data container for ComposeOptions. |
| 107 | `class` | `TrackRegistry` | docstring | Data container for TrackRegistry. |
| 115 | `class` | `ComposeResult` | docstring | Data container for ComposeResult. |
| 123 | `class` | `CoverageCell` | docstring | Data container for CoverageCell. |
| 134 | `class` | `CoverageSectionRow` | docstring | Data container for CoverageSectionRow. |
| 147 | `class` | `CoverageMatrix` | docstring | Data container for CoverageMatrix. |
| 153 | `function` | `CoverageMatrix.gray_cells` | docstring | Process gray cells. |

## `src/manuscript/sheaf/registry.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `load_track_registry` | docstring | Load track registry from a file. |
| 37 | `function` | `track_order_for_section` | docstring | Process track order for section. |
| 56 | `function` | `list_registered_tracks` | docstring | Process list registered tracks. |

## `src/manuscript/sheaf/renderers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_render_ontology` | inventory fallback | Inventory fallback for function `_render_ontology` defined at `src/manuscript/sheaf/renderers.py:18`. |
| 35 | `function` | `_require_track_spec` | inventory fallback | Inventory fallback for function `_require_track_spec` defined at `src/manuscript/sheaf/renderers.py:35`. |
| 42 | `function` | `render_track_body` | docstring | Render track body. |
| 51 | `function` | `_resolve_section_figures` | inventory fallback | Inventory fallback for function `_resolve_section_figures` defined at `src/manuscript/sheaf/renderers.py:51`. |
| 70 | `function` | `_resolve_layers_report` | inventory fallback | Inventory fallback for function `_resolve_layers_report` defined at `src/manuscript/sheaf/renderers.py:70`. |
| 90 | `function` | `resolve_track_body` | docstring | Resolve composed markdown for one bound track. |
| 105 | `function` | `validate_renderer_specs` | docstring | Validate renderer specs. |

## `src/manuscript/sheaf/report.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `class` | `HeatmapConfig` | docstring | Data container for HeatmapConfig. |
| 26 | `class` | `CoverageColorConfig` | docstring | Data container for CoverageColorConfig. |
| 35 | `class` | `ReportConfig` | docstring | Data container for ReportConfig. |
| 46 | `class` | `CoverageConfig` | docstring | Data container for CoverageConfig. |
| 55 | `class` | `CoverageReport` | docstring | Data container for CoverageReport. |
| 67 | `function` | `load_coverage_config` | docstring | Load coverage config from a file. |
| 115 | `function` | `default_coverage_config_path` | docstring | Process default coverage config path. |
| 120 | `function` | `build_coverage_report` | docstring | Build coverage report. |
| 152 | `function` | `_imrad_heading` | inventory fallback | Inventory fallback for function `_imrad_heading` defined at `src/manuscript/sheaf/report.py:152`. |
| 156 | `function` | `render_report_markdown` | docstring | Render report markdown. |
| 209 | `function` | `write_coverage_page` | docstring | Write coverage page to the output path. |

## `src/manuscript/sheaf/semantic_certificate.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 41 | `function` | `build_semantic_gluing_certificate` | docstring | Build a JSON-serializable semantic certificate from live project state. |
| 208 | `function` | `write_semantic_gluing_certificate` | docstring | Write semantic gluing certificate to the output path. |

## `src/manuscript/sheaf/semantic_evidence.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `_section_records` | inventory fallback | Inventory fallback for function `_section_records` defined at `src/manuscript/sheaf/semantic_evidence.py:21`. |
| 47 | `function` | `_claim_records` | inventory fallback | Inventory fallback for function `_claim_records` defined at `src/manuscript/sheaf/semantic_evidence.py:47`. |
| 67 | `function` | `build_evidence_crosswalk` | docstring | Build a claim-to-artifact crosswalk from the typed claim ledger. |
| 89 | `function` | `build_validation_dependency_graph` | docstring | Build script → artifact → manuscript/gate dependency records. |
| 96 | `function` | `validate_configured_artifact_producers` | docstring | Fail when required generated artifacts lack configured analysis producers. |
| 170 | `function` | `_semantic_artifact_sources` | inventory fallback | Inventory fallback for function `_semantic_artifact_sources` defined at `src/manuscript/sheaf/semantic_evidence.py:170`. |
| 174 | `function` | `_semantic_payloads` | inventory fallback | Inventory fallback for function `_semantic_payloads` defined at `src/manuscript/sheaf/semantic_evidence.py:174`. |
| 178 | `function` | `_semantic_track_rows` | inventory fallback | Inventory fallback for function `_semantic_track_rows` defined at `src/manuscript/sheaf/semantic_evidence.py:178`. |
| 192 | `function` | `_semantic_shared_symbols` | inventory fallback | Inventory fallback for function `_semantic_shared_symbols` defined at `src/manuscript/sheaf/semantic_evidence.py:192`. |
| 201 | `function` | `_canonical_restriction_snapshot` | inventory fallback | Inventory fallback for function `_canonical_restriction_snapshot` defined at `src/manuscript/sheaf/semantic_evidence.py:201`. |

## `src/manuscript/sheaf/semantic_gluing_outputs.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `write_semantic_gluing_outputs` | docstring | Write semantic certificate, evidence crosswalk, and dependency graph outputs. |
| 80 | `function` | `_stable_artifact_graph` | inventory fallback | Inventory fallback for function `_stable_artifact_graph` defined at `src/manuscript/sheaf/semantic_gluing_outputs.py:80`. |
| 92 | `function` | `_stable_certificate_fields` | inventory fallback | Inventory fallback for function `_stable_certificate_fields` defined at `src/manuscript/sheaf/semantic_gluing_outputs.py:92`. |
| 105 | `function` | `_semantic_lane_summary_issues` | inventory fallback | Inventory fallback for function `_semantic_lane_summary_issues` defined at `src/manuscript/sheaf/semantic_gluing_outputs.py:105`. |
| 125 | `function` | `validate_semantic_gluing` | docstring | Validate the live semantic certificate and its generated artifact. |

## `src/manuscript/sheaf/semantic_issues.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 32 | `function` | `semantic_gluing_issues` | docstring | Return semantic cross-track disagreements not covered by structural laws. |

## `src/manuscript/sheaf/semantic_refresh.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 9 | `function` | `_refresh_hydrated_manuscript` | inventory fallback | Inventory fallback for function `_refresh_hydrated_manuscript` defined at `src/manuscript/sheaf/semantic_refresh.py:9`. |
| 15 | `function` | `_refresh_artifact_contract_outputs` | docstring | Refresh contract artifacts that hash semantic outputs after final writes. |
| 35 | `function` | `_refresh_animation_outputs` | docstring | Refresh deterministic animation artifacts before semantic validation. |

## `src/manuscript/sheaf/semantic_restrictions.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `_rel` | inventory fallback | Inventory fallback for function `_rel` defined at `src/manuscript/sheaf/semantic_restrictions.py:17`. |
| 21 | `function` | `_configured_analysis_scripts` | inventory fallback | Inventory fallback for function `_configured_analysis_scripts` defined at `src/manuscript/sheaf/semantic_restrictions.py:21`. |
| 33 | `function` | `_claim_records` | inventory fallback | Inventory fallback for function `_claim_records` defined at `src/manuscript/sheaf/semantic_restrictions.py:33`. |
| 55 | `function` | `_claims_by_path` | inventory fallback | Inventory fallback for function `_claims_by_path` defined at `src/manuscript/sheaf/semantic_restrictions.py:55`. |
| 65 | `function` | `_animation_frame_count` | inventory fallback | Inventory fallback for function `_animation_frame_count` defined at `src/manuscript/sheaf/semantic_restrictions.py:65`. |
| 78 | `function` | `_lean_status` | inventory fallback | Inventory fallback for function `_lean_status` defined at `src/manuscript/sheaf/semantic_restrictions.py:78`. |
| 93 | `function` | `_policy_comparison_restrictions` | inventory fallback | Inventory fallback for function `_policy_comparison_restrictions` defined at `src/manuscript/sheaf/semantic_restrictions.py:93`. |
| 107 | `function` | `_policy_posterior_restrictions` | inventory fallback | Inventory fallback for function `_policy_posterior_restrictions` defined at `src/manuscript/sheaf/semantic_restrictions.py:107`. |
| 117 | `function` | `_runtime_diagnostics_restrictions` | inventory fallback | Inventory fallback for function `_runtime_diagnostics_restrictions` defined at `src/manuscript/sheaf/semantic_restrictions.py:117`. |
| 128 | `function` | `_restriction_class` | inventory fallback | Inventory fallback for function `_restriction_class` defined at `src/manuscript/sheaf/semantic_restrictions.py:128`. |
| 142 | `function` | `_restriction_lane` | inventory fallback | Inventory fallback for function `_restriction_lane` defined at `src/manuscript/sheaf/semantic_restrictions.py:142`. |
| 175 | `function` | `_restriction_lane_assignments` | inventory fallback | Inventory fallback for function `_restriction_lane_assignments` defined at `src/manuscript/sheaf/semantic_restrictions.py:175`. |
| 179 | `function` | `_restriction_value_ok` | inventory fallback | Inventory fallback for function `_restriction_value_ok` defined at `src/manuscript/sheaf/semantic_restrictions.py:179`. |
| 195 | `function` | `_restriction_lane_summaries` | inventory fallback | Inventory fallback for function `_restriction_lane_summaries` defined at `src/manuscript/sheaf/semantic_restrictions.py:195`. |
| 211 | `function` | `_proof_obligation_rows` | inventory fallback | Inventory fallback for function `_proof_obligation_rows` defined at `src/manuscript/sheaf/semantic_restrictions.py:211`. |
| 223 | `function` | `_graph_world_restrictions` | inventory fallback | Inventory fallback for function `_graph_world_restrictions` defined at `src/manuscript/sheaf/semantic_restrictions.py:223`. |
| 236 | `function` | `_pymdp_hash_restrictions` | inventory fallback | Inventory fallback for function `_pymdp_hash_restrictions` defined at `src/manuscript/sheaf/semantic_restrictions.py:236`. |
| 245 | `function` | `_gnn_symbols` | inventory fallback | Inventory fallback for function `_gnn_symbols` defined at `src/manuscript/sheaf/semantic_restrictions.py:245`. |
| 252 | `function` | `_section_ontology_symbols` | inventory fallback | Inventory fallback for function `_section_ontology_symbols` defined at `src/manuscript/sheaf/semantic_restrictions.py:252`. |
| 257 | `function` | `_expected_symbol_gaps` | inventory fallback | Inventory fallback for function `_expected_symbol_gaps` defined at `src/manuscript/sheaf/semantic_restrictions.py:257`. |

## `src/manuscript/sheaf/status.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_load_yaml` | inventory fallback | Inventory fallback for function `_load_yaml` defined at `src/manuscript/sheaf/status.py:18`. |
| 25 | `function` | `_claim_indexes` | inventory fallback | Inventory fallback for function `_claim_indexes` defined at `src/manuscript/sheaf/status.py:25`. |
| 52 | `function` | `_artifact_indexes` | inventory fallback | Inventory fallback for function `_artifact_indexes` defined at `src/manuscript/sheaf/status.py:52`. |
| 73 | `function` | `build_sheaf_section_status_matrix` | docstring | Build one explicit status row for every section x registered-track cell. |
| 199 | `function` | `build_sheaf_render_log` | docstring | Build a deterministic render/log summary for the sheaf manuscript layer. |
| 284 | `function` | `validate_sheaf_status_outputs` | docstring | Validate sheaf status outputs. |
| 331 | `function` | `write_sheaf_status_outputs` | docstring | Write sheaf status outputs to the output path. |

## `src/manuscript/variables.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 19 | `function` | `_ising_mi_saturation_from_sweep` | docstring | Maximum closed-form MI on the measured λ grid (nats). |
| 26 | `function` | `_free_energy_argmin_lambda` | docstring | λ minimizing free energy of the entangled posterior vs the mean-field prior. |
| 53 | `function` | `_policy_goal_counts_by_mode` | docstring | Goal-reaching run counts split by inference mode from si_policy_comparison runs. |
| 67 | `function` | `_pipeline_track_count` | docstring | Required pipeline tracks from ``tracks.yaml`` (distinct from ``sheaf_track_count``). |
| 77 | `function` | `_gnn_spec_version` | inventory fallback | Inventory fallback for function `_gnn_spec_version` defined at `src/manuscript/variables.py:77`. |
| 93 | `function` | `_efe_token_values` | docstring | Manuscript tokens for the closed-form Expected Free Energy decomposition. |
| 117 | `function` | `_precision_token_values` | docstring | Manuscript tokens for the closed-form precision (gamma) sweep. |
| 139 | `function` | `_cue_tmaze_token_values` | docstring | Manuscript tokens for the cue-then-reward T-maze epistemic-necessity result. |
| 158 | `function` | `_dirichlet_token_values` | docstring | Manuscript tokens for the deterministic Dirichlet likelihood-learning run. |
| 175 | `function` | `_load_variable_artifacts` | docstring | Load optional generated artifacts used by manuscript tokens. |
| 180 | `function` | `_core_token_values` | docstring | Return project, analytical, invariant, and structural manuscript tokens. |
| 207 | `function` | `_simulation_token_values` | docstring | Return SI, PyMDP runtime, posterior, and graph-world manuscript tokens. |
| 266 | `function` | `_validation_spine_token_values` | docstring | Return provenance, replay, and counterexample manuscript tokens. |
| 290 | `function` | `_toy_formal_token_values` | docstring | Return promoted toy-sweep, formal-interop, and animation manuscript tokens. |
| 327 | `function` | `_semantic_visualization_token_values` | docstring | Return semantic, visualization, staleness, and cross-track manuscript tokens. |
| 404 | `function` | `_canonical_sheaf_token_values` | docstring | Return canonical sheaf-track, release, proof, and scholarship tokens. |
| 507 | `function` | `generate_variables` | docstring | Generate manuscript tokens from live configuration and output artifacts. |

## `src/ontology/bindings.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 27 | `function` | `load_section_ontology` | docstring | Load section ontology from a file. |
| 44 | `function` | `validate_gnn_ontology` | docstring | Validate gnn ontology. |
| 59 | `function` | `_validate_section_ontology_exact` | inventory fallback | Inventory fallback for function `_validate_section_ontology_exact` defined at `src/ontology/bindings.py:59`. |
| 76 | `function` | `validate_all_gnn_ontology` | docstring | Validate every project GNN model against its model-specific ontology map. |

## `src/orchestration/analysis.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `write_parameter_sweep` | docstring | Write parameter sweep to the output path. |
| 40 | `function` | `write_invariants_report` | docstring | Write invariants report to the output path. |
| 55 | `function` | `summarize_sweep` | docstring | Process summarize sweep. |
| 61 | `function` | `write_analysis_statistics` | docstring | Write analysis statistics to the output path. |
| 79 | `function` | `run_analysis` | docstring | Run analysis. |

## `src/orchestration/coverage_pipeline.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `_coverage_input_paths` | inventory fallback | Inventory fallback for function `_coverage_input_paths` defined at `src/orchestration/coverage_pipeline.py:11`. |
| 23 | `function` | `_is_stale` | inventory fallback | Inventory fallback for function `_is_stale` defined at `src/orchestration/coverage_pipeline.py:23`. |
| 30 | `function` | `run_coverage_figures_and_page` | docstring | Render heatmap PNG and coverage page from existing coverage JSON. |
| 48 | `function` | `ensure_coverage_artifacts` | docstring | Ensure coverage JSON exists; optionally render heatmap and coverage page. |
| 90 | `function` | `run_coverage_pipeline` | docstring | Write coverage JSON, heatmap PNG, and coverage manuscript page. |

## `src/orchestration/full_verification.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `_relative_test_path` | inventory fallback | Inventory fallback for function `_relative_test_path` defined at `src/orchestration/full_verification.py:13`. |
| 17 | `function` | `_all_test_modules` | inventory fallback | Inventory fallback for function `_all_test_modules` defined at `src/orchestration/full_verification.py:17`. |
| 21 | `function` | `_chunked_test_groups` | inventory fallback | Inventory fallback for function `_chunked_test_groups` defined at `src/orchestration/full_verification.py:21`. |
| 59 | `function` | `_coverage_test_groups` | inventory fallback | Inventory fallback for function `_coverage_test_groups` defined at `src/orchestration/full_verification.py:59`. |
| 66 | `function` | `_coverage_command` | inventory fallback | Inventory fallback for function `_coverage_command` defined at `src/orchestration/full_verification.py:66`. |
| 80 | `function` | `_run` | inventory fallback | Inventory fallback for function `_run` defined at `src/orchestration/full_verification.py:80`. |
| 111 | `function` | `run_verification` | docstring | Run verification. |

## `src/orchestration/pipeline_manifest.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `class` | `ScriptStep` | docstring | Data container for ScriptStep. |
| 34 | `function` | `analysis_scripts` | docstring | Process analysis scripts. |

## `src/roadmap_tracks/figure_provenance.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `_is_deferred_source` | docstring | Pipeline-produced artifacts that do not exist at map-build time. |
| 27 | `function` | `_source_path_exists` | docstring | A listed source-code path must resolve to a real file or directory on disk. |
| 32 | `function` | `_figure_sources_mapped` | docstring | Re-derive `mapped` from the filesystem rather than trusting the hardcoded dict. |

## `src/roadmap_tracks/fixed_point.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/fixed_point.py:13`. |
| 17 | `function` | `_refresh_animation_outputs` | inventory fallback | Inventory fallback for function `_refresh_animation_outputs` defined at `src/roadmap_tracks/fixed_point.py:17`. |
| 29 | `function` | `_refresh_hydrated_manuscript` | inventory fallback | Inventory fallback for function `_refresh_hydrated_manuscript` defined at `src/roadmap_tracks/fixed_point.py:29`. |
| 38 | `function` | `_write_semantic_core` | inventory fallback | Inventory fallback for function `_write_semantic_core` defined at `src/roadmap_tracks/fixed_point.py:38`. |
| 63 | `function` | `_write_contract_artifacts` | inventory fallback | Inventory fallback for function `_write_contract_artifacts` defined at `src/roadmap_tracks/fixed_point.py:63`. |
| 119 | `function` | `_write_sheaf_owned_artifacts` | inventory fallback | Inventory fallback for function `_write_sheaf_owned_artifacts` defined at `src/roadmap_tracks/fixed_point.py:119`. |
| 136 | `function` | `_fingerprint` | inventory fallback | Inventory fallback for function `_fingerprint` defined at `src/roadmap_tracks/fixed_point.py:136`. |
| 165 | `function` | `_validate_fixed_point` | inventory fallback | Inventory fallback for function `_validate_fixed_point` defined at `src/roadmap_tracks/fixed_point.py:165`. |
| 179 | `function` | `_source_contract_issues` | docstring | Return source defects that generated-artifact settlement cannot repair. |
| 194 | `function` | `_existing_fixed_point_paths` | inventory fallback | Inventory fallback for function `_existing_fixed_point_paths` defined at `src/roadmap_tracks/fixed_point.py:194`. |
| 210 | `function` | `_write_fixed_point_pass` | inventory fallback | Inventory fallback for function `_write_fixed_point_pass` defined at `src/roadmap_tracks/fixed_point.py:210`. |
| 230 | `function` | `_write_final_validation_pass` | docstring | Refresh self-referential reports and write the certificate from the final live state. |
| 248 | `function` | `run_semantic_fixed_point` | docstring | Settle manuscript, semantic, and contract artifacts to a validated fixed point. |

## `src/roadmap_tracks/formal_interop.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/formal_interop.py:17`. |
| 24 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/formal_interop.py:24`. |
| 30 | `function` | `_gnn_paths` | inventory fallback | Inventory fallback for function `_gnn_paths` defined at `src/roadmap_tracks/formal_interop.py:30`. |
| 34 | `function` | `_model_to_payload` | docstring | Structured, JSON-serializable view of a parsed GNN model (sorted, deterministic). |
| 56 | `function` | `_model_payload` | inventory fallback | Inventory fallback for function `_model_payload` defined at `src/roadmap_tracks/formal_interop.py:56`. |
| 60 | `function` | `_payload_to_gnn_text` | docstring | Serialize a model payload back to GNN markdown. |
| 100 | `function` | `roundtrip_payload_lossless` | docstring | True iff serializing the STRUCTURAL payload to GNN text and re-parsing reproduces it. |
| 118 | `function` | `build_model_checking_witnesses` | docstring | Build model checking witnesses. |
| 187 | `function` | `build_gnn_roundtrip_report` | docstring | Build gnn roundtrip report. |
| 210 | `function` | `build_gnn_lint_report` | docstring | Build gnn lint report. |
| 283 | `function` | `build_ontology_alias_index` | docstring | Build ontology alias index. |
| 306 | `function` | `build_ontology_profile_matrix` | docstring | Build ontology profile matrix. |
| 367 | `function` | `_lean_files` | inventory fallback | Inventory fallback for function `_lean_files` defined at `src/roadmap_tracks/formal_interop.py:367`. |
| 371 | `function` | `_lean_text` | inventory fallback | Inventory fallback for function `_lean_text` defined at `src/roadmap_tracks/formal_interop.py:371`. |
| 375 | `function` | `build_lean_theorem_inventory` | docstring | Build lean theorem inventory. |
| 397 | `function` | `build_lean_graph_world_inventory` | docstring | Build lean graph world inventory. |
| 439 | `function` | `build_interop_roundtrip_report` | docstring | Build interop roundtrip report. |
| 465 | `function` | `_leading_tactic` | docstring | First tactic identifier in a proof body (after ``:= by``), skipping blanks/comments. |
| 477 | `function` | `build_proof_extraction_index` | docstring | Build proof extraction index. |
| 516 | `function` | `_formal_interop_artifact_builders` | docstring | Return the single registry for formal-interoperability output builders. |
| 548 | `function` | `write_formal_interop_artifacts` | docstring | Write all formal-interop artifacts, or only missing outputs when requested. |
| 559 | `function` | `validate_formal_interop_artifacts` | docstring | Validate formal interop artifacts. |

## `src/roadmap_tracks/integration_audit.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 93 | `function` | `write_manuscript_staleness_report` | docstring | Write the hydrated-manuscript staleness report. |
| 113 | `function` | `write_integration_audit_artifacts` | docstring | Write integration audit artifacts to the output path. |
| 201 | `function` | `validate_integration_audit_artifacts` | docstring | Validate integration audit artifacts. |

## `src/roadmap_tracks/integration_audit_artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 104 | `function` | `_blocked_scope_match` | inventory fallback | Inventory fallback for function `_blocked_scope_match` defined at `src/roadmap_tracks/integration_audit_artifacts.py:104`. |
| 112 | `function` | `_blocked_scope_negated` | inventory fallback | Inventory fallback for function `_blocked_scope_negated` defined at `src/roadmap_tracks/integration_audit_artifacts.py:112`. |
| 120 | `function` | `build_artifact_diffoscope` | docstring | Build artifact diffoscope. |
| 151 | `function` | `build_artifact_license_audit` | docstring | Build artifact license audit. |
| 179 | `function` | `build_release_notes_evidence` | docstring | Build release notes evidence. |
| 217 | `function` | `build_scope_boundary_audit` | docstring | Audit manuscript scope language against toy-only and blocked-context contracts. |
| 331 | `function` | `build_manuscript_evidence_tables` | docstring | Build manuscript evidence tables. |
| 482 | `function` | `build_adversarial_audit` | docstring | Build adversarial audit. |
| 489 | `function` | `build_integration_semantic_snapshot` | docstring | Build integration semantic snapshot. |

## `src/roadmap_tracks/integration_audit_builders.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 29 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/integration_audit_builders.py:29`. |
| 37 | `function` | `_analysis_scripts` | inventory fallback | Inventory fallback for function `_analysis_scripts` defined at `src/roadmap_tracks/integration_audit_builders.py:37`. |
| 42 | `function` | `build_integration_dependency_graph` | docstring | Build integration dependency graph. |
| 78 | `function` | `build_producer_completeness` | docstring | Build producer completeness. |
| 100 | `function` | `build_stale_artifact_report` | docstring | Build stale artifact report. |
| 127 | `function` | `build_cross_track_symbol_table` | docstring | Build cross track symbol table. |
| 267 | `function` | `build_manuscript_token_provenance` | docstring | Build manuscript token provenance. |
| 337 | `function` | `_expected_token_value` | inventory fallback | Inventory fallback for function `_expected_token_value` defined at `src/roadmap_tracks/integration_audit_builders.py:337`. |
| 350 | `function` | `build_manuscript_staleness_report` | docstring | Compare hydrated manuscript tokens against the current generated variables. |
| 413 | `function` | `build_claim_evidence_audit` | docstring | Build claim evidence audit. |
| 440 | `function` | `build_validation_gate_index` | docstring | Build validation gate index. |
| 444 | `function` | `build_validation_gate_index.gate` | docstring | Process gate. |

## `src/roadmap_tracks/integration_audit_figures.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `build_figure_source_map` | docstring | Map rendered figures to source artifacts, section bindings, and claim lanes. |
| 137 | `function` | `build_figure_hash_manifest` | docstring | Build figure hash manifest. |

## `src/roadmap_tracks/integration_audit_lanes.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 112 | `function` | `allowed_claim_lanes` | docstring | Return the stable figure/scope lane vocabulary used by validators. |
| 117 | `function` | `_lane_from_source` | inventory fallback | Inventory fallback for function `_lane_from_source` defined at `src/roadmap_tracks/integration_audit_lanes.py:117`. |
| 125 | `function` | `manifest_tracks_by_section` | docstring | Return sheaf track ids keyed by manuscript section id. |
| 137 | `function` | `figure_claim_lanes` | docstring | Derive claim lanes from source artifacts, sheaf tracks, and evidence role. |
| 149 | `function` | `claim_lane_summary` | docstring | Summarize per-figure claim lanes in a validation-friendly shape. |

## `src/roadmap_tracks/row_aggregates.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `rows` | docstring | Return a payload row list with a stable empty-list fallback. |
| 18 | `function` | `all_rows` | docstring | True only when the payload has rows and every row satisfies ``predicate``. |
| 24 | `function` | `all_field_present` | docstring | True iff every row has truthy values for all requested fields. |

## `src/roadmap_tracks/scholarship.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 249 | `function` | `_load_yaml` | inventory fallback | Inventory fallback for function `_load_yaml` defined at `src/roadmap_tracks/scholarship.py:249`. |
| 256 | `function` | `_bib_entries` | inventory fallback | Inventory fallback for function `_bib_entries` defined at `src/roadmap_tracks/scholarship.py:256`. |
| 265 | `function` | `_citation_present` | inventory fallback | Inventory fallback for function `_citation_present` defined at `src/roadmap_tracks/scholarship.py:265`. |
| 269 | `function` | `_section_id_from_path` | inventory fallback | Inventory fallback for function `_section_id_from_path` defined at `src/roadmap_tracks/scholarship.py:269`. |
| 278 | `function` | `_manuscript_section_files` | docstring | Read every manuscript section markdown file once: ``(section_id, text)`` pairs. |
| 298 | `function` | `_citation_sections` | inventory fallback | Inventory fallback for function `_citation_sections` defined at `src/roadmap_tracks/scholarship.py:298`. |
| 304 | `function` | `_registry_tracks` | inventory fallback | Inventory fallback for function `_registry_tracks` defined at `src/roadmap_tracks/scholarship.py:304`. |
| 309 | `function` | `_manifest_sections` | inventory fallback | Inventory fallback for function `_manifest_sections` defined at `src/roadmap_tracks/scholarship.py:309`. |
| 314 | `function` | `_has_locator` | inventory fallback | Inventory fallback for function `_has_locator` defined at `src/roadmap_tracks/scholarship.py:314`. |
| 319 | `function` | `_locator_kind` | inventory fallback | Inventory fallback for function `_locator_kind` defined at `src/roadmap_tracks/scholarship.py:319`. |
| 332 | `function` | `_scope_guarded` | inventory fallback | Inventory fallback for function `_scope_guarded` defined at `src/roadmap_tracks/scholarship.py:332`. |
| 338 | `function` | `_row_key` | inventory fallback | Inventory fallback for function `_row_key` defined at `src/roadmap_tracks/scholarship.py:338`. |
| 342 | `function` | `build_scholarship_source_matrix` | docstring | Build the literature-to-method traceability matrix. |
| 430 | `function` | `write_scholarship_source_matrix` | docstring | Write the source-backed scholarship matrix. |
| 438 | `function` | `validate_scholarship_source_matrix` | docstring | Validate the saved scholarship-source matrix against its row evidence. |

## `src/roadmap_tracks/security.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 194 | `function` | `_scan_paths` | inventory fallback | Inventory fallback for function `_scan_paths` defined at `src/roadmap_tracks/security.py:194`. |
| 203 | `function` | `_scan_secret_patterns` | inventory fallback | Inventory fallback for function `_scan_secret_patterns` defined at `src/roadmap_tracks/security.py:203`. |
| 223 | `function` | `_artifact_present` | inventory fallback | Inventory fallback for function `_artifact_present` defined at `src/roadmap_tracks/security.py:223`. |
| 229 | `function` | `_control_row` | inventory fallback | Inventory fallback for function `_control_row` defined at `src/roadmap_tracks/security.py:229`. |
| 257 | `function` | `build_security_posture_audit` | docstring | Build the APT/supply-chain posture matrix from live local evidence. |
| 291 | `function` | `write_security_posture_audit` | docstring | Write the deterministic security posture audit report. |
| 302 | `function` | `_row_key` | inventory fallback | Inventory fallback for function `_row_key` defined at `src/roadmap_tracks/security.py:302`. |
| 306 | `function` | `validate_security_posture_audit` | docstring | Validate the saved security posture audit against live evidence. |

## `src/roadmap_tracks/sheaf_track_validation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `_all_rows` | inventory fallback | Inventory fallback for function `_all_rows` defined at `src/roadmap_tracks/sheaf_track_validation.py:13`. |
| 17 | `function` | `_all_rows_absent` | inventory fallback | Inventory fallback for function `_all_rows_absent` defined at `src/roadmap_tracks/sheaf_track_validation.py:17`. |
| 21 | `function` | `_append_schema_issue` | inventory fallback | Inventory fallback for function `_append_schema_issue` defined at `src/roadmap_tracks/sheaf_track_validation.py:21`. |
| 26 | `function` | `_append_summary_issue` | inventory fallback | Inventory fallback for function `_append_summary_issue` defined at `src/roadmap_tracks/sheaf_track_validation.py:26`. |
| 31 | `function` | `_coerce_int` | inventory fallback | Inventory fallback for function `_coerce_int` defined at `src/roadmap_tracks/sheaf_track_validation.py:31`. |
| 43 | `function` | `_semantic_restriction_value_ok` | inventory fallback | Inventory fallback for function `_semantic_restriction_value_ok` defined at `src/roadmap_tracks/sheaf_track_validation.py:43`. |
| 57 | `function` | `_validate_registry_contract` | inventory fallback | Inventory fallback for function `_validate_registry_contract` defined at `src/roadmap_tracks/sheaf_track_validation.py:57`. |
| 74 | `function` | `validate_sheaf_track_source_contract` | docstring | Validate source-side sheaf contracts without regenerating artifacts. |
| 96 | `function` | `_validate_saved_semantic_certificate` | inventory fallback | Inventory fallback for function `_validate_saved_semantic_certificate` defined at `src/roadmap_tracks/sheaf_track_validation.py:96`. |
| 139 | `function` | `validate_sheaf_track_artifacts` | docstring | Validate canonical sheaf-track artifacts and their semantic certificate. |

## `src/roadmap_tracks/sheaf_tracks_builders_formal.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `build_counterexample_matrix` | docstring | Build counterexample matrix. |
| 87 | `function` | `build_model_checking_witnesses` | docstring | Build model checking witnesses. |
| 145 | `function` | `build_interop_roundtrip_report` | docstring | Build interop roundtrip report. |
| 181 | `function` | `build_adversarial_audit` | docstring | Build adversarial audit. |
| 213 | `function` | `build_blocked_scope_manifest` | docstring | Describe out-of-scope research capabilities and the artifacts needed to unblock them. |

## `src/roadmap_tracks/sheaf_tracks_builders_graph.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 43 | `function` | `_track_artifact` | inventory fallback | Inventory fallback for function `_track_artifact` defined at `src/roadmap_tracks/sheaf_tracks_builders_graph.py:43`. |
| 75 | `function` | `_pipeline_sheaf_tracks` | inventory fallback | Inventory fallback for function `_pipeline_sheaf_tracks` defined at `src/roadmap_tracks/sheaf_tracks_builders_graph.py:75`. |
| 85 | `function` | `build_track_lane_matrix` | docstring | Map every pipeline track to sheaf fragments, producers, artifacts, gates, and consumers. |
| 176 | `function` | `_artifact_contract_cycle_excluded` | inventory fallback | Inventory fallback for function `_artifact_contract_cycle_excluded` defined at `src/roadmap_tracks/sheaf_tracks_builders_graph.py:176`. |
| 194 | `function` | `_artifact_contract_track_maps` | inventory fallback | Inventory fallback for function `_artifact_contract_track_maps` defined at `src/roadmap_tracks/sheaf_tracks_builders_graph.py:194`. |
| 214 | `function` | `build_artifact_contract_index` | docstring | Index artifact producers, consumers, validators, freshness, and copy parity. |
| 311 | `function` | `build_track_improvement_scope` | docstring | Build track improvement scope. |
| 402 | `function` | `build_validation_dependency_graph` | docstring | Build validation dependency graph. |

## `src/roadmap_tracks/sheaf_tracks_builders_provenance.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 20 | `function` | `build_artifact_provenance` | docstring | Build canonical artifact, field-provenance, and bundle provenance rows. |
| 83 | `function` | `_artifact_bundles` | inventory fallback | Inventory fallback for function `_artifact_bundles` defined at `src/roadmap_tracks/sheaf_tracks_builders_provenance.py:83`. |
| 166 | `function` | `build_replay_matrix` | docstring | Build replay matrix. |

## `src/roadmap_tracks/sheaf_tracks_builders_release.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `_field_value` | inventory fallback | Inventory fallback for function `_field_value` defined at `src/roadmap_tracks/sheaf_tracks_builders_release.py:21`. |
| 31 | `function` | `build_evidence_field_index` | docstring | Build evidence field index. |
| 84 | `function` | `build_release_bundle_manifest` | docstring | Build release bundle manifest. |
| 155 | `function` | `build_theorem_traceability_matrix` | docstring | Build theorem traceability matrix. |

## `src/roadmap_tracks/sheaf_tracks_builders_toy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `build_sensitivity_sweep` | docstring | Build sensitivity sweep. |
| 87 | `function` | `build_uncertainty_summary` | docstring | Build uncertainty summary. |

## `src/roadmap_tracks/sheaf_tracks_context.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `class` | `_ProvenanceContext` | inventory fallback | Inventory fallback for class `_ProvenanceContext` defined at `src/roadmap_tracks/sheaf_tracks_context.py:12`. |
| 21 | `function` | `_provenance_context` | inventory fallback | Inventory fallback for function `_provenance_context` defined at `src/roadmap_tracks/sheaf_tracks_context.py:21`. |

## `src/roadmap_tracks/sheaf_tracks_helpers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_entropy` | inventory fallback | Inventory fallback for function `_entropy` defined at `src/roadmap_tracks/sheaf_tracks_helpers.py:18`. |
| 24 | `function` | `_root_output_dir` | inventory fallback | Inventory fallback for function `_root_output_dir` defined at `src/roadmap_tracks/sheaf_tracks_helpers.py:24`. |
| 32 | `function` | `_portable_repo_path` | docstring | Represent repository-local paths without embedding a developer home directory. |
| 43 | `function` | `_copied_parity` | inventory fallback | Inventory fallback for function `_copied_parity` defined at `src/roadmap_tracks/sheaf_tracks_helpers.py:43`. |
| 92 | `function` | `_remove_legacy_artifacts` | inventory fallback | Inventory fallback for function `_remove_legacy_artifacts` defined at `src/roadmap_tracks/sheaf_tracks_helpers.py:92`. |
| 99 | `function` | `_refresh_hydrated_manuscript` | inventory fallback | Inventory fallback for function `_refresh_hydrated_manuscript` defined at `src/roadmap_tracks/sheaf_tracks_helpers.py:99`. |
| 105 | `function` | `_canonical_artifact_rows` | inventory fallback | Inventory fallback for function `_canonical_artifact_rows` defined at `src/roadmap_tracks/sheaf_tracks_helpers.py:105`. |

## `src/roadmap_tracks/sheaf_tracks_io.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 22 | `function` | `_parse_yaml_cached` | docstring | Parse a YAML file, memoized on (path, mtime, size). |
| 36 | `function` | `_load_yaml` | inventory fallback | Inventory fallback for function `_load_yaml` defined at `src/roadmap_tracks/sheaf_tracks_io.py:36`. |
| 46 | `function` | `_load_structured` | inventory fallback | Inventory fallback for function `_load_structured` defined at `src/roadmap_tracks/sheaf_tracks_io.py:46`. |
| 55 | `function` | `_bridge_reference_section_status` | inventory fallback | Inventory fallback for function `_bridge_reference_section_status` defined at `src/roadmap_tracks/sheaf_tracks_io.py:55`. |
| 65 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/sheaf_tracks_io.py:65`. |
| 75 | `function` | `_analysis_scripts` | inventory fallback | Inventory fallback for function `_analysis_scripts` defined at `src/roadmap_tracks/sheaf_tracks_io.py:75`. |
| 80 | `function` | `_registry_tracks` | inventory fallback | Inventory fallback for function `_registry_tracks` defined at `src/roadmap_tracks/sheaf_tracks_io.py:80`. |
| 86 | `function` | `_manifest_sections` | inventory fallback | Inventory fallback for function `_manifest_sections` defined at `src/roadmap_tracks/sheaf_tracks_io.py:86`. |
| 92 | `function` | `_bound_tracks` | inventory fallback | Inventory fallback for function `_bound_tracks` defined at `src/roadmap_tracks/sheaf_tracks_io.py:92`. |
| 104 | `function` | `_pipeline_tracks` | inventory fallback | Inventory fallback for function `_pipeline_tracks` defined at `src/roadmap_tracks/sheaf_tracks_io.py:104`. |
| 110 | `function` | `_claim_records` | inventory fallback | Inventory fallback for function `_claim_records` defined at `src/roadmap_tracks/sheaf_tracks_io.py:110`. |
| 116 | `function` | `_claim_ids_by_path` | inventory fallback | Inventory fallback for function `_claim_ids_by_path` defined at `src/roadmap_tracks/sheaf_tracks_io.py:116`. |
| 126 | `function` | `_claim_ids_by_track` | inventory fallback | Inventory fallback for function `_claim_ids_by_track` defined at `src/roadmap_tracks/sheaf_tracks_io.py:126`. |
| 135 | `function` | `_artifact_maps` | inventory fallback | Inventory fallback for function `_artifact_maps` defined at `src/roadmap_tracks/sheaf_tracks_io.py:135`. |
| 141 | `function` | `_source_commit` | inventory fallback | Inventory fallback for function `_source_commit` defined at `src/roadmap_tracks/sheaf_tracks_io.py:141`. |
| 155 | `function` | `_deterministic_seed` | inventory fallback | Inventory fallback for function `_deterministic_seed` defined at `src/roadmap_tracks/sheaf_tracks_io.py:155`. |
| 160 | `function` | `_config_digest` | inventory fallback | Inventory fallback for function `_config_digest` defined at `src/roadmap_tracks/sheaf_tracks_io.py:160`. |

## `src/roadmap_tracks/sheaf_tracks_restrictions.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_canonical_restrictions` | inventory fallback | Inventory fallback for function `_canonical_restrictions` defined at `src/roadmap_tracks/sheaf_tracks_restrictions.py:18`. |

## `src/roadmap_tracks/sheaf_tracks_write.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 36 | `function` | `_run_prerequisite_promoters` | inventory fallback | Inventory fallback for function `_run_prerequisite_promoters` defined at `src/roadmap_tracks/sheaf_tracks_write.py:36`. |
| 51 | `function` | `_record_external_artifact_paths` | inventory fallback | Inventory fallback for function `_record_external_artifact_paths` defined at `src/roadmap_tracks/sheaf_tracks_write.py:51`. |
| 60 | `function` | `_write_primary_canonical_artifacts` | inventory fallback | Inventory fallback for function `_write_primary_canonical_artifacts` defined at `src/roadmap_tracks/sheaf_tracks_write.py:60`. |
| 113 | `function` | `_write_integration_audit_phase` | inventory fallback | Inventory fallback for function `_write_integration_audit_phase` defined at `src/roadmap_tracks/sheaf_tracks_write.py:113`. |
| 123 | `function` | `_write_post_audit_canonical_artifacts` | inventory fallback | Inventory fallback for function `_write_post_audit_canonical_artifacts` defined at `src/roadmap_tracks/sheaf_tracks_write.py:123`. |
| 166 | `function` | `_write_semantic_artifacts` | inventory fallback | Inventory fallback for function `_write_semantic_artifacts` defined at `src/roadmap_tracks/sheaf_tracks_write.py:166`. |
| 179 | `function` | `_write_supplemental_phase` | inventory fallback | Inventory fallback for function `_write_supplemental_phase` defined at `src/roadmap_tracks/sheaf_tracks_write.py:179`. |
| 185 | `function` | `_write_final_canonical_pass` | inventory fallback | Inventory fallback for function `_write_final_canonical_pass` defined at `src/roadmap_tracks/sheaf_tracks_write.py:185`. |
| 260 | `function` | `write_sheaf_track_artifacts` | docstring | Write the canonical promoted sheaf artifacts in deterministic phases. |

## `src/roadmap_tracks/supplemental.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 28 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/supplemental.py:28`. |
| 38 | `function` | `_statement_symbols` | docstring | Extract stable statement identifiers from a Lean theorem statement. |
| 58 | `function` | `build_proof_dependency_graph` | docstring | Build theorem-to-source, theorem-to-symbol, and theorem-to-witness edges. |
| 110 | `function` | `_graph_world_transition_rows` | inventory fallback | Inventory fallback for function `_graph_world_transition_rows` defined at `src/roadmap_tracks/supplemental.py:110`. |
| 144 | `function` | `_tmaze_transition_rows` | inventory fallback | Inventory fallback for function `_tmaze_transition_rows` defined at `src/roadmap_tracks/supplemental.py:144`. |
| 169 | `function` | `build_state_transition_table` | docstring | Build explicit finite transition rows for graph-world topologies and T-maze actions. |
| 192 | `function` | `build_ablation_sensitivity_report` | docstring | Join causal-ablation effects to sensitivity and uncertainty source rows. |
| 238 | `function` | `build_release_attestation` | docstring | Attest release bundle, validation, license, and blocked-scope status. |
| 343 | `function` | `write_supplemental_artifacts` | docstring | Write all supplemental canonical sheaf artifacts. |
| 366 | `function` | `validate_supplemental_artifacts` | docstring | Validate supplemental artifacts from row-derived conditions. |

## `src/roadmap_tracks/toy_sweep.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 77 | `function` | `write_toy_sweep_artifacts` | docstring | Write toy sweep artifacts to the output path. |
| 123 | `function` | `validate_toy_sweep_artifacts` | docstring | Validate toy sweep artifacts. |

## `src/roadmap_tracks/toy_sweep_builders.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 26 | `function` | `build_analytical_observable_sweep` | docstring | Build analytical observable sweep. |
| 83 | `function` | `build_analytical_assumption_index` | docstring | Index the finite-model assumptions behind the analytical equations. |
| 200 | `function` | `build_sensitivity_sweep` | docstring | Build sensitivity sweep. |
| 231 | `function` | `build_uncertainty_summary` | docstring | Build uncertainty summary. |
| 261 | `function` | `build_toy_benchmark_matrix` | docstring | Build toy benchmark matrix. |
| 300 | `function` | `build_policy_grid` | docstring | Build policy grid. |
| 331 | `function` | `build_efe_terms` | docstring | Build efe terms. |
| 371 | `function` | `_topology_trace` | inventory fallback | Inventory fallback for function `_topology_trace` defined at `src/roadmap_tracks/toy_sweep_builders.py:371`. |
| 386 | `function` | `build_graph_world_topology_sweep` | docstring | Build graph world topology sweep. |
| 410 | `function` | `build_graph_world_topology_traces` | docstring | Build graph world topology traces. |
| 434 | `function` | `_graph_world_trace_invariants` | docstring | Compute the three finite invariants from an actual topology trace (not hardcoded). |
| 463 | `function` | `build_graph_world_invariants` | docstring | Build graph world invariants. |
| 479 | `function` | `build_state_space_catalog` | docstring | Build state space catalog. |
| 525 | `function` | `build_causal_ablation_matrix` | docstring | Build causal ablation matrix. |

## `src/roadmap_tracks/toy_sweep_helpers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `function` | `_same_state_probability` | inventory fallback | Inventory fallback for function `_same_state_probability` defined at `src/roadmap_tracks/toy_sweep_helpers.py:10`. |
| 15 | `function` | `_posterior_correlation` | inventory fallback | Inventory fallback for function `_posterior_correlation` defined at `src/roadmap_tracks/toy_sweep_helpers.py:15`. |
| 20 | `function` | `_joint_entropy` | inventory fallback | Inventory fallback for function `_joint_entropy` defined at `src/roadmap_tracks/toy_sweep_helpers.py:20`. |
| 25 | `function` | `_marginal_entropy` | inventory fallback | Inventory fallback for function `_marginal_entropy` defined at `src/roadmap_tracks/toy_sweep_helpers.py:25`. |

## `src/roadmap_tracks/visualization_audit.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 46 | `function` | `_word_count` | inventory fallback | Inventory fallback for function `_word_count` defined at `src/roadmap_tracks/visualization_audit.py:46`. |
| 50 | `function` | `_image_metrics` | inventory fallback | Inventory fallback for function `_image_metrics` defined at `src/roadmap_tracks/visualization_audit.py:50`. |
| 65 | `function` | `_statistical_sources` | inventory fallback | Inventory fallback for function `_statistical_sources` defined at `src/roadmap_tracks/visualization_audit.py:65`. |
| 70 | `function` | `_all_sources_present` | inventory fallback | Inventory fallback for function `_all_sources_present` defined at `src/roadmap_tracks/visualization_audit.py:70`. |
| 74 | `function` | `_figure_section_bindings` | inventory fallback | Inventory fallback for function `_figure_section_bindings` defined at `src/roadmap_tracks/visualization_audit.py:74`. |
| 93 | `function` | `_section_id_from_path` | inventory fallback | Inventory fallback for function `_section_id_from_path` defined at `src/roadmap_tracks/visualization_audit.py:93`. |
| 103 | `function` | `_imrad_section_files` | docstring | Read every IMRaD manuscript markdown file once: ``(section_id, text)`` pairs. |
| 124 | `function` | `_figure_reference_sections` | inventory fallback | Inventory fallback for function `_figure_reference_sections` defined at `src/roadmap_tracks/visualization_audit.py:124`. |
| 131 | `function` | `_manifest_section_tracks` | inventory fallback | Inventory fallback for function `_manifest_section_tracks` defined at `src/roadmap_tracks/visualization_audit.py:131`. |
| 149 | `function` | `_reference_section_status` | inventory fallback | Inventory fallback for function `_reference_section_status` defined at `src/roadmap_tracks/visualization_audit.py:149`. |
| 159 | `function` | `_figure_evidence_rows` | docstring | Derive live figure evidence rows from registry, source maps, hashes, and renders. |
| 247 | `function` | `build_visualization_quality_audit` | docstring | Build figure accessibility, source, hash, and render-readiness rows. |
| 293 | `function` | `write_visualization_quality_audit` | docstring | Write the deterministic visualization-quality audit report. |
| 304 | `function` | `build_statistical_visualization_bridge` | docstring | Build the crosswalk from statistical figure rows to scholarship and sheaf bindings. |
| 404 | `function` | `write_statistical_visualization_bridge` | docstring | Write the statistical-visualization scholarship/sheaf crosswalk. |
| 415 | `function` | `validate_visualization_quality_audit` | docstring | Validate the saved visualization-quality audit against its row evidence. |
| 588 | `function` | `validate_statistical_visualization_bridge` | docstring | Validate the saved statistical visualization crosswalk against row evidence. |

## `src/roadmap_tracks/visualization_contract.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 61 | `function` | `_visualization_source_files` | inventory fallback | Inventory fallback for function `_visualization_source_files` defined at `src/roadmap_tracks/visualization_contract.py:61`. |
| 65 | `function` | `build_style_contract` | docstring | Build a live typography-token and source-literal contract. |
| 110 | `function` | `build_auxiliary_visualization_inventory` | docstring | Inventory visual files intentionally outside the numbered figure registry. |

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
| 217 | `function` | `CueAdvantage.to_dict` | docstring | Serialize this object to a plain dict for JSON output. |
| 231 | `function` | `compare_cue_vs_greedy` | docstring | Closed-form comparison proving epistemic cue-sampling is strictly necessary. |
| 252 | `function` | `cue_advantage_summary` | docstring | JSON-ready summary for the manuscript / figure / claim ledger. |

## `src/simulation/dirichlet_learning.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 45 | `class` | `DirichletLearningResult` | docstring | Trajectory of a deterministic Dirichlet likelihood-learning run. |
| 61 | `function` | `DirichletLearningResult.final_kl` | docstring | Process final kl. |
| 66 | `function` | `DirichletLearningResult.initial_kl` | docstring | Process initial kl. |
| 71 | `function` | `DirichletLearningResult.is_monotone_decreasing` | docstring | Check whether monotone decreasing. |
| 78 | `function` | `DirichletLearningResult.steps_to_converge` | docstring | First update step whose KL is below ``CONVERGENCE_KL_ATOL``. |
| 90 | `function` | `DirichletLearningResult.to_dict` | docstring | Serialize this object to a plain dict for JSON output. |
| 109 | `function` | `_true_likelihood` | docstring | Extract the (n_o, n_s) likelihood A from a (possibly list-wrapped) model. |
| 116 | `function` | `expected_likelihood` | docstring | Expected likelihood ``E[A] = pA / sum_o(pA)`` (column-normalised). |
| 123 | `function` | `_kl_columns` | docstring | ``sum_s KL(true_a[:, s] \|\| learned_a[:, s])`` in nats. |
| 139 | `function` | `learn_likelihood` | docstring | Deterministically learn ``A`` via Dirichlet concentration updates. |
| 184 | `function` | `summarize_learning` | docstring | JSON-ready summary used by figures, tokens, and the claim ledger. |

## `src/simulation/efe_decomposition.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 49 | `class` | `EFETerms` | docstring | The four EFE terms for a single policy, summed over the horizon. |
| 63 | `function` | `EFETerms.total` | docstring | Expected Free Energy G(pi) = risk + ambiguity. |
| 68 | `function` | `EFETerms.identity_residual` | docstring | ``(risk + ambiguity) + pragmatic_value + epistemic_value`` (== 0 when valid). |
| 73 | `function` | `EFETerms.identity_holds` | docstring | Process identity holds. |
| 77 | `function` | `EFETerms.to_dict` | docstring | Serialize this object to a plain dict for JSON output. |
| 90 | `function` | `_as_2d` | inventory fallback | Inventory fallback for function `_as_2d` defined at `src/simulation/efe_decomposition.py:90`. |
| 94 | `function` | `softmax_preference` | docstring | Preferred-outcome distribution ``p(o) = softmax(C)`` from log-preferences. |
| 102 | `function` | `_entropy` | docstring | Shannon entropy in nats, ignoring zero-probability outcomes. |
| 109 | `function` | `_kl_divergence` | docstring | KL(q \|\| p) in nats; +inf where q has support that p does not. |
| 123 | `function` | `_first_factor` | inventory fallback | Inventory fallback for function `_first_factor` defined at `src/simulation/efe_decomposition.py:123`. |
| 130 | `function` | `decompose_policy_efe` | docstring | Closed-form EFE term decomposition for one policy (action sequence). |
| 170 | `function` | `enumerate_policies` | docstring | All deterministic action sequences of length ``policy_len``. |
| 175 | `function` | `decompose_all_policies` | docstring | Decompose every length-``policy_len`` policy and summarise the result. |

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
| 31 | `function` | `inv_belief_entropy_finite` | docstring | Process inv belief entropy finite. |
| 38 | `function` | `inv_actions_length_matches_steps` | docstring | Process inv actions length matches steps. |
| 46 | `function` | `inv_observations_in_obs_space` | docstring | Process inv observations in obs space. |
| 55 | `function` | `inv_policy_len_matches_config` | docstring | Process inv policy len matches config. |
| 63 | `function` | `inv_goal_reached` | docstring | Process inv goal reached. |
| 75 | `function` | `inv_trace_step_count_matches_summary` | docstring | Process inv trace step count matches summary. |
| 92 | `function` | `run_simulation_invariants` | docstring | Run simulation invariants. |
| 98 | `function` | `build_merged_invariants_payload` | docstring | Single SSOT for merged analytical + simulation invariant reports. |
| 128 | `function` | `write_simulation_invariants` | docstring | Write simulation invariants to the output path. |
| 139 | `function` | `merge_simulation_into_invariants_report` | docstring | Process merge simulation into invariants report. |

## `src/simulation/logging_utils.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 24 | `function` | `_now_iso` | inventory fallback | Inventory fallback for function `_now_iso` defined at `src/simulation/logging_utils.py:24`. |
| 28 | `function` | `_json_default` | inventory fallback | Inventory fallback for function `_json_default` defined at `src/simulation/logging_utils.py:28`. |
| 34 | `function` | `validate_record` | docstring | Validate record. |
| 46 | `class` | `RunLogger` | docstring | Data container for RunLogger. |
| 52 | `function` | `RunLogger.__post_init__` | inventory fallback | Inventory fallback for function `RunLogger.__post_init__` defined at `src/simulation/logging_utils.py:52`. |
| 58 | `function` | `RunLogger.from_project_root` | docstring | Process from project root. |
| 70 | `function` | `RunLogger.fresh` | docstring | Process fresh. |
| 76 | `function` | `RunLogger.emit` | docstring | Process emit. |
| 86 | `function` | `RunLogger.emit_run_header` | docstring | Process emit run header. |
| 106 | `function` | `RunLogger.timed` | docstring | Process timed. |
| 116 | `function` | `RunLogger.records` | docstring | Process records. |
| 126 | `function` | `RunLogger.step_records` | docstring | Process step records. |

## `src/simulation/precision_sweep.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 49 | `function` | `_softmax` | inventory fallback | Inventory fallback for function `_softmax` defined at `src/simulation/precision_sweep.py:49`. |
| 55 | `function` | `_entropy` | docstring | Shannon entropy in nats, ignoring zero-probability outcomes. |
| 63 | `class` | `PrecisionPoint` | docstring | Policy-posterior summary at one precision value. |
| 72 | `function` | `PrecisionPoint.to_dict` | docstring | Serialize this object to a plain dict for JSON output. |
| 83 | `function` | `gamma_grid` | docstring | Deterministic precision grid ``[0, gamma_max]`` with ``grid_points`` samples. |
| 91 | `function` | `posterior_at_gamma` | docstring | Policy posterior ``q(pi) = softmax(-gamma * G)`` for a fixed precision. |
| 97 | `function` | `sweep_precision` | docstring | Sweep precision over the policy posterior of ``model``. |

## `src/simulation/pymdp_config.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `class` | `TMazeConfig` | docstring | Data container for TMazeConfig. |
| 29 | `class` | `AgentConfig` | docstring | Data container for AgentConfig. |
| 37 | `class` | `LoggingConfig` | docstring | Data container for LoggingConfig. |
| 45 | `class` | `ComparisonConfig` | docstring | Data container for ComparisonConfig. |
| 54 | `class` | `PymdpConfig` | docstring | Data container for PymdpConfig. |
| 67 | `function` | `PymdpConfig.policy_len` | docstring | Process policy len. |
| 71 | `function` | `PymdpConfig.__post_init__` | docstring | Reject configurations the minimal two-state harness cannot execute. |
| 76 | `function` | `_coerce_mode` | inventory fallback | Inventory fallback for function `_coerce_mode` defined at `src/simulation/pymdp_config.py:76`. |
| 85 | `function` | `validate_pymdp_config` | docstring | Validate dimensions, numeric domains, and safe local output paths. |
| 133 | `function` | `_parse_raw` | inventory fallback | Inventory fallback for function `_parse_raw` defined at `src/simulation/pymdp_config.py:133`. |
| 172 | `function` | `default_pymdp_config` | docstring | Process default pymdp config. |
| 177 | `function` | `pymdp_config_path` | docstring | Process pymdp config path. |
| 182 | `function` | `load_pymdp_config` | docstring | Load pymdp config from a file. |
| 195 | `function` | `apply_pymdp_overrides` | docstring | Process apply pymdp overrides. |
| 220 | `function` | `config_snapshot` | docstring | Process config snapshot. |
| 251 | `function` | `config_hash` | docstring | Process config hash. |

## `src/simulation/pymdp_runtime.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 19 | `function` | `_package_version` | inventory fallback | Inventory fallback for function `_package_version` defined at `src/simulation/pymdp_runtime.py:19`. |
| 26 | `function` | `_backend_flags` | inventory fallback | Inventory fallback for function `_backend_flags` defined at `src/simulation/pymdp_runtime.py:26`. |
| 39 | `function` | `_numpy_factors` | inventory fallback | Inventory fallback for function `_numpy_factors` defined at `src/simulation/pymdp_runtime.py:39`. |
| 43 | `function` | `_warning_record` | inventory fallback | Inventory fallback for function `_warning_record` defined at `src/simulation/pymdp_runtime.py:43`. |
| 52 | `function` | `construct_agent_with_diagnostics` | docstring | Construct ``pymdp.Agent`` while capturing the one audited JAX warning. |
| 100 | `function` | `build_runtime_diagnostics` | docstring | Build runtime diagnostics. |
| 209 | `function` | `write_runtime_diagnostics` | docstring | Write runtime diagnostics to the output path. |
| 221 | `function` | `validate_runtime_diagnostics` | docstring | Validate runtime diagnostics. |

## `src/simulation/si_artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 31 | `function` | `quantize_replay_floats` | docstring | Round every float in a JSON-serializable payload to the replay grid. |
| 48 | `function` | `write_si_artifacts` | docstring | Write si artifacts to the output path. |
| 116 | `function` | `run_and_persist` | docstring | Run and persist. |
| 134 | `function` | `write_policy_comparison` | docstring | Write deterministic state-vs-policy comparison rows without changing main SI artifacts. |
| 253 | `function` | `write_policy_posterior_grid` | docstring | Write step-level PyMDP policy posterior normalization evidence. |

## `src/simulation/si_belief.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 8 | `function` | `marginal_state_belief` | docstring | Process marginal state belief. |
| 24 | `function` | `belief_entropy` | docstring | Process belief entropy. |
| 30 | `function` | `qs_marginal_state1` | docstring | Process qs marginal state1. |
| 38 | `function` | `state_inference_action` | docstring | Process state inference action. |
| 43 | `function` | `state_inference_next_obs` | docstring | Process state inference next obs. |

## `src/simulation/si_loop.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 29 | `function` | `pymdp_available` | docstring | Process pymdp available. |
| 40 | `class` | `SIRunResult` | docstring | Data container for SIRunResult. |
| 57 | `function` | `_normalise_sampling_distribution` | docstring | Return a finite non-negative probability vector or fail closed. |
| 70 | `function` | `sample_next_state` | docstring | Process sample next state. |
| 81 | `function` | `sample_observation` | docstring | Process sample observation. |
| 92 | `function` | `run_si_tmaze` | docstring | Run state or policy inference on the minimal T-maze harness. |

## `src/simulation/si_policy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `_normalise_policy_posterior` | docstring | Validate and normalize a pymdp policy posterior. |
| 34 | `function` | `_expected_utility_fallback` | docstring | Select an action from one-step expected utility when pymdp lacks policy inference. |
| 90 | `function` | `select_policy_action` | docstring | Return action, method label, selected EFE, selected policy index, and policy evidence. |

## `src/simulation/statistics.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `_adjacent_switch_count` | inventory fallback | Inventory fallback for function `_adjacent_switch_count` defined at `src/simulation/statistics.py:11`. |
| 15 | `function` | `_entropy_stats` | inventory fallback | Inventory fallback for function `_entropy_stats` defined at `src/simulation/statistics.py:15`. |
| 44 | `function` | `summarize_si_trace` | docstring | Process summarize si trace. |
| 74 | `function` | `load_si_artifacts` | docstring | Load si artifacts from a file. |

## `src/simulation/tmaze_model.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `class` | `TMazeSpec` | docstring | Data container for TMazeSpec. |
| 27 | `function` | `spec_from_config` | docstring | Process spec from config. |
| 41 | `function` | `build_tmaze_generative_model` | docstring | Return A, B, C, D for a 2-state start/goal POMDP (single factor). |

## `src/validation_spine/artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 70 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/validation_spine/artifacts.py:70`. |
| 81 | `function` | `_file_fingerprint` | inventory fallback | Inventory fallback for function `_file_fingerprint` defined at `src/validation_spine/artifacts.py:81`. |
| 94 | `function` | `_configured_analysis_scripts` | inventory fallback | Inventory fallback for function `_configured_analysis_scripts` defined at `src/validation_spine/artifacts.py:94`. |
| 104 | `function` | `_config_digest` | inventory fallback | Inventory fallback for function `_config_digest` defined at `src/validation_spine/artifacts.py:104`. |
| 116 | `function` | `_deterministic_seed` | inventory fallback | Inventory fallback for function `_deterministic_seed` defined at `src/validation_spine/artifacts.py:116`. |
| 127 | `function` | `_source_commit` | inventory fallback | Inventory fallback for function `_source_commit` defined at `src/validation_spine/artifacts.py:127`. |
| 141 | `function` | `_artifact_record` | inventory fallback | Inventory fallback for function `_artifact_record` defined at `src/validation_spine/artifacts.py:141`. |
| 165 | `function` | `_config_record` | inventory fallback | Inventory fallback for function `_config_record` defined at `src/validation_spine/artifacts.py:165`. |
| 175 | `function` | `build_artifact_provenance` | docstring | Build deterministic artifact lineage and hash records. |
| 213 | `function` | `_same_json` | inventory fallback | Inventory fallback for function `_same_json` defined at `src/validation_spine/artifacts.py:213`. |
| 219 | `function` | `_copy_replay_inputs` | inventory fallback | Inventory fallback for function `_copy_replay_inputs` defined at `src/validation_spine/artifacts.py:219`. |
| 228 | `function` | `build_reproducibility_replay` | docstring | Replay deterministic toy producers in a temporary tree and compare outputs. |
| 305 | `function` | `build_counterexample_matrix` | docstring | Document expected-failure fixtures that keep the gates falsifiable. |
| 404 | `function` | `write_validation_spine_artifacts` | docstring | Write provenance, replay, and counterexample artifacts. |
| 431 | `function` | `validate_artifact_provenance` | docstring | Validate artifact provenance. |
| 478 | `function` | `validate_reproducibility_replay` | docstring | Validate reproducibility replay. |
| 530 | `function` | `validate_counterexample_matrix` | docstring | Validate counterexample matrix. |
| 559 | `function` | `validate_validation_spine` | docstring | Return all validation-spine artifact issues. |

## `src/visualizations/animation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `_load_trace_steps` | inventory fallback | Inventory fallback for function `_load_trace_steps` defined at `src/visualizations/animation.py:14`. |
| 29 | `function` | `write_belief_trajectory_gif` | docstring | Write a deterministic multi-frame GIF from trace entropy/action state. |
| 67 | `function` | `_frame_sha256` | inventory fallback | Inventory fallback for function `_frame_sha256` defined at `src/visualizations/animation.py:67`. |
| 73 | `function` | `_perceptual_hash` | docstring | Return a deterministic 8x8 average hash for a frame. |
| 85 | `function` | `build_animation_frame_deltas` | docstring | Compute a deterministic manifest proving adjacent GIF frames change. |
| 155 | `function` | `write_animation_frame_deltas` | docstring | Write the frame-delta manifest for the deterministic animation track. |
| 164 | `function` | `_live_animation_contract` | inventory fallback | Inventory fallback for function `_live_animation_contract` defined at `src/visualizations/animation.py:164`. |
| 194 | `function` | `validate_animation_frame_deltas` | docstring | Return frame-delta manifest issues. |

## `src/visualizations/figure_helpers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 19 | `function` | `save_styled_figure` | docstring | Save styled figure to the output path. |
| 35 | `function` | `style_grid` | docstring | Process style grid. |
| 46 | `function` | `wrap_text` | docstring | Wrap labels for compact figure panels. |
| 51 | `function` | `add_note` | docstring | Add a small source/claim note in axes coordinates. |
| 74 | `function` | `configure_axis` | docstring | Apply the common publication axis treatment. |
| 105 | `function` | `text_box` | docstring | Draw a wrapped labeled box in axes/data coordinates. |
| 135 | `function` | `draw_column_headers` | docstring | Draw aligned column headers for flow/table figures. |
| 143 | `function` | `draw_arrow` | docstring | Draw a compact left-to-right flow arrow. |
| 157 | `function` | `load_json_artifact` | docstring | Load a JSON artifact by project-relative path. |
| 166 | `function` | `add_value_labels` | docstring | Label vertical bars without changing axes limits too aggressively. |
| 183 | `function` | `styled_figure` | docstring | Load style, resolve output path, and apply matplotlib rc context. |

## `src/visualizations/figure_io.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `_normalize_rgb_extrema` | inventory fallback | Inventory fallback for function `_normalize_rgb_extrema` defined at `src/visualizations/figure_io.py:15`. |
| 24 | `function` | `image_render_metrics` | docstring | Return deterministic live PNG metrics used by render validators. |
| 65 | `function` | `save_figure_png` | docstring | Save a figure to PNG and optionally normalize to RGB for PDF pipelines. |

## `src/visualizations/figure_registry.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 19 | `class` | `FigureSpec` | docstring | Data container for FigureSpec. |
| 33 | `class` | `SectionFigureRef` | docstring | Data container for SectionFigureRef. |
| 42 | `function` | `_figures_yaml_path` | inventory fallback | Inventory fallback for function `_figures_yaml_path` defined at `src/visualizations/figure_registry.py:42`. |
| 46 | `function` | `_load_figures_yaml` | inventory fallback | Inventory fallback for function `_load_figures_yaml` defined at `src/visualizations/figure_registry.py:46`. |
| 53 | `function` | `load_figure_registry` | docstring | Load figure registry from a file. |
| 78 | `function` | `load_section_figures` | docstring | Load section figures from a file. |
| 103 | `function` | `figure_output_path` | docstring | Process figure output path. |
| 109 | `function` | `render_figure_markdown` | docstring | Render figure markdown. |
| 146 | `function` | `render_section_figures` | docstring | Render section figures. |
| 170 | `function` | `build_figure_registry_payload` | docstring | Build validator-facing registry JSON keyed by ``fig:{id}`` labels. |
| 191 | `function` | `write_figure_registry_json` | docstring | Write ``output/figures/figure_registry.json`` from ``figures.yaml``. |

## `src/visualizations/figure_style.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `_safe_float` | inventory fallback | Inventory fallback for function `_safe_float` defined at `src/visualizations/figure_style.py:14`. |
| 21 | `function` | `_safe_int` | inventory fallback | Inventory fallback for function `_safe_int` defined at `src/visualizations/figure_style.py:21`. |
| 67 | `class` | `FigureStyleConfig` | docstring | Data container for FigureStyleConfig. |
| 78 | `function` | `FigureStyleConfig.color` | docstring | Process color. |
| 82 | `function` | `FigureStyleConfig.text_size` | docstring | Process text size. |
| 87 | `function` | `FigureStyleConfig.layout_value` | docstring | Process layout value. |
| 91 | `function` | `FigureStyleConfig.rc_params` | docstring | Process rc params. |
| 112 | `function` | `active_style` | docstring | Process active style. |
| 117 | `function` | `load_figure_style` | docstring | Load figure style from a file. |
| 166 | `function` | `apply_style` | docstring | Process apply style. |

## `src/visualizations/figures.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 51 | `function` | `_read_sweep` | inventory fallback | Inventory fallback for function `_read_sweep` defined at `src/visualizations/figures.py:51`. |
| 59 | `function` | `_style_discrete_y` | inventory fallback | Inventory fallback for function `_style_discrete_y` defined at `src/visualizations/figures.py:59`. |
| 64 | `function` | `_apply_artifact_note` | inventory fallback | Inventory fallback for function `_apply_artifact_note` defined at `src/visualizations/figures.py:64`. |
| 68 | `function` | `figure_ising_mi_curve` | docstring | Process figure ising mi curve. |
| 128 | `function` | `figure_si_belief_entropy_curve` | docstring | Process figure si belief entropy curve. |
| 165 | `function` | `figure_si_obs_action_trace` | docstring | Process figure si obs action trace. |
| 199 | `function` | `figure_si_tmaze_actions` | docstring | Process figure si tmaze actions. |
| 235 | `function` | `figure_si_summary` | docstring | Deprecated alias for ``figure_si_tmaze_actions``. |
| 240 | `function` | `figure_free_energy_curve` | docstring | Process figure free energy curve. |
| 309 | `function` | `run_figure` | docstring | Dispatch a registry figure id to its generator. |
| 322 | `function` | `generate_all_figures` | docstring | Generate all figures. |

## `src/visualizations/figures_diagrams.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 34 | `function` | `_load_invariant_blocks` | inventory fallback | Inventory fallback for function `_load_invariant_blocks` defined at `src/visualizations/figures_diagrams.py:34`. |
| 47 | `function` | `figure_invariant_dashboard` | docstring | Process figure invariant dashboard. |
| 94 | `function` | `figure_tmaze_schematic` | docstring | Process figure tmaze schematic. |
| 161 | `function` | `_load_pipeline_track_labels` | inventory fallback | Inventory fallback for function `_load_pipeline_track_labels` defined at `src/visualizations/figures_diagrams.py:161`. |
| 168 | `function` | `_load_sheaf_track_labels` | inventory fallback | Inventory fallback for function `_load_sheaf_track_labels` defined at `src/visualizations/figures_diagrams.py:168`. |
| 176 | `function` | `figure_multi_track_architecture` | docstring | Process figure multi track architecture. |
| 188 | `function` | `figure_multi_track_architecture.chunks` | docstring | Process chunks. |
| 192 | `function` | `figure_multi_track_architecture.draw_group_column` | docstring | Process draw group column. |
| 250 | `function` | `figure_track_lane_promotion_map` | docstring | Render the pipeline-track promotion obligations and sheaf-lane bindings. |
| 358 | `function` | `figure_artifact_contract_map` | docstring | Render artifact-level producer, validator, freshness, and copy-parity obligations. |
| 457 | `function` | `figure_lean_boundary_status` | docstring | Process figure lean boundary status. |
| 489 | `function` | `figure_gnn_ontology_concordance` | docstring | Process figure gnn ontology concordance. |

## `src/visualizations/figures_semantic.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 27 | `function` | `figure_semantic_gluing_graph` | docstring | Process figure semantic gluing graph. |
| 117 | `function` | `figure_theorem_traceability_graph` | docstring | Render theorem → proof dependency → witness links from generated JSON rows. |
| 176 | `function` | `figure_causal_ablation_heatmap` | docstring | Render source-backed causal-ablation effects as topology × perturbation heatmap. |
| 241 | `function` | `figure_scholarship_source_map` | docstring | Render bibliography-to-method-source bindings from the scholarship matrix. |
| 298 | `function` | `figure_security_posture_map` | docstring | Render the local security posture controls and evidence bindings. |

## `src/visualizations/figures_sheaf.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 32 | `function` | `_figure_inputs` | inventory fallback | Inventory fallback for function `_figure_inputs` defined at `src/visualizations/figures_sheaf.py:32`. |
| 41 | `function` | `_has_explicit_panel_tracks` | inventory fallback | Inventory fallback for function `_has_explicit_panel_tracks` defined at `src/visualizations/figures_sheaf.py:41`. |
| 53 | `function` | `_layers_output_is_fresh` | inventory fallback | Inventory fallback for function `_layers_output_is_fresh` defined at `src/visualizations/figures_sheaf.py:53`. |
| 74 | `function` | `figure_sheaf_layers_overview` | docstring | Process figure sheaf layers overview. |
| 118 | `function` | `figure_sheaf_coverage_heatmap` | docstring | Render B/W/G sheaf coverage matrix with IMRAD row grouping. |

## `src/visualizations/figures_sheaf_draw.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `_imrad_group_label` | inventory fallback | Inventory fallback for function `_imrad_group_label` defined at `src/visualizations/figures_sheaf_draw.py:15`. |
| 19 | `function` | `_wrap_label` | inventory fallback | Inventory fallback for function `_wrap_label` defined at `src/visualizations/figures_sheaf_draw.py:19`. |
| 23 | `function` | `_draw_imrad_group_labels` | docstring | Annotate IMRAD block names on the left margin of the heatmap. |
| 60 | `function` | `draw_coverage_heatmap` | docstring | Process draw coverage heatmap. |
| 140 | `function` | `draw_track_layers_panel` | docstring | Process draw track layers panel. |
| 203 | `function` | `layers_overview_figure_height` | docstring | Figure height (inches) for the two-panel sheaf layers overview. |

## `src/visualizations/figures_sheaf_payload.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `class` | `HeatmapPayload` | docstring | Data container for HeatmapPayload. |
| 24 | `function` | `coverage_heatmap_payload` | docstring | Process coverage heatmap payload. |

## `src/visualizations/figures_simulation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `figure_efe_decomposition` | docstring | Expected Free Energy term decomposition across T-maze policies. |
| 96 | `function` | `figure_precision_sweep` | docstring | Policy-posterior sharpening as precision (gamma) increases. |
| 169 | `function` | `figure_cue_tmaze_advantage` | docstring | Epistemic necessity in the cue-then-reward T-maze. |
| 230 | `function` | `figure_dirichlet_convergence` | docstring | KL(true A \|\| learned A) versus Dirichlet update step (log-y). |

## `src/visualizations/lean_boundary.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `class` | `LeanBoundaryRow` | docstring | Data container for LeanBoundaryRow. |
| 28 | `function` | `_module_name` | inventory fallback | Inventory fallback for function `_module_name` defined at `src/visualizations/lean_boundary.py:28`. |
| 36 | `function` | `_declaration_block` | docstring | Return the declaration body from ``start`` until the next top-level def/theorem. |
| 45 | `function` | `_scan_lean_file` | inventory fallback | Inventory fallback for function `_scan_lean_file` defined at `src/visualizations/lean_boundary.py:45`. |
| 58 | `function` | `load_lean_boundary_rows` | docstring | Load lean boundary rows from a file. |

## `scripts/check_documentation_contract.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `build_parser` | docstring | Return the CLI parser for documentation contract checks. |
| 27 | `function` | `main` | docstring | CLI entry point. |

## `scripts/compose_manuscript.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | docstring | CLI entry point. |

## `scripts/compute_statistics.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | docstring | CLI entry point. |

## `scripts/generate_figures.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | docstring | CLI entry point. |

## `scripts/generate_formal_interop_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `main` | docstring | CLI entry point. |

## `scripts/generate_integration_audit.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | docstring | CLI entry point. |

## `scripts/generate_method_inventory.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `build_parser` | docstring | Return the CLI parser for method-inventory generation. |
| 32 | `function` | `main` | docstring | CLI entry point. |

## `scripts/generate_sheaf_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | docstring | CLI entry point. |

## `scripts/generate_toy_sweep_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | docstring | CLI entry point. |

## `scripts/generate_validation_spine.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | docstring | CLI entry point. |

## `scripts/inject_variables.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `main` | docstring | CLI entry point. |

## `scripts/render_animation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `build_parser` | docstring | Build parser. |
| 27 | `function` | `main` | docstring | CLI entry point. |

## `scripts/render_pdf.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 36 | `function` | `main` | docstring | CLI entry point. |

## `scripts/run_analytical_sweep.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | docstring | CLI entry point. |

## `scripts/run_full_verification.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | docstring | CLI entry point. |

## `scripts/simulate_si_graph_world.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `main` | docstring | CLI entry point. |

## `scripts/simulate_si_tmaze.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `build_parser` | docstring | Build parser. |
| 51 | `function` | `main` | docstring | CLI entry point. |

## `scripts/validate_outputs.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `main` | docstring | CLI entry point. |

## `scripts/z_generate_manuscript_variables.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 20 | `function` | `main` | docstring | CLI entry point. |

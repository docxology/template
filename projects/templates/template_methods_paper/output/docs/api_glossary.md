| Module | Name | Kind | Summary |
|---|---|---|---|
| `figure_specs` | `MethodsFigureSpec` | class | Registry contract for one generated methods-paper figure. |
| `manuscript_variables` | `generate_variables` | function | Generate all manuscript variables from config and analysis outputs. |
| `manuscript_variables` | `save_variables` | function | Persist *variables* as JSON for downstream rendering and debugging. |
| `methods_dsl.compiler` | `CycleError` | class | Raised by :func:`topological_order` when the step-dependency graph has a cycle. |
| `methods_dsl.compiler` | `MethodValidationError` | class | Raised by :func:`compile_method` when any validation gate fails. |
| `methods_dsl.compiler` | `Plan` | class | A deterministically compiled, scheduled execution plan. |
| `methods_dsl.compiler` | `PlanStep` | class | One scheduled step in a compiled :class:`Plan`. |
| `methods_dsl.compiler` | `compile_method` | function | Validate and deterministically compile *method* into a :class:`Plan`. |
| `methods_dsl.compiler` | `topological_order` | function | Return *method*'s steps in a deterministic dependency-respecting order. |
| `methods_dsl.examples_methods` | `all_example_methods` | function | Every example method, in the fixed order the script and manuscript report them. |
| `methods_dsl.examples_methods` | `pbs_preparation_method` | function | A phosphate-buffered-saline preparation protocol (manual bench work). |
| `methods_dsl.examples_methods` | `sensor_calibration_method` | function | An instrument-calibration controlled procedure (mixed automated + human steps). |
| `methods_dsl.export` | `to_csv_rows` | function | Return *plan* as CSV lines (header first), ready to join with ``\n``. |
| `methods_dsl.export` | `to_json` | function | Return the canonical JSON encoding :data:`Plan.plan_hash` was computed over. |
| `methods_dsl.export` | `to_mermaid` | function | Render *plan* as a Mermaid ``flowchart TD`` showing scheduled order. |
| `methods_dsl.export` | `to_worklist_markdown` | function | Render *plan* as a numbered, human-readable worklist. |
| `methods_dsl.export` | `write_all_exports` | function | Write worklist markdown, CSV, Mermaid, and canonical JSON for *plan* under *data_dir*. |
| `methods_dsl.export` | `write_csv` | function | Write *plan* as CSV to *path* and return the resolved path. |
| `methods_dsl.export` | `write_json` | function | Write *plan*'s canonical JSON to *path* and return the resolved path. |
| `methods_dsl.export` | `write_json_report` | function | Write an arbitrary JSON-serializable *payload* to *path* and return it. |
| `methods_dsl.model` | `Method` | class | A complete, named method: parameters, resources, and an ordered step set. |
| `methods_dsl.model` | `MethodModelError` | class | Raised when a model object is constructed with an invalid shape. |
| `methods_dsl.model` | `Parameter` | class | A named, quantified input to a step or method. |
| `methods_dsl.model` | `Resource` | class | A named physical or logical resource a method operates on. |
| `methods_dsl.model` | `Step` | class | One step in a method: an intent, its parameters, and its dependencies. |
| `methods_dsl.trust` | `ProvenanceTier` | class | How a state value was obtained, ordered from least to most trusted. |
| `methods_dsl.trust` | `StateRecord` | class | One entry in a hash-chained state history. |
| `methods_dsl.trust` | `append_record` | function | Append a new state record to *chain*, returning the extended chain. |
| `methods_dsl.trust` | `demo_chain_report` | function | Declare, calibrate, then verify one value — the manuscript's worked example. |
| `methods_dsl.trust` | `verify_chain` | function | Return whether every record's hash is consistent with its predecessor. |
| `methods_dsl.units` | `Dimension` | class | Physical dimension family a unit belongs to. |
| `methods_dsl.units` | `DimensionError` | class | Raised when an operation mixes incompatible physical dimensions. |
| `methods_dsl.units` | `Quantity` | class | A value paired with its unit, e.g. ``Quantity(10.0, "mL")``. |
| `methods_dsl.units` | `check_compatible` | function | Raise :class:`DimensionError` unless *a* and *b* share a dimension. |
| `methods_dsl.units` | `dimension_of` | function | Resolve *unit* to its :class:`Dimension`. |
| `methods_dsl.units` | `known_units` | function | Return every unit string the controlled vocabulary recognizes. |
| `methods_dsl.validation` | `GateResult` | class | Outcome of one validation gate: pass/fail plus the issues found. |
| `methods_dsl.validation` | `plan_gate` | function | Check the step-dependency graph is acyclic (a valid DAG). |
| `methods_dsl.validation` | `run_all_gates` | function | Run all four gates in the fixed order: structural, semantic, plan, target. |
| `methods_dsl.validation` | `semantic_gate` | function | Check every :class:`~src.methods_dsl.units.Quantity` resolves to a known dimension. |
| `methods_dsl.validation` | `structural_gate` | function | Check step-id uniqueness and that every dependency resolves. |
| `methods_dsl.validation` | `target_gate` | function | Check every step's target is compatible with the method's target and kind. |
| `methods_dsl.vocabulary` | `StepKind` | class | A controlled-vocabulary intent for one method step. |
| `methods_dsl.vocabulary` | `Target` | class | Execution backend a method (or step) is compiled for. |
| `methods_dsl.vocabulary` | `target_accepts` | function | Return whether *target* can execute a step of *kind*. |
| `project_paths` | `project_output_dirs` | function | Return common output directories for the methods-paper exemplar. |
| `project_paths` | `resolve_project_root` | function | Process resolve project root. |

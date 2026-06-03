### Appendix track: proof extraction

`proof_extraction` binds `output/data/proof_extraction_index.json` into the full
sheaf appendix. Extracted theorems: {{proof_extraction_theorem_count}}.
Constructive status: `{{proof_extraction_all_constructive}}`.

The extraction index is intentionally modest: it records theorem names,
statements, source files, leading tactics, and forbidden proof-token checks.
That makes the Lean boundary inspectable without pretending that every proof
term has been translated into a proof object. A row with a missing statement or
forbidden token fails the formal interop gate and the canonical sheaf gate.

`output/data/proof_dependency_graph.json` adds the dependency view used by the
appendix figure. It contributes {{proof_dependency_edge_count}} theorem-source,
theorem-tactic, theorem-definition, and theorem-witness edges, with resolved
edge status `{{proof_dependency_all_resolved}}`; this is the artifact that keeps
the theorem-traceability graph tied to generated Lean and model-checking rows.

# Limitations: Non-Claims, Misuse Modes, and Human Review

The limitations section is configured to state non-claims, identify misuse modes, preserve human review, and require domain validators for domain claims. The central limitation is that deterministic token injection can make manuscript assembly auditable, but it cannot make a weak claim true or a missing source appear.

The declared failure modes are Unresolved placeholder, Overclaimed generated prose, Config-source drift, Figure provenance gap, Domain misuse, Method row drift, Field-origin opacity, Visual-method mismatch, Fork without validators, Digest invariant drift, Claim ledger omission, Review packet incompleteness, Fork migration ambiguity. They are included in the manuscript because this template is meant to teach the boundary, not hide it. A useful fork should extend this table when it adds domain-specific claims, validators, or publication targets.

The author remains responsible for theory, citations, reader expectations, and domain evidence. The generator can enforce structure and provenance; it cannot supply judgment. That division is the main safety property of the exemplar.

## Failure Modes

| Failure mode | Risk | Detection | Mitigation |
| --- | --- | --- | --- |
| Unresolved placeholder | A source Markdown token is added without a generated variable. | Project test scans output/manuscript and rendered web output for uppercase placeholders. | Add variable generation, tests, and rerun z_generate_manuscript_variables.py before render. |
| Overclaimed generated prose | Generated text implies a standalone DOI, empirical validation, or external release that does not exist. | Claim ledger review, publication metadata review, and evidence registry validation. | Keep publication fields blank and use local-only claim boundaries until evidence exists. |
| Config-source drift | Documentation names a schema feature that source code no longer parses. | Config tests instantiate the schema and docs point to generated tables. | Update config loader, docs, and tests together. |
| Figure provenance gap | A figure is referenced in manuscript output without a registry entry. | Stage 04 figure registry validation. | Emit figure_registry.json from src.analysis before rendering. |
| Domain misuse | A fork treats lexical substitution as evidence for a domain-specific research claim. | Failure-mode table, scope text, and downstream domain validators. | Add domain-specific data, validators, and claim ledgers before making domain claims. |
| Method row drift | The Methods prose describes a protocol row or phase that no longer exists in config. | Composition tests, summary report review, and generated method tables. | Update method_protocol, pipeline_phases, composition prose, and tests together. |
| Field-origin opacity | A rendered field appears configured even though it came from a loader default. | configured_field_inventory.json and configured-field summary figures. | Expose explicit/default counts in the manuscript and review optional defaults before release. |
| Visual-method mismatch | A figure implies a method claim that is not backed by generated data or registry metadata. | Figure registry validation, nonblank figure tests, and manual visual QA. | Generate figures only from config, TokenPlan, and inventory data, then rerun validation. |
| Fork without validators | A downstream project changes vocabulary or claims but keeps only the exemplar's generic gates. | Authoring contract review and claim ledger review. | Add domain validators, domain evidence artifacts, and claim-ledger entries before asserting domain findings. |
| Digest invariant drift | A future edit lets renderer state, file order, or ambient prose influence token selection. | Seed-stability, category-sensitivity, and method-invariant tests. | Keep token selection isolated in src/tokens.py and document allowed digest inputs in Methods. |
| Claim ledger omission | A generated claim appears in prose or documentation without a matching local evidence row or non-claim boundary. | Claim ledger review, evidence registry validation, and documentation review. | Add claim-ledger rows or remove the unsupported claim before rendering copied outputs. |
| Review packet incompleteness | A reviewer receives PDF or HTML without the data, reports, figures, validation output, or copy statistics needed to inspect the method. | Stage 05 output statistics and copied-output validation. | Regenerate Stages 02-05 and include the full copied output surface in review. |
| Fork migration ambiguity | A fork leaves authors unsure which exemplar surfaces must change for a domain-specific manuscript. | README, STANDALONE notes, manuscript README, and Authoring Contract review. | Document required config, source, test, claim-ledger, validator, and pipeline changes before making domain claims. |

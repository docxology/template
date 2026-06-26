# Authoring Contract: Human Review and Forking Obligations

The authoring contract is configured to state human responsibilities, name fork obligations, connect review to generated evidence, require domain validators before domain claims, and document fork migration notes. It addresses pipeline maintainers directly because the generator can preserve structure, provenance, and reviewability, but it cannot decide what a field should claim. Human authors remain responsible for theory, interpretation, citations, and the choice to publish.

The declared obligations are Review generated claims, Review config diffs, Extend claim evidence, Add domain validators, Rerun the full project path, Review method invariants, Assemble reviewer packet, Write fork migration notes. They convert responsible use into a checklist: review generated claims in the hydrated manuscript, inspect the generated evidence tables, extend the claim ledger when new claims appear, and add domain-specific validators before the template is used for a real empirical or theoretical manuscript.

The quality standard is claim humility. A fork that only changes words has not preserved the exemplar. A responsible fork changes the config, adjusts source-owned composition where necessary, regenerates artifacts, and reruns the same tests and validation gates before treating the output as reader-ready.

## Authoring Obligations

| Obligation | Required action | Review surface |
| --- | --- | --- |
| Review generated claims | Inspect hydrated manuscript bodies before copied outputs are treated as reader-ready. | `output/manuscript and output/web` |
| Review config diffs | Treat lexicon, slot, title, move, and section-switch edits as source-data changes. | `manuscript/config.yaml` |
| Extend claim evidence | Update the claim ledger when generated prose adds a new claim boundary. | `data/claim_ledger.yaml` |
| Add domain validators | Add tests and validation artifacts before using the template for domain-specific claims. | `tests and output/reports` |
| Rerun the full project path | Regenerate analysis artifacts, render outputs, validate outputs, and copy deliverables. | `pipeline command logs` |
| Review method invariants | Confirm changed tokens are explained only by seed, slot, category, ordinal, or category inventory changes. | `src/tokens.py, token_inventory.json, and output/manuscript/02_methodology.md` |
| Assemble reviewer packet | Provide hydrated manuscript, rendered outputs, figures, data, reports, validation report, and output statistics together. | `output/templates/template_madlib` |
| Write fork migration notes | Document config, source, test, validator, and claim-ledger changes required by a domain fork. | `README.md, STANDALONE.md, and data/claim_ledger.yaml` |

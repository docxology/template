# Bounded unpaid runtime acceptance

The normal scripts retain their offline default. A separate acceptance command
tests the source-declared `retrieval`, `fulltext`, `extraction`, `local-model`,
and `kg` capabilities using unpaid Crossref/Europe PMC or licensed publisher
content and an explicitly selected installed local Ollama model. No model,
credential, paid API, deposit, or publication is acquired.

From the repository root:

```bash
uv run python projects/templates/template_literature_meta_analysis/scripts/_run_unpaid_acceptance.py --mode core
uv run python projects/templates/template_literature_meta_analysis/scripts/_run_unpaid_acceptance.py \
  --mode live --model llama3.2:1b --endpoint http://127.0.0.1:11434 \
  --output-dir output/.pipeline/literature_acceptance/a-fresh-run
```

`core` inspects the committed corpus and declares no live capability execution;
the numbered scripts remain the complete offline analysis route. The separate
underscore-prefixed acceptance command is excluded from default script discovery.
Live execution requires the declared platform SDK, Python 3.14/3.15, the project's installed
dependencies including `pypdf` and `rdflib`, and a loopback Ollama service with the
selected model.

The acceptance run takes a bounded CC-BY-4.0-filtered Crossref sample from the
configured query, deduplicates records, round-trips complete BibTeX, and runs the
existing meta-analysis pipeline on the actual retrieved corpus. An independent
counter checks year counts and citation totals against the generated descriptive
statistics; required analysis outputs must be present and finite JSON. Undefined
network assortativity is `null`, not a measured zero. A small biased sample and
missing citation edges cannot establish bibliometric conclusions.

One retrieved article must supply substantial exact-DOI full text. Publisher PDFs
require an active deposited license matching their content version. Europe PMC
XML must carry the selected DOI and embedded CC-BY-4.0 rights. Raw source bytes,
extraction bytes, and license evidence are retained; missing rights/full text is
blocked and malformed responding content fails. No abstract substitutes for full
text.

Two real model calls produce a bounded workflow of one to three nodes and one
relation to a configured hypothesis. Every node and relation must quote the exact
consumed excerpt. The existing workflow graph/composite scoring runs on those
nodes; an independent algebra check binds its result. Dangling dependencies and
zero citation structure remain partial or null results. Model ratings are
uncalibrated and no complete workflow recovery is claimed. The second annotation
is materialized through the real RDF graph and nanopublication implementation.
The persisted nanopublication JSON is read back and its assertion is compared
with the graph membership; this is not independent semantic validation of RDF. Unit assertion weights are declared explicitly;
they are not calibrated confidence or proof that the quote entails the relation.

Fresh ignored run directories retain URL/redirect receipts, source/license bytes,
analysis artifacts, workflow/RDF products, exact local requests/responses, the
stable installed-model digest, token ceilings and process deadlines. Source
custody covers actual project producers and all public platform Python plus root
package/lock metadata. Loaded-code and interpreter/distribution identity are
checked across controller/workers and again before `receipt.json` promotion.
Request process deadlines are at most 60 seconds and the acceptance run budget is
at most 600 seconds; a late run cannot pass. Published outputs are preserved.

Exit `0` requires every declared producer; `75` records unavailable unpaid
providers/models or exhausted deadlines; `1` records malformed or partial
required producers, fabricated quotes, invalid domain products, or custody drift.
Normal tests exercise real loopback HTTP/process controls with synthetic provider
responses. Such conformance evidence is distinct from actual provider/model
acceptance and does not establish scientific extraction accuracy.

Actual implementation custody distinguishes a source checkout from an installed
platform wheel. Checkout evidence includes public infrastructure/scripts and root
package/lock files; wheel evidence instead binds installed public Python, the
selected distribution's METADATA/RECORD, its exact declared file set, and the
selected runtime. Workers start with a fresh owned bytecode prefix before imports,
audit actual executed module code against held source and execution-time cache
bytes, and recheck custody before promotion. Standalone startup seeds the actual
already-running main frame before business imports; this compares compiled code
fields and does not recover original comment bytes. Configuration consumers parse
the exact immutable bytes admitted at freeze time, including hypotheses and
classification where those are declared; reopening a changed snapshot cannot
change the consumed config. Its persisted snapshot is still verified at promotion.
No absent checkout lock is fabricated inside a wheel. The project declares the
platform SDK dependency in `pyproject.toml`; standalone execution installs an admitted platform wheel
and the exemplar wheel into the selected environment.

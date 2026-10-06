# Bounded unpaid runtime acceptance

The normal pipeline uses the committed offline corpus by default. The additional
acceptance command explicitly tests the declared `retrieval`, `fulltext`, and
`local-synthesis` capabilities against real unpaid services and an already
installed local Ollama model. It acquires no model, credentials, or paid service.

From the repository root:

```bash
uv run python projects/templates/template_search_project/scripts/_run_unpaid_acceptance.py --mode core
uv run python projects/templates/template_search_project/scripts/_run_unpaid_acceptance.py \
  --mode live --model llama3.2:1b --endpoint http://127.0.0.1:11434 \
  --output-dir output/.pipeline/literature_acceptance/a-fresh-run
```

`core` here inspects the committed reference corpus and declares zero tested
live capabilities. Run the normal project scripts for the full offline pipeline.
The underscore-prefixed acceptance orchestrator is deliberately excluded from
automatic analysis-script discovery. Live execution requires platform 4.0.0,
Python 3.12–3.14, `pypdf`, and a running loopback-only Ollama service containing
the explicitly selected model.

The live command queries Crossref with the configured topic and retrieves at
most three records by default (explicit ceiling five), deduplicates their IDs,
and writes independently parsed BibTeX. It selects one substantial identity-bound
full text from at most three candidates. A publisher PDF requires an active
deposited CC-BY-4.0 license for the matching content version; Europe PMC XML
requires the exact DOI and an embedded CC-BY-4.0 license. Unknown rights, missing
full text, or unavailable services remain blocked. Abstracts never replace full
text. This is a license-filtered bounded sample, not an exhaustive search.

One actual local generation creates a short synthesis tied to its citation key
and a verbatim quote from the consumed full-text excerpt. Exact quote inclusion
establishes source custody; it does not establish entailment, extraction accuracy,
scientific truth, or a systematic review. The prompt is restricted to an excerpt
and does not send private files or credentials.

Fresh ignored run directories retain HTTP URLs and redirects, exact source bytes,
license evidence, BibTeX, provider requests/responses, stable installed-model
digest, token limits, process deadlines, and the final `receipt.json`. The source
manifest binds project source/configuration plus all public platform Python,
root package/lock metadata, the selected interpreter, and installed distributions.
The controller and workers verify loaded implementations and exact custody
before execution and before acceptance. Per-request process deadlines are at
most 60 seconds; the run budget is at most 600 seconds and no receipt is promoted
after its budget. Historical publication outputs are untouched.

Exit `0` requires every declared producer to pass; unavailable providers/models
or exhausted deadlines return `75`; malformed responding producers, fabricated
quotes, partial required producers, and custody changes return `1`. Tests use
real loopback HTTP/process conformance oracles with synthetic responses. Those
controls are separate from an actual network and installed-model acceptance run.

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
platform 4.0.0 dependency; standalone execution installs an admitted platform wheel
and the exemplar wheel into the selected environment.

# Reproducibility Module — Agent Directives

## Overview

Decomposes each paper's own described pipeline into a workflow graph
and scores how reproducible that pipeline is from the paper's text
alone. Orchestration: `reproducibility/runner.py`
(`scripts/10_reproducibility_assessment.py`). Implements the workflow-graph
extraction and scoring model from arXiv:2605.02651, with two ambiguities in
that source paper resolved by explicit modeling choices documented below and
in `scoring.py`'s module docstring — this is the most expensive operation in
the module (LLM extraction over full paper text, not just the abstract), so
prefer the default incremental mode whenever possible.

## The Four Node Types

Every extracted workflow step is classified as exactly one `NodeType`
(`models.py`):

- **`source`** — raw data, materials, or external inputs the pipeline consumes.
- **`method`** — a procedure, algorithm, or protocol applied to inputs.
- **`experiment`** — an evaluation, trial, or measurement run.
- **`sink`** — an output, result, or artifact the pipeline produces.

Each node also carries a `reproducibility_rating` in `[1, 4]` (1 = missing
info, 4 = sufficient detail for independent reconstruction) and a
`source_quote` — the verbatim sentence(s) from the paper's full text that
support the node. `depends_on` lists the raw, possibly-dangling `node_id`
values a node depends on; `build_workflow_graph()` resolves these into
directed `WorkflowEdge`s (edge points from the depended-on/upstream node to
the depending/downstream node — see `models.py`'s module docstring for the
full direction rationale).

## Composite Scoring Formula

```
R = sqrt(Rc * Rs)
```

`Rc` (content score) is a renormalized, weighted average of per-stage
`reproducibility_rating` averages — only stages that actually have >=1 node
contribute, and their weights are renormalized to sum to 1 so a paper with no
`experiment` nodes is not penalized for a stage it never claimed to have.

`Rs` (structural score) is a fixed convex combination of five structural
components (`rc1`..`rc5`, see `scoring.py:structural_score()`):
source-consumption, sink-production, reference-resolution,
source-to-sink path coverage, and weak-component cohesion.

`R` is the geometric mean of `Rc` and `Rs` — a deliberate *no-compensation*
design: a paper cannot buy a high composite score by being perfect on one
axis while structurally incoherent on the other (dangling references
everywhere, `Rs` near 0.0), or vice versa. Either axis at zero drives the
composite to zero. `composite_score()` short-circuits an empty graph
(zero nodes) to an all-zero `ReproducibilityScore` before any division or
`sqrt`, so it can never raise `ZeroDivisionError` or a `math.sqrt` domain
error.

## Extension Pattern — Adjusting Weights

`ContentWeights` and `StructuralWeights` are plain `@dataclass`es with
hardcoded defaults in `scoring.py`. To change them for a project without
editing source:

1. Add a `content_weights` and/or `structural_weights` block under
   `reproducibility_assessment` (or nested `project_config.reproducibility_assessment`)
   in `manuscript/config.yaml`, keyed by the same attribute names
   (`sources`/`methods`/`experiments`/`sinks` for content;
   `source_consumption`/`sink_production`/`reference_resolution`/
   `path_coverage`/`cohesion` for structural).
2. `config_loader.load_reproducibility_config()` reads the block;
   `runner._build_content_weights()` / `runner._build_structural_weights()`
   apply only the keys present, falling back to dataclass defaults for the
   rest — no need to specify every key.
3. `ContentWeights`' renormalization means the *ratios* between weights
   matter, not their absolute sum. `StructuralWeights` are used as-is (never
   renormalized), so a structural-weights block that doesn't sum to 1.0
   will shift `Rs`'s effective range.

Adding a sixth structural component (`rc6`) is a larger change: it requires
a new pure function in `scoring.py` alongside `rc1`..`rc5`, a new
`StructuralWeights` field, and a new key in `structural_score()`'s
`components` dict and weighted sum — there is no plugin/registry seam for
this, unlike `knowledge_graph.hypothesis`'s `STANDARD_HYPOTHESES` list.

## Invariants Agents Must Preserve

- **`source_quote` is mandatory, never default to empty string.** A
  `WorkflowNode`'s entire evidentiary basis is its quote from the paper's
  full text. `extraction.py:extract_workflow_nodes()` drops (does not
  coerce) any parsed node whose `source_quote` is missing or empty — never
  change this to `item.get("source_quote", "")` or any other default that
  would silently fabricate an unsupported reproducibility claim.
- **`rc3` (reference_resolution) counts only method+experiment node
  references, never source.** `SOURCE` nodes' own `depends_on` entries
  describe what raw data rests on (e.g. an external repository), not a
  paper's internal pipeline structure — counting them in `rc3`'s numerator
  or denominator would conflate two different reproducibility questions.
  See `scoring.py:reference_resolution()`.
- **`rc4` (source_sink_path_coverage) normalizes by the product of source
  and sink counts, not set union size.** The denominator is
  `|sources| * |sinks|` — uniform-pair-probability semantics over every
  (source, sink) pair. This repo's implementation *fixes* two ambiguities
  left unresolved in the source paper (arXiv:2605.02651): the `rc3` scope
  question above and this `rc4` normalization question. Do not revert either
  to the paper's literal ambiguous wording; both are deliberate, documented
  modeling choices (see `scoring.py`'s module docstring, "Ambiguity
  resolutions" section) made here, not claims the source paper itself makes.
- **Node-type validation is strict.** `extract_workflow_nodes()` rejects
  (drops) any parsed node whose `node_type` does not match one of the four
  `NodeType` values exactly — never coerce an unrecognized type to a
  default.
- **Incremental extraction.** `extract_workflow_graphs_llm()` skips papers
  already present in `workflow_graphs.jsonl` (resume semantics via
  `get_processed_paper_ids()`). Never delete this file without an explicit
  `--clear-workflow-graphs` flag unless asked to restart; deleting it
  triggers full LLM re-extraction over every paper with available fulltext.
- **A paper with no fulltext file on disk is skipped, not fabricated.**
  `extract_workflow_graphs_llm()` only calls the LLM for a paper when
  `<fulltext_dir>/<safe_filename(canonical_id)>.txt` exists. There is no
  path that builds a workflow graph from title/abstract alone.
- **No mock policy.** Tests must use real `WorkflowNode`/`WorkflowGraph`
  objects and real score computations; HTTP-boundary tests use
  `pytest-httpserver`, mirroring `knowledge_graph`'s pattern exactly.

## Workflow

```bash
# Incremental (default) — skips already-processed papers, no-op if
# project_config.fulltext.enabled is false and --fulltext-dir is not passed
uv run python scripts/10_reproducibility_assessment.py

# Full re-extraction (WARNING: overwrites existing workflow graphs)
uv run python scripts/10_reproducibility_assessment.py --clear-workflow-graphs

# Point at a pre-populated fulltext directory explicitly
uv run python scripts/10_reproducibility_assessment.py --fulltext-dir output/fulltext
```

Ollama must be running at `http://localhost:11434` with `gemma3:4b` pulled
(same LLM boundary as `knowledge_graph`, sharing `LLMConfig`,
`call_ollama()`, and `parse_llm_response()`).

## Known Limitations

- **Uncalibrated weights.** `ContentWeights` (0.30/0.20/0.20/0.30) and
  `StructuralWeights` (0.25/0.25/0.20/0.15/0.15) are reasonable defaults, not
  values fit against a labeled reproducibility dataset. Treat both as
  configuration knobs (see "Extension Pattern" above), not validated
  parameters.
- **No inter-rater study on the 1-4 rating.** `reproducibility_rating` is
  produced by a single LLM call per paper with no human-agreement (kappa)
  study behind it, unlike `knowledge_graph`'s `min_confidence: 0.6` threshold
  (which does cite a `κ > 0.70` calibration requirement). Treat individual
  ratings as a first-pass signal, not a validated measurement.
- **`pypdf` silently degrades to `None` on unparseable PDFs.**
  `literature.fulltext_download` catches any exception from `pypdf.PdfReader`
  and returns `None`/`[]` rather than raising (see that module's
  degrade-to-`None` convention). `runner.py` distinguishes this case
  (`n_skipped_unparseable_pdf`) from "no fulltext downloaded at all"
  (`n_skipped_no_fulltext`) in its summary output specifically so this
  failure mode is visible rather than silently conflated with plain
  unavailability — but the underlying PDF-parsing failure itself is never
  surfaced with a reason (which page, which pypdf exception).
- **First scripts/ orchestrator to consume the `fulltext` config block.**
  Per `config_loader.load_fulltext_config()`'s own docstring: prior to
  `reproducibility.runner.run_reproducibility_pipeline`, no `scripts/`
  orchestrator read `project_config.fulltext` (`enabled`, `download_dir`,
  `unpaywall_email`) at all. `download_and_extract_fulltext()` itself
  (`literature/fulltext_download.py`) still has zero callers anywhere under
  `scripts/` — this module only *reads* `.txt` files that some other,
  currently-unbuilt orchestrator would need to have populated via that
  function. Until `project_config.fulltext.enabled` is `true` in
  `manuscript/config.yaml` (or `--fulltext-dir` is passed explicitly
  pointing at a directory someone else populated), `run_reproducibility_pipeline`
  is a true no-op: it logs a loud warning and still writes a valid,
  well-formed but empty set of outputs (graceful degradation, never a
  silent skip and never a crash).

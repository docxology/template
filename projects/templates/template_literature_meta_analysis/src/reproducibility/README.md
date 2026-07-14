# Reproducibility Module

Reproducibility-assessment engine for the literature meta-analysis. Decomposes
each paper's own described pipeline into a workflow graph of discrete steps
(source/method/experiment/sink), then computes content and structural
reproducibility scores over that graph. Implements the workflow-graph model
from arXiv:2605.02651, with two source-paper ambiguities resolved by explicit
modeling choices (see `scoring.py`'s module docstring and
[AGENTS.md](AGENTS.md) for the invariants that protect those choices).

## Components

### `models.py`

`NodeType` (str `Enum`: `SOURCE`/`METHOD`/`EXPERIMENT`/`SINK`), `WorkflowNode`
and `WorkflowEdge` dataclasses, and the `WorkflowGraph` dataclass that
assembles them for one paper. `WorkflowNode.depends_on` lists raw,
possibly-dangling `node_id` references; `build_workflow_graph()` resolves
those into directed `WorkflowEdge`s pointing from the depended-on (upstream)
node to the depending (downstream) node — see the module docstring for the
full direction rationale (out-degree on a `SOURCE` measures fan-out,
in-degree on a `SINK` measures fan-in). Unresolved references are dropped
from `edges` and counted in `dangling_reference_count` rather than raising.

Key functions/types:

- `WorkflowNode: dataclass` — `node_id`, `node_name`, `node_type`,
  `source_quote`, `description`, `reproducibility_rating`, `rationale`,
  `depends_on`, `paper_id`
- `WorkflowEdge: dataclass` — `source_node_id`, `target_node_id`, `relation`
- `WorkflowGraph: dataclass` — `paper_id`, `nodes`, `edges`,
  `dangling_reference_count`; `.to_dict()` / `.from_dict()`
- `build_workflow_graph(paper_id, nodes) -> WorkflowGraph`
- `serialize_workflow_graphs(graphs) -> list[str]` — JSON Lines strings
- `deserialize_workflow_graphs(path) -> list[WorkflowGraph]`
- `merge_workflow_graphs(existing, new) -> list[WorkflowGraph]` —
  deduplicate by `paper_id`, new wins
- `get_processed_paper_ids(graphs) -> set[str]`
- `append_workflow_graphs(graphs, path) -> None` — atomic append + merge,
  temp-file + rename

### `scoring.py`

Pure, zero-I/O, stdlib-only scoring functions over a `WorkflowGraph`, plus a
standalone quote-verification helper. Nothing here calls an LLM or touches
the filesystem or network.

```
Rc (content score)    = renormalized weighted average of per-stage rating averages
Rs (structural score) = fixed convex combination of rc1..rc5
R  (composite score)  = sqrt(Rc * Rs)
```

Key types/functions:

- `ContentWeights: dataclass` — `sources=0.30`, `methods=0.20`,
  `experiments=0.20`, `sinks=0.30`
- `StructuralWeights: dataclass` — `source_consumption=0.25`,
  `sink_production=0.25`, `reference_resolution=0.20`, `path_coverage=0.15`,
  `cohesion=0.15`
- `ReproducibilityScore: dataclass` — `content_score`, `structural_score`,
  `composite_score`, `stage_scores`, `structural_components`, `n_nodes`,
  `n_edges`, `n_dangling_references`
- `normalized_rating(node) -> float` — rescales `[1, 4]` into `[0.0, 1.0]`
- `stage_average(graph, node_type) -> Optional[float]`
- `content_score(graph, weights=ContentWeights()) -> tuple[float, dict[str, float]]`
- `source_consumption(graph) -> float` — `rc1`, fraction of `SOURCE` nodes with out-degree > 0
- `sink_production(graph) -> float` — `rc2`, fraction of `SINK` nodes with in-degree > 0
- `reference_resolution(graph) -> float` — `rc3`, resolution rate of
  `METHOD`+`EXPERIMENT` node `depends_on` references only
- `source_sink_path_coverage(graph) -> float` — `rc4`, fraction of
  `(source, sink)` pairs joined by a directed path; denominator is
  `|sources| * |sinks|`
- `weak_component_coverage(graph) -> float` — `rc5`, largest weakly-connected
  component's share of all nodes
- `structural_score(graph, weights=StructuralWeights()) -> tuple[float, dict[str, float]]`
- `composite_score(graph, content_weights=ContentWeights(), structural_weights=StructuralWeights()) -> ReproducibilityScore`
- `score_corpus(graphs, **weights) -> dict[str, ReproducibilityScore]`
- `verify_source_quote(quote, fulltext, *, fuzzy_threshold=0.85) -> bool` —
  exact-substring fast path, then a word-aligned sliding-window
  `difflib.SequenceMatcher` fuzzy match

### `prompts.py`

Prompt templates for LLM reproducibility-workflow extraction. The system
prompt documents the four node types, the exact JSON schema (`node_id`,
`node_name`, `node_type`, `source_quote`, `description`,
`reproducibility_rating`, `rationale`, `depends_on`), and the 1-4 rating
scale; it requests a bare JSON array with no markdown fences or commentary.

Key function:

- `build_prompt(paper_title, fulltext) -> str` — the user-turn prompt for
  one paper's full text, paired with the module-level system prompt

### `extraction.py`

LLM-based extraction of reproducibility workflow graphs from paper fulltext.
Follows `knowledge_graph.llm_extraction`'s structure line for line: the HTTP
call and JSON parsing delegate to the shared `knowledge_graph.llm_client`
helpers and `knowledge_graph.llm_config.LLMConfig` dataclass — nothing here
reimplements or forks either. Validation is manual (plain dict access, no
Pydantic): a parsed node is dropped outright when its `node_type` doesn't
match one of the four `NodeType` values or its `source_quote` is missing or
empty; `reproducibility_rating` is coerced to `int` and clamped into
`[1, 4]` rather than rejecting the node.

Key functions:

- `extract_workflow_nodes(paper, fulltext, config) -> list[WorkflowNode]` —
  single-paper LLM call + manual validation; retries up to
  `config.max_retries` with exponential backoff
  (`config.retry_delay * 2 ** (attempt - 1)`) on
  `(ValueError, requests.RequestException, KeyError)`, raising a plain
  `RuntimeError` once retries are exhausted
- `extract_workflow_graph(paper, fulltext, config) -> WorkflowGraph` — nodes
  then `build_workflow_graph()`, kept as two separate calls so dependency
  resolution stays independently testable with plain data
- `extract_workflow_graphs_llm(papers, fulltext_dir, config, *, output_path=None, existing=None) -> list[WorkflowGraph]` —
  incremental multi-paper driver with checkpointing every
  `config.checkpoint_interval` papers; skips a paper entirely (zero LLM
  calls) when it is already processed or its
  `<fulltext_dir>/<safe_filename(canonical_id)>.txt` does not exist

### `runner.py`

Pipeline orchestrator, mirroring `knowledge_graph.kg_runner`'s incremental
shape: load config, load the corpus, determine which papers still need a
workflow graph, run LLM extraction only for those, score every graph
(existing plus new) via the pure `scoring` functions, and write three
JSON/JSONL artifacts. Full-text availability is opt-in and gated by
`project_config.fulltext` in `manuscript/config.yaml`
(`config_loader.load_fulltext_config()`); when disabled and no
`--fulltext-dir` override is passed, this logs a loud warning and still
produces a valid, empty-but-well-formed set of outputs.

Key function:

- `run_reproducibility_pipeline(args, *, project_root) -> None`

Outputs (under `<output_dir>/data/`):

- `workflow_graphs.jsonl` — one `WorkflowGraph.to_dict()` per line
- `reproducibility_scores.json` — per-paper `ReproducibilityScore` plus
  `quote_verification_rate` (`None` when the paper's fulltext isn't on disk
  or the graph has zero nodes — distinct from "0% of quotes verified")
- `reproducibility_summary.json` — `mean_composite_score`,
  `n_papers_scored`, `n_low_score`, `low_score_threshold`,
  `n_skipped_no_fulltext`, `n_skipped_unparseable_pdf`,
  `fulltext_available`

## Scoring Formula

See [AGENTS.md](AGENTS.md) for the full `R = sqrt(Rc * Rs)` derivation, the
four node types, and the two ambiguity resolutions (`rc3` scope, `rc4`
normalization) this implementation fixes relative to the source paper
(arXiv:2605.02651). Key edge case: an empty graph (zero nodes) short-circuits
to an all-zero `ReproducibilityScore` before any division or `sqrt` — it can
never raise `ZeroDivisionError` or a `math.sqrt` domain error.

See [AGENTS.md](AGENTS.md) for agent-specific constraints.

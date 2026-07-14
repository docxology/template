---
name: Reproducibility Workflow-Graph Assessment
description: LLM-based extraction of per-paper workflow graphs and content/structural reproducibility scoring.
---

# Instructions

You are interacting with the `src/reproducibility/` module. This decomposes a paper's own described pipeline (source/method/experiment/sink steps) into a workflow graph and scores how reproducible that pipeline is from the paper's own text.

## Agentic Interface (MCP Strategy)

1. **Config-Driven Orchestration**: Never hardcode LLM parameters or scoring weights (`ContentWeights`, `StructuralWeights`) within Python scripts. Bind them to `LLMConfig` and the `reproducibility_assessment` block of `config.yaml`, loaded via `config_loader.load_reproducibility_config()`.
2. **Evidence-Backed Nodes Only**: Every `WorkflowNode` must carry a non-empty `source_quote` copied verbatim from the paper's full text. Never accept or fabricate a node without one — this is the node's entire evidentiary basis.
3. **Fulltext Gating**: This module only extracts from full text on disk, never from title/abstract alone. When `project_config.fulltext.enabled` is false and no `--fulltext-dir` override is supplied, treat a `reproducibility_assessment` run as a no-op that still yields valid, empty-but-well-formed outputs — never mistake the warning for a crash.

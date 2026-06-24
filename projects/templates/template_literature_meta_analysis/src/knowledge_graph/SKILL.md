---
name: LLM Extraction & KG Construction
description: Core inference logic, prompt construction, and RDF/Nanopublication serialization.
---

# Instructions

You are interacting with the `src/knowledge_graph/` module. This handles the transition from natural language text to structured assertions via Large Language Models.

## Agentic Interface (MCP Strategy)

1. **Config-Driven Orchestration**: Never hardcode LLM parameters (models, temperature, minimum confidence thresholds) within Python scripts. Bind them tightly to `LLMConfig` structures derived securely from `config.yaml`.
2. **Robust Categorization**: Respect strict boundaries on confidence gating. When crafting or modifying prompt templates, ensure the extraction schema firmly permits "irrelevant", "neutral", and "don't know" states to neutralize base-model hallucination tendencies.
3. **Streaming Persistence**: Assertions must emit safely to disk via incremental JSON Lines or valid TriG records. High-volume document processing should not accumulate global lists in RAM.

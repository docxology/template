# Pipeline scripts

These commands are thin entry points for the advanced review's 11-stage
workflow. Multi-phase retrieval and filtering live in `../src/multi_phase/`;
shared literature, analysis, knowledge-graph, reproducibility, visualization,
and manuscript logic live in `../src/`.

Run commands from the repository root with `uv run python`. The deterministic
offline verification path starts with the committed evidence snapshot. Stage
01 and stage 11 are explicit network refresh/enrichment boundaries.

See `AGENTS.md` for stage order, inputs, outputs, and validation commands.

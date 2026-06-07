# Abstract {#sec:abstract}

This exemplar documents **template_sia**, a deterministic implementation of the Self-Improvement Agent (SIA) harness contract described in [@sia2026]. The default pipeline replays fixture-backed generations for the `mini_classify` task; opt-in live mode runs bounded target subprocesses and optional Ollama-backed meta/feedback steps.

**Run snapshot.** Task `mini_classify`, run 1, 3 generation(s), live=false. Final accuracy=0.8333 over 6 held-out samples. Values are injected by `scripts/z_generate_manuscript_variables.py` after analysis.

**Keywords:** self-improvement agents, benchmark harness, reproducible evaluation, agent loops

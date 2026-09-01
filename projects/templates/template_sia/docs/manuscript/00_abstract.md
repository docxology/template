# Abstract {#sec:abstract}

This exemplar documents **template_sia**, a deterministic implementation of the Self-Improvement Agent (SIA) harness contract described in [@sia2026]. The default pipeline replays fixture-backed generations for the `mini_classify` task; opt-in live mode runs bounded target subprocesses and optional Ollama-backed meta/feedback steps.

**Run snapshot.** Task `{{SIA_TASK_NAME}}`, run {{SIA_RUN_ID}}, {{SIA_GENERATION_COUNT}} generation(s), live={{SIA_LIVE_MODE}}. Final {{SIA_FINAL_METRIC_NAME}}={{SIA_FINAL_METRIC_VALUE}} over {{SIA_FINAL_N_SAMPLES}} held-out samples. Values are injected by `scripts/z_generate_manuscript_variables.py` after analysis.

**Keywords:** self-improvement agents, benchmark harness, reproducible evaluation, agent loops

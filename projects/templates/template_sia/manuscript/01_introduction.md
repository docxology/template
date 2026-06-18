# Introduction {#sec:introduction}

This exemplar ships **template_sia**, a deterministic research harness for Self-Improvement Agent (SIA) loops [@sia2026]. It documents how the template repository separates generic orchestration (`infrastructure/sia/`) from a reproducible project surface (`projects/templates/template_sia/`) without vendoring the upstream [upstream SIA orchestrator repository](https://github.com/hexo-ai/sia).

Compared with the AutoResearch exemplar, SIA focuses on **meta → target → feedback** generations with public/private task splits rather than candidate-model search and readiness gates. Default CI replays fixture-backed generations; live mode remains opt-in.

**Scope.** The bundled `mini_classify` task is a threshold classifier on one feature column. Results demonstrate harness wiring and artifact contracts—not state-of-the-art accuracy.

**Run contract.** Task `{{SIA_TASK_NAME}}`, run {{SIA_RUN_ID}}, up to {{SIA_MAX_GENERATIONS}} generation(s), live={{SIA_LIVE_MODE}}.

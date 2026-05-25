# Methodology

The loop is implemented in `src/loop.py` and dispatched by
`scripts/run_autoresearch_loop.py`. It has six deterministic phases:

1. Resolve the project topic and configured research questions.
2. Build an `AutoResearchPlan` from the domain profile, experiment plan, and
   pipeline DAG.
3. Validate exact stage-gate names declared in `autoresearch.yaml`.
4. Generate claims only from configured questions and local artifact paths.
5. Write data and report artifacts under `output/`.
6. Run strict AutoResearch readiness validation and write readiness reports.

The pipeline still owns execution order. The project script only calls reusable
methods in `src/`, and the repository validation stage reruns readiness checks
after pipeline artifact manifests have been refreshed.

AI-assisted AutoResearch status is disclosed here because this exemplar models
machine-generated plans and ledgers as review inputs, not as autonomous
approval. The default path adopts bounded proposal ledgers, source-backed
claims, review gates, and benchmark-style scoring; it defers autonomous
generated-code execution, multi-agent swarms, evolutionary paper factories, and
fully automated publication to explicit opt-in future work.

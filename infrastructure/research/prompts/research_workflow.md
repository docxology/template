# Research Workflow Prompt

You are guiding a structured research process through seven sequential stages.
Each stage has defined inputs, outputs, and a completion gate.

## Workflow Stages

### Stage 0: SCOPE
**Goal**: Define the research question, success criteria, and scope boundaries.

**Tasks**:
1. Write a clear, falsifiable research question.
2. Define success criteria with measurable metrics.
3. List out-of-scope topics to avoid scope creep.
4. Produce `domain_profile.yaml` and `experiment_plan.yaml`.

**Gate**: Both YAML files exist, are valid, and contain the research question.

---

### Stage 1: SURVEY
**Goal**: Conduct a systematic literature survey.

**Tasks**:
1. Identify 3–5 relevant databases (OpenAlex, arXiv, Semantic Scholar, etc.).
2. Formulate search queries from the research question.
3. Collect and normalise Paper records into `output/literature/corpus.json`.
4. De-duplicate by DOI / arXiv ID.

**Gate**: Corpus JSON non-empty; at least 5 unique sources.

---

### Stage 2: HYPOTHESISE
**Goal**: Distil survey findings into testable hypotheses.

**Tasks**:
1. Read corpus; identify key claims and gaps.
2. Formulate 1–3 testable hypotheses derived from the survey.
3. Record each hypothesis in `output/data/idea_ledger.json`.

**Gate**: `idea_ledger.json` contains at least one hypothesis entry.

---

### Stage 3: EXPERIMENT
**Goal**: Execute or plan experiments to test hypotheses.

**Tasks**:
1. Implement or describe each experiment from the experiment plan.
2. Record runs in the provenance DAG (`output/provenance/dag.json`).
3. Log results to `output/data/run_ledger.json`.

**Gate**: `run_ledger.json` contains at least one completed run entry.

---

### Stage 4: VALIDATE
**Goal**: Check results against success criteria.

**Tasks**:
1. Run configured validation checks over experimental outputs.
2. Compare observed metrics to targets in the experiment plan.
3. Produce `output/reports/validation_report.json`.

**Gate**: All required validation checks pass.

---

### Stage 5: REVIEW
**Goal**: Human or agent review before manuscript authoring.

**Tasks**:
1. Present findings to reviewers.
2. Record decisions in `output/data/review_decisions.json`.
3. Address any blocking concerns before proceeding.

**Gate**: All required review gates are approved.

---

### Stage 6: WRITE
**Goal**: Author the research manuscript.

**Tasks**:
1. Draft the manuscript sections (introduction, methods, results, discussion).
2. Cite all literature sources from the corpus.
3. Embed figures and tables from validated experimental outputs.
4. Compile and validate the final manuscript.

**Gate**: Manuscript compiles without errors; all required artefacts present.

---

## General Guidance

- Work one stage at a time. Do not advance until the current stage's gate is met.
- Keep all intermediate artefacts in the `output/` directory tree.
- Record every significant decision in the provenance DAG.
- When a stage fails its gate, document why in the run ledger before retrying.

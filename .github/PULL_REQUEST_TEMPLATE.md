# 🔀 Pull Request: [Title]

## 📝 Description

<!-- 
Provide a clear, concise summary of the changes. 
Link to any relevant issues using 'Closes #123' syntax.
-->

**Impact Area:** [e.g., Core Infrastructure, Project X, CI/CD]
**Issue(s):** Closes #

### Local development (mirror CI)

```bash
uv sync
uv run ruff check infrastructure/ projects/*/src/
uv run ruff format --check infrastructure/ projects/*/src/
uv run mypy infrastructure/ projects/*/src/
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60 -m "not requires_ollama"
uv run pytest projects/*/tests/ --ignore=projects/fep_lean/tests/ --cov-fail-under=90 -m "not requires_ollama"
```

See [`.github/AGENTS.md`](../.github/AGENTS.md) for full troubleshooting and security commands.

---

## 🚀 Technical Requirements

### 💎 Quality Standards
- [ ] **Zero-Mock Policy**: Confirmed no use of `MagicMock`, `mocker.patch`, or `unittest.mock`. All tests use real data/computation.
- [ ] **Thin Orchestrator Pattern**: All business/scientific logic resides in `src/`. Scripts remain thin coordinators.
- [ ] **Architecture Alignment**: Changes respect the Layer 1 (Infra) vs Layer 2 (Project) separation.

### 🧪 Testing & Coverage
- [ ] **Infrastructure Coverage**: ≥ 60% (as reported by CI)
- [ ] **Project Coverage**: ≥ 90% (as reported by CI)
- [ ] **Pipeline Validation**: Full `./run.sh --pipeline` (or specific stages) passed locally.
- [ ] **Skill manifest** (if `infrastructure/**/SKILL.md` changed): Ran `uv run python -m infrastructure.skills write` and included `.cursor/skill_manifest.json` in the PR.
- [ ] **fep_lean CI** (only if `projects/fep_lean/**` changed): The **`fep_lean (real gauss + lake)`** job runs when `projects/fep_lean/lean/lean-toolchain` exists; otherwise it is skipped. Confirm expectations for forks without Lean/Open Gauss.

---

## 📊 Impact Analysis

- **[ ] Breaking Change**: Does this change break backward compatibility? (If so, detail migration path below)
- **[ ] Performance**: Any significant impact on import times or execution speed? (Threshold: ≤ 5s imports)
- **[ ] Dependencies**: Have any new dependencies been added to `pyproject.toml`?

---

## 🛠️ Pipeline Stages Affected

Select stages that changed or need verification (matches `./run.sh` / [`docs/RUN_GUIDE.md`](../docs/RUN_GUIDE.md); script numbers are `scripts/NN_*.py`):

| Stage | Primary path | Role |
| :--- | :--- | :--- |
| [ ] **0 — Clean** | `infrastructure/core/files/cleanup.py`, `infrastructure/core/pipeline/` | Pre-step output cleanup |
| [ ] **1 — Setup** | `scripts/00_setup_environment.py` | Env verification |
| [ ] **2 — Infra tests** | `scripts/01_run_tests.py`, `tests/infra_tests/` | Infrastructure suite |
| [ ] **3 — Project tests** | `scripts/01_run_tests.py`, `projects/*/tests/` | Project suite |
| [ ] **4 — Analysis** | `scripts/02_run_analysis.py`, `projects/*/scripts/` | Analysis scripts |
| [ ] **5 — Render** | `scripts/03_render_pdf.py` | PDF / multi-format render |
| [ ] **6 — Validate** | `scripts/04_validate_output.py`, `infrastructure/validation/` | Output QA |
| [ ] **7 — LLM review** | `scripts/06_llm_review.py` | Reviews (Ollama) |
| [ ] **8 — LLM translations** | `scripts/06_llm_review.py` | Translations (Ollama) |
| [ ] **9 — Copy** | `scripts/05_copy_outputs.py` | Deliverables → `output/` |
| [ ] **Executive report** | `scripts/07_generate_executive_report.py` | Multi-project summary |

---

## 📸 Testing Evidence

<!-- 
Please provide screenshots, command outputs, or logs confirming local success.
Example: uv run pytest output summary.
-->

<details>
<summary><b>View Testing Logs</b></summary>

```text
# Paste command output here
```
</details>

---

## ✅ Checklist

- [ ] `AGENTS.md` and `README.md` updated in the affected directories.
- [ ] All code is PEP8 compliant (Ruff check/format passed).
- [ ] Mypy type checking passes with zero errors.
- [ ] Security scan (`uv run bandit`) reveals no new issues.
- [ ] Commits follow project conventions (e.g., 'feat:', 'fix:', 'docs:').

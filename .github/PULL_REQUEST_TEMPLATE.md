# 🔀 Pull Request: [Title]

## 📝 Description

<!-- 
Provide a clear, concise summary of the changes. 
Link to any relevant issues using 'Closes #123' syntax.
-->

**Impact Area:** [e.g., Core Infrastructure, Project X, CI/CD]
**Issue(s):** Closes #

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

---

## 📊 Impact Analysis

- **[ ] Breaking Change**: Does this change break backward compatibility? (If so, detail migration path below)
- **[ ] Performance**: Any significant impact on import times or execution speed? (Threshold: ≤ 5s imports)
- **[ ] Dependencies**: Have any new dependencies been added to `pyproject.toml`?

---

## 🛠️ Pipeline Stages Affected

Select all stages modified or requiring verification:

| Stage | Path | Role |
| :--- | :--- | :--- |
| [ ] **01_clean** | `infrastructure/core/file_cleanup.py` | Directory cleanup |
| [ ] **02_setup** | `scripts/00_setup_environment.py` | Env verification |
| [ ] **03_infra_test** | `tests/infra_tests/` | Shared capabilities |
| [ ] **04_project_test** | `projects/*/tests/` | Domain logic |
| [ ] **05_analysis** | `projects/*/scripts/` | Scientific workflows |
| [ ] **06_render** | `projects/*/manuscript/` | PDF generation |
| [ ] **07_validate** | `infrastructure/validation/` | QA gates |
| [ ] **08_llm** | `scripts/06_llm_review.py` | AI evaluation |
| [ ] **09_report** | `scripts/07_generate_executive_report.py` | Multi-project reporting |
| [ ] **10_copy** | `scripts/05_copy_outputs.py` | Delivery |

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

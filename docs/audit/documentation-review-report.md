# Comprehensive Documentation Review
**Repository:** Research Project Template  
**Review Date:** 2026-04-27  
**Reviewer:** Hermes Agent (automated deep review)  
**Scope:** `/Users/4d/Documents/GitHub/template/docs` (all Markdown documentation)

---

## Executive Summary

A systematic review of all 165 Markdown files (42,134 lines) across the `docs/` directory revealed:

- **Broken internal links:** 5 critical broken references + 2 incorrect relative paths
- **Factual inaccuracies:** 2 locations with incorrect pipeline stage descriptions; 4 locations with incorrect command syntax
- **Outdated examples:** 5+ references to archived project `fep_lean` that should use current exemplar `code_project`
- **Missing cross-references:** 2 important top-level documents (PAI.md, CLOUD_DEPLOY.md) not surfaced in docs/README.md
- **Overall health:** Strong structure, comprehensive coverage, consistent terminology — mostly accurate and up-to-date.

---

## 1. Broken Internal Links (Critical)

These links point to files that do not exist in the current repository tree and will frustrate users clicking through documentation.

| # | File | Line | Broken Link | Correct Target / Recommendation |
|---|------|------|-------------|--------------------------------|
| 1 | `docs/README.md` | ~137 | `../projects/fep_lean/docs/` | Change to `../projects/code_project/docs/` (fep_lean archived, code_project is active exemplar) |
| 2 | `docs/best-practices/multi-project-management.md` | 36 | `../../projects/fep_lean/docs/` | Change to `../../projects/code_project/docs/` |
| 3 | `docs/documentation-index.md` | 192 | `../projects/fep_lean/` | Rephrase: refer to active projects via `_generated/active_projects.md` or use `code_project` |
| 4 | `docs/documentation-index.md` | 239 | `../projects/fep_lean/docs/` | Change to `../projects/code_project/docs/` |
| 5 | `docs/operational/config/configuration.md` | 143 | `../../../projects/fep_lean/src/gauss/cli.py` | Update to archived path `../../../projects_archive/fep_lean/src/gauss/cli.py` OR drop hyperlink while preserving conditional info |
| 6 | `docs/rules/documentation_standards.md` | 142 | `../infrastructure/AGENTS.md` | Should be `../../infrastructure/AGENTS.md` (from `docs/rules/` to `infrastructure/`) |
| 7 | `docs/rules/documentation_standards.md` | 410 | `configuration.md` | File does not exist; should be `../operational/config/configuration.md` |

**Impact:** Users following these links encounter 404s, undermining confidence in documentation accuracy.

---

## 2. Factual Inaccuracies (High Priority)

### 2.1 Incorrect Pipeline Stages in Glossary

- **File:** `docs/reference/glossary.md` — entry "Build Pipeline" (lines 45–47)
- **Incorrect:** "Stages: Tests → Scripts → Validation → Glossary → Individual PDFs → Combined PDF"
- **Reality:** The actual executor pipeline (pipeline.yaml + executor) runs: Clean Output Directories → Environment Setup → Infrastructure Tests → Project Tests → Project Analysis → PDF Rendering → Output Validation → Copy Outputs → [optional: LLM Scientific Review + LLM Translations]. There is no "Glossary" executor stage; glossary generation happens during rendering.
- **Fix:** Replace the stage list with a concise accurate description or reference the Preferred Terms entry (line 17) which is correct.

### 2.2 Invalid Coverage Commands in Quick-Start Cheatsheet

- **File:** `docs/reference/quick-start-cheatsheet.md`
- **Lines:** 24, 104, 113
- **Issue:** Uses `--cov=projects.code_project.src` (dot notation)
- **Correct:** `--cov=projects/code_project/src` (filesystem path)
- **Fix:** Replace all three occurrences with path-based coverage argument.

### 2.3 Invalid Import Example in Cheatsheet

- **File:** `docs/reference/quick-start-cheatsheet.md` — Line 88
- **Issue:** `from projects.code_project.src.example import calculate_average` assumes `projects/` is a package and references a non-existent module.
- **Fix:** Use real imports from code_project exemplar, e.g.: `from src.optimizer import gradient_descent`

---

## 3. Outdated Project Examples (Medium Priority)

The `fep_lean` project is archived under `projects_archive/` and is no longer an active project. Documentation should use `code_project` as the stable exemplar.

| File | Line(s) | Current Text | Recommended Change |
|------|---------|--------------|--------------------|
| `docs/README.md` | 137 | Example project with local docs: `../projects/fep_lean/docs/` | Change to `../projects/code_project/docs/` |
| `docs/best-practices/multi-project-management.md` | 36 | Example per-project docs hub: `projects/fep_lean/docs/` | Change to `projects/code_project/docs/` |
| `docs/documentation-index.md` | 192 (heading) | "fep_lean / CI paths" section | Rephrase to refer to generic active projects or `code_project` |
| `docs/documentation-index.md` | 239 | Example: `projects/fep_lean/docs/` | Change to `projects/code_project/docs/` |
| `docs/operational/config/configuration.md` | 143 | Link to `projects/fep_lean/src/gauss/cli.py` | Update to archived path `../../../projects_archive/fep_lean/src/gauss/cli.py` OR remove hyperlink (keep conditional text) |

**Note:** `docs/_generated/canonical_facts.md` contains historical fep_lean measurements — acceptable as archival snapshot; should not be hand-edited.

---

## 4. Missing Cross-References (Enhancement)

`docs/README.md` omits two important top-level documents from its Quick Links table:

- **`PAI.md`** — System identity and agent context
- **`CLOUD_DEPLOY.md`** — Headless cloud deployment guide

Adding these would improve discoverability for newcomers and automated agents.

---

## 5. Consistency & Completeness Check

- **AGENTS.md coverage:** All `docs/` subdirectories and all infrastructure modules have required AGENTS.md + README.md ✓
- **Pipeline stage count:** Consistently documented: Full = 10 stages in pipeline.yaml; Core = 8 stages (LLM stages excluded) ✓
- **No-mocks policy, coverage gates** all correctly documented ✓

---

## 6. Prioritized Action Items

**Priority 1 — Immediately address broken links:**
1. Update all fep_lean example paths to code_project in README, multi-project-management, documentation-index
2. Fix broken relative path in rules/documentation_standards.md line 142

**Priority 2 — Fix accuracy errors:**
3. Correct coverage commands in quick-start-cheatsheet.md
4. Fix invalid import example in the same file
5. Repair glossary Build Pipeline entry

**Priority 3 — Improve discoverability:**
6. Add PAI.md and CLOUD_DEPLOY.md to docs/README.md Quick Links
7. Update operational/config/configuration.md link to archived fep_lean path or remove hyperlink

---

## Conclusion

The documentation is **largely comprehensive and accurate**; the issues identified are mostly isolated broken links and accuracy slips that are straightforward to fix. Addressing these will raise the set to production-grade reliability.

**Regeneration note:** `audit_filepaths.py` validates link mechanics; a full contextual review (like this one) remains a manual periodic task.


# 📊 Comprehensive Filepath and Reference Audit Report

**Generated:** 2025-12-30 15:19:26
**Files Scanned:** 328
**Total Issues:** 599
**Scan Duration:** 0.61 seconds

## 📈 Executive Summary

🚨 **599 issues** found across 5 categories.

### Issues by Category

- **Broken Anchor Links:** 20 issues
- **Broken File Refs:** 3 issues
- **Code Block Paths:** 342 issues
- **Placeholder Consistency:** 168 issues
- **Cross Reference Issues:** 66 issues

## 📋 Repository Metadata

**Projects Found:** 10
- test, small_code_project, project1, small_prose_project, ento_linguistics, project, active_inference_meta_pragmatic, test_project, infrastructure, project2

**Documentation Distribution:**
- **.cursorrules/:** 17 files
- **.github/:** 4 files
- **.pytest_cache/:** 1 files
- **.venv/:** 9 files
- **docs/:** 80 files
- **infrastructure/:** 43 files
- **projects/:** 146 files
- **scripts/:** 2 files
- **tests/:** 22 files

## 🔍 Detailed Issues

### Broken Anchor Links (20 issues)

Anchor links that reference non-existent headings

**1.** `projects/active_inference_meta_pragmatic/manuscript/02_introduction.md:27`
- **Target:** `#fig:quadrant_matrix`
- **Issue:** Anchor not found in file
- **Text:** 1

**2.** `projects/active_inference_meta_pragmatic/manuscript/02_introduction.md:48`
- **Target:** `#sec:methodology`
- **Issue:** Anchor not found in file
- **Text:** 2

**3.** `projects/active_inference_meta_pragmatic/manuscript/02_introduction.md:48`
- **Target:** `#sec:experimental_results`
- **Issue:** Anchor not found in file
- **Text:** 3

**4.** `projects/active_inference_meta_pragmatic/manuscript/02_introduction.md:48`
- **Target:** `#sec:discussion`
- **Issue:** Anchor not found in file
- **Text:** 4

**5.** `projects/active_inference_meta_pragmatic/manuscript/02_introduction.md:48`
- **Target:** `#sec:conclusion`
- **Issue:** Anchor not found in file
- **Text:** 5

**6.** `projects/active_inference_meta_pragmatic/manuscript/03_methodology.md:7`
- **Target:** `#fig:quadrant_matrix`
- **Issue:** Anchor not found in file
- **Text:** 1

**7.** `projects/active_inference_meta_pragmatic/manuscript/04_experimental_results.md:172`
- **Target:** `#fig:efe_decomposition`
- **Issue:** Anchor not found in file
- **Text:** 2

**8.** `projects/active_inference_meta_pragmatic/manuscript/04_experimental_results.md:174`
- **Target:** `#fig:perception_action_loop`
- **Issue:** Anchor not found in file
- **Text:** 3

**9.** `projects/active_inference_meta_pragmatic/manuscript/04_experimental_results.md:176`
- **Target:** `#fig:generative_model_structure`
- **Issue:** Anchor not found in file
- **Text:** 4

**10.** `projects/active_inference_meta_pragmatic/manuscript/04_experimental_results.md:178`
- **Target:** `#fig:meta_level_concepts`
- **Issue:** Anchor not found in file
- **Text:** 5

*... and 10 more issues in this category*

### Broken File References (3 issues)

File paths that don't exist on disk

**1.** `.venv/lib/python3.12/site-packages/nltk-3.9.2.dist-info/licenses/README.md:15`
- **Target:** `CONTRIBUTING.md`
- **Issue:** File or directory does not exist: /Users/4d/Documents/GitHub/template/.venv/lib/python3.12/site-packages/nltk-3.9.2.dist-info/licenses/CONTRIBUTING.md
- **Text:** CONTRIBUTING.md

**2.** `projects/active_inference_meta_pragmatic/README.md:115`
- **Target:** `../LICENSE`
- **Issue:** File or directory does not exist: /Users/4d/Documents/GitHub/template/projects/LICENSE
- **Text:** LICENSE

**3.** `projects/ento_linguistics/.venv/lib/python3.12/site-packages/nltk-3.9.2.dist-info/licenses/README.md:15`
- **Target:** `CONTRIBUTING.md`
- **Issue:** File or directory does not exist: /Users/4d/Documents/GitHub/template/projects/ento_linguistics/.venv/lib/python3.12/site-packages/nltk-3.9.2.dist-info/licenses/CONTRIBUTING.md
- **Text:** CONTRIBUTING.md

### Invalid Code Block Paths (342 issues)

File paths in code examples that don't exist

**1.** `/Users/4d/Documents/GitHub/template/.cursorrules/AGENTS.md:179`
- **Target:** `infrastructure/<module>/`
- **Issue:** File path in code block does not exist: infrastructure/<module>/

**2.** `/Users/4d/Documents/GitHub/template/.cursorrules/api_design.md:293`
- **Target:** `infrastructure/example/__init__.py`
- **Issue:** File path in code block does not exist: infrastructure/example/__init__.py

**3.** `/Users/4d/Documents/GitHub/template/.cursorrules/documentation_standards.md:721`
- **Target:** `infrastructure/AGENTS.md)`
- **Issue:** File path in code block does not exist: infrastructure/AGENTS.md)

**4.** `/Users/4d/Documents/GitHub/template/.cursorrules/documentation_standards.md:421`
- **Target:** `infrastructure/AGENTS.md](../infrastructure/AGENTS.md)`
- **Issue:** File path in code block does not exist: infrastructure/AGENTS.md](../infrastructure/AGENTS.md)

**5.** `/Users/4d/Documents/GitHub/template/.cursorrules/documentation_standards.md:440`
- **Target:** `infrastructure/AGENTS.md)`
- **Issue:** File path in code block does not exist: infrastructure/AGENTS.md)

**6.** `/Users/4d/Documents/GitHub/template/.cursorrules/folder_structure.md:92`
- **Target:** `infrastructure/module/`
- **Issue:** File path in code block does not exist: infrastructure/module/

**7.** `/Users/4d/Documents/GitHub/template/.cursorrules/infrastructure_modules.md:11`
- **Target:** `infrastructure/<module>/`
- **Issue:** File path in code block does not exist: infrastructure/<module>/

**8.** `/Users/4d/Documents/GitHub/template/.cursorrules/infrastructure_modules.md:40`
- **Target:** `infrastructure/test_<module>/`
- **Issue:** File path in code block does not exist: infrastructure/test_<module>/

**9.** `/Users/4d/Documents/GitHub/template/.cursorrules/infrastructure_modules.md:289`
- **Target:** `infrastructure/example_module/`
- **Issue:** File path in code block does not exist: infrastructure/example_module/

**10.** `/Users/4d/Documents/GitHub/template/.cursorrules/testing_standards.md:64`
- **Target:** `infrastructure/test_<module>/`
- **Issue:** File path in code block does not exist: infrastructure/test_<module>/

*... and 332 more issues in this category*

### Placeholder Inconsistencies (168 issues)

Inconsistent use of {name} vs actual project names

**1.** `/Users/4d/Documents/GitHub/template/.cursorrules/AGENTS.md:41`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

**2.** `/Users/4d/Documents/GitHub/template/.cursorrules/AGENTS.md:45`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

**3.** `/Users/4d/Documents/GitHub/template/.cursorrules/AGENTS.md:46`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

**4.** `/Users/4d/Documents/GitHub/template/.cursorrules/AGENTS.md:50`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

**5.** `/Users/4d/Documents/GitHub/template/.cursorrules/AGENTS.md:51`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

**6.** `/Users/4d/Documents/GitHub/template/.cursorrules/AGENTS.md:377`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

**7.** `/Users/4d/Documents/GitHub/template/AGENTS.md:30`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

**8.** `/Users/4d/Documents/GitHub/template/AGENTS.md:31`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

**9.** `/Users/4d/Documents/GitHub/template/AGENTS.md:32`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

**10.** `/Users/4d/Documents/GitHub/template/AGENTS.md:33`
- **Target:** `{name}`
- **Issue:** Using placeholder {name} when specific project names exist: ['test', 'small_code_project', 'project1', 'small_prose_project', 'ento_linguistics', 'project', 'active_inference_meta_pragmatic', 'test_project', 'infrastructure', 'project2']

*... and 158 more issues in this category*

### Cross-Reference Issues (66 issues)

Invalid references between documentation files

**1.** `.cursorrules/AGENTS.md:152`
- **Target:** `../infrastructure/AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../infrastructure/AGENTS.md
- **Text:** ../infrastructure/AGENTS.md

**2.** `.cursorrules/AGENTS.md:182`
- **Target:** `../projects/project/manuscript/AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../projects/project/manuscript/AGENTS.md
- **Text:** ../projects/project/manuscript/AGENTS.md

**3.** `.cursorrules/AGENTS.md:245`
- **Target:** `../AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../AGENTS.md
- **Text:** Root AGENTS.md

**4.** `.cursorrules/AGENTS.md:246`
- **Target:** `../infrastructure/AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../infrastructure/AGENTS.md
- **Text:** Infrastructure AGENTS.md

**5.** `.cursorrules/AGENTS.md:248`
- **Target:** `../projects/project/AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../projects/project/AGENTS.md
- **Text:** Project AGENTS.md

**6.** `.cursorrules/AGENTS.md:362`
- **Target:** `../AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../AGENTS.md
- **Text:** Root AGENTS.md

**7.** `.cursorrules/AGENTS.md:367`
- **Target:** `../AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../AGENTS.md
- **Text:** Root AGENTS.md

**8.** `.cursorrules/AGENTS.md:371`
- **Target:** `../infrastructure/AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../infrastructure/AGENTS.md
- **Text:** infrastructure/AGENTS.md

**9.** `.cursorrules/AGENTS.md:380`
- **Target:** `../tests/AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../tests/AGENTS.md
- **Text:** tests/AGENTS.md

**10.** `.cursorrules/AGENTS.md:409`
- **Target:** `../infrastructure/llm/AGENTS.md`
- **Issue:** Invalid AGENTS.md reference: ../infrastructure/llm/AGENTS.md
- **Text:** infrastructure/llm/AGENTS.md

*... and 56 more issues in this category*

## 💡 Recommendations

**Fix Broken Anchor Links:**
- Update heading names to match anchor references
- Use the correct heading case and formatting
- Consider using explicit anchor IDs: `# Heading {#custom-anchor}`

**Fix Broken File References:**
- Verify file paths exist and are spelled correctly
- Use relative paths from the document's location
- Update paths after file reorganization

**Fix Code Block Paths:**
- Ensure example file paths actually exist
- Use real project names instead of placeholders where appropriate
- Update examples after project restructuring

**Standardize Placeholders:**
- Use `{name}` consistently for template examples
- Use actual project names when referencing specific projects
- Document which placeholders should be replaced

**Fix Cross-References:**
- Ensure AGENTS.md files exist for all documented directories
- Update references after file reorganization
- Use consistent relative paths for cross-references

**General Best Practices:**
- Run this audit regularly (e.g., pre-commit hooks)
- Update documentation immediately after code changes
- Use relative paths for better portability
- Test all code examples manually

## 🔧 Technical Details

### Validation Categories

- **Markdown Links:** Internal `[text](path)` and anchor `[text](#anchor)` links
- **File References:** Direct file path references in documentation
- **Code Blocks:** File paths mentioned in code examples
- **Directory Structures:** ASCII tree representations vs actual filesystem
- **Python Imports:** Import statements in code blocks
- **Placeholders:** Template variables like `{name}` vs actual names
- **Cross-References:** References between documentation files

### Exclusions

- Output directory references (generated files)
- External URLs (http/https)
- Template placeholders that cannot be resolved

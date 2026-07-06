# Manuscript Section Numbering System - Documentation

## Overview — the section numbering scheme supported by the render pipeline

The render pipeline supports main sections, supplemental sections, and proper reference
ordering. The file names below are **illustrative slots** the ordering rules support — not
files that ship in any exemplar. The canonical `template_code_project/manuscript/` ships
`00_*.md` through `07_*.md` plus `99_references.md`; add the optional `08`/`09`/`S##`/`98`
slots only if your project needs them.

---

## 📋 Numbering Scheme

### Main Sections (00-09)

Core manuscript content with sequential numbering (example titles):

- `00_abstract.md` - Research overview
- `01_introduction.md` - Project introduction
- `02_methodology.md` - Methods and algorithms
- `03_results.md` - Results and evaluation
- `04_conclusion.md` - Summary and future work
- `08_acknowledgments.md` - Funding and acknowledgments (optional slot)
- `09_appendix.md` - Technical details and proofs (optional slot)

### Supplemental Sections (S01-S0N)

Additional material supporting main manuscript (optional slots — none shipped by default):

- `S01_supplemental_methods.md` - Extended methodological details (optional slot)
- `S02_supplemental_results.md` - Additional experimental results (optional slot)
- `S##_*.md` - Future supplemental sections

### Reference Sections (98-99)

Always appear last in document:

- `98_symbols_glossary.md` - Auto-generated API reference (second to last)
- `99_references.md` - Bibliography (always last)

---

## 🔄 Document Ordering

The build system ensures proper ordering:

1. **Main Sections** (01-09) - Core manuscript content
2. **Supplemental Sections** (S01-S0N) - Additional material
3. **Glossary** (98) - API reference
4. **References** (99) - Bibliography (always last)

**Example order:**

```
01_abstract.md
02_introduction.md
03_methodology.md
04_experimental_results.md
05_discussion.md
06_conclusion.md
08_acknowledgments.md
09_appendix.md
S01_supplemental_methods.md
S02_supplemental_results.md
98_symbols_glossary.md
99_references.md
```

---

## 🧩 Optional Section Slots (illustrative)

The slots below are supported by the ordering rules but are **not shipped in any exemplar**.
The content lists describe what each slot is *for* if you choose to add it.

### 1. **08_acknowledgments.md** (Main Section)

**Content:**

- Funding sources
- Computing resources
- Collaborations
- Data and software acknowledgments
- Feedback and review
- Institutional support

**Cross-references:**

- References experimental results ([@sec:experimental_results])

### 2. **09_appendix.md** (Main Section)

**Content:**

- Detailed proofs (convergence, complexity)
- Extended experimental details
- Hyperparameter settings
- Computational environment
- Additional benchmark comparisons
- Implementation pseudocode

**Cross-references:**

- References equations from methodology (e.g., [@eq:convergence])
- References figures from results (e.g., [@fig:convergence_plot])

### 3. **S01_supplemental_methods.md** (Supplemental Section)

**Content:**

- Extended algorithm variants (stochastic, mini-batch)
- Detailed convergence analysis
- Additional theoretical results
- Implementation considerations
- Generalized objective functions
- Convergence diagnostics
- Parameter sensitivity analysis

**Cross-references:**

- References main methodology ([@sec:methodology])
- References main equations (e.g., [@eq:update])

### 4. **S02_supplemental_results.md** (Supplemental Section)

**Content:**

- Extended benchmark results (15 additional datasets)
- performance comparison
- Detailed convergence behavior
- Scalability analysis
- Robustness analysis
- Domain-specific comparisons
- Real-world case studies

**Cross-references:**

- References main results ([@sec:experimental_results])
- References main figures (e.g., [@fig:convergence_plot])

---

## 🛠️ Build System Changes

### 1. **Manuscript discovery (`infrastructure/rendering/manuscript_discovery.py`)**

#### `discover_manuscript_files()` function

The render pipeline (driven by `scripts/pipeline/stage_03_render.py` / `scripts/execute_pipeline.py`)
delegates section discovery and ordering to the Python function
`discover_manuscript_files()`, which buckets and sorts sections by prefix:

1. Main sections (`00_*.md`–`09_*.md` and any other non-`98`/`99` sections)
2. Supplemental sections (`S##_*.md`)
3. Glossary (`98_*.md`)
4. References (`99_*.md`, always last)

**Effect:** Ensures correct document ordering regardless of filesystem ordering.

#### Updated glossary generation

Glossary generation simplified:

```bash
# Run glossary generation (example: template_code_project)
uv run python -m infrastructure.documentation.generate_glossary_cli \
  projects/templates/template_code_project/src/ projects/templates/template_code_project/manuscript/98_symbols_glossary.md
```

**Effect:** Generates glossary directly in `manuscript/98_symbols_glossary.md` - no intermediate files or copy steps needed.

### 2. **File Renames**

| Old Name | New Name | Reason |
|----------|----------|--------|
| `07_references.md` | `99_references.md` | Always last section |
| `98_symbols_glossary.md` | `98_symbols_glossary.md` | Second to last (before references) |

### 3. **Directory Structure Simplification**

**Removed:** `markdown/` directory (no longer needed)

- Previously used as staging area for glossary generation
- Glossary now generated directly in `manuscript/98_symbols_glossary.md`
- Eliminates redundant copy step

---

## 📚 Documentation Updates

### 1. **manuscript/AGENTS.md**

**Updated sections:**

- File Structure table with all sections
- Numbering Convention with detailed explanation
- Adding New Sections instructions
- Cross-referencing examples
- Troubleshooting section ordering issues

### 2. **manuscript/README.md**

**Updated sections:**

- Structure section with all files
- Numbering Convention explained
- Section Ordering details
- Quick reference commands

### 3. **manuscript/98_symbols_glossary.md**

**Current status:**

```markdown
**Note:** This glossary is auto-generated from `src/` via `python -m infrastructure.documentation.generate_glossary_cli` (see [`docs/modules/modules-guide.md`](../modules/modules-guide.md)); run manually with explicit `src/` and glossary markdown paths per project.
```

---

## ✅ Testing and Validation

### Discovery Function Test

```bash
cd manuscript
(find . -maxdepth 1 -name "0[0-9]_*.md" | sort; \
 find . -maxdepth 1 -name "S[0-9][0-9]_*.md" | sort; \
 find . -maxdepth 1 -name "98_*.md"; \
 find . -maxdepth 1 -name "99_*.md")
```

**Expected Output (illustrative — assumes all optional slots are populated):**

```
01_abstract.md
02_introduction.md
03_methodology.md
04_experimental_results.md
05_discussion.md
06_conclusion.md
08_acknowledgments.md
09_appendix.md
S01_supplemental_methods.md
S02_supplemental_results.md
98_symbols_glossary.md
99_references.md
```

The canonical `template_code_project/manuscript/` ships only `00_*.md`–`07_*.md` and
`99_references.md`; the optional `08`/`09`/`S##`/`98` slots above appear only if you add them.

---

## 🎯 Usage Examples

### Adding New Main Section

```bash
# Create new main section
vim manuscript/07_limitations.md

# Add section header
# Limitations {#sec:limitations}
#
# Content here...

# Build and verify
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

**Result:** Section appears between 06_conclusion.md and 08_acknowledgments.md.

### Adding New Supplemental Section

```bash
# Create new supplemental section
vim manuscript/S03_supplemental_figures.md

# Add section header
# Supplemental Figures {#sec:supplemental_figures}
#
# Extended visualizations...

# Reference from main text
# See [@sec:supplemental_figures] for additional figures.

# Build and verify
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

**Result:** Section appears after S02 and before glossary (98).

### Deleting markdown/ directory

**Answer: Already deleted! ✅**

The `markdown/` directory was a temporary staging area that is no longer needed.

**Current workflow:**

```
python -m infrastructure.documentation.generate_glossary_cli → manuscript/98_symbols_glossary.md
                           ↓ (include)
                       Combined PDF
```

**Benefits:**

- Simpler build process
- No redundant files
- No intermediate copy step
- Single source of truth

---

## 🔍 Cross-Referencing

All cross-references use Pandoc bracket-cite syntax `[@sec:label]` — never
raw `\ref{}` (see [Manuscript Semantics](../guides/manuscript-semantics.md)).

### Main ↔ Main

```markdown
As described in [@sec:methodology]...
```

### Main → Supplemental

```markdown
Extended details in [@sec:supplemental_methods]...
Additional results in [@sec:supplemental_results]...
```

### Supplemental → Main

```markdown
Building on the framework from [@sec:methodology]...
```

### Any → Glossary/References

```markdown
See API reference in [@sec:glossary]...
Citations in [@sec:references]...
```

---

## 📊 Section Summary

This table lists every slot the ordering rules support. "Slot status" indicates whether the
canonical `template_code_project` exemplar ships a file for that slot.

| Slot | Example File | Type | Slot Status |
|------|--------------|------|-------------|
| 00-07 | abstract / introduction / methodology / results / conclusion / setup / reproducibility / scope | Main | Shipped by `template_code_project` |
| 08 | acknowledgments.md | Main | Optional (not shipped) |
| 09 | appendix.md | Main | Optional (not shipped) |
| S01 | supplemental_methods.md | Supplement | Optional (not shipped) |
| S02 | supplemental_results.md | Supplement | Optional (not shipped) |
| 98 | symbols_glossary.md | Reference | Optional, auto-generated when present |
| 99 | references.md | Reference | Shipped by `template_code_project` |

---

## 🎉 Benefits of New System

### 1. **Clear Separation**

- Main content: 01-09
- Supplemental material: S01-S0N
- References: 98-99 (always last)

### 2. **Extensible**

- Easy to add new main sections (10+)
- Easy to add supplemental sections (S03+)
- No renumbering required for existing sections

### 3. **Predictable Ordering**

- Explicit ordering rules in build script
- References always last
- Glossary always second to last

### 4. **Professional Structure**

- Matches academic publication standards
- Clear distinction between main and supplemental
- Proper reference placement

---

## ✅ Capabilities Supported by the Numbering System

- ✅ Optional main-section slots (08, 09)
- ✅ Optional supplemental-section slots (S01, S02, …)
- ✅ References pinned last (99)
- ✅ Glossary pinned second-to-last (98), auto-generated when present
- ✅ Deterministic ordering in the build system
- ✅ Cross-referencing across main/supplemental/glossary/references

**The system is ready for use with section numbering support — add the optional slots as needed.**

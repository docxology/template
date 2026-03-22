# InferAnt Stream #018.1 — overview

**When:** 22 March 2026, 22:00 UTC  
**Host:** Daniel Friedman  
**Paper:** *A `template/` approach to Reproducible Generative Research: Architecture and
Ergonomics from Configuration through Publication*

---

## Links

- **Livestream:** [YouTube](https://www.youtube.com/live/YvnvWzHTQu8)
- **Paper (Zenodo):** [zenodo.org/records/19139090](https://zenodo.org/records/19139090)
- **Repository:** [github.com/docxology/template](https://github.com/docxology/template) (Apache-2.0)

---

## Teaser (one screen)

- Computational reproducibility is often a **workflow problem**: manuscript, code, data, and
  build steps drift apart because nothing in the toolchain **enforces** them as one system.
- **`template/`** treats the research lifecycle as **infrastructure-as-code**: versioned
  manuscript, tests, analysis scripts, and outputs wired through a **single pipeline** with
  explicit quality gates.
- **Two-layer layout:** reusable `infrastructure/` (generic tooling) vs `projects/<name>/`
  workspaces (domain code, tests, manuscript). Scripts stay thin; logic lives in importable
  modules under test.
- **No-mock tests** and **coverage floors** (90% project `src/`, 60% infrastructure) use real
  files, subprocesses, and local HTTP where APIs matter—not stubbed collaborators.
- **Rendering:** Pandoc + XeLaTeX PDFs, optional slides/HTML; **optional LLM** stages for review
  and translations when Ollama (or equivalent) is available.
- **Provenance / watermarking:** SHA-256 manifests and steganographic PDF hardening are available
  via **`./secure_run.sh`**, a wrapper around the standard pipeline—not the default
  `./run.sh --pipeline` path alone.

---

## Suggested run-of-show

| Segment | Minutes | Focus |
|--------|--------|--------|
| 1. Hook | ~3 | Why “reproducibility” fails without enforced invariants; cite Sources below. |
| 2. Design | ~8 | Two-layer architecture; thin orchestrators; `projects/` vs `projects_in_progress/`. |
| 3. Pipeline | ~10 | Core vs full run: `execute_pipeline.py --core-only` vs `./run.sh --pipeline`; where LLM fits. |
| 4. Quality | ~7 | Coverage, no-mock policy, validation CLI; what actually breaks the build. |
| 5. Docs + agents | ~7 | README + AGENTS “duality”; `SKILL.md` on **major** infrastructure subpackages (not every leaf module). |
| 6. Paper | ~10 | Comparative claims, figures, Zenodo artifact—**as argued in the paper**, not re-derived live. |
| 7. Q&A | ~10 | Clone, `uv sync`, `./run.sh`; Apache-2.0; limitations / WIP. |

*(Adjust timing to your format.)*

---

## Expanded abstract (paper voice, tightened)

### Motivation

The reproducibility crisis in computational work is structural as often as statistical: artifacts
live in LaTeX editors, notebooks, and one-off scripts, without a single enforced mechanism keeping
code, data, and manuscript aligned. Survey and meta-scientific work suggests widespread concern
about false-positive rates, limited replication in some fields, and poor notebook executability at
scale—see **Sources** for entry points rather than paraphrasing headlines as settled fact.

Workflow engines (Snakemake, Nextflow, CWL) orchestrate computation; literate stacks (Quarto,
Jupyter Book, R Markdown, and hosted editors) render documents; data tools (DVC, etc.) track
artifacts. **`template/`** is aimed at the gap where **cross-cutting quality rules** (tests,
coverage, validation, rendering) should be **architectural invariants**, not optional hygiene.

### System design

`template/` applies infrastructure-as-code to the research lifecycle: the manuscript, test suite,
and build graph stay version-controlled, deterministically rebuildable, and independently
checkable where the pipeline is configured to run.

A **two-layer architecture** separates generic **`infrastructure/`** (many Python modules and
subpackages) from **`projects/<name>/`** workspaces. An orchestrated flow runs **environment setup
and cleanup**, **tests** (infrastructure + per-project), **analysis scripts**, **PDF (and related)
rendering**, **output validation**, then **copy to `output/<name>/`**. That **core** path omits LLM
stages. A **full** `./run.sh --pipeline` adds **optional LLM review and translations** (when
enabled and a local model endpoint is available). **Cryptographic hashing and steganographic PDF
post-processing** are provided through **`./secure_run.sh`**, which runs the standard pipeline and
then hardens PDFs—see repo docs for details.

Documentation is organized so humans get **`README.md`** and tooling/agents get **`AGENTS.md`**
across major directories. Major **`infrastructure/<area>/`** trees also ship **`SKILL.md`** files
describing capabilities for agent workflows (aligned with common “skills” / MCP-style usage—not a
claim that every single `.py` file has its own skill file).

### Evidence and scope

At the scale of **this repository snapshot** (pytest collection, March 2026): **`code_project`**
carries **39** collected tests; the **default suite** collects on the order of **~2,900** tests
across infrastructure, integration, and included projects (exact count moves with branches and
markers). The Zenodo paper discusses **additional heterogeneous workspaces** (e.g. a large
meta-analysis pipeline and a self-referential architectural project); some of those live under
**`projects_in_progress/`** in upstream layouts, while **`./run.sh` discovers `projects/` only**—so
“three projects on every laptop” is a **paper / configuration** claim, not the default menu on an
arbitrary clone.

The manuscript-as-pipeline point still holds when you run the stack end-to-end: prose, metrics,
and figures can be produced by the same pipeline they describe—**subject to** which projects are
active and which optional stages are enabled.

### Comparative claims and limitations

A tabular comparison against other tools appears **in the paper**; treat strong uniqueness claims
as **paper findings** to be read and challenged there. **`template/`** is **open source**
(Apache-2.0) and explicitly **work in progress**.

---

## Sources (reproducibility context)

Use these for on-stream attribution; quote the papers, not blog summaries.

1. Ioannidis, J. P. A. (2005). *Why Most Published Research Findings Are False.* PLoS Medicine.
   (Often summarized; read the assumptions before repeating “most findings are false.”)
2. Open Science Collaboration (2015). *Estimating the reproducibility of psychological science.*
   Science.
3. Pimentel, J. F. et al. (2019). *A Large-Scale Study About Quality and Reproducibility of Jupyter
   Notebooks.* IEEE/ACM MSR. (Large GitHub-scale sample; executability definitions and percentages
   vary by study—compare methods before citing a single number.)

---

## Speaker notes / CTA

- Skim the **Zenodo PDF** for definitions, tables, and citations you do not want to improvise.
- **Try it:** clone [github.com/docxology/template](https://github.com/docxology/template),
  `uv sync`, then `./run.sh` (interactive) or `./run.sh --pipeline` / core-only per
  [CLAUDE.md](https://github.com/docxology/template/blob/main/CLAUDE.md).
- **Optional hardening:** `./secure_run.sh` after you have PDFs you want to post-process.

---

## Pytest collection (sanity check)

Recorded from this tree with `uv run pytest --collect-only -q` (March 2026): **2,898** tests
collected (**12** deselected by default markers); **`projects/code_project/tests/`** → **39**
collected. Re-run before publishing if numbers matter for the livestream.

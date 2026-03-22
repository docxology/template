# InferAnt Stream #018.1 — Reproducible research as infrastructure

<https://www.youtube.com/live/YvnvWzHTQu8>

**When:** 22 March 2026  
**Host:** Daniel Friedman  
**Paper:** *A `template/` approach to Reproducible Generative Research: Architecture and Ergonomics from Configuration through Publication*

---

## Opening overview (first ~60s)

**What you’ll see in ~55 minutes**

1. **Why reproducibility is a workflow problem** — not only a statistics problem — and what breaks when nothing *enforces* one build graph.
2. **A live walk through the repo** — two layers (`infrastructure/` vs `projects/<name>/`), thin scripts, real tests (no mocks), coverage floors.
3. **Demo A → Demo B** — `./run.sh` (menu or full pipeline), then `./secure_run.sh` so you see **plain PDFs** vs **hardened companions** and hash manifests.
4. **Paper + Q&A** — Zenodo artifact for deep claims; chat drives “what should we run next?”

**Follow-along (optional)**

| Need | Command / note |
|------|----------------|
| Python deps | `uv sync` from repo root |
| Full PDF path | `pandoc` + `xelatex` on PATH (see [RUN_GUIDE.md](../RUN_GUIDE.md) if installs fail) |
| LLM stages | Optional; local endpoint (e.g. Ollama) if you want reviews/translations live |
| Shorter run | `python3 scripts/execute_pipeline.py --project <name> --core-only` skips LLM stages |

**Host cue:** *“Type `1` if you’re here for the pipeline, `2` for stego, `3` for both — I’ll weight the demo.”*

---

## Links

- **Livestream:** [YouTube](https://www.youtube.com/live/YvnvWzHTQu8)
- **Paper (Zenodo):** [zenodo.org/records/19139090](https://zenodo.org/records/19139090)
- **Repository:** [github.com/docxology/template](https://github.com/docxology/template) (Apache-2.0)

---

## TL;DR bullets

- Computational reproducibility is often a **workflow problem**: manuscript, code, data, and build steps drift because nothing in the toolchain **enforces** them as one system.
- **`template/`** treats the research lifecycle as **infrastructure-as-code**: versioned manuscript, tests, analysis scripts, and outputs wired through a **single pipeline** with explicit quality gates.
- **Two-layer layout:** reusable `infrastructure/` (generic tooling) vs `projects/<name>/` workspaces (domain code, tests, manuscript). Scripts stay thin; logic lives in importable modules under test.
- **No-mock tests** and **coverage floors** (90% project `src/`, 60% infrastructure) use real files, subprocesses, and local HTTP where APIs matter — not stubbed collaborators.
- **Rendering:** Pandoc + XeLaTeX PDFs, optional slides/HTML; **optional LLM** stages for review and translations when a local model endpoint is available.
- **Provenance / hardening:** cryptographic manifests and steganographic PDF post-processing ship behind **`./secure_run.sh`** (wrapper around the same pipeline as `./run.sh`), not as an invisible side effect of `./run.sh --pipeline` alone.

---

## Agenda — run of show

| # | Segment | Minutes | Focus | Interactive beat |
|---|---------|--------:|-------|------------------|
| 1 | Hook | ~3 | Why “reproducibility” fails without enforced invariants | Chat: *“What failed last time you tried to reproduce a paper?”* |
| 2 | Design | ~8 | Two-layer architecture; thin orchestrators; `projects/` vs `projects_in_progress/` | *“Guess: where does business logic live — `scripts/` or `src/`?”* |
| 3 | **Demo — `run.sh`** | ~12 | Interactive menu vs `./run.sh --pipeline`; logs `[0/9]` clean then `[1/9]`–`[9/9]` | *“Pause: tests, LaTeX, or validation — which breaks first on a dirty laptop?”* |
| 4 | **Demo — `secure_run.sh`** | ~10 | Two-act wrapper: pipeline then stego; `--steganography-only` shortcut | Side-by-side: original PDF vs `*_steganography.pdf`; show `.hashes.json` |
| 5 | Quality | ~7 | Coverage, no-mock policy, validation CLI; what actually fails the build | Quick: open a failing log path from chat |
| 6 | Docs + agents | ~7 | README + AGENTS “duality”; `SKILL.md` on **major** infrastructure subpackages | *“Where would you point an agent first?”* |
| 7 | Paper | ~10 | Comparative claims, figures, Zenodo artifact — **as argued in the paper** | *“Save deep uniqueness debates for the PDF.”* |
| 8 | Q&A | ~10 | Clone, `uv sync`, `./run.sh`; Apache-2.0; limitations / WIP | Stack ranked: features vs pain points |

### Minute strip (glance card)

| Clock | Beat |
|------:|------|
| 0:00 | Welcome, links in chat, follow-along disclaimer (LaTeX time) |
| 0:05 | Problem frame + “one pipeline” promise |
| 0:15 | Repo tree: `infrastructure/`, `projects/`, `output/` |
| 0:25 | **`./run.sh`** — show menu, then or instead `--pipeline` |
| 0:40 | **`./secure_run.sh`** — narrate STEP 1/2 vs STEP 2/2 |
| 0:52 | Quality gates + docs map |
| 0:62 | Paper pointer + Q&A |

Adjust spacing if you run **`execute_pipeline.py --core-only`** for a shorter middle act.

---

## Live demo — `./run.sh` then `./secure_run.sh`

### Act 1 — `./run.sh` (the standard front door)

- **Interactive:** Running `./run.sh` with no pipeline flags opens the **menu** (environment, tests, analysis, render, validate, copy, optional LLM operations, full pipeline). Good for *showing* how operators slice the workflow.
- **Non-interactive full pipeline:** `./run.sh --pipeline` runs the **full** sequence. Progress logs use **`[0/9]`** for the clean pre-step and **`[1/9]` … `[9/9]`** for the numbered stages (see [run.sh](../../run.sh) comments and help).
- **Resume:** `./run.sh --pipeline --resume` continues from checkpoint (mention if you hit a long build).
- **Core-only via secure entry:** `./secure_run.sh --core-only` forwards `--core-only` to `run.sh`, skipping LLM stages but still running the stego pass afterward.

**Host cues**

- *“Watch the stage counter — that’s the spine of the episode.”*
- *“If this catches fire, we’ll open the log path the script prints, not guess.”*

### Act 2 — `./secure_run.sh` (pipeline + hardening)

[`secure_run.sh`](../../secure_run.sh) is intentionally a **two-step story**:

1. **STEP 1/2 —** Runs `bash run.sh` with any forwarded args (`--project`, `--core-only`, `--skip-infra`, etc.).
2. **STEP 2/2 —** Steganographic post-processing on generated PDFs: companion **`*_steganography.pdf`** files and **`.hashes.json`** manifests; **original PDFs stay untouched**.

**Already built?** Use `./secure_run.sh --steganography-only --project <name>` to re-run **only** the hardening pass (useful if the stream ran the pipeline off-air).

**Where to point the screen**

| Artifact | Typical location (per `secure_run.sh` completion banner) |
|----------|---------------------------------------------------------|
| Standard PDFs | `projects/<name>/output/pdf/*.pdf` |
| Hardened copies | `projects/<name>/output/pdf/*_steganography.pdf` |
| Hash manifests | `projects/<name>/output/pdf/*.hashes.json` |

The copy stage also mirrors deliverables under **`output/<name>/`** (see [05_copy_outputs.py](../../scripts/05_copy_outputs.py)); if PDFs were only under `output/<name>/`, the stego processor’s fallback search can still find them — but the script’s **printed** locations center `projects/<name>/output/pdf/`.

**Interactive beats**

- Before STEP 1: *“Chat poll: will we fail on tests, TeX, or validation?”*
- After STEP 2: *“Spot the diff — zoom a page footer; ask what metadata now exists.”*

---

## Motivation

**Host cue:** *“We’re not dunking on notebooks — we’re showing what happens when nothing *binds* manuscript + code + outputs.”*

The reproducibility crisis in computational work is structural as often as statistical: artifacts live in LaTeX editors, notebooks, and one-off scripts, without a single enforced mechanism keeping code, data, and manuscript aligned. Survey and meta-scientific work raises concerns about false-positive rates, limited replication in some fields, and poor notebook executability at scale — use **Sources** below as entry points; treat headlines as pointers, not settled law on air.

---

## System design

**Host cue:** *“If you remember one thing: logic in modules, scripts coordinate.”*

`template/` applies infrastructure-as-code to the research lifecycle: the manuscript, test suite, and build graph stay version-controlled, deterministically rebuildable, and independently checkable where the pipeline is configured to run.

A **two-layer architecture** separates generic **`infrastructure/`** (many Python modules and subpackages) from **`projects/<name>/`** workspaces. An orchestrated flow runs **environment setup and cleanup**, **tests** (infrastructure + per-project), **analysis scripts**, **PDF (and related) rendering**, **output validation**, then **copy to `output/<name>/`**. That **core** path omits LLM stages. A **full** `./run.sh --pipeline` adds **optional LLM review and translations** when enabled and a local model endpoint is available. **Cryptographic hashing and steganographic PDF post-processing** are provided through **`./secure_run.sh`**, which runs the standard pipeline (via `run.sh`) and then hardens PDFs — see [AGENTS.md](../../AGENTS.md) and [scripts/AGENTS.md](../../scripts/AGENTS.md) for detail.

Documentation is organized so humans get **`README.md`** and tooling/agents get **`AGENTS.md`** across major directories. Major **`infrastructure/<area>/`** trees also ship **`SKILL.md`** files describing capabilities for agent workflows (aligned with common “skills” / MCP-style usage — not a claim that every `.py` file has its own skill file).

---

## Evidence and scope

**Host cue:** *“Numbers are from *this* clone — your pytest count will move with branches.”*

At the scale of **this repository snapshot** (pytest collection, March 2026): **`code_project`** carries **39** collected tests; the **default suite** collects on the order of **~2,900** tests across infrastructure, integration, and included projects (exact count moves with branches and markers). The Zenodo paper discusses **additional heterogeneous workspaces** (e.g. a large meta-analysis pipeline and a self-referential architectural project); some of those live under **`projects_in_progress/`** in upstream layouts, while **`./run.sh` discovers `projects/` only** — so “three projects on every laptop” is a **paper / configuration** claim, not the default menu on an arbitrary clone.

The manuscript-as-pipeline point still holds when you run the stack end-to-end: prose, metrics, and figures can be produced by the same pipeline they describe — **subject to** which projects are active and which optional stages are enabled.

---

## Comparative claims and limitations

**Host cue:** *“Strong uniqueness lives in the paper’s tables — challenge it there.”*

A tabular comparison against other tools appears **in the paper**; treat strong uniqueness claims as **paper findings** to be read and challenged there. **`template/`** is **open source** (Apache-2.0) and explicitly **work in progress**.

---

## Sources (entry points)

- [Zenodo record 19139090](https://zenodo.org/records/19139090) — versioned paper + artifact context  
- [template repository](https://github.com/docxology/template) — source, issues, `README.md` / `AGENTS.md`  
- Further citations and comparison tables — **see the paper’s bibliography** (not duplicated here to avoid drift from the published PDF)

# Technology

```{=latex}
\begin{multicols}{3}
```

**Systems and software**

**SAN FRANCISCO.** Stem `05_technology` is where the exemplar winks at its own stack. Pandoc converts CommonMark plus fenced `{=latex}` into LaTeX; XeLaTeX sets the type; BibTeX (when invoked) resolves `\cite{template2026gazette}` from `references.bib`. None of that is news, but it belongs in a technology folio the way a real paper covers Silicon Valley.

Product managers debated release cadences for developer tools. Feature flags, staged rollouts, and telemetry ethics appear as phrases without SDK names, avoiding trademark noise in a template repository. If you need literal package versions, print them from `uv.lock` in supplemental prose during release notes, not in this static slice.

Security editors summarized supply-chain hygiene: verify hashes, pin dependencies, rotate keys. The template’s own stance appears in root tests: no mocks in project suites, subprocess calls for scripts, and coverage floors on `src/`. Extending that story here keeps the technology desk aligned with engineering policy.

Cloud architects sketched multi-region failover without naming vendors. Diagrams would normally accompany this section; the layout schematic in `S01` is the closest built-in figure besides the masthead. Consider generating architecture PNGs from matplotlib the same way `layout_figure.render_layout_schematic_png` works.

Open-source maintainers pleaded for contributor documentation. `AGENTS.md` files per directory echo that plea. AI assistants read them for API surfaces; humans read them for operational commands. Dual documentation is a deliberate pattern, not duplication for its own sake.

Consumer hardware reviewers compared battery life claims under standardized loops. Numbers are absent on purpose. When you add benchmarks, store CSV under `output/data/` and cite the path in supplemental text so validators can find assets.

A networking brief explained latency budgets for interactive applications. Web output from `WebRenderer` uses MathJax-ready HTML; slide decks use Beamer. Each format reuses the same ordered manuscript list, proving the single-source claim in the system docs.

Closing line: upgrade paths belong in `docs/`, not in hot type. This folio ends so `06_sports` can pick up with a different voice and rhythm, which helps multicolumn balance across spreads.

**Depth notes.** Semantic versioning communicates breaking changes to library consumers. Changelogs pair with migration guides. The template’s root `pyproject.toml` pins tool versions; newspaper-specific deps live in `projects/traditional_newspaper/pyproject.toml`. Keep those files honest when bumping matplotlib or numpy used by masthead and layout figures.

Container images bake OS packages and Python wheels. Supply-chain attestations (SLSA, Sigstore) gain traction. CI pipelines that build PDFs should record compiler and Pandoc versions in build logs; `execute_pipeline` already captures stage timing for regression hunts.

Accessibility on the web means keyboard navigation, focus order, and alt text for figures. PDF accessibility adds tagged structure and reading order headaches. This project’s HTML path is secondary to print-shaped PDFs, but `convert_latex_images.lua` tries to preserve captions—verify with a browser after changes.

Observability stacks correlate logs, metrics, and traces. SREs define SLOs and error budgets. Research pipelines can adopt the same language: success rate of PDF compiles, p95 stage duration, count of validation warnings per run.

Firmware updates for embedded devices sometimes brick hardware; rollback strategies matter. Similarly, LaTeX package updates can break subtle macros. Snapshot containers or document known-good TeX Live years when labs need archival reproduction.

API rate limits shape client backoff strategies. Academic APIs (Crossref, ORCID) expect courteous traffic. Template fetchers for metadata belong in tested modules, not in manuscript bodies.

Cryptographic agility means planning algorithm transitions before emergencies. Publishing integrity sometimes uses signed PDFs or manifests; this repo’s steganography tooling lives under `infrastructure/steganography/` for projects that enable it.

Technology desk signs off: `05_technology` names tools without endorsing vendors. Sports is next; expect shorter sentences and more tempo.

```{=latex}
\end{multicols}
```

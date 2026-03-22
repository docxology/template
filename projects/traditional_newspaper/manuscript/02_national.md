# National

```{=latex}
\begin{multicols}{3}
```

**Capitol and provinces**

```{=latex}
\noindent\textsc{National}\par\noindent\rule{\linewidth}{0.4pt}\par\smallskip
```

**WASHINGTON.** This slice is stem `02_national`, the second entry in `PAGE_SLICES`. It exists so multicolumn text that mentions domestic policy boilerplate can wrap realistically on tabloid stock. All numbers below are illustrative; they are not extracted from a database at build time.

Budget watchers issued a placeholder brief noting that baseline outlays remain a function of assumptions chosen in spreadsheet models, not of anything compiled here. Committee staff said they would reserve comment until the template’s PDF validator finishes scanning for unresolved references. A sidebar in a real paper might chart ten-year windows; this edition charts nothing except line breaks.

Provincial desks filed synthetic updates on infrastructure timelines. Municipal leaders described gravel procurement as “on track” without naming suppliers, because this manuscript deliberately avoids external network calls during the pipeline. Copy editors normalized spelling to U.S. English for consistency with the default Pandoc locale; multilingual editions would swap `metadata.language` and proof hyphenation separately.

Transportation agencies reiterated winter maintenance talking points. Snow routes, brine stockpiles, and contractor rotations appear as prose only. If you extend the project, replace this block with CSV-driven sentences generated in `src/` and covered by tests, keeping the thin orchestrator rule intact.

Agriculture correspondents summarized crop insurance deadlines in plain language. Risk pools and indemnity triggers are named generically so the glossary can define “folio” and “slice” without agronomic footnotes stealing the margin. Photographers would normally supply a weather file; here the only raster assets are the masthead and the layout schematic from analysis scripts.

Veterans’ affairs advocates called for predictable funding streams. Their statement, like every quotation in this edition, is authored for column measure rather than advocacy impact. Layout stress increases when proper names cluster; repeated department acronyms test kerning and small-cap section rails if you enable them via `snippets.section_label`.

Election administrators reminded readers that certification dates vary by statute. This paragraph nods to the separation between **content** (markdown slices) and **orchestration** (root `scripts/`). Changing vote counts would not alter how `PDFRenderer` inserts `\newpage` between stems; only editing this file would.

Finally, national security editors filed a holding paragraph on coordination between civilian agencies. It closes the national desk loop while keeping word count high enough to force another column break on 11×17 paper at nine-point body. Re-run `scripts/report_manuscript_stats.py` after edits to refresh `manuscript_stats.json` for reviewers who track length programmatically.

**Depth notes.** Census field operations once depended on paper maps and enumerator judgment; modern designs blend address frames with digital instruments. This edition does not ship census microdata—it ships a reproducible PDF. Still, the national desk metaphor matters: large surveys and large builds both need checkpoints, manifests, and logs that survive audits months later.

Intergovernmental fiscal transfers—block grants, matching funds, maintenance-of-effort clauses—shape how states implement federal programs. Lawyers read appropriations language; compositors read `\columnsep`. Both professions punish ambiguity. When you author real policy PDFs inside this template, keep statutory citations in BibTeX and keep layout constants in `layout_spec.py` so tests fail if the two drift.

Emergency management exercises stress radio interoperability and joint information centers. Newsrooms mirror that structure during hurricanes: a single copy chief slows contradictory push alerts. The pipeline analogue is a single `PDFRenderer` pass list: parallelizing LaTeX runs across folios is possible but out of scope here; combined manuscripts assume one ordered narrative string before the engine.

Rural broadband advocates argue maps overstate coverage because providers report advertised speeds by census block. Skeptics reply that reverse auctions improve targeting. This folio takes no position; it only needs enough tokens to wrap columns. If you generate maps, store GeoJSON under `output/data/` and cite the path in `S03_validation_and_outputs.md`.

Veterans’ preference in hiring and contracting appears in federal HR manuals. Summaries risk oversimplifying carve-outs for disabled veterans versus other eligible groups. Template authors should prefer linking to primary sources over paraphrasing fine print in static markdown unless lawyers sign off.

National laboratories publish technology transfer metrics. Startups license patents; tech scouts visit demo days. None of that appears numerically here. The connection to the template is lighter: `src/newspaper/` is the place for deterministic figure code, while `manuscript/` remains mostly declarative prose.

Public-health crossovers—vaccine procurement, strategic stockpiles—often surface on national desks during outbreaks. Detailed dosing belongs in `13_health.md` tone, not in procurement ledes. Cross-desk consistency is an editorial skill; cross-module consistency is enforced by imports and tests.

Finally, remember that `validate_inventory` only checks filenames exist. It does not judge readability. Pair inventory tests with markdown validation and occasional human proofing of PDFs after font updates. National coverage ends; international coverage resumes on the world folio.

```{=latex}
\end{multicols}
```

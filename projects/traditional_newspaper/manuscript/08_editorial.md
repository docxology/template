# Editorial

```{=latex}
\begin{multicols}{3}
```

**The template’s view**

**OPINION PAGE.** `08_editorial` carries the institutional voice. It argues, calmly, that reproducible research publishing should treat manuscripts, tests, and figures as one versioned artifact. Editors here are not neutral reporters; they are stand-ins for project maintainers explaining design trade-offs.

First, multicolumn layout stresses paragraph shaping more than single-column preprints. If your science prefers one column, swap `multicols` for a simpler environment in `preamble.md` and adjust `layout_spec.py` so tests and diagrams stay truthful.

Second, deterministic fixtures beat live scrapers for CI. Random network failures should not gate typography. When real data arrives, isolate fetching in `src/`, test it, and keep markdown mostly declarative.

Third, supplemental slices (`S01`, `S02`, `S03`) exist so long methodology prose does not bloat every “news” page. Readers who want pipeline detail can jump to the end matter without forcing casual reviewers through twenty screens of build steps.

Fourth, captions and labels matter. Floats with `\label{fig:...}` enable `Figure~\ref{...}` references. HTML export relies on Lua filters that parse captions; avoid nested braces inside `\caption{}` text.

Fifth, glossary rows (`98_*`) anchor vocabulary. New contributors should skim them before renaming stems or scripts, lest `validate_inventory` and discovery logs diverge from filenames on disk.

The board acknowledges limitations: this PDF is not a CMS, not a subscription product, and not legal advice. It is an exemplar proving the root pipeline can emit a tabloid-shaped bundle alongside more conventional monographs.

The editorial concludes: ship small, measure output, document the path from markdown to PDF, and rerun tests when fonts or Pandoc versions change. Next folio opens the opinion desk to named columnists—still fictional, still static.

**Depth notes.** Editorial boards meet privately; minutes rarely publish. Transparency policies differ across organizations. Open-source projects substitute public issues and pull requests—different medium, similar accountability tension.

Endorsements carry legal and reputational risk. Disclaimers clarify that candidate preferences do not infect news reporting staff. In this repo, news and opinion are literally different files; separation mirrors structural firewalls.

Corrections columns repair trust after mistakes. Speed-to-publish incentives worsen error rates online. Print editions bake in a slower clock; CI pipelines can gate merges on tests analogous to copydesk reads.

Conflict-of-interest disclosures matter for nonprofits and universities receiving industry funding. Editors should update boilerplate when grants change. Template metadata in `config.yaml` can record funding statements if journals require them.

Whistleblower protections and shield laws vary by country. Investigative desks rely on them; template authors rarely do—unless documenting how to handle sensitive paths in `.gitignore`.

Plagiarism detection software flags overlap; human editors judge intent. Academic overlap with prior methods sections is expected; copying without attribution is not. The template’s no-mocks testing policy pushes teams toward original integration tests.

Editorial page design sometimes uses wider measure or different fonts than news. This project keeps one preamble for simplicity; themed variants would fork `preamble.md` carefully.

Board recess: `08_editorial` rests its case. `09_opinion.md` prints signed columns with rhetorical spice.

```{=latex}
\end{multicols}
```

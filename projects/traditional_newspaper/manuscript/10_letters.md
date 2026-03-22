# Letters

```{=latex}
\begin{multicols}{3}
```

**To the editor**

**LETTERS POLICY.** `10_letters` simulates reader mail. Names and towns are generic; viewpoints are mild. Real letters pages verify identities; this build verifies only that LaTeX special characters survive when apostrophes and dashes appear often.

**On pipelines.** A reader praised reproducible builds but asked for clearer error messages when Pandoc fails. Maintainers agree: logs already include stderr; future work could aggregate hints the way `pdf_validator` scans for `??` references.

**On fonts.** Another writer requested open-source font stacks only. XeLaTeX can load system fonts; pinning free fonts improves portability. Document choices in `preamble.md` comments.

**On length.** A third correspondent complained that sixteen folios feel long for a demo. Counter: tabloid spreads need volume to expose bad breaks. Shrink slices if your use case is a pamphlet.

**On figures.** A fourth note thanked the team for captioned mastheads. The writer asked whether raster diagrams should be PDF for print shops. Answer: either works if downstream RIPs accept them; vector PDF often scales cleaner.

**On HTML.** A web developer wanted nav sidebars in combined HTML. `WebRenderer` output evolves with template CSS; patches belong in infrastructure, not in this markdown.

**On tests.** A contributor offered to add snapshot tests for PDF bytes. The project prefers structural checks and content validators over brittle binary equality. Discussion continues in issues, not on this page.

The letters editor thanks everyone and reminds readers that policy limits personal attacks. Here, there is nothing personal—only placeholders.

**Depth notes.** Letter columns historically anchored civic discourse; selected missives signaled public mood to elected officials. Email flooded inboxes; social platforms fragmented audiences. Print letters pages shrank but did not vanish.

Verification workflows confirm authors exist and sometimes redact addresses. Libel law applies to letters same as news. Editors cut defamation risks before press time.

Translation services help non-native writers participate. Tone differs across languages; bilingual editors smooth edges. Markdown source files stay UTF-8; ensure your editor preserves encoding.

Seasonal spikes follow controversial editorials. Volume metrics inform page budget. Pipeline metrics—stage durations, failure rates—should inform engineering budgets similarly.

Thank-you letters after crises remind newsrooms why accuracy matters. Errors during emergencies cost trust and sometimes lives. Testing philosophy here is serious even when prose is playful.

Kids’ letters pages teach media literacy early. Simplified explanations of how news is made pair well with this exemplar: show the `scripts/` layer, show tests, show PDF output.

Letters fold: `10_letters` seals the envelope. `11_local.md` zooms from national mail to neighborhood beats.

```{=latex}
\end{multicols}
```

# Science

```{=latex}
\begin{multicols}{3}
```

**Methods and results**

**SCIENCE.** `14_science` mirrors how labs talk about uncertainty. Hypotheses, controls, and replication appear as vocabulary without claiming novel discoveries. The exemplar’s actual “result” is a green PDF build with resolved references.

Researchers described pre-registration as a guard against p-hacking. Outcome switching still happens; transparency norms evolve. None of this cites real trials.

Instrument calibration paragraphs mentioned drift, reference standards, and environmental controls. Bench scientists will recognize the shape; statisticians will want effect sizes—omitted here.

Fieldwork sections covered sampling grids and GPS waypoints in the abstract. Geospatial figures would pair well with `layout_figure` style PNGs if someone maps coordinates.

Computational notes tied container images to hash stability. That rhymes with the template’s Docker story in `infrastructure/docker/`. Reproducible environments and reproducible typesetting share rhetoric.

Peer review got a neutral treatment: gatekeeping plus delay tradeoffs. Open review experiments were name-checked without endorsing a single platform.

Interdisciplinary collaboration bridged physics-informed models with domain expertise. Jargon density increases deliberately to test hyphenation on long compounds.

Science signs off by pointing to `98_newspaper_and_pipeline_terms.md` for definitions of “folio” and “slice,” which are publishing terms here, not experimental units.

**Depth notes.** Open science practices—open data, open code, preregistration—aim to speed self-correction. Journal incentives still favor novelty over replication. Meta-analyses aggregate effect sizes; this folio aggregates paragraphs.

Measurement error splits into precision and accuracy. Instruments may be precise yet biased. Similarly, PDF builds may be repeatable yet wrong if the source markdown encodes false claims—tests cannot catch semantic falsehoods.

Model assumptions hide in supplementary PDFs; readers skip them. Plain-language assumption summaries in main text improve comprehension. Template supplements (`S01`–`S03`) try that for build tooling.

Citizen science projects crowdsource classifications; quality control uses gold-standard items. Newsroom analogues include moderated reader submissions—different validation stack.

Ethics boards review human subjects protocols; IACUC reviews animal work. Robotics and simulation reduce some burdens but raise new questions about embodied harm.

Data management plans now accompany many grants. Repositories assign DOIs to datasets. Zenodo integration lives in `infrastructure/publishing/` for teams that publish artifacts.

Science exit: `14_science` hands the tone to `15_obituaries.md`, where precision yields to compassion.

```{=latex}
\end{multicols}
```

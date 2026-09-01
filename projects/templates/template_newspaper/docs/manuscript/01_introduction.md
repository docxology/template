# Introduction

Most reproducible-research tooling treats a document as a linear stream: a
manuscript is sections of prose, rendered top to bottom. A newspaper is the
opposite — a deliberately *non-linear*, spatial artifact, in which a reader's
eye is guided by a hierarchy of headline sizes, by rules and gutters, by the
placement of a photograph and the interruption of a pull quote. Building one
programmatically is therefore an unusually demanding test of a layout system,
and an unusually legible demonstration when it succeeds.

`template_newspaper` exists to be that demonstration within the research
template. It is the third canonical exemplar, joining `template_code_project`
(a computational pipeline) and `template_prose_project` (a manuscript-quality
pipeline). All three share one directory contract and one orchestration
pipeline; they differ only in what they render.

The design follows a single principle: **content is data, the engine is the
press.** An edition is a small set of YAML files under `content/` — a masthead
manifest and one file per page, each declaring its stories, boxes and figures.
The engine in `src/newspaper/` reads that data and renders it; it contains no
copy and, outside a single typography module, names no fonts. Producing a
different paper — a school gazette, a conference daily, a neighborhood
broadsheet — is an edit to the data, not the code.

The remainder of this manuscript describes the engine's architecture
(Section 2), its typography and figure generation (Section 3), and how the
artifact is produced and verified reproducibly (Section 4).

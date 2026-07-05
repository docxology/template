"""Chapter/lab/question stub scaffolder and structural validator.

This is the meta-template engine. ``scaffold_chapter`` emits a comprehensive
stub that demonstrates every content primitive — labelled heading, figure with
caption + alt text, metadata badge, study blueprint, vignette, prose with
glossary links and citations, a worked formalism (equation + parameter table),
an inline Mermaid diagram, a callout, cross-references, and the standard
pedagogy sections — every element marked with a stub flag so authors can fill it
out to arbitrary length without breaking the structure.

``validate_chapter`` enforces the same contract from :mod:`textbook.constants`,
so a freshly scaffolded chapter passes validation by construction and the
manuscript-integrity tests catch any hand-edited chapter that drifts.
"""

from __future__ import annotations

import re

from textbook.config import ChapterRef, UnitIntroRef
from textbook.constants import (
    CITATION_KEYS,
    GLOSSARY_ANCHORS,
    REQUIRED_SECTION_HEADINGS,
    REQUIRED_TOKENS,
    STUB_MARKERS,
)
from textbook.toc import lab_label, question_label, section_label, unit_intro_label


def _rotate(items: tuple[str, ...], seed: str, count: int) -> list[str]:
    """Deterministically pick ``count`` items starting at a seed-derived offset."""
    if not items:
        return []
    offset = sum(ord(ch) for ch in seed) % len(items)
    return [items[(offset + i) % len(items)] for i in range(min(count, len(items)))]


def _glossary_links(seed: str, count: int) -> str:
    anchors = _rotate(GLOSSARY_ANCHORS, seed, count)
    return ", ".join(f"[**{a}**](#gl:{a})" for a in anchors)


def _citations(seed: str, count: int) -> str:
    keys = _rotate(CITATION_KEYS, seed, count)
    return "; ".join(f"@{k}" for k in keys)


def scaffold_chapter(chapter: ChapterRef) -> str:
    """Return a complete, contract-satisfying stub for ``chapter``."""
    stem = chapter.stem
    sec = section_label(chapter)
    fig = f"fig:{chapter.part_id}_{stem}"
    tbl = f"tbl:{chapter.part_id}_{stem}_parameters"
    eq = f"eq:{chapter.part_id}_{stem}_model"
    gloss = _glossary_links(stem, 3)
    key_terms = _glossary_links(stem + "keys", 4)
    cite_one = _citations(stem, 2)
    cite_two = _citations(stem + "two", 1)
    cite_read = _citations(stem + "read", 1)

    return f"""# {chapter.title} {{#{sec}}}

![Overview schematic for "{chapter.title}". Replace this generated placeholder \
with a real figure produced by `src/visualization/plots.py`.](../../output/figures/{chapter.part_id}_{stem}.png){{#{fig} width=90%}}

<!-- alt: Placeholder overview schematic for the chapter "{chapter.title}". \
TODO: write descriptive alt text once the real figure exists. -->

<!-- chapter-metadata-badge -->
> Level 1/3 · 30 min read · 45 min lecture · Prerequisites: none

## Learning Objectives

By the end of this chapter you should be able to:

1. <!-- STUB: objective --> TODO: state the first measurable learning objective.
2. <!-- STUB: objective --> TODO: state the second learning objective.
3. <!-- STUB: objective --> TODO: state the third learning objective.

<!-- curriculum-scaffold-start -->
### Study Blueprint

- **Big idea:** <!-- STUB: one-sentence thesis for this chapter. -->
- **Core concepts:** {gloss}.
- **Quantitative lens:** the worked formalism in [@{eq}].
- **Data skill:** <!-- STUB: which data move the reader practises here. -->
- **Common misconception to repair:** <!-- STUB. -->
- **Primary lab:** [@{lab_label(chapter)}].
- **Question bank:** [@{question_label(chapter)}].
- **Bridge to computation:** `textbook.models`.
<!-- curriculum-scaffold-end -->

---

> **Opening Vignette: TKTK — a motivating story**
>
> <!-- STUB: open with a concrete, specific example that makes the reader care. \
> Two to four sentences. Cite a primary source [{cite_two}]. -->

---

## Orientation

<!-- STUB: 2-4 paragraphs introducing the chapter. --> This section introduces
the central ideas of *{chapter.title}*. Foundational treatments include
[{cite_one}]. Key terms such as {gloss} are defined in the glossary.

## A Worked Formalism

The recurring quantitative model for this chapter is shown in [@{eq}]:

$$ N(t) = \\frac{{K}}{{1 + \\left(\\dfrac{{K - N_0}}{{N_0}}\\right) e^{{-rt}}}} $$ {{#{eq}}}

It is implemented and tested in `textbook.models.logistic_growth`; never retype
the maths in prose or scripts — call the tested function. The parameters appear
in [@{tbl}].

: Parameters of the worked model for this chapter. {{#{tbl}}}

| Symbol | Meaning | Units |
| ------ | ------- | ----- |
| $r$ | intrinsic rate | 1/time |
| $K$ | carrying capacity | quantity |
| $N_0$ | initial value | quantity |

A concept map of how the pieces fit together:

```mermaid
graph TD
  A[Inputs / assumptions] --> B[Model]
  B --> C[Predictions]
  C --> D[Comparison with data]
  D -->|revise| A
```

> **Note**
>
> <!-- STUB: an aside, caveat, or historical note. -->

## Going Deeper

<!-- STUB: the substantive body of the chapter. Expand freely — figures,
tables, equations, and subsections may repeat as needed. --> See the overview in
[@{fig}] and revisit the objectives above as you read. Further evidence:
[{cite_one}].

## Summary

<!-- STUB: 3-5 sentence recap of the chapter's load-bearing claims. -->

## Key Terms

{key_terms}.

## Further Reading

- <!-- STUB: annotated pointer --> TODO: one-line annotation [{cite_read}].

## Practice

- **Lab:** [@{lab_label(chapter)}]
- **Question bank:** [@{question_label(chapter)}]
"""


def scaffold_lab(chapter: ChapterRef) -> str:
    """Return a stub lab activity bound to ``chapter``."""
    return f"""# Lab — {chapter.title} {{#{lab_label(chapter)}}}

<!-- chapter-metadata-badge -->
> Lab · 60 min · Materials: notebook, calculator (or `textbook.models`)

## Objectives

<!-- STUB: what the learner will be able to do after this lab. -->

## Background

Linked chapter: [@{section_label(chapter)}]. <!-- STUB: bridge the chapter
concepts to the hands-on activity. -->

## Procedure

1. <!-- STUB --> TODO: first step.
2. <!-- STUB --> TODO: second step.

## Analysis

<!-- STUB --> Summarise results with `textbook.models.descriptive_statistics`.

## Computational Workflow

```python
from textbook.models import logistic_growth
# TODO: parameterise and plot the model for this lab's scenario.
```

## Reflection

<!-- STUB: 2-3 reflective prompts. -->
"""


def scaffold_question_bank(chapter: ChapterRef) -> str:
    """Return a stub question bank (recall -> application -> synthesis)."""
    return f"""# Question Bank — {chapter.title} {{#{question_label(chapter)}}}

Linked chapter: [@{section_label(chapter)}].

## Recall

1. <!-- STUB: question --> TODO. *(Answer: <!-- STUB -->)*
2. <!-- STUB: question --> TODO. *(Answer: <!-- STUB -->)*

## Application

3. <!-- STUB: question --> TODO. *(Answer: <!-- STUB -->)*
4. <!-- STUB: question --> TODO. *(Answer: <!-- STUB -->)*

## Synthesis

5. <!-- STUB: question --> TODO. *(Answer: <!-- STUB -->)*
"""


def scaffold_unit_intro(intro: UnitIntroRef, chapters: list[ChapterRef]) -> str:
    """Return a stub unit introduction for ``intro`` listing its chapters."""
    chapter_lines = "\n".join(f"- *{chapter.title}* — [@{section_label(chapter)}]" for chapter in chapters)
    label = unit_intro_label(intro.part_id)
    return f"""# Part {intro.part_label}: {intro.part_title} {{#{label}}}

<!-- STUB: write a 1-2 paragraph introduction to Part {intro.part_label}. -->
This part covers **{intro.part_title.lower()}**. It contains the following chapters:

{chapter_lines}

> **How to use this part.** <!-- STUB: orient the reader; note prerequisites and how the chapters build on each other. -->
"""


def validate_unit_intro(text: str) -> list[str]:
    """Return structural problems with a unit intro markdown file."""
    issues: list[str] = []

    if not re.search(r"^#\s+\S", text, flags=re.MULTILINE):
        issues.append("missing H1 title")

    if "[@sec:" not in text:
        issues.append("missing at least one chapter cross-reference ([@sec:...])")

    return issues


def validate_chapter(text: str) -> list[str]:
    """Return structural problems with a chapter's markdown (empty == valid)."""
    issues: list[str] = []

    if not re.search(r"^#\s+\S", text, flags=re.MULTILINE):
        issues.append("missing H1 title")

    for token in REQUIRED_TOKENS:
        if token not in text:
            issues.append(f"missing required token: {token!r}")

    for heading in REQUIRED_SECTION_HEADINGS:
        if not re.search(rf"^##\s+{re.escape(heading)}\s*$", text, flags=re.MULTILINE):
            issues.append(f"missing required section: '## {heading}'")

    if not re.search(r"\[@[\w:-]+", text):
        issues.append("missing at least one citation ([@key])")

    if "(#gl:" not in text:
        issues.append("missing at least one glossary link ((#gl:...))")

    # Chapters live at manuscript/<part>/<chap>.md, so every figure image path
    # must reach the project figure dir as ``../../output/figures/...``. A bare
    # ``../figures/...`` (the old scaffold bug) resolves to a nonexistent
    # manuscript/figures/ dir and renders as a missing image.
    for image_path in re.findall(r"!\[[^\]]*\]\(([^)]*figures/[^)]*)\)", text):
        if not image_path.startswith("../../output/figures/"):
            issues.append(
                f"figure path does not resolve from a chapter (expected '../../output/figures/...'): {image_path!r}"
            )

    return issues


def count_stub_markers(text: str) -> int:
    """Count stub flags in ``text`` (a measure of remaining work)."""
    return sum(text.count(marker) for marker in STUB_MARKERS)


def count_words(text: str) -> int:
    """Rough word count of prose (used to track fill progress)."""
    return len(re.findall(r"\b\w+\b", text))


__all__ = [
    "count_stub_markers",
    "count_words",
    "scaffold_chapter",
    "scaffold_lab",
    "scaffold_question_bank",
    "scaffold_unit_intro",
    "validate_chapter",
    "validate_unit_intro",
]

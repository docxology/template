# Core Methods and Tools {#sec:part_0_core_methods}

![Overview schematic for "Core Methods and Tools". Replace this generated placeholder with a real figure produced by `src/visualization/plots.py`.](../../output/figures/part_0_core_methods.png){#fig:part_0_core_methods width=90%}

<!-- alt: Placeholder overview schematic for the chapter "Core Methods and Tools". TODO: write descriptive alt text once the real figure exists. -->

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
- **Core concepts:** [**model**](#gl:model), [**parameter**](#gl:parameter), [**variable**](#gl:variable).
- **Quantitative lens:** the worked formalism in [@eq:part_0_core_methods_model].
- **Data skill:** <!-- STUB: which data move the reader practises here. -->
- **Common misconception to repair:** <!-- STUB. -->
- **Primary lab:** [@sec:lab_part_0_core_methods].
- **Question bank:** [@sec:q_part_0_core_methods].
- **Bridge to computation:** `textbook.models`.
<!-- curriculum-scaffold-end -->

---

> **Opening Vignette: TKTK — a motivating story**
>
> <!-- STUB: open with a concrete, specific example that makes the reader care. > Two to four sentences. Cite a primary source [@lee2021systems]. -->

---

## Orientation

<!-- STUB: 2-4 paragraphs introducing the chapter. --> This section introduces
the central ideas of *Core Methods and Tools*. Foundational treatments include
[@kim2020data; @brown2017principles]. Key terms such as [**model**](#gl:model), [**parameter**](#gl:parameter), [**variable**](#gl:variable) are defined in the glossary.

## A Worked Formalism

The recurring quantitative model for this chapter is shown in [@eq:part_0_core_methods_model]:

$$ N(t) = \frac{K}{1 + \left(\dfrac{K - N_0}{N_0}\right) e^{-rt}} $$ {#eq:part_0_core_methods_model}

It is implemented and tested in `textbook.models.logistic_growth`; never retype
the maths in prose or scripts — call the tested function. The parameters appear
in [@tbl:part_0_core_methods_parameters].

: Parameters of the worked model for this chapter. {#tbl:part_0_core_methods_parameters}

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
[@fig:part_0_core_methods] and revisit the objectives above as you read. Further evidence:
[@kim2020data; @brown2017principles].

## Summary

<!-- STUB: 3-5 sentence recap of the chapter's load-bearing claims. -->

## Key Terms

[**emergence**](#gl:emergence), [**regulation**](#gl:regulation), [**boundary**](#gl:boundary), [**state**](#gl:state).

## Further Reading

- <!-- STUB: annotated pointer --> TODO: one-line annotation [@wilson2021analysis].

## Practice

- **Lab:** [@sec:lab_part_0_core_methods]
- **Question bank:** [@sec:q_part_0_core_methods]

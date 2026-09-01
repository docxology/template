# Preface

<!-- This is a STUB preface. It is structurally complete but deliberately
generic: replace the placeholder prose with your own voice, motivation, and
specifics. Keep the section shape (purpose, audience, how to use the book) — the
manuscript-integrity tests and the quality audit expect a preface to exist. -->

## Why This Book Exists

<!-- STUB: purpose --> *TKTK — state, in two or three paragraphs, the problem
this book solves and why it is worth a reader's time. What gap in the existing
literature does it fill? What will a reader be able to do after finishing it that
they could not do before?*

This template is domain-neutral by design. Wherever the sample chapters speak of
"systems", "dynamics", or "regulation", substitute the concepts of your own
field. The structure — orientation, fundamentals, core systems, applications —
generalises across most technical subjects; the content is yours to supply.

## Who This Book Is For

<!-- STUB: audience --> *TKTK — describe the intended reader. Assumed background?
A prerequisite course or a specific level of mathematical maturity? Whether the
book suits self-study, a one-semester course, or a reference shelf.*

The book assumes the quantitative foundations laid out in **Part 0** and nothing
more. A reader comfortable with that material can follow every chapter.

## How to Use the Labs and Question Banks

Each chapter is paired with two companion documents:

- **A lab** (under [`labs/`](labs/)) — a guided, hands-on exercise that puts the
  chapter's worked formalism to work. Labs are meant to be *done*, not just read:
  run the tested functions in `textbook.models`, vary the parameters, and observe
  how the predictions change. Work the lab immediately after reading the chapter,
  while the ideas are fresh.
- **A question bank** (under [`questions/`](questions/)) — self-check questions
  that confirm you can recall and apply the chapter's load-bearing claims. Use it
  as a diagnostic: a question you cannot answer points you back to a specific
  section.

Instructors can assign the lab as homework and draw exam or quiz items from the
question bank. Because both are generated from the same `config.yaml` as the
chapters, they stay in lockstep with the manuscript as it grows.

## A Note on Reproducibility

<!-- STUB --> Every equation in this book is implemented as a tested function and
every figure is generated deterministically from code. Nothing in the prose is
computed by hand. If you build the book yourself you will get byte-identical
figures and numbers — see [`README.md`](README.md) for the build commands.

<!-- STUB: sign off with your name, place, and date once the book is written. -->
*— The Author, TKTK (place), TKTK (date)*

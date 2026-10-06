# Preface {#sec:preface}

## Purpose

This book introduces systems, quantitative models and reproducible computational
reasoning through a small tested backbone. Its aim is to help a learner say what
an equation represents, what a computation checks and what observation would
challenge a prediction. A precise number is useful only when its meaning and
custody remain visible. The chapters therefore pair equations with input domains,
worked arithmetic, deterministic figures, labs and answer discussions.

The examples are instructional. A smooth growth curve does not document a real
population; a six-row fixture does not report a new experiment. Synthetic inputs
make selected mathematical properties transparent, while the bundled case-study
CSV binds one worked example to exact source values. The distinction between
these demonstrations and empirical research is part of the lesson, not an
incidental disclaimer.

## Audience and prerequisites

Readers need basic arithmetic, familiarity with graphs and a willingness to work
through a short Python call. Derivatives and logarithms are explained where they
enter a formalism, and the mathematical review supplies additional examples.
The book is suitable for a guided introductory course or self-directed study.
It is not a domain-specific engineering design manual, an experimental protocol
or a claim that a single family of models explains every system.

## How to use the book

Begin with a question and a written prediction before running a computation.
Read the quantities and assumptions in the parameter table. Run the example in
a fresh interpreter, preserve its output and compare it with the stated boundary
case. In the lab, change one input while holding the rest fixed. In the question
bank, explain your reasoning before reading the solution. A failed expectation
is useful evidence if its inputs and cause remain inspectable.

The units progress from observation and methods to model components, dynamic
systems and applications. Cross-references connect each chapter to its lab and
questions, while the glossary defines recurring terms. The reference appendices
cover notation, derivations, authoring conventions, rendering primitives and a
section-based index. Their purpose is to support the authored examples rather
than hide unfinished sections behind an attractive table of contents.

## Computational record

The mathematical functions live in `textbook.models`; figures and analysis
scripts call the tested source rather than maintaining separate formulas.
Tests exercise real arrays and files, with explicit negative controls for the
content gate. The canonical complete-manuscript audit checks every configured
rendered section. The separate scaffold API still creates drafts for new books,
and tests those drafts independently of this finished canonical content.

A passing content gate establishes structure and absence of declared draft
markers. It does not establish scientific validity, hosted execution or a new
publication deposit. Historical publication identifiers continue to identify
the releases to which they were assigned. This source is an authored teaching
record whose computations and interpretation can be inspected and improved.

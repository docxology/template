# Front Matter {#sec:front_matter}

## About this book

*The Template Textbook* is an authored introduction to systems, models and
reproducible research. Its chapters combine a question, a mathematical formalism,
a deterministic figure, a worked computation and paired practice. Every
instructional example declares its assumptions. The book's structure is read
from `manuscript/config.yaml`; chapter numbering and cross-references are derived
at render time rather than maintained as duplicated prose.

## Reading and computation

The source is Markdown. The computational backbone is Python with NumPy, and
figures are regenerated through the supplied scripts. Install the project or
run from its documented environment before executing a code block. Run the
worked examples in a fresh interpreter to avoid hidden state from an earlier
calculation. Preserve the original input and record a changed-input experiment
as a new comparison.

The canonical manuscript is complete at the declared content boundary. It also
contains an authoring appendix because the underlying engine can scaffold other
books. Draft scaffolding is a separate workflow: it must not replace canonical
chapters during an ordinary build. The strict audit and manuscript tests keep
that distinction visible.

## Evidence and scope

The logistic, decay, response, normalization and fitted-line examples use
constructed inputs. The case-study observations come from the bundled
`assets/data/sample_dataset.csv` fixture. These are teaching records rather
than new empirical findings. An exact synthetic answer checks a computation;
an observation plan and independent data are needed to evaluate a real system.

Source files and generated figures support inspection and reuse. A test receipt
is local evidence for the revision that produced it. Previously published PDFs,
DOIs and artifact URLs retain their historical version meanings, and an intended
release does not become published through editing this manuscript.

## Licensing

Book content uses the configured Creative Commons Attribution 4.0 license; the
computational code uses the configured Apache-2.0 license. Consult the repository
license files for the governing text. Bibliography entries identify verified
primary publications; they are not placeholders or invented reading suggestions.
No ISBN or new publication identifier is asserted here.

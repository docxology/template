# Verification and provenance

The rendering stage checks the results for the enabled formats. A PDF
build needs a usable combined manuscript. Other projects can enable an
HTML edition or slide PDFs. Output validation then checks the applicable
artifact set and manuscript Markdown, and writes validation and artifact
records. The provenance receipt binds inputs such as tracked source and
configuration to selected outputs and the manuscript sections consumed during
composition [@template-source].

A reproducibility check depends on what the verifier observes. A valid
PDF shows that an output exists and passes structural checks. Inspecting
its extracted text and images can additionally establish that selected
sections, citations, and figures appeared. A source-bound receipt can
detect that a later input or output changed. These checks serve different
purposes, consistent with the distinction between evaluating artifacts
and establishing independent results [@acm-artifacts].

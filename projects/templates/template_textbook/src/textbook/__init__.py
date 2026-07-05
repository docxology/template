"""template_textbook engine package.

Modules:
    constants  — shared contract (citation keys, glossary anchors, required tokens)
    config     — load + validate manuscript/config.yaml
    toc        — table of contents, chapter numbering, lab/question titles
    audit      — manuscript structure audit (shared CLI + test gate)
    models     — domain-neutral computational backbone (the formalisms)
    content    — chapter stub scaffolder + structural validator
"""

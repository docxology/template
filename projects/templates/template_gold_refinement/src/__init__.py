"""Gold Refinement exemplar - metallurgical manuscript composition.

Maps gold-refining stages (ore -> smelting -> assaying -> cupellation ->
certification) onto scientific manuscript purity with mega-madlib token
injection. The refinery is a load-bearing pipeline: each stage maps to
a real template-infrastructure operation.

This package is a namespace shim: the exemplar's public modules live in
``src/template_gold_refinement/`` (the unique package). Import the exemplar as::

    from template_gold_refinement.composition import TokenChoice

Per the TEST-ISOLATION-SYSPATH-1 recipe, ``src/__init__.py`` performs no
imports so that ``import src`` never collides across exemplars in one pytest
process.
"""

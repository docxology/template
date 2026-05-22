"""Regression test tier — pinned numerical outputs for manuscript claims.

See ``tests/regression/README.md`` and ``docs/maintenance/regression-testing.md``
for the full philosophy. In short: every quantitative claim in a manuscript
has a corresponding test here that re-derives the value and compares to a
pinned ground-truth committed in ``pinned_values/``.

This tier is INDEPENDENT of the coverage floor — coverage signals code
execution; these signal scientific claim integrity.
"""

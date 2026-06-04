"""Deterministic figure generation for the template textbook.

Public API lives in :mod:`visualization.plots`. Every figure is reproducible
(fixed inputs, no randomness, ``Agg`` backend) so the rendered PDF is
byte-stable across runs.
"""

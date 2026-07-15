"""Manuscript variable injection module.

Provides template variable computation from pipeline output data
for auto-injecting real values into manuscript files.
"""

from .variables import compute_variables, inject_variables

__all__ = ["compute_variables", "inject_variables"]

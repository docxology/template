"""Manuscript template variable computation and injection."""

from manuscript.variables.compute import compute_variables
from manuscript.variables.formatters import humanize_key as _humanize_key
from manuscript.variables.formatters import humanize_list as _humanize_list
from manuscript.variables.formatters import latex_number as _latex_number
from manuscript.variables.inject import inject_variables
from manuscript.variables.io import count_jsonl_lines as _count_jsonl_lines
from manuscript.variables.io import count_total_references as _count_total_references
from manuscript.variables.io import load_json as _load_json

__all__ = [
    "compute_variables",
    "inject_variables",
    "_latex_number",
    "_count_jsonl_lines",
    "_count_total_references",
    "_humanize_list",
    "_humanize_key",
    "_load_json",
]

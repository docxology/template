"""Actual Pandoc source accounting for mathematical contextual obligations."""

from __future__ import annotations

import shutil
import subprocess

import pytest

from infrastructure.reporting.native_format_scientific_math import scientific_math_from_ast


def test_original_pandoc_accounts_for_heading_note_table_and_display_math() -> None:
    executable = shutil.which("pandoc")
    if executable is None:
        pytest.skip("the original source parser is not installed")
    source = """# Heading $x^2$

Body with a note.[^one]

[^one]: Footnote $z+1$.

| Field | Value |
|---|---|
| Math | $q/2$ |

$$\\int_0^1 t\\,dt$$
"""
    result = subprocess.run(
        [executable, "--from=markdown+tex_math_dollars", "--to=json"],
        input=source.encode(),
        capture_output=True,
        check=True,
        timeout=30,
    )
    nodes = scientific_math_from_ast(result.stdout)
    assert len(nodes) == 4
    assert len({node.identity for node in nodes}) == 4
    assert {node.context for node in nodes} == {"heading:1", "footnote", "table", "body"}
    assert {node.mode for node in nodes} == {"InlineMath", "DisplayMath"}
    assert [node.source for node in nodes] == ["x^2", "z+1", "q/2", r"\int_0^1 t\,dt"]

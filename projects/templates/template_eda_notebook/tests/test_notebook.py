"""Validate the EDA walkthrough notebook (no mocks; reads the real .ipynb).

These tests enforce the *notebook -> tested src extraction* contract:

1. The notebook is valid ``nbformat`` JSON.
2. Every name imported ``from src`` exists in ``src.__all__``.
3. No code cell defines its own ``def`` / ``class`` — logic stays in ``src/``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import src as eda_pkg

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_NOTEBOOK = _PROJECT_ROOT / "notebooks" / "eda_walkthrough.ipynb"


def _load_notebook() -> dict:
    return json.loads(_NOTEBOOK.read_text(encoding="utf-8"))


def _code_sources(nb: dict) -> list[str]:
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


class TestNotebookStructure:
    def test_notebook_exists(self):
        assert _NOTEBOOK.is_file()

    def test_valid_nbformat(self):
        nb = _load_notebook()
        assert nb["nbformat"] == 4
        assert "cells" in nb and len(nb["cells"]) > 0

    def test_has_markdown_and_code_cells(self):
        nb = _load_notebook()
        kinds = {c["cell_type"] for c in nb["cells"]}
        assert {"markdown", "code"} <= kinds


class TestNotebookSrcBinding:
    def test_imported_names_exist_in_src(self):
        nb = _load_notebook()
        joined = "\n".join(_code_sources(nb))
        # Capture the parenthesised `from src import (...)` block.
        match = re.search(r"from src import \(([^)]*)\)", joined)
        assert match is not None, "notebook must import from src"
        names = [n.strip().rstrip(",") for n in match.group(1).split() if n.strip().rstrip(",")]
        names = [n for n in names if n and n != ","]
        assert names, "expected at least one imported name"
        for name in names:
            assert name in eda_pkg.__all__, f"{name} not exported by src.__all__"

    def test_cells_define_no_business_logic(self):
        nb = _load_notebook()
        for source in _code_sources(nb):
            stripped = "\n".join(line for line in source.splitlines())
            assert not re.search(r"^\s*def \w+\(", stripped, re.MULTILINE), (
                "notebook cells must not define functions — extract to src/"
            )
            assert not re.search(r"^\s*class \w+", stripped, re.MULTILINE), (
                "notebook cells must not define classes — extract to src/"
            )

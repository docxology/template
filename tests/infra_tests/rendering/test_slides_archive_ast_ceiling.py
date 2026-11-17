"""Archive slide decks keep a finite node ceiling sized for book-scale chapters.

The accessible composer walks the Pandoc tree recursively and projects writer
fallbacks, so it keeps the tighter 100,000-node ceiling. The archive route hands
one whole manuscript section to Pandoc's Beamer writer; a valid IMRaD methods
chapter measured ~130,000 nodes there, which the shared accessible ceiling
refused. These tests pin the archive ceiling, its upper bound, and that the
accessible boundary is unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_limits import (
    MAX_ACCESSIBLE_PANDOC_AST_NODES,
    MAX_ACCESSIBLE_PANDOC_JSON_BYTES,
    MAX_ARCHIVE_PANDOC_AST_NODES,
    validate_accessible_ast_limits,
)
from infrastructure.rendering._slides_archive_source import prepare_archive_source
from infrastructure.rendering.config import RenderingConfig


def _node_count(document: object) -> int:
    count = 0
    stack = [document]
    while stack:
        value = stack.pop()
        count += 1
        if isinstance(value, dict):
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    return count


def _chapter(path: Path, *, words: int) -> Path:
    """Write a plain prose chapter; ~5 Pandoc JSON nodes per word."""
    paragraphs = "\n\n".join(" ".join(["evidence"] * 100) for _ in range(words // 100))
    path.write_text(f"## Methods\n\n{paragraphs}\n", encoding="utf-8")
    return path


def test_archive_ceiling_is_finite_and_above_the_accessible_ceiling() -> None:
    assert MAX_ACCESSIBLE_PANDOC_AST_NODES < MAX_ARCHIVE_PANDOC_AST_NODES
    # The byte bound stays the binding allocation guard at either ceiling.
    assert MAX_ARCHIVE_PANDOC_AST_NODES < MAX_ACCESSIBLE_PANDOC_JSON_BYTES


def test_archive_ceiling_admits_a_tree_the_accessible_ceiling_refuses() -> None:
    document = {"blocks": [None] * MAX_ACCESSIBLE_PANDOC_AST_NODES}

    with pytest.raises(RenderingError, match=r"\[slides\.schema\.pandoc-limits\]"):
        validate_accessible_ast_limits(document, source="manuscript/03_methods.md")
    validate_accessible_ast_limits(
        document, source="manuscript/03_methods.md", maximum_nodes=MAX_ARCHIVE_PANDOC_AST_NODES
    )


def test_archive_ceiling_still_refuses_beyond_its_bound() -> None:
    document = {"blocks": [None] * MAX_ARCHIVE_PANDOC_AST_NODES}

    with pytest.raises(RenderingError, match=r"\[slides\.schema\.pandoc-limits\]") as exc_info:
        validate_accessible_ast_limits(
            document, source="manuscript/huge.md", maximum_nodes=MAX_ARCHIVE_PANDOC_AST_NODES
        )

    assert exc_info.value.context["maximum_nodes"] == MAX_ARCHIVE_PANDOC_AST_NODES
    assert exc_info.value.context["observed_nodes"] == MAX_ARCHIVE_PANDOC_AST_NODES + 1


@pytest.mark.parametrize("maximum", (0, -1, MAX_ARCHIVE_PANDOC_AST_NODES + 1, True, 1.5, None))
def test_node_ceiling_cannot_be_disabled_or_raised_past_the_archive_bound(maximum: object) -> None:
    with pytest.raises(ValueError, match="maximum_nodes"):
        validate_accessible_ast_limits({"blocks": []}, source="manuscript/x.md", maximum_nodes=maximum)  # type: ignore[arg-type]


@pytest.mark.slow
def test_real_pandoc_archive_source_admits_a_book_scale_chapter(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    source = _chapter(tmp_path / "03_methods.md", words=24_000)
    output = tmp_path / "slides"
    output.mkdir()

    selected, temporaries = prepare_archive_source(
        RenderingConfig(slides_profile="archive", output_dir=str(output), slides_dir=str(output)),  # type: ignore[arg-type]
        source,
        output,
        manuscript_dir=None,
        figures_dir=None,
    )

    assert temporaries == (selected,)
    observed = _node_count(json.loads(selected.read_text(encoding="utf-8")))
    assert MAX_ACCESSIBLE_PANDOC_AST_NODES < observed <= MAX_ARCHIVE_PANDOC_AST_NODES


@pytest.mark.slow
def test_real_pandoc_archive_source_refuses_beyond_the_archive_ceiling_and_cleans_up(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    source = _chapter(tmp_path / "huge.md", words=52_000)
    output = tmp_path / "slides"
    output.mkdir()

    with pytest.raises(RenderingError, match=r"\[slides\.schema\.pandoc-limits\]") as exc_info:
        prepare_archive_source(
            RenderingConfig(slides_profile="archive", output_dir=str(output), slides_dir=str(output)),  # type: ignore[arg-type]
            source,
            output,
            manuscript_dir=None,
            figures_dir=None,
        )

    assert exc_info.value.context["maximum_nodes"] == MAX_ARCHIVE_PANDOC_AST_NODES
    assert list(output.iterdir()) == []

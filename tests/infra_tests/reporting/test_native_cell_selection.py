"""Cell-local admissibility and the single union completeness assertion."""

from __future__ import annotations

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_cell_selection import cell_selection, union_selection


def _partition(size: int) -> list[tuple[str, ...]]:
    return [tuple(PUBLIC_PROJECT_NAMES[index : index + size]) for index in range(0, len(PUBLIC_PROJECT_NAMES), size)]


def test_one_declared_scope_is_an_admissible_cell() -> None:
    assert cell_selection(("templates/template_code_project",)) is True


@pytest.mark.parametrize(
    "scopes",
    [(), ("templates/template_code_project", "templates/template_formal"), ("templates/not_declared",), ("root",)],
)
def test_a_cell_is_admissible_only_with_exactly_one_declared_scope(scopes: tuple[str, ...]) -> None:
    assert cell_selection(scopes) is False


@pytest.mark.parametrize("size", [1, 2, 3, 5])
def test_a_complete_partition_of_the_roster_satisfies_the_union(size: int) -> None:
    cells = _partition(size)
    assert len(cells) > 1
    assert union_selection(cells) is True


def test_the_union_refuses_a_missing_scope() -> None:
    cells = list(_partition(2))
    cells[-1] = cells[-1][:-1]
    assert union_selection(cells) is False


def test_the_union_refuses_a_duplicated_scope() -> None:
    cells = list(_partition(2))
    cells.append((PUBLIC_PROJECT_NAMES[0],))
    assert union_selection(cells) is False


def test_the_union_refuses_an_undeclared_scope() -> None:
    cells = list(_partition(2))
    cells[0] = ("templates/not_declared",)
    assert union_selection(cells) is False


def test_the_union_refuses_no_cells() -> None:
    assert union_selection(()) is False

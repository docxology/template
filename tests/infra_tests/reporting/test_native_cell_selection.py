"""Cell-local admissibility and the single union completeness assertion."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_cell_selection import (
    cell_selection,
    union_selection,
    native_transport_scopes,
    validate_native_transport_receipt,
    native_cell_directories,
    native_union_members,
)
from infrastructure.reporting.native_hosted_original_custody import (
    collect_native_hosted_cell_union,
    NativeHostedCellUnion,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.native_installed_launcher import main as launch_native


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


def _receipt(scopes: tuple[str, ...]) -> dict:
    return {
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": {scope + ":formats": {"status": "pass"} for scope in scopes},
        "native_formats": {
            "selected_projects": list(scopes),
            "observed_projects": len(scopes),
            "complete_selection": scopes == PUBLIC_PROJECT_NAMES,
        },
    }


@pytest.mark.parametrize("scopes", [(scope,) for scope in PUBLIC_PROJECT_NAMES] + [PUBLIC_PROJECT_NAMES])
def test_transport_accepts_each_exact_cell_and_the_ordered_full_roster(tmp_path, scopes) -> None:
    """Actual snapshot bytes exercise the production DATA guard, without native authority."""
    target = tmp_path / "output/readiness/native-selection/receipt.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(_receipt(scopes)))
    held = SnapshotReader(tmp_path).read(target.relative_to(tmp_path).as_posix())
    assert native_transport_scopes(scopes) == scopes
    validate_native_transport_receipt(scopes, held.json_object())
    assert cell_selection(scopes) is (len(scopes) == 1)


@pytest.mark.parametrize(
    "scopes",
    [
        (),
        PUBLIC_PROJECT_NAMES[:2],
        PUBLIC_PROJECT_NAMES[:-1],
        tuple(reversed(PUBLIC_PROJECT_NAMES)),
        (PUBLIC_PROJECT_NAMES[0],) * 2,
        ("templates/foreign",),
    ],
)
def test_transport_refuses_other_partial_duplicate_foreign_or_reordered_selections(scopes) -> None:
    with pytest.raises(ValueError, match="one declared cell or the complete ordered"):
        native_transport_scopes(scopes)


@pytest.mark.parametrize(
    "fault",
    [
        "extra-gate",
        "failed-gate",
        "wrong-selected",
        "missing-observation",
        "bool-observation",
        "false-completeness",
        "wrong-roster",
    ],
)
def test_transport_receipt_cannot_borrow_other_cells_or_claim_union_completeness(fault) -> None:
    selected = (PUBLIC_PROJECT_NAMES[0],)
    receipt = _receipt(selected)
    if fault == "extra-gate":
        receipt["gates"][PUBLIC_PROJECT_NAMES[1] + ":formats"] = {"status": "pass"}
    elif fault == "failed-gate":
        receipt["gates"][selected[0] + ":formats"]["status"] = "fail"
    elif fault == "wrong-selected":
        receipt["native_formats"]["selected_projects"] = [PUBLIC_PROJECT_NAMES[1]]
    elif fault == "missing-observation":
        receipt["native_formats"]["observed_projects"] = 0
    elif fault == "bool-observation":
        receipt["native_formats"]["observed_projects"] = True
    elif fault == "false-completeness":
        receipt["native_formats"]["complete_selection"] = True
    else:
        receipt["roster"] = list(selected)
    with pytest.raises(ValueError, match="exact completed local selection"):
        validate_native_transport_receipt(selected, receipt)


def _members():
    return [
        (
            scope,
            [
                {
                    "path": f"output/readiness/native-cells/{scope.split('/')[-1]}/receipt.json",
                    "sha256": hashlib.sha256(scope.encode()).hexdigest(),
                    "bytes": len(scope),
                }
            ],
        )
        for scope in PUBLIC_PROJECT_NAMES
    ]


@pytest.mark.parametrize("fault", ["none", "missing", "duplicate", "foreign", "shared-identical", "shared-conflict"])
def test_union_members_preserve_exact_whole_roster_and_conflicting_byte_refusals(fault) -> None:
    cells = _members()
    if fault == "missing":
        cells.pop()
    elif fault == "duplicate":
        cells[-1] = cells[0]
    elif fault == "foreign":
        cells[-1] = ("templates/foreign", cells[-1][1])
    elif fault.startswith("shared-"):
        shared = {"path": "output/readiness/shared-provider.whl", "sha256": "a" * 64, "bytes": 4}
        cells[0][1].append(shared)
        cells[1][1].append({**shared, "sha256": "b" * 64} if fault == "shared-conflict" else dict(shared))
    if fault in {"missing", "duplicate", "foreign", "shared-conflict"}:
        with pytest.raises(ValueError):
            native_union_members(cells)
    else:
        rows = native_union_members(cells)
        assert len(rows) == len(PUBLIC_PROJECT_NAMES) + (fault == "shared-identical")
        assert len({row["path"] for row in rows}) == len(rows)


@pytest.mark.parametrize("fault", ["absolute", "traversal", "bad-hash", "bool-size", "oversize", "extra-field"])
def test_union_members_refuse_unsafe_or_ambiguous_bindings(fault) -> None:
    cells = _members()
    row = cells[0][1][0]
    if fault == "absolute":
        row["path"] = "/foreign"
    elif fault == "traversal":
        row["path"] = "output/../foreign"
    elif fault == "bad-hash":
        row["sha256"] = "z" * 64
    elif fault == "bool-size":
        row["bytes"] = True
    elif fault == "oversize":
        row["bytes"] = 64 * 1024 * 1024 + 1
    else:
        row["other"] = "ambiguous"
    with pytest.raises(ValueError):
        native_union_members(cells)


def test_original_cell_paths_are_distinct_before_receipt_or_transport_creation() -> None:
    assert native_cell_directories(None) == ("output/readiness/native", "output/readiness/native-transport")
    paths = [native_cell_directories(scope.split("/")[-1]) for scope in PUBLIC_PROJECT_NAMES]
    assert len({path for pair in paths for path in pair}) == 2 * len(PUBLIC_PROJECT_NAMES)
    with pytest.raises(ValueError):
        native_cell_directories("../foreign")


@pytest.mark.parametrize(
    "function",
    [
        collect_native_hosted_cell_union,
        lambda source, directory, **kwargs: NativeHostedCellUnion(
            source, {}, deadline=kwargs["deadline"], key=object()
        ),
    ],
)
def test_union_factory_refuses_context_free_data_without_minting_custody(tmp_path, function) -> None:
    with pytest.raises(ValueError):
        function(
            None,
            tmp_path / "must-not-exist",
            repository="docxology/template",
            run_id=1,
            head_sha="a" * 40,
            deadline=time.monotonic() + 30,
        )
    assert not (tmp_path / "must-not-exist").exists()


@pytest.mark.parametrize("mode,cell", [("original", None), ("preflight", None), ("reader", "template_code_project")])
def test_launcher_refuses_union_with_a_producer_or_single_cell_before_preparation(mode, cell) -> None:
    arguments = [
        "--mode",
        mode,
        "--source-root",
        str(Path(__file__).resolve().parents[3]),
        "--native-cell-union",
        "--print-preparation-scopes",
    ]
    if cell is not None:
        arguments += ["--matrix-cell", cell]
    with pytest.raises(SystemExit) as failure:
        launch_native(arguments)
    assert failure.value.code == 2


@pytest.mark.parametrize("mode", ["reader", "handoff"])
def test_explicit_union_keeps_every_source_provider_in_the_real_preparation_query(mode, capsys) -> None:
    assert (
        launch_native(
            [
                "--mode",
                mode,
                "--source-root",
                str(Path(__file__).resolve().parents[3]),
                "--native-cell-union",
                "--print-preparation-scopes",
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.splitlines() == list(PUBLIC_PROJECT_NAMES)


def test_union_members_refuse_a_declared_total_beyond_the_source_eight_gib_bound() -> None:
    cells = _members()
    cells[0] = (
        cells[0][0],
        [
            {"path": f"output/readiness/large/{index}.bin", "sha256": "a" * 64, "bytes": 64 * 1024 * 1024}
            for index in range(129)
        ],
    )
    with pytest.raises(ValueError, match="whole-target census"):
        native_union_members(cells)

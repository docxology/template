"""Local cell admissibility and the single union completeness assertion.

A sharded native cell is admissible on its own terms: it names exactly one
declared public exemplar. Completeness is never asserted per cell. It exists
only where the cells are joined, mirroring the scope replay's
``completed=0, expected=2`` binding: the local run is judged locally and the
union is the one place that may claim the roster.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from pathlib import Path
import re
import sys
from typing import Any

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES, public_cell_scope
from infrastructure.reporting.native_hosted_transport_archive import (
    INDEX_ARTIFACT,
    SHARD_PREFIX,
    MAX_ARCHIVE,
    MAX_MEMBERS,
    MAX_TOTAL,
    _path,
    _hash,
)


_CELL_ARTIFACT_PREFIX = "required-source-native-cell-"
_SHARD_ORDINAL_SUFFIX = re.compile(r"-shard-[0-9]{4}$")


def cell_artifact_names(cell: str | None) -> tuple[str, str]:
    """Return the (primary index artifact, shard artifact prefix) for one native target.

    A cell renames only the artifacts. The producer's index filename and shard
    member names stay the same, so per-artifact discovery and the published
    candidate schema are unchanged.
    """
    if cell is None:
        return INDEX_ARTIFACT, SHARD_PREFIX
    public_cell_scope(cell)
    primary = _CELL_ARTIFACT_PREFIX + cell
    return primary, primary + "-shard-"


def native_cell_matrix_json() -> str:
    """Name every current hosted native cell in canonical Source order."""
    matrix = {"include": [{"cell": scope.removeprefix("templates/")} for scope in PUBLIC_PROJECT_NAMES]}
    return json.dumps(matrix, separators=(",", ":"))


def native_primary_artifact_differences(cells: Sequence[str], names: Iterable[str]) -> tuple[list[str], list[str]]:
    """Compare the exact primary names, keeping duplicate primary names visible."""
    if not cells or len(cells) != len(set(cells)):
        raise ValueError("native job matrix must name each nominated cell once")
    expected = {cell_artifact_names(cell)[0]: cell for cell in cells}
    actual = Counter(
        name
        for name in names
        if name in expected
        or (
            name.startswith(_CELL_ARTIFACT_PREFIX)
            and name != _CELL_ARTIFACT_PREFIX
            and _SHARD_ORDINAL_SUFFIX.search(name) is None
        )
    )
    missing = sorted(cell for name, cell in expected.items() if not actual[name])
    extra_names = (actual - Counter(expected.keys())).elements()
    unexpected = sorted(name.removeprefix(_CELL_ARTIFACT_PREFIX) for name in extra_names)
    return missing, unexpected


def check_native_artifact_listing(matrix_json: str, artifact_names_path: str) -> int:
    """Precheck the emitted job matrix against the names-only listing."""
    cells = [row["cell"] for row in json.loads(matrix_json)["include"]]
    count = len(cells)
    sys.stdout.write(f"expected native cells: {count}\n")
    names = Path(artifact_names_path).read_text(encoding="utf-8").splitlines()
    missing, unexpected = native_primary_artifact_differences(cells, names)
    if missing:
        sys.stdout.write(f"::error::missing native cell artifacts for: {' '.join(missing)}\n")
        return 1
    if unexpected:
        sys.stdout.write(f"::error::unexpected native cell artifacts for: {' '.join(unexpected)}\n")
        return 1
    sys.stdout.write(f"complete native cell union: {count} of {count}\n")
    return 0


def cell_selection(scopes: Sequence[str]) -> bool:
    """One sharded cell is admissible when it names exactly one declared scope."""
    return len(scopes) == 1 and scopes[0] in PUBLIC_PROJECT_NAMES


def union_selection(cell_scopes: Iterable[Sequence[str]]) -> bool:
    """The union is the only completeness assertion: every roster scope exactly once, nothing extra."""
    flattened = [scope for cell in cell_scopes for scope in cell]
    return len(flattened) == len(set(flattened)) and set(flattened) == set(PUBLIC_PROJECT_NAMES)


def native_transport_scopes(scopes: Sequence[str]) -> tuple[str, ...]:
    """Check local transport selection DATA, without granting native authority.

    Legacy transport names the complete ordered roster; a matrix transport
    names exactly one declared scope. No other partial selection is supported.
    """
    selected = tuple(scopes)
    if selected != PUBLIC_PROJECT_NAMES and not cell_selection(selected):
        raise ValueError("native transport requires one declared cell or the complete ordered public roster")
    return selected


def validate_native_transport_receipt(scopes: Sequence[str], receipt: Mapping[str, Any]) -> None:
    """Bind a local selection to its exact receipt DATA; this is no acceptance entry."""
    selected = native_transport_scopes(scopes)
    gates = receipt.get("gates")
    native = receipt.get("native_formats")
    if (
        receipt.get("roster") != list(PUBLIC_PROJECT_NAMES)
        or not isinstance(gates, dict)
        or set(gates) != {scope + ":formats" for scope in selected}
        or any(not isinstance(row, dict) or row.get("status") != "pass" for row in gates.values())
        or not isinstance(native, dict)
        or native.get("selected_projects") != list(selected)
        or type(native.get("observed_projects")) is not int
        or native["observed_projects"] != len(selected)
        or native.get("complete_selection") is not (selected == PUBLIC_PROJECT_NAMES)
    ):
        raise ValueError("native transport receipt differs from its exact completed local selection")


def native_cell_directories(cell: str | None) -> tuple[str, str]:
    """Name distinct original receipt/transport paths at birth, preserving legacy paths."""
    if cell is None:
        return "output/readiness/native", "output/readiness/native-transport"
    public_cell_scope(cell)
    return f"output/readiness/native-cells/{cell}", f"output/readiness/native-cell-transports/{cell}"


def native_union_members(
    cells: Sequence[tuple[str, Sequence[Mapping[str, Any]]]],
) -> tuple[dict[str, Any], ...]:
    """Check complete union membership DATA; only live custodians supply it in production."""
    if not union_selection((scope,) for scope, _ in cells):
        raise ValueError("native cell union requires every declared public scope exactly once")
    members: dict[str, dict[str, Any]] = {}
    total = 0
    for _, rows in cells:
        for row in rows:
            if not isinstance(row, Mapping) or set(row) != {"path", "sha256", "bytes"}:
                raise ValueError("native cell union requires exact retained member fields")
            label, digest, size = _path(row["path"]), _hash(row["sha256"]), row["bytes"]
            if type(size) is not int or not 0 <= size <= MAX_ARCHIVE:
                raise ValueError("native cell union member exceeds its unchanged logical-file bound")
            normalized = {"path": label, "sha256": digest, "bytes": size}
            if label in members:
                if members[label] != normalized:
                    raise ValueError("native cell union has conflicting retained bytes for one path")
                continue
            members[label] = normalized
            total += size
            if len(members) > MAX_MEMBERS or total > MAX_TOTAL:
                raise ValueError("native cell union exceeds its existing whole-target census")
    return tuple(members[label] for label in sorted(members))

"""Reconstruct every authenticated actual read/write event from held Source bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from infrastructure.core.analysis_data_custody import DATA_FILES, DATA_ROOTS, MAX_FILE_BYTES
from infrastructure.core.analysis_read_custody import MAX_READ_METADATA_BYTES
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def _hash(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _binding(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256, "bytes": len(snapshot.content)}


def reconstruct_returned_reads(
    raw: object,
    scope: str,
    request: dict[str, Any],
    process: dict[str, Any],
    incoming: dict[str, dict[str, Any]],
    source: NativeSourceContext,
    reader: SnapshotReader,
    deadline: float,
) -> dict[str, Any]:
    """Rebuild each actual returned body without manufacturing read completeness."""
    fields = {
        "schema",
        "run_id",
        "stage_key",
        "analysis_nonce",
        "request_digest",
        "owner_pid",
        "records",
        "total_returned_bytes",
        "completed_writes",
        "coverage_boundary",
        "content_digest",
    }
    if (
        not isinstance(raw, dict)
        or set(raw) != fields
        or raw.get("schema") != "template-analysis-returned-read-bytes-v2"
        or any(raw.get(key) != request.get(key) for key in ("run_id", "stage_key", "analysis_nonce"))
        or raw.get("request_digest") != canonical_digest(request)
        or type(raw.get("owner_pid")) is not int
        or raw.get("owner_pid") != process.get("pid")
        or raw.get("coverage_boundary")
        != "registered-Source-API-reads-only; native-direct-external-reads-not-qualified"
        or raw.get("content_digest")
        != canonical_digest({key: value for key, value in raw.items() if key != "content_digest"})
        or not isinstance(raw.get("records"), list)
        or len(raw["records"]) > 10000
        or len(
            json.dumps(
                {key: value for key, value in raw.items() if key != "content_digest"},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )
        > MAX_READ_METADATA_BYTES
    ):
        raise ValueError("native returned-read observations differ from their actual Source/request/process boundary")
    from infrastructure.reporting.native_analysis_write_replay import reconstruct_completed_writes

    writes = reconstruct_completed_writes(raw["completed_writes"], raw, scope, source, reader, deadline=deadline)
    total = 0
    rebuilt = []
    for ordinal, row in enumerate(raw["records"], 1):
        remaining(deadline)
        if (
            not isinstance(row, dict)
            or set(row)
            != {"ordinal", "path", "sha256", "bytes", "native_identity", "retained_path", "origin", "consumer"}
            or row.get("ordinal") != ordinal
            or type(row.get("ordinal")) is not int
            or not isinstance(row.get("path"), str)
            or not _hash(row.get("sha256"))
            or type(row.get("bytes")) is not int
            or not 0 <= row["bytes"] <= MAX_FILE_BYTES
        ):
            raise ValueError("native returned-read roster lost an exact original ordered body")
        path = Path(row["path"])
        reader.public_path(f"projects/{scope}/{path}")
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != row["path"]
            or not (
                row["path"] in DATA_FILES
                or any(path.is_relative_to(Path(root)) for root in DATA_ROOTS)
                or path.is_relative_to(Path("output"))
            )
            or path.is_relative_to(Path("output/.pipeline"))
            or any(part == ".env" or part.startswith(".env.") for part in path.parts)
        ):
            raise ValueError("native returned-read body escaped its original project")
        identity = row.get("native_identity")
        if (
            not isinstance(identity, list)
            or len(identity) != 5
            or any(type(value) is not int or value < 0 for value in identity)
            or identity[2] != row["bytes"]
        ):
            raise ValueError("native returned-read body omitted its actual original OS identity")
        selected = incoming.get(row["path"])
        expected_origin = (
            "original-incoming-body"
            if selected is not None and (selected["sha256"], selected["native_identity"]) == (row["sha256"], identity)
            else "not-unchanged-selected-incoming-body; original-write-causality-unqualified"
        )
        selected_write = next(
            (
                written
                for written in reversed(writes["records"])
                if (written["path"], written["sha256"], written["native_identity"])
                == (row["path"], row["sha256"], identity)
                and written["prior_registered_read_count"] < ordinal
            ),
            None,
        )
        if selected_write is not None:
            expected_origin = f"actual-completed-Source-write:{selected_write['ordinal']}"
        if row.get("origin") != expected_origin:
            raise ValueError("native returned-read incoming/write classification differs from complete original bytes")
        expected_path = (
            Path("output/.pipeline/analysis-data")
            / hashlib.sha256(request["run_id"].encode()).hexdigest()
            / "blobs"
            / row["sha256"]
        ).as_posix()
        if row.get("retained_path") != expected_path:
            raise ValueError("native returned-read body moved outside its original run-owned hash slot")
        retained = reader.read(f"projects/{scope}/{expected_path}", max_bytes=MAX_FILE_BYTES)
        if retained.sha256 != row["sha256"] or len(retained.content) != row["bytes"]:
            raise ValueError("native returned-read body differs from the actual held original bytes")
        consumer = row.get("consumer")
        if (
            not isinstance(consumer, dict)
            or set(consumer) != {"source", "source_sha256", "function", "line"}
            or not isinstance(consumer.get("source"), str)
            or not _hash(consumer.get("source_sha256"))
            or not isinstance(consumer.get("function"), str)
            or not consumer["function"]
            or type(consumer.get("line")) is not int
            or consumer["line"] < 1
            or not Path(consumer["source"]).is_relative_to(Path("projects") / scope)
        ):
            raise ValueError("native returned-read body omitted its actual project Source consumer")
        code = reader.read(consumer["source"], max_bytes=8 * 1024 * 1024)
        if (
            source.reference.read(code.relative) != code.content
            or code.sha256 != consumer["source_sha256"]
            or consumer["line"] > len(code.content.splitlines())
        ):
            raise ValueError("native returned-read actual consumer differs from independently admitted Source")
        rebuilt.append({**row, "retained": _binding(retained), "consumer_source": _binding(code)})
        total += row["bytes"]
    if total != raw.get("total_returned_bytes") or total > 256 * 1024 * 1024:
        raise ValueError("native returned-read full event/body total differs from its held ceiling")
    return {
        "content_digest": raw["content_digest"],
        "records": rebuilt,
        "total_returned_bytes": total,
        "completed_writes": writes,
        "coverage_boundary": raw["coverage_boundary"],
    }

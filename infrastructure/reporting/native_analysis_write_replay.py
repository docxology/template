"""Reconstruct completed Source writes and exact returned-read temporal edges.

Authenticated frozen worker Code/OS custody is required by the caller. Byte
and temporal lineage do not assert that every prior read scientifically caused
an output. Native/direct/external writes remain explicitly unqualified.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from infrastructure.core.analysis_data_custody import MAX_FILE_BYTES
from infrastructure.core.analysis_write_custody import MAX_WRITE_METADATA_BYTES, SCHEMA
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def reconstruct_completed_writes(
    raw: object,
    reads: dict[str, Any],
    scope: str,
    source: NativeSourceContext,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, Any]:
    fields = {
        "schema",
        "run_id",
        "stage_key",
        "analysis_nonce",
        "request_digest",
        "owner_pid",
        "records",
        "total_written_bytes",
        "coverage_boundary",
        "content_digest",
    }
    if (
        not isinstance(raw, dict)
        or set(raw) != fields
        or raw.get("schema") != SCHEMA
        or any(
            raw.get(key) != reads.get(key)
            for key in ("run_id", "stage_key", "analysis_nonce", "request_digest", "owner_pid")
        )
        or raw.get("coverage_boundary")
        != "registered-Source-API-writes-only; native-direct-external-writes-not-qualified"
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
        > MAX_WRITE_METADATA_BYTES
    ):
        raise ValueError("actual completed writes differ from their genuine worker/read/Source boundary")
    rebuilt, total = [], 0
    run_hash = hashlib.sha256(reads["run_id"].encode()).hexdigest()
    for ordinal, row in enumerate(raw["records"], 1):
        remaining(deadline)
        if (
            not isinstance(row, dict)
            or set(row)
            != {
                "ordinal",
                "path",
                "sha256",
                "bytes",
                "native_identity",
                "retained_path",
                "prior_observed",
                "prior_observation_authority",
                "producer",
                "prior_registered_read_count",
                "prior_registered_read_prefix_digest",
            }
            or type(row.get("ordinal")) is not int
            or row["ordinal"] != ordinal
            or not isinstance(row.get("path"), str)
            or type(row.get("bytes")) is not int
            or not 0 <= row["bytes"] <= MAX_FILE_BYTES
            or type(row.get("prior_registered_read_count")) is not int
            or not 0 <= row["prior_registered_read_count"] <= len(reads["records"])
            or row.get("prior_registered_read_prefix_digest")
            != canonical_digest(reads["records"][: row["prior_registered_read_count"]])
        ):
            raise ValueError("completed write roster/prefix differs from actual full ordered events")
        path = Path(row["path"])
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != row["path"]
            or not path.is_relative_to(Path("output"))
            or len(path.parts) < 2
            or any(part.startswith(".") for part in path.parts)
        ):
            raise ValueError("completed write body escaped its actual Source-owned output")
        identity = row["native_identity"]
        if (
            not isinstance(identity, list)
            or len(identity) != 5
            or any(type(value) is not int or value < 0 for value in identity)
            or identity[2] != row["bytes"]
        ):
            raise ValueError("completed write lost its actual original OS identity")
        expected = f"output/.pipeline/analysis-data/{run_hash}/blobs/{row['sha256']}"
        if row["retained_path"] != expected:
            raise ValueError("completed write lost its original run-owned retained body")
        body = reader.read(f"projects/{scope}/{expected}", max_bytes=MAX_FILE_BYTES)
        if body.sha256 != row["sha256"] or len(body.content) != row["bytes"]:
            raise ValueError("completed write differs from independently held whole output bytes")
        if row["prior_observation_authority"] != "prior-path-observation-only; not-compare-and-swap-history":
            raise ValueError("completed write improperly grants prior-target replacement history")
        previous = row["prior_observed"]
        if previous is not None:
            if not isinstance(previous, dict) or set(previous) != {
                "sha256",
                "bytes",
                "native_identity",
                "retained_path",
            }:
                raise ValueError("completed write substituted its prior path observation")
            old_path = f"output/.pipeline/analysis-data/{run_hash}/blobs/{previous['sha256']}"
            old = reader.read(f"projects/{scope}/{old_path}", max_bytes=MAX_FILE_BYTES)
            old_identity = previous["native_identity"]
            if (
                previous["retained_path"] != old_path
                or old.sha256 != previous["sha256"]
                or len(old.content) != previous["bytes"]
                or not isinstance(old_identity, list)
                or len(old_identity) != 5
                or any(type(value) is not int or value < 0 for value in old_identity)
                or old_identity[2] != previous["bytes"]
            ):
                raise ValueError("completed write prior observed retained body/OS identity differs")
        producer = row["producer"]
        if (
            not isinstance(producer, dict)
            or set(producer) != {"source", "source_sha256", "function", "line"}
            or not isinstance(producer["source"], str)
            or not Path(producer["source"]).is_relative_to(Path("projects") / scope)
            or not isinstance(producer["function"], str)
            or not producer["function"]
            or type(producer["line"]) is not int
            or producer["line"] < 1
        ):
            raise ValueError("completed write lost its actual producing project Source frame")
        code = reader.read(producer["source"], max_bytes=8 * 1024 * 1024)
        if (
            code.content != source.reference.read(code.relative)
            or code.sha256 != producer["source_sha256"]
            or producer["line"] > len(code.content.splitlines())
        ):
            raise ValueError("completed write producer differs from independently admitted whole Source")
        rebuilt.append(
            {
                **row,
                "retained": {"path": body.relative, "sha256": body.sha256},
                "producer_source": {"path": code.relative, "sha256": code.sha256},
            }
        )
        total += row["bytes"]
    if total != raw["total_written_bytes"] or total > 256 * 1024 * 1024 or not reader.unchanged():
        raise ValueError("completed writes changed or exceeded their whole actual body ceiling")
    return {
        "content_digest": raw["content_digest"],
        "records": rebuilt,
        "total_written_bytes": total,
        "coverage_boundary": raw["coverage_boundary"],
    }

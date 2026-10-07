"""Lossless bounded source-policy parts; serialization never grants acceptance."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import stat
import zlib
from pathlib import PurePosixPath
from typing import Any

from infrastructure.project.public_acceptance_case_policy import RootCasePolicy
from infrastructure.project.public_root_census_encoding import MAX_BYTES, _inflate
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
    json_object_from_bytes,
)

SCHEMA = "template-root-policy-encoding-v1"
PART_SCHEMA = "template-root-policy-part-v1"
PART_DATA_BYTES = 256 * 1024
MAX_PART_BYTES = 512 * 1024
MAX_PARTS = 64
MAX_MANIFEST_BYTES = 16 * 1024


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def policy_part_path(policy_path: str, ordinal: int) -> str:
    """Derive source filenames; a manifest cannot introduce arbitrary paths."""
    path = PurePosixPath(policy_path)
    if (
        str(path) != policy_path
        or path.is_absolute()
        or path.parent != PurePosixPath("infrastructure/config")
        or path.suffix != ".json"
        or "\\" in policy_path
        or "\0" in policy_path
        or type(ordinal) is not int
        or not 0 <= ordinal < MAX_PARTS
    ):
        raise ValueError("policy parts require an exact public source-policy path and ordinal")
    return str(path.with_name(f"{path.stem}.part-{ordinal:04d}.json"))


def encode_policy(value: dict[str, Any]) -> tuple[dict[str, Any], tuple[bytes, ...]]:
    """Retain every literal family/member/hash in deterministic finite JSON parts."""
    policy = RootCasePolicy.parse(value)
    content = _canonical(value)
    if not 0 < len(content) <= MAX_BYTES:
        raise ValueError("source policy exceeds the unchanged expanded byte ceiling")
    encoded = base64.b64encode(zlib.compress(content, level=9)).decode("ascii")
    pieces = tuple(
        _canonical(
            {"schema_version": PART_SCHEMA, "ordinal": ordinal, "data": encoded[offset : offset + PART_DATA_BYTES]}
        )
        + b"\n"
        for ordinal, offset in enumerate(range(0, len(encoded), PART_DATA_BYTES))
    )
    if not 1 <= len(pieces) <= MAX_PARTS or any(len(piece) > MAX_PART_BYTES for piece in pieces):
        raise ValueError("source policy parts exceed unchanged per-file or aggregate limits")
    manifest = {
        "schema_version": SCHEMA,
        "encoding": "canonical-json-zlib-9-base64-parts",
        "decoded_bytes": len(content),
        "decoded_sha256": hashlib.sha256(content).hexdigest(),
        "policy_sha256": policy.sha256,
        "parts": [
            {"ordinal": ordinal, "bytes": len(piece), "sha256": hashlib.sha256(piece).hexdigest()}
            for ordinal, piece in enumerate(pieces)
        ],
    }
    if len(_canonical(manifest)) > MAX_MANIFEST_BYTES:
        raise ValueError("source policy manifest exceeds its finite byte ceiling")
    return manifest, pieces


def decode_policy(reader: SnapshotReader, snapshot: ArtifactSnapshot) -> dict[str, Any]:
    """Authenticate complete source parts before the unchanged policy admission."""
    manifest = snapshot.json_object()
    if manifest.get("schema_version") != SCHEMA:
        return manifest
    parts = manifest.get("parts")
    if (
        set(manifest) != {"schema_version", "encoding", "decoded_bytes", "decoded_sha256", "policy_sha256", "parts"}
        or len(snapshot.content) > MAX_MANIFEST_BYTES
        or manifest["encoding"] != "canonical-json-zlib-9-base64-parts"
        or type(manifest["decoded_bytes"]) is not int
        or not 0 < manifest["decoded_bytes"] <= MAX_BYTES
        or any(
            not isinstance(manifest[key], str) or re.fullmatch(r"[0-9a-f]{64}", manifest[key]) is None
            for key in ("decoded_sha256", "policy_sha256")
        )
        or not isinstance(parts, list)
        or not 1 <= len(parts) <= MAX_PARTS
    ):
        raise ValueError("source policy manifest has ambiguous fields or exceeds finite limits")
    admitted = []
    for ordinal, row in enumerate(parts):
        if (
            not isinstance(row, dict)
            or set(row) != {"ordinal", "bytes", "sha256"}
            or type(row["ordinal"]) is not int
            or row["ordinal"] != ordinal
            or type(row["bytes"]) is not int
            or not 0 < row["bytes"] <= MAX_PART_BYTES
            or not isinstance(row["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is None
        ):
            raise ValueError("source policy part identity is missing, unordered or unbounded")
        relative = policy_part_path(snapshot.relative, ordinal)
        path = reader.public_path(relative)
        observed = path.lstat()
        if not stat.S_ISREG(observed.st_mode) or observed.st_size != row["bytes"]:
            raise ValueError("source policy part bytes differ before bounded admission")
        admitted.append((row, relative, reader._identity(path)))
    held = []
    data = []
    for row, relative, identity in admitted:
        part = reader.read(relative, max_bytes=row["bytes"])
        if part.identity != identity or len(part.content) != row["bytes"] or part.sha256 != row["sha256"]:
            raise ValueError("source policy part changed or disagrees with its original binding")
        value = part.json_object()
        if (
            set(value) != {"schema_version", "ordinal", "data"}
            or value["schema_version"] != PART_SCHEMA
            or type(value["ordinal"]) is not int
            or value["ordinal"] != row["ordinal"]
            or not isinstance(value["data"], str)
            or not 0 < len(value["data"]) <= PART_DATA_BYTES
        ):
            raise ValueError("source policy part payload is malformed or unbounded")
        held.append(part.content)
        data.append(value["data"])
    try:
        packed = base64.b64decode("".join(data), validate=True)
    except (ValueError, UnicodeError) as error:
        raise ValueError("source policy compressed bytes are malformed") from error
    content = _inflate(packed, manifest["decoded_bytes"])
    if hashlib.sha256(content).hexdigest() != manifest["decoded_sha256"]:
        raise ValueError("source policy differs from its complete original decoded digest")
    value = json_object_from_bytes(content)
    expected, pieces = encode_policy(value)
    if expected != manifest or tuple(held) != pieces or not reader.unchanged():
        raise ValueError("source policy encoding is altered, incomplete or noncanonical")
    return value

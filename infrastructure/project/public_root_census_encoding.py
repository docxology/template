"""Lossless original census JSON DAG; limits and every observation remain intact."""

from __future__ import annotations

import base64
import hashlib
import json
import zlib
from typing import Any

from infrastructure.project.public_acceptance_case_policy import digest

DAG_SCHEMA = "template-root-census-encoding-v1"
SCHEMA = "template-root-census-encoding-v2"
MAX_BYTES = 64 * 1024 * 1024
MAX_NODES = 250000


def _encode_dag(value: dict[str, Any]) -> dict[str, Any]:
    """Intern repeated source/fixture/marker objects in the original producer."""
    nodes: list[Any] = []
    known: dict[str, int] = {}

    def visit(item: Any, depth: int = 0) -> Any:
        if depth > 64:
            raise ValueError("census metadata nesting exceeds its finite bound")
        if not isinstance(item, (dict, list)) and item is not None and type(item) not in (str, bool, int, float):
            raise ValueError("census metadata must be finite JSON")
        identity = digest(item)
        if identity not in known:
            if isinstance(item, dict):
                if any(not isinstance(key, str) for key in item):
                    raise ValueError("census metadata keys must be strings")
                node = ["object", [[key, visit(item[key], depth + 1)] for key in sorted(item)]]
            elif isinstance(item, list):
                node = ["array", [visit(child, depth + 1) for child in item]]
            else:
                node = ["scalar", item]
            known[identity] = len(nodes)
            nodes.append(node)
            if len(nodes) > MAX_NODES:
                raise ValueError("census metadata exceeds its finite node ceiling")
        return known[identity]

    root = visit(value)
    result = {"schema_version": DAG_SCHEMA, "value_sha256": digest(value), "nodes": nodes, "root": root}
    if len(json.dumps(result, separators=(",", ":"), allow_nan=False).encode()) > MAX_BYTES:
        raise ValueError("encoded census exceeds the unchanged artifact byte ceiling")
    return result


def _decode_dag(value: dict[str, Any]) -> dict[str, Any]:
    """Admit one canonical acyclic encoding before any existing custody readback."""
    if set(value) != {"schema_version", "value_sha256", "nodes", "root"} or value["schema_version"] != DAG_SCHEMA:
        raise ValueError("unsupported census encoding")
    nodes = value["nodes"]
    if not isinstance(nodes, list) or not nodes or len(nodes) > MAX_NODES:
        raise ValueError("census encoding has invalid node inventory")
    expanded: list[Any] = []
    sizes: list[int] = []

    def child(item: Any, bound: int) -> tuple[Any, int]:
        if type(item) is not int or not 0 <= item < bound:
            raise ValueError("census reference is malformed, cyclic or forward")
        return expanded[item], sizes[item]

    for index, node in enumerate(nodes):
        if not isinstance(node, list) or len(node) != 2:
            raise ValueError("census node is malformed")
        size = 2
        if node[0] == "object":
            if not isinstance(node[1], list):
                raise ValueError("census object inventory must be explicit")
            result: Any = {}
            for pair in node[1]:
                if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], str) or pair[0] in result:
                    raise ValueError("census object repeats or omits a key")
                actual, length = child(pair[1], index)
                result[pair[0]] = actual
                size += len(json.dumps(pair[0]).encode()) + length + 2
        elif node[0] == "array":
            if not isinstance(node[1], list):
                raise ValueError("census array inventory must be explicit")
            result = []
            for item in node[1]:
                actual, length = child(item, index)
                result.append(actual)
                size += length + 1
        elif node[0] == "scalar":
            result = node[1]
            if result is not None and type(result) not in (str, bool, int, float):
                raise ValueError("census scalar must be finite JSON")
            size = len(json.dumps(result, allow_nan=False).encode())
        else:
            raise ValueError("unsupported census node kind")
        if size > MAX_BYTES:
            raise ValueError("expanded census exceeds the unchanged artifact byte ceiling")
        expanded.append(result)
        sizes.append(size)
    result, _ = child(value["root"], len(nodes))
    if not isinstance(result, dict) or digest(result) != value["value_sha256"] or _encode_dag(result) != value:
        raise ValueError("census encoding is altered, ambiguous or contains unused observations")
    return result


def _canonical(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, allow_nan=False).encode()


def _inflate(data: bytes, expected_size: int, *, limit: int = MAX_BYTES) -> bytes:
    """Bound allocation before decompression; refuse trailing and partial streams."""
    if type(expected_size) is not int or not 0 < expected_size <= limit or len(data) > limit:
        raise ValueError("compressed census exceeds the unchanged byte ceiling")
    try:
        stream = zlib.decompressobj()
        content = stream.decompress(data, expected_size + 1)
    except zlib.error as error:
        raise ValueError("compressed census stream is corrupt") from error
    if len(content) != expected_size or not stream.eof or stream.unused_data or stream.unconsumed_tail:
        raise ValueError("compressed census is oversized, truncated or has trailing bytes")
    return content


def encode(value: dict[str, Any]) -> dict[str, Any]:
    """Compress only original canonical DAG bytes, preserving every observation."""
    dag = _canonical(_encode_dag(value))
    if len(dag) > MAX_BYTES:
        raise ValueError("canonical census exceeds the unchanged artifact byte ceiling")
    packed = zlib.compress(dag, level=9)
    result = {
        "schema_version": SCHEMA,
        "encoding": "zlib-9-base64",
        "decoded_size": len(dag),
        "decoded_sha256": hashlib.sha256(dag).hexdigest(),
        "data": base64.b64encode(packed).decode("ascii"),
    }
    if len(_canonical(result)) > MAX_BYTES:
        raise ValueError("compressed census exceeds the unchanged artifact byte ceiling")
    return result


def decode(value: dict[str, Any]) -> dict[str, Any]:
    """Read the bounded canonical compressed envelope and its original DAG."""
    if (
        set(value) != {"schema_version", "encoding", "decoded_size", "decoded_sha256", "data"}
        or value.get("schema_version") != SCHEMA
        or value.get("encoding") != "zlib-9-base64"
        or not isinstance(value.get("data"), str)
        or len(_canonical(value)) > MAX_BYTES
    ):
        raise ValueError("unsupported compressed census encoding")
    try:
        packed = base64.b64decode(value["data"], validate=True)
    except (ValueError, UnicodeError) as error:
        raise ValueError("compressed census base64 is corrupt") from error
    dag = _inflate(packed, value["decoded_size"])
    if hashlib.sha256(dag).hexdigest() != value["decoded_sha256"]:
        raise ValueError("compressed census digest differs from original DAG")
    result = _decode_dag(json.loads(dag))
    if encode(result) != value:
        raise ValueError("compressed census representation is ambiguous")
    return result

"""Current-source and exact-output admission for explicit deep-search composition.

This disk-source snapshot is an artifact dependency record. It does not substitute
for the separate audited live-provider or installed-wheel acceptance receipts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import infrastructure
from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined
from infrastructure.core.implementation_custody import source_file_manifest

from template_search_project.publish.bibliography import GENERATED_SUPPLEMENT_NAME, generated_path
from template_search_project.publish.config import DeepSearchConfig


def _source_hashes() -> dict[str, str]:
    roots = {
        "project": Path(__file__).absolute().parents[1],
        "platform": Path(infrastructure.__file__).absolute().parent,
    }
    return {
        f"{label}/{name}": digest
        for label, root in roots.items()
        for name, digest in source_file_manifest(root, frozenset({".py"}), max_entries=16384, max_depth=64).items()
    }


def _config_hash(config: DeepSearchConfig) -> str:
    return hashlib.sha256(json.dumps(asdict(config), sort_keys=True).encode()).hexdigest()


def begin_deep_producer(config: DeepSearchConfig) -> dict[str, object]:
    """Capture the declared configuration and source snapshot before execution."""
    return {"config_sha256": _config_hash(config), "source_hashes": _source_hashes()}


def finish_deep_producer(
    root: Path,
    config: DeepSearchConfig,
    initial: dict[str, object],
    output_dir: Path,
    *,
    successful: bool = True,
) -> Path:
    """Bind the successful producer's actual outputs; reject source/config drift."""
    if begin_deep_producer(config) != initial:
        raise ValueError("Deep-search producer source or configuration changed")
    if not output_dir.is_relative_to(root / "output") or ".." in output_dir.parts:
        raise ValueError("Deep-search output directory must remain under project output/")
    relative_files = source_file_manifest(output_dir, frozenset({".json", ".md"}), max_entries=4096, max_depth=64)
    artifact_paths = [output_dir / relative for relative in relative_files]
    if config.write_unified_bibtex:
        artifact_paths.append(generated_path(root, config.unified_bibtex_path))
    artifacts = {
        path.relative_to(root).as_posix(): hashlib.sha256(read_bytes_confined(root, path)).hexdigest()
        for path in artifact_paths
        if path.name not in {"producer_receipt.json", "composition_summary.json", "run_summary.json"}
    }
    receipt = {
        "schema_version": 1,
        "kind": "deep-search-producer",
        "binding_kind": "disk-source-snapshot",
        "status": "passed" if successful else "failed",
        "live_provider_acceptance": False,
        **initial,
        "artifacts": artifacts,
    }
    target = output_dir / "producer_receipt.json"
    if begin_deep_producer(config) != initial:
        raise ValueError("Deep-search producer source or configuration changed during artifact custody")
    atomic_write_text_confined(root, target, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return target


def admit_deep_producer(root: Path, config: DeepSearchConfig, output_dir: Path) -> dict[Path, bytes]:
    """Refuse missing, changed, partial, or historical producer dependencies."""
    receipt = json.loads(read_bytes_confined(root, output_dir / "producer_receipt.json"))
    if (
        not isinstance(receipt, dict)
        or type(receipt.get("schema_version")) is not int
        or receipt.get("live_provider_acceptance") is not False
        or any(
            receipt.get(key) != value
            for key, value in {
                "schema_version": 1,
                "kind": "deep-search-producer",
                "binding_kind": "disk-source-snapshot",
                "status": "passed",
                "live_provider_acceptance": False,
            }.items()
        )
    ):
        raise ValueError("Deep-search producer receipt is not an admitted artifact dependency")
    for key, expected in begin_deep_producer(config).items():
        if receipt.get(key) != expected:
            raise ValueError("Deep-search producer source or configuration is stale")
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("Deep-search producer artifact custody is missing")
    required = (output_dir / "aggregate.json").relative_to(root).as_posix()
    if required not in artifacts:
        raise ValueError("Deep-search producer aggregate custody is missing")
    admitted: dict[Path, bytes] = {}
    for relative, digest in artifacts.items():
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise ValueError("Deep-search producer artifact custody is malformed")
        path = root / relative
        if Path(relative).is_absolute() or not path.is_relative_to(root / "output") or ".." in Path(relative).parts:
            raise ValueError("Deep-search producer artifact escapes output")
        raw = read_bytes_confined(root, path)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError("Deep-search producer artifact bytes changed")
        admitted[path] = raw
    if receipt.get("source_hashes") != _source_hashes():
        raise ValueError("Deep-search producer source changed during artifact admission")
    return admitted


def admit_composed_supplement(root: Path, config: DeepSearchConfig, admitted: dict[Path, bytes]) -> bytes | None:
    """Bind a present generated supplement to the exact current producer inputs."""
    target = root / "output" / "manuscript" / GENERATED_SUPPLEMENT_NAME
    try:
        raw = read_bytes_confined(root, target)
    except FileNotFoundError:
        return None
    summary_path = root / config.output_dir / "composition_summary.json"
    summary = json.loads(read_bytes_confined(root, summary_path))
    expected = {
        path.relative_to(root).as_posix(): hashlib.sha256(content).hexdigest() for path, content in admitted.items()
    }
    if (
        not isinstance(summary, dict)
        or type(summary.get("schema_version")) is not int
        or summary.get("schema_version") != 1
        or summary.get("kind") != "deep-search-composition"
        or summary.get("generated_supplement") is not True
        or summary.get("producer_receipt_sha256")
        != hashlib.sha256(read_bytes_confined(root, root / config.output_dir / "producer_receipt.json")).hexdigest()
        or summary.get("producer_inputs") != expected
        or summary.get("supplement_sha256") != hashlib.sha256(raw).hexdigest()
    ):
        raise ValueError("Generated deep-search supplement does not match its current producer inputs")
    return raw

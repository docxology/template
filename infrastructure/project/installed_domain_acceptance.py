"""Functional installed execution with exported project inputs kept as data."""

from __future__ import annotations

import base64
import hashlib
import importlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined

AUTOPOIESIS_SCHEMA = "template-installed-autopoiesis-v1"
AUTOPOIESIS_DOMAINS = ("optimization", "dynamics", "statistics", "signal", "graph")


def _artifact(root: Path, path: Path) -> dict[str, str]:
    content = read_bytes_confined(root, path, max_bytes=4 * 1024 * 1024)
    return {"sha256": hashlib.sha256(content).hexdigest(), "content_base64": base64.b64encode(content).decode()}


def artifact_object(value: object) -> dict[str, Any]:
    """Reconstruct the original bounded observation rather than trusting its summary."""
    if not isinstance(value, dict) or set(value) != {"sha256", "content_base64"}:
        raise ValueError("installed domain requires exact observed artifact bytes")
    encoded = value["content_base64"]
    if not isinstance(encoded, str) or len(encoded) > 6 * 1024 * 1024:
        raise ValueError("installed domain artifact exceeds its byte ceiling")
    try:
        content = base64.b64decode(encoded, validate=True)
    except ValueError as error:
        raise ValueError("installed domain artifact has invalid byte encoding") from error
    if hashlib.sha256(content).hexdigest() != value["sha256"]:
        raise ValueError("installed domain artifact differs from its bound bytes")
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("installed domain artifact must contain one object")
    return payload


def validate_autopoiesis_observation(value: object) -> dict[str, Any]:
    """Require all selected real child producers, coverage and independent results."""
    if not isinstance(value, dict) or value.get("schema_version") != AUTOPOIESIS_SCHEMA:
        raise ValueError("installed Autopoiesis requires its actual functional observation")
    receipt = artifact_object(value.get("receipt"))
    expected = list(AUTOPOIESIS_DOMAINS)
    if (
        receipt.get("schema_version") != "autopoiesis/selected-child-execution/2"
        or receipt.get("status") != "passed"
        or receipt.get("mode") != "core"
        or receipt.get("selection_scope") != "one-per-selected-domain"
        or type(receipt.get("selected_count")) is not int
        or receipt["selected_count"] != len(expected)
        or receipt.get("platform_version") != "4.0.1"
    ):
        raise ValueError("installed Autopoiesis omitted its required selected-child execution")
    generator = receipt.get("active_generator_custody", {})
    platform = receipt.get("platform_custody", {})
    for custody, version in ((generator, "2.0.0"), (platform, "4.0.1")):
        distribution = custody.get("distribution") if isinstance(custody, dict) else None
        if (
            not isinstance(custody, dict)
            or custody.get("binding_kind") != "installed-distribution"
            or custody.get("bytecode_binding") != "fresh-owned-prefix"
            or not isinstance(distribution, dict)
            or distribution.get("version") != version
            or not distribution.get("public_python")
            or not distribution.get("declared_files")
        ):
            raise ValueError("installed child execution lacks genuine fresh distribution custody")
    selected = receipt.get("selected_children")
    records = receipt.get("executed_children")
    observed = value.get("children")
    if (
        not isinstance(selected, list)
        or not isinstance(records, list)
        or not isinstance(observed, list)
        or len(selected) != len(expected)
        or len(records) != len(expected)
        or len(observed) != len(expected)
        or [item.get("primitive_domain") for item in selected if isinstance(item, dict)] != expected
        or [item.get("domain") for item in records if isinstance(item, dict)] != expected
        or [item.get("domain") for item in observed if isinstance(item, dict)] != expected
    ):
        raise ValueError("installed child selection/observation is incomplete or duplicated")
    for spec, record, observation in zip(selected, records, observed, strict=True):
        if record.get("status") != "passed" or record.get("spec") != spec:
            raise ValueError("installed child result differs from its selected specification")
        for stage in ("tests", "analysis"):
            process = record.get(stage, {})
            if (
                not isinstance(process, dict)
                or type(process.get("returncode")) is not int
                or process["returncode"] != 0
                or process.get("timed_out") is not False
                or process.get("command_error")
            ):
                raise ValueError("installed child producer failed or did not execute")
        sources = record.get("source_sha256")
        independent = record.get("independent_analysis", {})
        if (
            not isinstance(sources, dict)
            or not sources
            or sources != record.get("export_source_sha256")
            or not isinstance(independent, dict)
            or independent.get("status") != "passed"
            or independent.get("domain") != record["domain"]
            or type(independent.get("primitive_count")) is not int
            or independent["primitive_count"] <= 0
        ):
            raise ValueError("installed child source/export or independent calculation failed")
        analysis = artifact_object(observation.get("analysis"))
        coverage = artifact_object(observation.get("coverage"))
        totals = coverage.get("totals", {})
        if not isinstance(totals, dict):
            raise ValueError("installed child coverage totals are missing")
        percentage = totals.get("percent_covered")
        if (
            analysis.get("schema_version") != "autopoiesis/child-analysis/1"
            or analysis.get("domain") != record["domain"]
            or not isinstance(analysis.get("results"), dict)
            or len(analysis["results"]) != independent["primitive_count"]
            or record.get("analysis_artifact_sha256") != observation["analysis"]["sha256"]
            or not isinstance(coverage.get("files"), dict)
            or not coverage["files"]
            or isinstance(percentage, bool)
            or not isinstance(percentage, (int, float))
            or not math.isfinite(percentage)
            or not 90 <= percentage <= 100
            or type(totals.get("num_statements")) is not int
            or totals["num_statements"] <= 0
        ):
            raise ValueError("installed child numerical/coverage artifact is invalid or incomplete")
    return receipt


def run_autopoiesis_installed(project_root: Path, installed_prefix: Path) -> dict[str, Any]:
    """Run the genuine installed generator; never add exported source to imports."""
    if project_root.is_symlink() or not project_root.is_dir() or sys.pycache_prefix is None:
        raise ValueError("installed child execution requires real project data and fresh bytecode")
    project = project_root.resolve()
    module = importlib.import_module("template_autopoiesis.gates.realization_contract")
    if module.__file__ is None or not Path(module.__file__).resolve().is_relative_to(installed_prefix.resolve()):
        raise ValueError("selected generator was not imported from the installed environment")
    receipt_path = module.realize_selected_children(project, fresh_pycache_prefix=Path(sys.pycache_prefix))
    receipt = json.loads(read_bytes_confined(project, receipt_path, max_bytes=4 * 1024 * 1024))
    verify = importlib.import_module("template_autopoiesis.gates.child_results").verify_analysis_results
    records = receipt.get("executed_children")
    if not isinstance(records, list):
        raise ValueError("installed generator did not report its child executions")
    observations = []
    for record in records:
        child = receipt_path.parent / "exports" / record["export_name"]
        if verify(child, record["domain"]) != record["independent_analysis"]:
            raise ValueError("exported child numerical results changed after execution")
        observations.append(
            {
                "domain": record["domain"],
                "analysis": _artifact(project, child / "output/data/analysis_results.json"),
                "coverage": _artifact(project, child / "coverage.json"),
            }
        )
    result = {
        "schema_version": AUTOPOIESIS_SCHEMA,
        "receipt": _artifact(project, receipt_path),
        "children": observations,
    }
    validate_autopoiesis_observation(result)
    return result

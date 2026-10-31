"""Explicit selected-child execution contract with independent source custody."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .._platform import required_platform_version
from ..core.expand import SCHEMA_VERSION, Spec, enumerate_all, expand
from ..core.grammar import KNOWN_DOMAINS, load_grammar
from ..core.honesty import build_manifest
from .child_execution import ChildCapabilityBlocked, execute_child
from .child_results import verify_analysis_results
from .custody_paths import confined_path
from .generator_custody import capture_execution_custody
from .materialize import materialize
from .verify import verify_child

RECEIPT_SCHEMA = "autopoiesis/selected-child-execution/2"
MAX_DECLARED_CELLS = 10000


def _json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _hash(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"custody requires a regular source file: {path.name}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_custody(project: Path) -> dict[str, str]:
    """Re-read the supplied project configuration and reference-oracle sources."""
    paths = [
        project / "manuscript/config.yaml",
        *sorted((project / "src").rglob("*.py")),
        *sorted((project / "tests/primitives").glob("test_primitives_*.py")),
    ]
    return {
        path.relative_to(project).as_posix(): _hash(
            confined_path(project, path.relative_to(project).as_posix(), regular=True)
        )
        for path in paths
    }


def selected_specs(project: Path, *, single: bool = False) -> tuple[Spec, ...]:
    """Choose one exact filtered cell per selected domain; never claim all cells ran."""
    grammar = load_grammar(project)
    if grammar.product_size > MAX_DECLARED_CELLS:
        raise ValueError(f"bounded child selection permits at most {MAX_DECLARED_CELLS} nominal cells")
    cells = enumerate_all(grammar)
    if any(cell.get("primitive_domain") not in KNOWN_DOMAINS for cell in cells):
        raise ValueError("selected grammar contains an unsupported primitive domain")
    preferred = dict(expand(grammar).selections)
    selected: list[Spec] = []
    for domain in KNOWN_DOMAINS:
        candidates = [cell for cell in cells if cell.get("primitive_domain") == domain]
        if not candidates:
            continue
        # Preserve seed-derived non-domain selections where the declared
        # filters permit them; otherwise choose the first permitted cell.
        cell = next(
            (
                cell
                for cell in candidates
                if all(value == preferred.get(key) for key, value in cell.items() if key != "primitive_domain")
            ),
            candidates[0],
        )
        selected.append(
            Spec(
                SCHEMA_VERSION,
                grammar.seed,
                grammar.grammar_hash,
                tuple((slot.name, cell[slot.name]) for slot in grammar.slots),
                grammar.deps,
                domain,
            )
        )
    if not selected:
        raise ValueError("configured archetype filters select no required children")
    if single:
        preferred_domain = preferred.get("primitive_domain")
        selected = [next((spec for spec in selected if spec.primitive_domain == preferred_domain), selected[0])]
    return tuple(selected)


def _verify_source(child: Path, expected: dict[str, str]) -> dict[str, str]:
    actual: dict[str, str] = {}
    for relative, content in expected.items():
        path = confined_path(child, relative, regular=True)
        if path.read_text(encoding="utf-8") != content:
            raise ValueError(f"generated child source drift: {relative}")
        actual[relative] = _hash(path)
    if not verify_child(child).all_passed:
        raise ValueError("recomputed child provenance failed")
    return actual


def realize_selected_children(
    project_root: Path, *, single: bool = False, fresh_pycache_prefix: Path | None = None
) -> Path:
    """Run every manifest-selected child, then export only independently verified results."""
    if project_root.is_symlink() or not project_root.is_dir():
        raise ValueError("child realization requires a real source project directory")
    project = project_root.resolve()
    receipt_path = confined_path(
        project, "output/.pipeline/child_realization/" + ("single.json" if single else "archetypes.json")
    )
    receipt: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA,
        "mode": "core",
        "status": "incomplete",
        "selection_scope": "one-per-selected-domain" if not single else "one-selected-child",
        "child_pdf_rendering": "unsupported",
        "executed_children": [],
        "platform_version": None,
        "child_process_deadline_sec": 60,
        "max_declared_cells": MAX_DECLARED_CELLS,
    }
    try:
        receipt["platform_version"] = required_platform_version()
        # Admit the actual supervisor and imported generator before any child
        # materialization. Supplied project sources are reference inputs only.
        active_generator, platform = capture_execution_custody(fresh_pycache_prefix=fresh_pycache_prefix)
        receipt.update(active_generator_custody=active_generator, platform_custody=platform)
        grammar = load_grammar(project)
        specs = selected_specs(project, single=single)
        source = source_custody(project)
        honesty = build_manifest(project)
        if not honesty.all_passed:
            raise ValueError("independently recomputed structural honesty manifest failed")
        receipt.update(
            source_sha256=source,
            honesty=asdict(honesty),
            archetype_filters=dict(grammar.archetype_filters),
            declared_filtered_cells=len(enumerate_all(grammar)),
            selected_children=[spec.to_dict() for spec in specs],
            selected_count=len(specs),
        )
        # Runtime workspaces never execute from published child exports.
        runtime_root = confined_path(project, "output/.pipeline/child_realization/workspaces")
        runtime_root.mkdir(parents=True, exist_ok=True)
        export_root = confined_path(project, "output/.pipeline/child_realization/exports")
        export_root.mkdir(parents=True, exist_ok=True)
        for spec in specs:
            record: dict[str, Any] = {"domain": spec.primitive_domain, "spec": spec.to_dict(), "status": "incomplete"}
            receipt["executed_children"].append(record)
            with TemporaryDirectory(prefix="child-run-", dir=runtime_root) as temporary:
                result = materialize(spec, temporary, project)
                record["source_sha256"] = _verify_source(result.root, result.files)
                for stage, script, arguments in (
                    (
                        "tests",
                        "__pytest__",
                        (
                            "-p",
                            "pytest_cov",
                            "tests",
                            "-q",
                            "--cov=primitives",
                            "--cov=analysis",
                            "--cov-fail-under=90",
                            "--cov-report=json:coverage.json",
                        ),
                    ),
                    ("analysis", "analysis.py", ()),
                ):
                    outcome = execute_child(result.root, script, arguments=arguments)
                    record[stage] = asdict(outcome)
                    _json(receipt_path, receipt)
                    if outcome.returncode != 0 or outcome.timed_out:
                        raise ValueError(f"required {spec.primitive_domain} child {stage} producer failed")
                record["independent_analysis"] = verify_analysis_results(result.root, spec.primitive_domain)
                _verify_source(result.root, result.files)
                destination = export_root / result.name
                if destination.is_symlink():
                    raise ValueError("child export destination must not be a symlink")
                if destination.exists():
                    if not destination.is_dir() or destination.resolve().parent != export_root.resolve():
                        raise ValueError("child export must be a direct generator-owned directory")
                    shutil.rmtree(destination)
                shutil.copytree(
                    result.root,
                    destination,
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".coverage*"),
                )
                record["export_source_sha256"] = _verify_source(destination, result.files)
                artifact = destination / "output/data/analysis_results.json"
                record.update(status="passed", export_name=result.name, analysis_artifact_sha256=_hash(artifact))
                _json(receipt_path, receipt)
        current_generator, current_platform = capture_execution_custody(fresh_pycache_prefix=fresh_pycache_prefix)
        if (
            source_custody(project) != source
            or asdict(build_manifest(project)) != asdict(honesty)
            or current_generator != active_generator
            or current_platform != platform
        ):
            raise ValueError("generator, platform, or reference sources changed during child execution")
        receipt["status"] = "passed"
    except ChildCapabilityBlocked as exc:
        receipt.update(status="blocked", diagnostic=str(exc))
        raise
    except (OSError, ValueError, TypeError, NotImplementedError) as exc:
        receipt.update(status="failed", diagnostic=str(exc))
        raise
    finally:
        _json(receipt_path, receipt)
    return receipt_path

"""Select and replay scientific Office controls beside basic native controls.

Selection comes from the complete Source-owned artifact contract. Retained
JSON selects no role or capability; the fixed original child and genuine
current reader authenticate each actual control independently.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def office_scientific_control_kinds(contract: tuple[NativeArtifact, ...]) -> tuple[str, ...]:
    """Each required native Office kind retains its full scientific suite."""
    return tuple(sorted({item.format for item in contract} & {"docx", "epub"}))


def observe_selected_office_scientific_controls(
    root: Path,
    directory: Path,
    contract: tuple[NativeArtifact, ...],
    *,
    scope: str,
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    observer_tools: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Run all ten original controls for every required DOCX or EPUB kind."""
    from infrastructure.reporting.native_office_scientific_controls import supervise_office_scientific_controls

    suites = {}
    for kind in office_scientific_control_kinds(contract):
        suites[kind] = supervise_office_scientific_controls(
            root,
            directory,
            kind,
            scope=scope,
            interpreter=interpreter,
            env=env,
            deadline=deadline,
            run_id=run_id,
            epubcheck_jar=Path(observer_tools["epubcheck_jar"])
            if kind == "epub" and observer_tools.get("epubcheck_jar")
            else None,
            java_executable=Path(observer_tools["java_executable"])
            if kind == "epub" and observer_tools.get("java_executable")
            else None,
            frozen_epub_engine=root / observer_tools["frozen_epub_engine"]
            if kind == "epub" and observer_tools.get("frozen_epub_engine")
            else None,
        )
    return suites


def replay_selected_office_scientific_controls(
    controls: dict[str, Any],
    contract: tuple[NativeArtifact, ...],
    reader: SnapshotReader,
    directory: Path,
    *,
    scope: str,
    source: NativeSourceContext,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    original_deadline: float,
    deadline: float,
    env: dict[str, str],
    observer_tools: dict[str, Any],
) -> dict[str, Any]:
    """Require exact suite coverage while preserving original engine labels."""
    from infrastructure.reporting.native_office_scientific_replay import replay_office_scientific_controls

    kinds = office_scientific_control_kinds(contract)
    if not kinds:
        if "office_scientific" in controls:
            raise ValueError("scientific Office controls occur outside the required Source artifact contract")
        return {}
    suites = controls.get("office_scientific")
    if not isinstance(suites, dict) or set(suites) != set(kinds):
        raise ValueError("scientific Office suite omitted, duplicated or added a required native kind")
    results: dict[str, Any] = {}
    for kind in kinds:
        arguments: list[str] = []
        if kind == "epub":
            for option, key in (("--epubcheck-jar", "epubcheck_jar"), ("--java-executable", "java_executable")):
                if observer_tools.get(key) is not None:
                    arguments.extend((option, observer_tools[key]))
            if observer_tools.get("frozen_epub_engine") is not None:
                arguments.extend(
                    ("--frozen-epub-engine", str(Path(custody["root"]) / observer_tools["frozen_epub_engine"]))
                )
        results[kind + "_scientific"] = replay_office_scientific_controls(
            reader.root,
            directory,
            kind,
            suites[kind],
            reader,
            scope=scope,
            source=source,
            run_id=run_id,
            custody=custody,
            runtime=runtime,
            versions=versions,
            original_deadline=original_deadline,
            deadline=deadline,
            env=env,
            original_epub_arguments=tuple(arguments),
        )
    return results

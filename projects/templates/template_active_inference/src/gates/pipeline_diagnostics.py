"""Bounded failure observations for the selected Active evidence refresh.

These records preserve bytes and actual validator issues; they grant no
pipeline, semantic, publication or release acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from gates.artifact_manifest import REQUIRED_OUTPUTS

MAX_FILES = 256
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_ISSUES = 256
MAX_ISSUE_CHARS = 1024
SOURCE_INPUTS = (
    "pyproject.toml",
    "uv.lock",
    "experiment_plan.yaml",
    "tracks.yaml",
    "pymdp.yaml",
    "manuscript/config.yaml",
)
EXTRA_GENERATED = (
    "output/data/manuscript_variables.json",
    "output/reports/validation_report.json",
    "output/reports/rendered_provenance.json",
)
VALIDATORS = (
    ("semantic_gluing", "manuscript.sheaf.semantic_issues", "semantic_gluing_issues"),
    ("integration_audit", "roadmap_tracks.integration_audit", "validate_integration_audit_artifacts"),
    ("canonical_sheaf", "roadmap_tracks.sheaf_track_validation", "validate_sheaf_track_artifacts"),
)


def _directory(path: Path) -> Path:
    """Reject linked or unavailable directory ancestors before observing children."""
    path = path.absolute()
    for parent in (*reversed(path.parents), path):
        if not stat.S_ISDIR(parent.lstat().st_mode):
            raise ValueError("diagnostic directory has a linked or non-directory ancestor")
    return path


def _destination(project: Path, directory: Path) -> Path:
    """Keep diagnostic writes outside the observed project's own state."""
    directory = _directory(directory)
    if directory == project or directory.is_relative_to(project):
        raise ValueError("diagnostic destination must be outside the project")
    return directory


def selected_paths(project: Path) -> tuple[tuple[str, bool], ...]:
    """Select only declared JSON, source-config hashes and flat compiled sections."""
    project = _directory(project)
    generated = {rel for rel in (*REQUIRED_OUTPUTS, *EXTRA_GENERATED) if rel.endswith(".json")}
    if any(not re.fullmatch(r"output/(data|reports|figures)/[A-Za-z0-9_]+\.json", rel) for rel in generated):
        raise ValueError("diagnostic JSON roster contains an unsupported path")
    for relative in ("output/data", "output/reports", "manuscript"):
        directory = project / relative
        if not directory.exists() and not directory.is_symlink():
            continue
        _directory(directory)
        with os.scandir(directory) as entries:
            for index, entry in enumerate(entries):
                if index >= MAX_FILES:
                    raise ValueError("diagnostic directory census exceeds its finite bound")
                pattern = r"[0-9]{2}_[A-Za-z0-9_]+\.md" if relative == "manuscript" else r"[A-Za-z0-9_]+\.json"
                if re.fullmatch(pattern, entry.name):
                    generated.add(relative + "/" + entry.name)
    paths = tuple(sorted((*((rel, True) for rel in generated), *((rel, False) for rel in SOURCE_INPUTS))))
    if len(paths) > MAX_FILES:
        raise ValueError("diagnostic file roster exceeds its finite bound")
    return paths


def _write(directory: Path, name: str, payload: dict[str, Any]) -> Path:
    """Atomically retain one finite diagnostic record without following links."""
    path = directory / name
    body = (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    atomic_write_bytes_confined(directory, path, body, mode=0o600)
    return path


def record_snapshot(project: Path, directory: Path, phase: str, *, retain: bool = False) -> Path:
    """Observe exact selected bytes or explicit read refusals within fixed bounds."""
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", phase):
        raise ValueError("diagnostic phase is not a bounded label")
    project = _directory(project)
    directory = _destination(project, directory)
    rows: list[dict[str, Any]] = []
    total = 0
    for relative, generated in selected_paths(project):
        row: dict[str, Any] = {"path": relative, "generated": generated}
        try:
            body = read_bytes_confined(project, project / relative, max_bytes=MAX_FILE_BYTES)
            if total + len(body) > MAX_TOTAL_BYTES:
                raise ValueError("diagnostic aggregate read budget exceeded")
            total += len(body)
            row.update(status="observed", bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            if retain and generated:
                name = "raw-" + relative.replace("/", "__")
                atomic_write_bytes_confined(directory, directory / name, body, mode=0o600)
                row["raw_file"] = name
        except (OSError, ValueError) as error:
            row.update(status="unavailable", reason=f"{type(error).__name__}: {error}"[:512])
        rows.append(row)
    return _write(
        directory,
        phase + "-manifest.json",
        {
            "schema_version": "active-refresh-diagnostic-manifest-v1",
            "diagnostic_only": True,
            "acceptance_authorized": False,
            "phase": phase,
            "interpreter": sys.executable,
            "python": sys.version,
            "observed_bytes": total,
            "files": rows,
        },
    )


def record_validator_issues(project: Path, directory: Path, role: str) -> Path:
    """Call each actual project validator and retain its issues or actual exception."""
    if role not in {"root", "active"}:
        raise ValueError("diagnostic interpreter role must be root or active")
    project = _directory(project)
    directory = _destination(project, directory)
    observations = []
    for label, module_name, function_name in VALIDATORS:
        observation: dict[str, Any] = {"validator": label}
        try:
            module = importlib.import_module(module_name)
            module_file = module.__file__
            if module_file is None:
                raise ValueError("validator has no physical source file")
            module_path = Path(module_file).resolve()
            if not module_path.is_relative_to(project / "src"):
                raise ValueError("validator was imported outside the observed project source")
            observation["module_file"] = str(module_path)
            issues = getattr(module, function_name)(project)
            if not isinstance(issues, list) or any(not isinstance(issue, str) for issue in issues):
                raise ValueError("validator did not return its actual string issue list")
            observation.update(
                status="observed",
                issue_count=len(issues),
                issues=[issue[:MAX_ISSUE_CHARS] for issue in issues[:MAX_ISSUES]],
                dropped_issues=max(0, len(issues) - MAX_ISSUES),
            )
        except Exception as error:  # noqa: BLE001 - a diagnostic records actual refusals without acceptance
            observation.update(status="unavailable", exception=type(error).__name__, reason=str(error)[:1024])
        observations.append(observation)
    return _write(
        directory,
        "validator-issues-" + role + ".json",
        {
            "schema_version": "active-refresh-validator-issues-v1",
            "diagnostic_only": True,
            "acceptance_authorized": False,
            "role": role,
            "interpreter": sys.executable,
            "python": sys.version,
            "observations": observations,
        },
    )


def main(argv: list[str] | None = None) -> int:
    """Write selected phase DATA; never translate it into a successful gate verdict."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("snapshot", "raw", "validators"))
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--phase", required=True)
    args = parser.parse_args(argv)
    if args.mode == "validators":
        path = record_validator_issues(args.project_root, args.directory, args.phase)
    else:
        path = record_snapshot(args.project_root, args.directory, args.phase, retain=args.mode == "raw")
    print(json.dumps({"diagnostic_only": True, "record": str(path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

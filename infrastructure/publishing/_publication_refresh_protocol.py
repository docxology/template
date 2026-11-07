"""Shared command and receipt contract for coordinated publication refresh."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, TypedDict

COMMAND_STREAMS = ("stdout", "stderr")


def generation_commands(root: Path, plan: dict[str, Any], wave: list[str]) -> list[tuple[str, list[str]]]:
    """Select only the frozen original refresh or unchanged-output rebind CLI."""
    commands = []
    for scope in wave:
        if scope == "root":
            continue
        if scope in plan["dependent_analysis"]:
            commands.append(
                (
                    scope.replace("/", "__") + "-analysis",
                    [str(root / ".venv/bin/python"), "scripts/pipeline/stage_02_analysis.py", "--project", scope],
                )
            )
        argv = [
            str(root / ".venv/bin/python"),
            "scripts/maintenance/refresh_rendered_provenance.py",
            "--project",
            scope,
        ]
        if scope in plan["rebind"]:
            argv.append("--rebind")
        else:
            argv.append("--no-analysis-recovery")
        commands.append((scope.replace("/", "__") + "-generate", argv))
    return commands


def gate_commands(root: Path, directory: Path) -> dict[str, list[str]]:
    """Select the exact committed candidate checks."""
    python = str(root / ".venv/bin/python")
    return {
        "exemplar-config": [python, "scripts/audit/check_exemplar_configs.py"],
        "publication-gate": [
            python,
            "scripts/audit/check_publication_outputs.py",
            "--all-public",
            "--strict",
            "--jobs",
            "4",
            "--receipts",
            str(directory / "diagnostics/publication-gate"),
        ],
        "rendered-audit": [
            python,
            "-m",
            "infrastructure.validation.cli",
            "publication-audit",
            "--all-public",
            "--strict",
            "--rendered",
            "--format",
            "json",
        ],
    }


class _CommandReceipt(TypedDict):
    argv: list[str]
    returncode: int
    original_exit_code: object
    process: dict[str, Any]
    source_commit: str
    stdout_sha256: str
    stderr_sha256: str


def command_receipt(argv: list[str], process: dict[str, Any], source_commit: str) -> _CommandReceipt:
    """Record the original process observation and its normalized result."""
    original: object = process["exit_code"]
    code = original if type(original) is int and original != 0 else 0 if process["accepted"] else 1
    if process["timed_out"]:
        code = 124
    return {
        "argv": argv,
        "returncode": code,
        "original_exit_code": original,
        "process": process,
        "source_commit": source_commit,
        "stdout_sha256": process["streams"]["stdout"]["sha256"],
        "stderr_sha256": process["streams"]["stderr"]["sha256"],
    }


def successful_command_receipt(directory: Path, label: str, argv: list[str], source_commit: str) -> bool:
    """Check the original command, source commit and retained stream bytes."""
    diagnostics = directory / "diagnostics"
    receipt = json.loads((diagnostics / f"{label}.exit.json").read_bytes())
    return (
        type(receipt.get("returncode")) is int
        and receipt["returncode"] == 0
        and receipt.get("source_commit") == source_commit
        and receipt.get("argv") == argv
        and receipt.get("original_exit_code") == 0
        and receipt.get("process", {}).get("accepted") is True
        and all(
            receipt.get(stream + "_sha256")
            == hashlib.sha256((diagnostics / f"{label}.{stream}").read_bytes()).hexdigest()
            for stream in COMMAND_STREAMS
        )
    )

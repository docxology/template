"""Retain actual failed pipeline OS outcomes without granting positive custody."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_auxiliary_supervision import complete_auxiliary_observation

from infrastructure.project.installed_acceptance_artifacts import write_binary
from infrastructure.core.files.secure_write import read_bytes_confined


class AuxiliaryPipelineFailure(ValueError):
    """Keep the actual failed child/stage observation before positive readback."""

    def __init__(
        self,
        process: dict[str, Any],
        facts: dict[str, Any],
        bindings: dict[str, Any],
        *,
        validation_error: str = "",
    ) -> None:
        self.observation = {
            "role": "failed-pipeline-diagnostic-only",
            "original_exit_code": process["exit_code"],
            "timed_out": process["timed_out"],
            "facts_exit_code": facts.get("original_exit_code"),
            "validation_error": validation_error,
            "outcomes": [],
            **bindings,
        }
        execution = facts.get("execution")
        if isinstance(execution, dict) and isinstance(execution.get("outcomes"), list):
            self.observation["outcomes"] = [row for row in execution["outcomes"] if isinstance(row, dict)]
        self.code = 124 if process["timed_out"] else 130 if process["exit_code"] in (130, -2) else 1
        failed = [
            str(row.get("stage_key")) + ": " + str(row.get("diagnostic", ""))
            for row in self.observation["outcomes"]
            if row.get("status") != "succeeded"
        ]
        super().__init__(
            f"actual portable pipeline child exited {process['exit_code']}; " + (validation_error or "; ".join(failed))
        )

    @property
    def worker_observation(self) -> dict[str, Any]:
        """Failure-only worker fields; the caller retains original code separately."""
        return {
            "status": "fail",
            "diagnostic": str(self),
            "failure_class": type(self).__name__,
            "original_pipeline_failure": self.observation,
        }


def _retain_pipeline_child_facts(
    root: Path, directory: Path, inner: Path, process: dict[str, Any], bindings: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Preserve actual OS failure even when a killed child cannot finish facts."""
    facts: dict[str, Any] = {}
    facts_binding: dict[str, str] = {}
    facts_error = "actual core pipeline child omitted original facts"
    path = inner / "facts.json"
    if path.is_file():
        content = path.read_bytes()
        facts_binding = write_binary(root, directory / "pipeline-child-facts.json", content)
        try:
            decoded = json.loads(content)
        except (ValueError, UnicodeDecodeError):
            facts_error = "actual core pipeline child left malformed original facts"
        else:
            if isinstance(decoded, dict):
                facts = decoded
                facts_error = ""
            else:
                facts_error = "actual core pipeline child left non-object original facts"
    diagnostic = {**bindings, "facts_artifact": facts_binding, "facts_error": facts_error}
    if not complete_auxiliary_observation(process) or process["exit_code"] != 0:
        raise AuxiliaryPipelineFailure(process, facts, diagnostic)
    if facts_error:
        raise ValueError(facts_error)
    if facts.get("original_exit_code") != 0:
        raise AuxiliaryPipelineFailure(process, facts, diagnostic)
    return facts, facts_binding


def retain_pipeline_failure_logs(root: Path, directory: Path, copied: Path, output: Path) -> list[dict[str, Any]]:
    """Retain bounded actual combined-render diagnostics without following links.

    These failure-only artifacts cannot establish successful pipeline custody.
    A missing, oversized, or unsafe log must never hide the original OS outcome.
    """
    retained: list[dict[str, Any]] = []
    for filename in ("_combined_manuscript.log", "_combined_manuscript.tex"):
        path = output / "pdf" / filename
        try:
            content = read_bytes_confined(copied, path, max_bytes=2 * 1024 * 1024)
        except FileNotFoundError:
            continue
        except (OSError, ValueError) as error:
            retained.append({"relative": "pdf/" + filename, "diagnostic": str(error)})
        else:
            retained.append(
                {
                    "relative": "pdf/" + filename,
                    "artifact": write_binary(root, directory / "pipeline-failure-logs" / filename, content),
                }
            )
    return retained

"""Genuine cold native diagnostic lifecycle; never a complete release receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from infrastructure.core.implementation_custody import source_file_bytes
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.public_package_dependencies import local_dependency_closure
from infrastructure.reporting.native_format_acceptance import run_native_format_acceptance
from infrastructure.reporting.native_format_joint_source import NativeSDKSelection
from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumSelection
from infrastructure.reporting.native_mermaid_runtime_selection import NativeMermaidSelection
from infrastructure.reporting.native_original_progress import _preflight_phase, _representative_preflight_diagnostics
from infrastructure.reporting.native_preflight_budget import PREFLIGHT_MAX_OPERATION_SECONDS

PREFLIGHT_SCOPE = "templates/template_code_project"
PREFLIGHT_SCHEMA = "template-native-diagnostic-preflight-v2"


def preflight_provider_scopes(root: Path) -> tuple[str, ...]:
    """Nominate only the diagnostic project and its actual local providers."""
    return tuple(
        dict.fromkeys(
            (PREFLIGHT_SCOPE, *(scope for scope in local_dependency_closure(root, PREFLIGHT_SCOPE) if scope != "root"))
        )
    )


def diagnostic_exit_code(result: dict[str, object], *, deadline: float) -> int:
    """Keep an actual early nonzero result; success needs its incomplete scope."""
    code = result.get("exit_code")
    if type(code) is not int:
        raise ValueError("diagnostic preflight requires an actual integer exit code")
    summary = result.get("native_formats")
    if code == 0 and (
        not isinstance(summary, dict)
        or summary.get("complete_selection") is not False
        or summary.get("selected_projects") != [PREFLIGHT_SCOPE]
    ):
        raise ValueError("diagnostic preflight cannot claim the complete release selection")
    if code == 0:
        remaining(deadline)
    return code


def refusal_reason(result: dict[str, object]) -> str | None:
    """Read the actual refusal reason from the result this process already holds.

    The reason is per project in ``native_formats.results``. It is read from that
    in-memory object, never from a sibling artifact, and never recomputed. An
    absent or unexpected shape yields no reason rather than an invented one: a
    missing reason is the honest state, a guessed reason is worse than the gap.
    """
    summary = result.get("native_formats")
    if not isinstance(summary, dict):
        return None
    rows = summary.get("results")
    if not isinstance(rows, list):
        return None
    observed: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        diagnostic = row.get("diagnostic")
        if not isinstance(diagnostic, str) or not diagnostic.strip():
            continue
        project = row.get("project")
        observed.append(f"{project}: {diagnostic}" if isinstance(project, str) else diagnostic)
    return "; ".join(observed) if observed else None


def diagnostic_record(
    result: dict[str, object],
    *,
    code: int,
    provider_scopes: list[str],
    operation_started: float,
    environment_nomination: str | None,
) -> dict[str, object]:
    """Build the retained preflight record, naming the reason when one exists.

    Every field that existed before is unchanged, so no reader has to migrate.
    ``refused_because`` is additive and appears only when the reason is actually
    known from this process.
    """
    record: dict[str, object] = {
        "schema_version": PREFLIGHT_SCHEMA,
        "reference_commit_nomination": environment_nomination,
        "provider_scopes": provider_scopes,
        "preparation_profile": "selected-project-and-local-providers",
        "representative_scope": PREFLIGHT_SCOPE,
        "exit_code": code,
        "complete_release_acceptance": False,
        "publication_authorized": False,
        "elapsed_seconds": time.monotonic() - operation_started,
    }
    reason = refusal_reason(result)
    if reason is not None:
        record["refused_because"] = reason
    return record


def main(argv: list[str] | None = None) -> int:
    """Run one genuine installed Original/Current exemplar under its original clock."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "repo-root",
        "current-analysis-root",
        "evidence-dir",
        "sdk-package-root",
        "implementation-input",
        "pdfium-site",
        "pdfium-wheel",
        "mermaid-package-root",
        "mermaid-dependency-root",
        "mermaid-node-executable",
        "mermaid-chrome-executable",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--provider-wheel", action="append", default=[])
    parser.add_argument("--office-font-file", action="append", type=Path, default=[])
    parser.add_argument("--epubcheck-jar", type=Path)
    parser.add_argument("--java-executable", type=Path)
    parser.add_argument("--expected-platform", choices=("Linux", "Darwin"), required=True)
    parser.add_argument("--operation-started-monotonic", type=float, required=True)
    parser.add_argument("--timeout", type=int, required=True)
    args = parser.parse_args(argv)
    if (
        not 0 < args.timeout <= PREFLIGHT_MAX_OPERATION_SECONDS
        or not 0 < args.operation_started_monotonic < time.monotonic()
    ):
        parser.error(
            f"diagnostic preflight requires its original bounded at-most-{PREFLIGHT_MAX_OPERATION_SECONDS}-second outer clock"
        )
    deadline = args.operation_started_monotonic + args.timeout
    remaining(deadline)
    with _representative_preflight_diagnostics(deadline):
        return _run_preflight(args, deadline)


def _run_preflight(args: argparse.Namespace, deadline: float) -> int:
    """Keep diagnostics inside the original clock without altering preparation or outcomes."""
    _preflight_phase("preparation-begin", deadline)
    raw = source_file_bytes(args.implementation_input)
    if hashlib.sha256(raw).hexdigest() != args.implementation_sha256:
        raise ValueError("preflight SDK differs from the actual externally held input")
    wheels: dict[str, Path] = {}
    for nomination in args.provider_wheel:
        scope, separator, path = nomination.partition("=")
        if not separator or scope not in PUBLIC_PROJECT_NAMES or scope in wheels or not path:
            raise ValueError("preflight needs unique actual canonical provider nominations")
        wheels[scope] = Path(path)
    if PREFLIGHT_SCOPE not in wheels:
        raise ValueError("preflight requires the selected canonical provider nomination")
    root = args.repo_root.resolve(strict=True)
    if set(wheels) != set(preflight_provider_scopes(root)):
        raise ValueError("preflight provider nominations differ from its selected Source dependency closure")
    sdk = NativeSDKSelection(args.sdk_package_root, raw)
    selection = NativePDFiumSelection(args.pdfium_site, args.pdfium_wheel)
    # The production route owns fresh Source, provider and reader admission.
    # A duplicate preparatory capability cannot authorize or accelerate it.
    # This uses the production supervisor, real project/native execution and
    # independent Current analysis. Its one-scope selection remains incomplete.
    _preflight_phase("preparation-end", deadline)
    result = run_native_format_acceptance(
        root,
        projects=(PREFLIGHT_SCOPE,),
        timeout_seconds=args.timeout,
        evidence_dir=args.evidence_dir / "representative",
        sdk_selection=sdk,
        provider_wheels=wheels,
        pdfium_selection=selection,
        mermaid_selection=NativeMermaidSelection(
            args.mermaid_package_root,
            args.mermaid_dependency_root,
            args.mermaid_node_executable,
            args.mermaid_chrome_executable,
        ),
        office_font_files=tuple(args.office_font_file),
        epubcheck_jar=args.epubcheck_jar,
        java_executable=args.java_executable,
        expected_platform=args.expected_platform,
        operation_started=args.operation_started_monotonic,
        current_analysis_root=args.current_analysis_root,
    )
    _preflight_phase("preflight-returned", deadline)
    code = diagnostic_exit_code(result, deadline=deadline)
    record = diagnostic_record(
        result,
        code=code,
        provider_scopes=list(wheels),
        operation_started=args.operation_started_monotonic,
        environment_nomination=os.environ.get("TEMPLATE_PUBLIC_REFERENCE_COMMIT"),
    )
    write_json(root, args.evidence_dir / "diagnostic.json", record)
    sys.stdout.write(
        json.dumps(
            {
                "schema_version": PREFLIGHT_SCHEMA,
                "exit_code": code,
                "complete_release_acceptance": False,
                "publication_authorized": False,
                **({"refused_because": record["refused_because"]} if "refused_because" in record else {}),
            },
            sort_keys=True,
        )
        + "\n"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())

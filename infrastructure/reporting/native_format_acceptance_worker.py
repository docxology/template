"""Fresh core execution and native observers for one admitted public project."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.fingerprints import source_content_fingerprint
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.project.public_acceptance_evidence import (
    bootstrap_command,
    evidence_directory,
    read_json,
    runtime_identity,
    verify_runtime_execution,
    write_json,
)
from infrastructure.reporting.native_format_acceptance_checks import (
    NativeToolUnavailable,
    audit_pdf_raster,
    native_tool_record,
    parse_native_bytes,
)
from infrastructure.reporting.native_format_acceptance_contracts import (
    CONTROL_SCHEMA,
    NATIVE_SCHEMA,
    WORKER_MODULE,
    PROCESS_SCHEMA,
    contract_digest,
    native_artifact_contract,
    public_source_digest,
    unsupported_native_controls,
    validate_native_specification,
    native_environment,
    SOURCE_RENDER_ENV_NAMES,
    create_private_native_directory,
)
from infrastructure.reporting.native_format_content_contracts import compile_pdf_content_contract
from infrastructure.reporting.native_format_observer_dispatch import observe_native_artifact, observe_format_controls
from infrastructure.reporting.native_format_observer_outcome import native_observer_outcome
from infrastructure.project.native_format_library_custody import (
    observe_native_library_custody,
    validate_native_library_custody,
)
from infrastructure.reporting.native_format_portable_custody import executable_observation, producer_custody
from infrastructure.reporting.native_format_pdf_oracles import (
    PDF_CONTROL_CODES,
    PDF_CONTROL_SCHEMA,
    inspect_pdf_content,
    pdf_control_bytes,
    pdf_control_contract,
    require_pdf_control_result,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.readiness_receipts import deliverable_identity
from infrastructure.rendering.config import RenderingConfig
from infrastructure.validation.publication.audit import (
    build_publication_audit,
    format_publication_audit_json,
    validate_publication_audit,
)
from infrastructure.validation.publication.rendered_provenance import validate_rendered_provenance


def require_canonical_native_stages(plan: Any) -> None:
    """A renamed or replaced no-op plan cannot certify existing native artifacts."""
    targets = [stage.script for stage in plan.stages]
    required = [f"scripts/pipeline/stage_{suffix}.py" for suffix in ("02_analysis", "03_render", "04_validate")]
    if any(targets.count(target) != 1 for target in required):
        raise ValueError("native acceptance requires each canonical analysis/render/validation target exactly once")
    if [targets.index(target) for target in required] != sorted(targets.index(target) for target in required):
        raise ValueError("native acceptance targets are not in analysis/render/validation order")


def _parser_control(
    root: Path, directory: Path, run_id: str, kind: str, env: dict[str, str], deadline: float
) -> dict[str, Any]:
    name = f"invalid-native-{kind}"
    path = directory / f"{name}.json"
    command = bootstrap_command(
        Path(sys.executable),
        root,
        WORKER_MODULE,
        "--root",
        str(root),
        "--control",
        kind,
        "--run-id",
        run_id,
        "--control-output",
        str(path),
    )
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("native negative-control deadline expired")
    process = run_bounded_subprocess(command, cwd=root, env=env, timeout=min(remaining, 60))
    raw = read_json(root, path)
    if process.returncode != 1 or process.original_returncode != 1 or raw.get("exit_code") != 1:
        raise ValueError("actual native parser negative control did not fail as required")
    observed = write_json(
        root,
        directory / f"{name}-process.json",
        {
            "schema_version": PROCESS_SCHEMA,
            "run_id": run_id,
            "command": list(command),
            "exit_code": process.returncode,
            "original_exit_code": process.original_returncode,
            "timed_out": process.timed_out,
            "custody_refused": process.custody_refused,
        },
    )
    snapshot = SnapshotReader(root).read(path.relative_to(root).as_posix())
    return {
        "name": name,
        "expected_exit_code": 1,
        "observed_exit_code": 1,
        "artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "process_artifact": observed,
    }


def _pdf_oracle_control(
    root: Path, directory: Path, run_id: str, name: str, env: dict[str, str], deadline: float
) -> dict[str, Any]:
    """Require a real valid-PDF baseline before accepting specific mutant faults."""
    path = directory / f"pdf-oracle-{name}.json"
    command = bootstrap_command(
        Path(sys.executable),
        root,
        WORKER_MODULE,
        "--root",
        str(root),
        "--pdf-oracle-control",
        name,
        "--run-id",
        run_id,
        "--control-output",
        str(path),
        "--deadline-monotonic",
        str(deadline),
    )
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("actual valid-PDF controls exhausted the original deadline")
    process = run_bounded_subprocess(command, cwd=root, env=env, timeout=min(remaining, 60))
    raw = read_json(root, path)
    code = require_pdf_control_result(name, raw["pdf_content"])
    if process.returncode != code or process.original_returncode != code or raw.get("exit_code") != code:
        raise ValueError("actual valid-PDF control process did not preserve its intended original outcome")
    observed = write_json(
        root,
        directory / f"pdf-oracle-{name}-process.json",
        {
            "schema_version": PROCESS_SCHEMA,
            "run_id": run_id,
            "command": list(command),
            "exit_code": process.returncode,
            "original_exit_code": process.original_returncode,
            "timed_out": process.timed_out,
            "custody_refused": process.custody_refused,
        },
    )
    snapshot = SnapshotReader(root).read(path.relative_to(root).as_posix())
    return {
        "name": name,
        "expected_exit_code": code,
        "observed_exit_code": code,
        "artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "process_artifact": observed,
    }


def run_pdf_oracle_control(root: Path, output: Path, name: str, nonce: str, deadline: float) -> int:
    """Internal actual child: unexpected setup errors cannot manufacture a receipt."""
    if name not in PDF_CONTROL_CODES or re.fullmatch(r"[0-9a-f]{32}", nonce) is None:
        raise ValueError("valid-PDF control requires its exact name and admitted run nonce")
    if not math.isfinite(deadline) or deadline <= time.monotonic():
        raise TimeoutError("valid-PDF control requires the remaining original finite deadline")
    directory = output.parent / f"pdf-oracle-{name}-artifacts"
    create_private_native_directory(root, directory)
    pdf = directory / "invented-control.pdf"
    atomic_write_bytes_confined(root, pdf, pdf_control_bytes(name), mode=0o600)
    reader = SnapshotReader(root)
    snapshot = reader.read(pdf.relative_to(root).as_posix())
    observation = parse_native_bytes("pdf", snapshot.content)
    env = native_environment(root, Path(sys.executable), directory)
    raster = audit_pdf_raster(
        root, directory, snapshot, observation, env=env, deadline=deadline, run_id=nonce, ordinal=0
    )
    contract = pdf_control_contract()
    oracle = inspect_pdf_content(
        snapshot.content,
        tuple(reader.read(item["path"]).content for item in raster["rasters"]),
        contract,
        deadline=deadline,
    )
    code = require_pdf_control_result(name, oracle)
    if not reader.unchanged():
        raise ValueError("valid-PDF control custody changed during its observation")
    write_json(
        root,
        output,
        {
            "schema_version": PDF_CONTROL_SCHEMA,
            "run_id": nonce,
            "name": name,
            "exit_code": code,
            "content_contract": contract.to_dict(),
            "pdf_content": oracle,
            "artifact": {
                "id": "invented-control:pdf",
                "format": "pdf",
                "path": snapshot.relative,
                "sha256": snapshot.sha256,
                "observation": observation,
                "raster": raster,
            },
        },
    )
    return code


def run_native_worker(root: Path, specification: dict[str, Any]) -> dict[str, Any]:
    """Run the whole current core plan, then inspect exact native deliverables.

    Cleanup is explicitly omitted to preserve archived publication inputs.
    Resume and incremental reuse are disabled; the canonical render target
    removes its current renderer-owned outputs before producing them again.
    Shared infrastructure verification belongs to the separate root gate.
    """
    root = root.resolve()
    validate_native_specification(specification)
    if any(key in SOURCE_RENDER_ENV_NAMES or key.startswith("SLIDES_") for key in os.environ):
        raise ValueError("native worker received an ambient rendering override")
    scope, run_id = specification["scope"], specification["run_id"]
    directory = evidence_directory(root, root / specification["directory"])
    deadline = specification["deadline_monotonic"]
    formats = tuple(specification["formats"])
    before = public_source_digest(root)
    if before != specification["source_digest"]:
        raise ValueError("native admission source changed before execution")
    runtime = runtime_identity()
    interpreter_before = executable_observation(Path(sys.executable))
    runtime_binding = write_json(root, directory / "runtime.json", {**runtime, "execution_exit_code": 0})
    raw: dict[str, Any] = {
        "schema_version": NATIVE_SCHEMA,
        "scope": scope,
        "run_id": run_id,
        "status": "fail",
        "execution_exit_code": 1,
        "source_digest_before": before,
        "source_digest_after": "",
        "deliverables_identity_after": "",
        "runtime": runtime,
        "producer_custody": producer_custody(root, runtime, before),
        "interpreter_observation_before": interpreter_before,
        "interpreter_observation_after": {},
        "runtime_artifact": runtime_binding,
        "pipeline": {},
        "formats": {},
        "artifacts": [],
        "contract_digest": "",
        "tool_artifacts": [],
        "negative_controls": [],
        "pdf_negative_controls": [],
        "observer_controls": {},
        "library_custody_before": {},
        "library_custody_after": {},
        "publication_audit_artifact": {},
        "blockers": [],
        "diagnostic": "",
    }
    env = native_environment(root, Path(sys.executable), directory)
    try:
        if runtime["missing"] or runtime["python_version"] not in {"3.12", "3.13", "3.14"}:
            raise NativeToolUnavailable("selected supported interpreter/test stack is not prepared")
        raw["library_custody_before"] = observe_native_library_custody(formats, repo_root=root)
        reader = SnapshotReader(root)
        config_raw = reader.read(f"projects/{scope}/manuscript/config.yaml").content
        import yaml

        rendering = RenderingConfig.from_project_config(yaml.safe_load(config_raw), env={})
        for name, arguments in (
            (rendering.pandoc_path, ["--version"]),
            (rendering.latex_compiler, ["--version"]),
            ("pdftoppm", ["-v"]),
            ("pdffonts", ["-v"]),
        ):
            tool = native_tool_record(
                root,
                directory,
                name,
                arguments,
                env=env,
                deadline=deadline,
                run_id=run_id,
                purpose=f"tool-version-{len(raw['tool_artifacts'])}",
            )
            raw["tool_artifacts"].append(tool["artifact"])
            if tool["exit_code"] != 0 or tool["original_exit_code"] != 0:
                raise ValueError("actual native tool version probe failed")
        with project_output_lock(root / "projects" / scope, timeout=max(0.0, deadline - time.monotonic())):
            config = PipelineConfig(
                scope,
                root,
                clean=False,
                skip_infra=True,
                mode="core",
                run_timeout_seconds=specification["timeout_seconds"],
            )
            plan = compile_execution_plan(config)
            require_canonical_native_stages(plan)
            reader.read(plan.provenance)
            executor = PipelineExecutor(config)
            results = executor.execute_plan(plan, deadline_monotonic=deadline)
            outcome = executor.run_result(results)
            raw["pipeline"] = {
                "mode": "core",
                "run_id": executor.run_id,
                "selection": {"skip_clean": True, "skip_infra": True},
                "plan": plan.to_dict(),
                "plan_digest": plan.digest,
                "expected_stage_keys": list(plan.expected_stage_keys),
                "outcomes": [item.to_dict() for item in outcome.outcomes],
                "source_content_identity": source_content_fingerprint(
                    root, config.project_dir, definition_path=root / plan.provenance
                ),
            }
            raw["execution_exit_code"] = outcome.exit_code
            if (
                not outcome.complete
                or outcome.exit_code
                or any(item.status.value != "succeeded" for item in outcome.outcomes)
            ):
                raw["status"] = "blocked" if outcome.exit_code == 75 else "fail"
                if raw["status"] == "blocked":
                    raw["blockers"].append(
                        {"tool": "core execution contract", "reason": "native core execution paused or was blocked"}
                    )
                raise ValueError("fresh source-owned core execution did not complete")
            if not validate_rendered_provenance(root, scope).valid:
                raise ValueError("fresh native outputs lack valid current rendered provenance")
            native_reader = SnapshotReader(root)
            contract = native_artifact_contract(root, scope, formats, native_reader)
            raw["contract_digest"] = contract_digest(contract)
            for index, artifact in enumerate(contract):
                snapshot = native_reader.read(artifact.path)
                observation = parse_native_bytes(artifact.format, snapshot.content)
                row = {**asdict(artifact), "sha256": snapshot.sha256, "observation": observation}
                if artifact.format == "pdf":
                    row["raster"] = audit_pdf_raster(
                        root, directory, snapshot, observation, env=env, deadline=deadline, run_id=run_id, ordinal=index
                    )
                    content = compile_pdf_content_contract(root, scope, artifact, native_reader, deadline=deadline)
                    row["content_contract"] = content.to_dict()
                    row["pdf_content"] = inspect_pdf_content(
                        snapshot.content,
                        tuple(native_reader.read(item["path"]).content for item in row["raster"]["rasters"]),
                        content,
                        deadline=deadline,
                    )
                    if row["pdf_content"]["findings"]:
                        raise ValueError(
                            f"actual PDF content/layout/visibility failed: {row['pdf_content']['findings']}"
                        )
                    raw["blockers"].extend(
                        {"tool": f"PDF source oracle {artifact.id}", "reason": reason}
                        for reason in row["pdf_content"]["blockers"]
                    )
                selected_tools = specification.get("observer_tools", {})
                observer = observe_native_artifact(
                    root,
                    directory,
                    scope,
                    artifact,
                    snapshot,
                    native_reader,
                    env=env,
                    deadline=deadline,
                    run_id=run_id,
                    ordinal=index,
                    epubcheck_jar=Path(selected_tools["epubcheck_jar"])
                    if selected_tools.get("epubcheck_jar")
                    else None,
                    java_executable=Path(selected_tools["java_executable"])
                    if selected_tools.get("java_executable")
                    else None,
                    frozen_epub_engine=root / selected_tools["frozen_epub_engine"]
                    if selected_tools.get("frozen_epub_engine")
                    else None,
                )
                row["native_observer"] = observer
                result = native_observer_outcome(observer)
                if result.get("status") == "fail" or result.get("findings"):
                    raise ValueError(f"actual native observer failed for {artifact.id}: {result.get('findings')}")
                raw["blockers"].extend(
                    {"tool": f"native source oracle {artifact.id}", "reason": reason}
                    for reason in result.get("blockers", [])
                )
                raw["artifacts"].append(row)
            for kind in formats:
                id_ = f"manuscript:{kind}"
                primary: dict[str, Any] | None = next((item for item in raw["artifacts"] if item["id"] == id_), None)
                if kind == "slides":
                    primary = next((item for item in raw["artifacts"] if item["id"].endswith(":slides")), None)
                if primary is None:
                    raise ValueError("required native format has no actual artifact")
                raw["formats"][kind] = {"path": primary["path"], "sha256": primary["sha256"], "validated": True}
            for kind in sorted({artifact.format for artifact in contract}):
                raw["negative_controls"].append(_parser_control(root, directory, run_id, kind, env, deadline))
            if any(artifact.format == "pdf" for artifact in contract):
                # Dict insertion order puts the positive actual baseline first.
                for name in PDF_CONTROL_CODES:
                    raw["pdf_negative_controls"].append(
                        _pdf_oracle_control(root, directory, run_id, name, env, deadline)
                    )
            selected_tools = specification.get("observer_tools", {})
            raw["observer_controls"] = observe_format_controls(
                root,
                directory,
                formats,
                env=env,
                deadline=deadline,
                run_id=run_id,
                interpreter=Path(sys.executable),
                epubcheck_jar=Path(selected_tools["epubcheck_jar"]) if selected_tools.get("epubcheck_jar") else None,
                java_executable=Path(selected_tools["java_executable"])
                if selected_tools.get("java_executable")
                else None,
                frozen_epub_engine=root / selected_tools["frozen_epub_engine"]
                if selected_tools.get("frozen_epub_engine")
                else None,
            )
            invalid_pdf = directory / "invented-invalid.pdf"
            invalid_pdf.write_bytes(b"invented public malformed PDF negative control\n")
            tool = native_tool_record(
                root,
                directory,
                "pdftoppm",
                [str(invalid_pdf), str(directory / "invalid-raster")],
                env=env,
                deadline=deadline,
                run_id=run_id,
                purpose="invalid-pdf-tool",
            )
            if tool["exit_code"] != 1 or tool["original_exit_code"] != 1:
                raise ValueError("actual PDF raster tool did not reject malformed native input with its required exit")
            raw["negative_controls"].append(
                {
                    "name": "invalid-pdf-tool",
                    "expected_exit_code": 1,
                    "observed_exit_code": 1,
                    "artifact": tool["artifact"],
                }
            )
            audit = build_publication_audit(root, projects=[scope], rendered=True, require_figure_accessibility=True)
            audit_payload = json.loads(format_publication_audit_json(audit))
            raw["publication_audit_artifact"] = write_json(root, directory / "publication-audit.json", audit_payload)
            if validate_publication_audit(audit, strict=True) != 0 or not native_reader.unchanged():
                raise ValueError("fresh strict rendered publication audit or artifact custody failed")
            verify_runtime_execution(root / "projects" / scope)
            raw["deliverables_identity_after"] = deliverable_identity(root, scope)
            raw["blockers"].extend(unsupported_native_controls(scope, formats))
            raw["status"] = "blocked" if raw["blockers"] else "pass"
            raw["execution_exit_code"] = 75 if raw["blockers"] else 0
    except NativeToolUnavailable as error:
        raw["status"], raw["execution_exit_code"] = "blocked", 75
        raw["blockers"].append({"tool": "native installed tool", "reason": str(error)})
    except TimeoutError as error:
        raw["status"], raw["execution_exit_code"], raw["diagnostic"] = "fail", 124, str(error)
    except Exception as error:  # noqa: BLE001 - every unexpected observer failure remains failed
        raw["diagnostic"] = str(error)
        if raw["status"] != "blocked":
            raw["status"] = "fail"
            raw["execution_exit_code"] = raw["execution_exit_code"] or 1
    try:
        raw["source_digest_after"] = public_source_digest(root)
    except (OSError, ValueError) as error:
        raw["source_digest_after"] = ""
        raw["diagnostic"] = f"public source custody unavailable after native execution: {error}"
    if raw["source_digest_after"] != before:
        raw["status"], raw["execution_exit_code"], raw["diagnostic"] = (
            "fail",
            raw["execution_exit_code"] if raw["execution_exit_code"] in {130, 124} else 1,
            raw["diagnostic"] or "public source changed during native execution",
        )
    if raw["library_custody_before"]:
        try:
            raw["library_custody_after"] = observe_native_library_custody(formats, repo_root=root)
            validate_native_library_custody(
                raw["library_custody_before"],
                raw["library_custody_after"],
                formats=formats,
                reader=SnapshotReader(root),
                runtime=runtime,
            )
        except (OSError, ValueError) as error:
            raw["status"] = "fail"
            raw["execution_exit_code"] = raw["execution_exit_code"] if raw["execution_exit_code"] in {124, 130} else 1
            raw["diagnostic"] = f"native decoder custody unavailable or changed: {error}"
    raw["interpreter_observation_after"] = executable_observation(Path(sys.executable))
    if raw["interpreter_observation_after"] != interpreter_before:
        raw["status"], raw["execution_exit_code"] = "fail", 1
        raw["diagnostic"] = "native interpreter changed during execution"
    return raw


def main(argv: list[str] | None = None) -> int:
    """Internal supervised worker; public CLI owns selection and final bindings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--control", choices=("pdf", "html", "docx", "epub", "pptx", "png"))
    parser.add_argument(
        "--control-suite", action="store_true", help="Internal actual nested parser-control transport check"
    )
    parser.add_argument("--run-id")
    parser.add_argument("--control-output", type=Path)
    parser.add_argument("--pdf-oracle-control", choices=tuple(PDF_CONTROL_CODES))
    parser.add_argument("--deadline-monotonic", type=float)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.pdf_oracle_control:
        if (
            args.spec
            or args.control
            or args.control_suite
            or args.control_output is None
            or not args.run_id
            or args.deadline_monotonic is None
        ):
            parser.error("valid-PDF control requires only its exact admitted output/run/deadline")
        output = SnapshotReader(root).public_path(args.control_output.relative_to(root).as_posix())
        return run_pdf_oracle_control(root, output, args.pdf_oracle_control, args.run_id, args.deadline_monotonic)
    if args.deadline_monotonic is not None:
        parser.error("control deadline requires a valid-PDF control")
    if args.control_suite:
        if args.spec or args.control or args.control_output is None or not args.run_id:
            parser.error("control suite requires only its admitted directory and run identity")
        directory = evidence_directory(root, args.control_output)
        env = native_environment(root, Path(sys.executable), directory)
        deadline = time.monotonic() + 120
        controls = [
            _parser_control(root, directory, args.run_id, kind, env, deadline)
            for kind in ("pdf", "html", "docx", "epub", "pptx", "png")
        ]
        write_json(root, directory / "parser-controls.json", {"run_id": args.run_id, "controls": controls})
        return 0
    if args.control:
        code = 0
        try:
            parse_native_bytes(args.control, b"invented public malformed native artifact")
        except Exception:  # noqa: BLE001 - negative control records actual parser refusal
            code = 1
        if args.control_output is None or not args.run_id:
            parser.error("negative control requires its admitted output and run identity")
        write_json(
            root,
            args.control_output,
            {
                "schema_version": CONTROL_SCHEMA,
                "run_id": args.run_id,
                "name": f"invalid-native-{args.control}",
                "format": args.control,
                "exit_code": code,
            },
        )
        return code
    if args.spec is None:
        parser.error("native worker requires an admitted specification")
    specification = read_json(root, args.spec)
    raw = run_native_worker(root, specification)
    write_json(root, root / specification["directory"] / "native-execution.json", raw)
    code = raw["execution_exit_code"]
    if type(code) is not int:
        raise ValueError("native worker outcome is not a typed exit code")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

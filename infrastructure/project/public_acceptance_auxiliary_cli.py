"""Explicit CLI for source-bound auxiliary acceptance; never publishes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from infrastructure.project.public_acceptance_auxiliary import (
    admitted_root_export,
    admitted_runtime_providers,
    run_auxiliary_acceptance,
    run_sandbox_transfer,
)
from infrastructure.project.public_acceptance_auxiliary_native import LITERATURE_MODULES


def main() -> int:
    """Execute the explicitly selected real checks under one deadline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--gate", action="append")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--interpreter", type=Path)
    parser.add_argument("--local-model", help="Explicit already-installed loopback Ollama model for literature gates")
    parser.add_argument(
        "--auxiliary-workers",
        type=int,
        choices=(1, 2, 3),
        default=1,
        help="Bounded owned auxiliary child supervisors; one gate per project, one original deadline",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare-transfer", action="store_true")
    mode.add_argument("--prepare-runtime-providers", action="store_true")
    mode.add_argument("--emit-transfer", action="store_true")
    mode.add_argument("--installed", action="store_true")
    mode.add_argument("--all", action="store_true", help="Every source-declared auxiliary requirement")
    from infrastructure.project.public_acceptance_cli import interpreter

    parser.add_argument("--installed-interpreter", type=interpreter, action="append", default=[])
    parser.add_argument(
        "--installed-workers",
        type=int,
        choices=(1, 2, 3),
        default=1,
        help="Bounded isolated installed package workers; preserves all runtime cells",
    )
    parser.add_argument("--export-receipt", type=Path)
    parser.add_argument("--installed-receipt", type=Path)
    parser.add_argument("--upload-outputs", type=Path)
    parser.add_argument("--downloaded-directory", type=Path)
    parser.add_argument("--repository")
    parser.add_argument("--github-run-id")
    parser.add_argument("--source-commit")
    parser.add_argument("--docker-image-id", help="Explicit existing immutable Docker image for SIA")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.installed:
        from infrastructure.project.installed_acceptance import run_installed_acceptance

        report = run_installed_acceptance(
            root,
            dict(args.installed_interpreter),
            project_workers=args.installed_workers,
            timeout_seconds=args.timeout_seconds,
            evidence_dir=args.evidence_dir,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return int(report["exit_code"])
    if args.prepare_runtime_providers:
        if args.installed_receipt is None:
            parser.error("--prepare-runtime-providers requires --installed-receipt")
        print(json.dumps(admitted_runtime_providers(root, args.installed_receipt)))
        return 0
    if args.prepare_transfer:
        if args.export_receipt is None:
            parser.error("--prepare-transfer requires --export-receipt")
        export = admitted_root_export(root, args.export_receipt.absolute())
        print(json.dumps({"export_artifact": export, "upload_path": str(root / export["path"])}))
        return 0
    if args.emit_transfer:
        if any(
            value is None
            for value in (
                args.export_receipt,
                args.upload_outputs,
                args.downloaded_directory,
                args.repository,
                args.github_run_id,
                args.source_commit,
                args.evidence_dir,
            )
        ):
            parser.error("--emit-transfer requires export/upload/download/repository/run/revision/evidence inputs")
        report = run_sandbox_transfer(
            root,
            export_receipt=args.export_receipt,
            upload_outputs=args.upload_outputs,
            downloaded_directory=args.downloaded_directory,
            repository=args.repository,
            run_id=args.github_run_id,
            source_commit=args.source_commit,
            evidence_dir=args.evidence_dir,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return int(report["exit_code"])
    selected = args.gate
    if args.all:
        from infrastructure.reporting.release_readiness_profile import required_profile
        from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
        from infrastructure.reporting.readiness_receipts import source_fingerprint

        profile, faults = required_profile(root, SnapshotReader(root), source_fingerprint(root))
        if faults:
            raise ValueError("complete auxiliary source profile is invalid")
        selected = [
            requirement.id
            for requirement in profile
            if requirement.kind in {"roster", "transfer", "docs", "oracle", "platform", "pipeline", "domain", "live"}
        ]
    report = run_auxiliary_acceptance(
        args.repo_root,
        gates=selected,
        timeout_seconds=args.timeout_seconds,
        evidence_dir=args.evidence_dir,
        interpreter=args.interpreter,
        workers=args.auxiliary_workers,
        producer_inputs={
            scope: {"model": args.local_model, "image_id": args.docker_image_id}
            for scope in (
                *LITERATURE_MODULES,
                "templates/template_sia",
                "templates/template_autoscientists",
                "templates/template_code_project",
                "templates/template_prose_project",
                "templates/template_gold_refinement",
            )
        },
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

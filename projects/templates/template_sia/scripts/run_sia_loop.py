#!/usr/bin/env python3
"""Thin orchestrator for the deterministic SIA harness loop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from infrastructure.core.logging.utils import get_logger

from template_sia.loop.loop import run_sia_loop_project
from template_sia.loop.live_proposals import ProposalSettings, run_live_proposals
from template_sia.loop.proposal_domain import LiveCapabilityBlocked, LiveProposalFailed
from template_sia.loop.loop_config import load_sia_settings

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        default=str(PROJECT_ROOT),
        help="Project root directory",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--live-sia",
        action="store_true",
        help="Run fixed reference subprocess diagnostics (no mutation or live-capability acceptance).",
    )
    modes.add_argument(
        "--live-proposals",
        action="store_true",
        help="Request real local Ollama numeric proposals and evaluate only in Docker.",
    )
    parser.add_argument("--model", default=None, help="Explicit local Ollama model; defaults to project config.")
    parser.add_argument("--container-image", default="", help="Already installed immutable Docker sha256 image id.")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434", help="HTTP loopback Ollama origin.")
    parser.add_argument("--proposal-output-dir", type=Path, help="Fresh directory under the project's output tree.")
    args = parser.parse_args(argv)
    project_root = Path(args.project_root).resolve()
    if args.live_proposals:
        try:
            configured = load_sia_settings(project_root)
            settings = ProposalSettings(
                model=args.model if args.model is not None else configured.llm_model,
                image_id=args.container_image,
                endpoint=args.ollama_endpoint,
                max_generations=configured.max_generations,
                target_timeout_sec=configured.target_timeout_sec,
            )
            destination = (
                args.proposal_output_dir or project_root / "output" / f"live_proposals_run_{configured.run_id}"
            )
            receipt = run_live_proposals(project_root, destination, settings)
        except LiveCapabilityBlocked as exc:
            print(f"SIA live capability blocked: {exc}")
            return 75
        except (LiveProposalFailed, OSError) as exc:
            print(f"SIA live proposal failed: {exc}")
            return 1
        except ValueError as exc:
            print(f"SIA invocation rejected: {exc}")
            return 2
        print(receipt)
        return 0
    logger.info("Running SIA loop (live=%s)", args.live_sia)
    result = run_sia_loop_project(project_root, live=args.live_sia)
    summary = json.loads(result.run_summary.read_text(encoding="utf-8"))
    print(result.report_path)
    print(result.run_summary)
    print(json.dumps({"generations": len(summary.get("generations", []))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

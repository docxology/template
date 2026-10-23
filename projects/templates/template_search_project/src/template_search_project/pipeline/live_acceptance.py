"""Explicit unpaid live search/full-text/synthesis acceptance; offline remains default."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from infrastructure.search.literature.live_artifacts import (
    annotation_prompt,
    annotation_schema,
    export_citations,
    read_core_reference,
    validate_annotation,
)
from infrastructure.search.literature.live_contract import (
    LiteratureBlocked,
    LiteratureFailed,
    LiveSession,
    LiveSettings,
    write_json,
)
from infrastructure.search.literature.live_providers import (
    CROSSREF_URL,
    EUROPEPMC_URL,
    licensed_fulltext,
    retrieve_crossref,
)
from infrastructure.search.literature.live_transport import LocalGenerator

from template_search_project.publish.config import load_project_config

CAPABILITIES = ["retrieval", "fulltext", "local-synthesis"]


def run_live(
    project_root: Path,
    directory: Path,
    settings: LiveSettings,
    *,
    crossref_endpoint: str = CROSSREF_URL,
    europepmc_endpoint: str = EUROPEPMC_URL,
) -> Path:
    """Require actual success from every declared producer in a fresh ignored directory."""
    session = LiveSession(
        project_root, directory, settings, CAPABILITIES, active_source_root=Path(__file__).absolute().parents[1]
    )
    generator = LocalGenerator(session, max_calls=1)
    try:
        config_bytes = session.freeze_project_input_bytes("manuscript/config.yaml")
        config = load_project_config(session.directory / "inputs/manuscript/config.yaml", source_bytes=config_bytes)
        papers = retrieve_crossref(session, config.search.query, endpoint=crossref_endpoint)
        keys = export_citations(session, papers)
        write_json(session.directory / "corpus.json", [paper.to_dict() for paper in papers])
        session.receipt["producer_results"]["retrieval"] = {
            "status": "passed",
            "paper_count": len(papers),
            "bibtex_count": len(keys),
            "scope": "bounded CC-BY-4.0 discovery sample; not an exhaustive systematic review",
        }
        paper, fulltext, fulltext_receipt = licensed_fulltext(session, papers, europepmc_endpoint=europepmc_endpoint)
        session.receipt["producer_results"]["fulltext"] = fulltext_receipt
        source = fulltext[:6000]
        annotation = validate_annotation(
            generator.generate(
                annotation_prompt(source, "Write one short summary of this paper excerpt in summary."),
                annotation_schema(source),
            ),
            source,
        )
        note: dict[str, Any] = {
            "paper_id": paper.id,
            "citation_key": keys[paper.id],
            **annotation,
            "claim_boundary": "model annotation and literal quote custody; entailment has not been independently validated",
        }
        write_json(session.directory / "synthesis.json", note)
        session.receipt["producer_results"]["local-synthesis"] = {
            "status": "passed",
            "selected_paper_id": paper.id,
            "model_sha256": generator.model_sha256,
            "calls": generator.calls,
            "scope": "one source-bound local synthesis annotation",
        }
        return session.finalize("passed")
    except LiteratureBlocked as exc:
        return session.finalize("blocked", issue=str(exc))
    except (LiteratureFailed, OSError, ValueError, KeyError, TypeError) as exc:
        return session.finalize("failed", issue=f"{type(exc).__name__}: {exc}")


def main(project_root: Path, argv: list[str] | None = None) -> int:
    """Core references never stand in for an explicitly selected live capability."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("core", "live"), default="core")
    parser.add_argument("--model")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-results", type=int, default=3)
    args = parser.parse_args(argv)
    if args.mode == "core":
        print(json.dumps(read_core_reference(project_root, project_root / "data/corpus.json"), sort_keys=True))
        return 0
    if args.model is None or args.output_dir is None:
        parser.error("live mode requires --model and a fresh --output-dir")
    settings = LiveSettings(args.model, args.endpoint, max_results=args.max_results)
    path = run_live(project_root, args.output_dir, settings)
    print(path)
    status = json.loads(path.read_text())["status"]
    return {"passed": 0, "blocked": 75, "failed": 1}[status]

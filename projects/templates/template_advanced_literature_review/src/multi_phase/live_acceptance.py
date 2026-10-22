"""Bounded unpaid phase retrieval, screening calibration, and local classification."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
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
    exact_json,
    write_json,
)
from infrastructure.search.literature.live_providers import (
    CROSSREF_URL,
    EUROPEPMC_URL,
    OPENALEX_URL,
    licensed_fulltext,
    retrieve_crossref,
    retrieve_openalex_crossref,
)
from infrastructure.search.literature.live_transport import LocalGenerator

from literature.corpus import Corpus
from literature.models import Author, Paper
from multi_phase.contracts import (
    score_llm_calibration,
    validate_phase_artifact_manifest,
)
from multi_phase.models import PhaseMetadata
from multi_phase.search import MultiPhaseSearchRunner

CAPABILITIES = ["retrieval", "screening", "local-classification", "licensed-fulltext"]


def _domain_paper(record: Any) -> Paper:
    return Paper(
        title=record.title,
        abstract=record.abstract or "",
        year=record.year,
        doi=record.doi,
        authors=[Author(name) for name in record.authors],
        venue=record.venue,
        references=[
            "doi:" + row["DOI"].lower()
            for row in record.raw.get("reference", [])
            if isinstance(row, dict) and isinstance(row.get("DOI"), str)
        ],
    )


def _write_phase_outputs(session: LiveSession, runner: MultiPhaseSearchRunner, phases: list[str]) -> None:
    """Use established domain membership/overlap/citation and manifest contracts."""
    for phase in phases:
        papers = [row.paper for row in runner.all_phased_papers.values() if phase in row.phases_found_in]
        Corpus(papers=papers).save(session.directory / f"{phase}_corpus.jsonl")
    papers = [row.paper for row in runner.all_phased_papers.values()]
    Corpus(papers=papers).save(session.directory / "combined_corpus.jsonl")
    citations = runner.validate_cross_phase_citations()
    analysis = runner.build_cross_phase_analysis(citations)
    write_json(session.directory / "cross_phase_analysis.json", analysis)
    write_json(
        session.directory / "phase_metadata.json",
        {
            "phases": {key: asdict(value) for key, value in runner.phase_metadata.items()},
            "total_unique_papers": len(papers),
            "execution_scope": "first configured query per phase; bounded configured-engine sample",
        },
    )
    write_json(
        session.directory / "phase_validation_report.json",
        runner.validate_phase_configuration(),
    )
    runner._write_phase_artifact_manifest(session.directory, phase_ids=phases, execution_mode="live-unpaid-bounded")
    manifest_path = session.directory / "phase_artifact_manifest.json"
    manifest = exact_json(session.consume(manifest_path))
    issues = validate_phase_artifact_manifest(manifest, artifact_root=session.directory)
    if issues:
        raise LiteratureFailed(f"source-bound phase artifact contract failed: {issues}")
    for artifact in manifest["artifacts"]:
        session.consume(session.directory / artifact["path"])
    for phase in phases:
        observed = set(analysis["phase_membership"][phase]["paper_ids"])
        expected = {row.paper.canonical_id for row in runner.all_phased_papers.values() if phase in row.phases_found_in}
        if observed != expected:
            raise LiteratureFailed("independent phase membership reconciliation failed")


def _fulltext_candidates(phase_candidates: dict[str, list[Any]]) -> list[Any]:
    """Cover configured phases before second records; never rank by access outcome."""
    candidates: list[Any] = []
    selected_ids: set[str] = set()
    for rank in range(max(map(len, phase_candidates.values()), default=0)):
        for records in phase_candidates.values():
            if rank < len(records) and records[rank].id not in selected_ids and len(candidates) < 3:
                candidates.append(records[rank])
                selected_ids.add(records[rank].id)
    return candidates


def run_live(
    project_root: Path,
    directory: Path,
    settings: LiveSettings,
    *,
    crossref_endpoint: str = CROSSREF_URL,
    europepmc_endpoint: str = EUROPEPMC_URL,
    openalex_endpoint: str = OPENALEX_URL,
) -> Path:
    session = LiveSession(
        project_root,
        directory,
        settings,
        CAPABILITIES,
        active_source_root=Path(__file__).absolute().parents[1],
    )
    generator = LocalGenerator(session, max_calls=7)
    try:
        config_bytes = session.freeze_project_input_bytes("manuscript/config.yaml")
        runner = MultiPhaseSearchRunner(
            session.directory / "inputs/manuscript/config.yaml",
            project_root=project_root,
            output_dir=session.directory,
            config_source_bytes=config_bytes,
        )
        report = runner.validate_phase_configuration()
        if report["status"] != "pass":
            raise LiteratureFailed(f"phase configuration failed: {report['issues']}")
        phases = list(runner.search_phases)
        if not 1 <= len(phases) <= 3:
            raise LiteratureFailed("bounded live acceptance requires one to three configured phases")
        all_records: dict[str, Any] = {}
        phase_sources: dict[str, str] = {}
        selected_queries: dict[str, str] = {}
        selected_providers: dict[str, str] = {}
        phase_candidates: dict[str, list[Any]] = {}
        for index, phase in enumerate(phases):
            config = runner.search_phases[phase]
            query = config["queries"][0]
            engines = config.get("engines", {})
            selected_queries[phase] = query
            start = time.time()
            if engines.get("openalex") is True:
                limits = config.get("deterministic_filters", {})
                records = retrieve_openalex_crossref(
                    session,
                    query,
                    label=f"phase_{index}_retrieval",
                    endpoint=openalex_endpoint,
                    crossref_endpoint=crossref_endpoint,
                    year_min=limits.get("min_year"),
                    year_max=limits.get("max_year"),
                )
                selected_providers[phase] = "openalex-crossref"
            elif engines.get("crossref") is True:
                records = retrieve_crossref(
                    session,
                    query,
                    label=f"phase_{index}_retrieval",
                    endpoint=crossref_endpoint,
                )
                selected_providers[phase] = "crossref"
            else:
                raise LiteratureBlocked("bounded unpaid acceptance requires a configured OpenAlex or Crossref engine")
            papers = runner._deduplicate_papers([_domain_paper(record) for record in records])
            filtered = runner.apply_deterministic_filters(papers, config.get("deterministic_filters", {}))
            if not filtered:
                raise LiteratureBlocked(
                    f"selected phase {phase} retained no records after its real deterministic filters"
                )
            runner._record_phase_papers(filtered, phase)
            runner.phase_metadata[phase] = PhaseMetadata(
                phase,
                config.get("name", phase),
                config.get("description", ""),
                start,
                end_time=time.time(),
                queries_executed=[query],
                papers_discovered=len(papers),
                papers_after_deterministic_filters=len(filtered),
                papers_after_llm_filters=len(filtered),
                papers_final=len(filtered),
                deterministic_filters_applied=config.get("deterministic_filters", {}),
                depends_on=config.get("depends_on", []),
                llm_filter_status="acceptance-classification-pending",
            )
            phase_sources[phase] = filtered[0].abstract
            retained_ids = {paper.canonical_id for paper in filtered}
            phase_candidates[phase] = [
                record for record in records if _domain_paper(record).canonical_id in retained_ids
            ]
            for record in phase_candidates[phase]:
                all_records.setdefault(record.id, record)
        _write_phase_outputs(session, runner, phases)
        keys = export_citations(session, list(all_records.values()))
        session.receipt["producer_results"]["retrieval"] = {
            "status": "passed",
            "selected_queries": selected_queries,
            "selected_provider": next(iter(set(selected_providers.values())))
            if len(set(selected_providers.values())) == 1
            else "configured-per-phase",
            "selected_providers": selected_providers,
            "paper_count": len(all_records),
            "bibtex_count": len(keys),
            "phase_count": len(phases),
            "scope": (
                "first configured query per phase; review-size/citation quality gates "
                "are not satisfied by this acceptance sample"
            ),
        }
        calibration = exact_json(session.freeze_project_input_bytes("data/llm_filter_calibration.json"))
        cases = calibration["cases"]
        if not isinstance(cases, list) or len(cases) != 4:
            raise LiteratureFailed("bounded screening requires the four declared calibration cases")
        predictions: dict[str, str] = {}
        labels = ["yes", "no"]
        for case in cases:
            source = case["abstract"]
            annotation = validate_annotation(
                generator.generate(
                    annotation_prompt(
                        source,
                        "Does this abstract report an observational measurement or evaluate an observational method "
                        "on a named target? Return label yes or no plus an exact source_quote.",
                    ),
                    annotation_schema(source, labels=labels),
                ),
                source,
                labels=labels,
            )
            predictions[case["id"]] = annotation["label"]
        result = score_llm_calibration(cases, predictions)
        write_json(session.directory / "screening_calibration.json", result)
        if result["status"] != "pass" or result["accuracy"] < 0.75:
            raise LiteratureFailed("actual local screening calibration failed its declared 0.75 accuracy threshold")
        session.receipt["producer_results"]["screening"] = {
            **result,
            "status": "passed",
            "scope": "four declared synthetic filter-behavior regression controls; not scientific validation",
        }
        classifications: dict[str, Any] = {}
        categories = ["observational", "theoretical", "review", "other"]
        for phase, source in phase_sources.items():
            if len(source.strip()) < 20:
                raise LiteratureBlocked(f"selected phase {phase} has no substantial abstract for local classification")
            classifications[phase] = validate_annotation(
                generator.generate(
                    annotation_prompt(
                        source[:6000],
                        "Classify study type: observational uses real telescope/instrument measurements; "
                        "theoretical uses models/simulations; review summarizes papers; other otherwise. "
                        "Return label and exact source_quote.",
                    ),
                    annotation_schema(source[:6000], labels=categories),
                ),
                source[:6000],
                labels=categories,
            )
        write_json(session.directory / "phase_classification.json", classifications)
        session.receipt["producer_results"]["local-classification"] = {
            "status": "passed",
            "model_sha256": generator.model_sha256,
            "calls": generator.calls,
            "classified_phase_count": len(classifications),
            "scope": "one retrieved abstract per selected phase",
        }
        candidates = _fulltext_candidates(phase_candidates)
        selection_path = session.directory / "fulltext_selection.json"
        write_json(
            selection_path,
            {
                "policy": "phase-filtered round-robin in configured phase/provider order, before access attempts",
                "max_candidates": 3,
                "candidate_ids": [record.id for record in candidates],
                "phase_eligible_ids": {
                    phase: [record.id for record in rows] for phase, rows in phase_candidates.items()
                },
            },
        )
        session.consume(selection_path)
        _, _, fulltext_receipt = licensed_fulltext(session, candidates, europepmc_endpoint=europepmc_endpoint)
        session.receipt["producer_results"]["licensed-fulltext"] = fulltext_receipt
        return session.finalize("passed")
    except LiteratureBlocked as exc:
        return session.finalize("blocked", issue=str(exc))
    except (
        LiteratureFailed,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RuntimeError,
    ) as exc:
        return session.finalize("failed", issue=f"{type(exc).__name__}: {exc}")


def main(project_root: Path, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("core", "live"), default="core")
    parser.add_argument("--model")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-results", type=int, default=3)
    args = parser.parse_args(argv)
    if args.mode == "core":
        print(json.dumps(read_core_reference(project_root, project_root / "output/data/corpus.jsonl")))
        return 0
    if args.model is None or args.output_dir is None:
        parser.error("live mode requires --model and a fresh --output-dir")
    path = run_live(
        project_root,
        args.output_dir,
        LiveSettings(args.model, args.endpoint, max_results=args.max_results),
    )
    print(path)
    return {"passed": 0, "blocked": 75, "failed": 1}[json.loads(path.read_text())["status"]]

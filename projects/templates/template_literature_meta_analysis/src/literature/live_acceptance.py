"""Explicit unpaid retrieval/full-text/model/KG acceptance with current source custody."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

import template_literature_meta_analysis.knowledge_graph.hypothesis as hypotheses
from template_literature_meta_analysis.analysis.pipeline_runner import run_meta_analysis_pipeline
from template_literature_meta_analysis.config_loader import load_project_config
from template_literature_meta_analysis.config_validation import require_valid_config
from template_literature_meta_analysis.knowledge_graph.graph_builder import KnowledgeGraph
from template_literature_meta_analysis.knowledge_graph.nanopublication import (
    Assertion,
    append_nanopubs,
    create_nanopub,
    deserialize_nanopubs,
)
from template_literature_meta_analysis.literature.corpus import Corpus
from template_literature_meta_analysis.literature.live_workflow import parse_workflow, workflow_schema
from template_literature_meta_analysis.literature.models import Author, Paper
from template_literature_meta_analysis.reproducibility.scoring import composite_score

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
    licensed_fulltext,
    retrieve_crossref,
)
from infrastructure.search.literature.live_transport import LocalGenerator

CAPABILITIES = ["retrieval", "fulltext", "extraction", "local-model", "kg"]


def domain_paper(record: Any) -> Paper:
    """Preserve source citation/reference metadata when entering the project domain."""
    citations = record.raw.get("is-referenced-by-count", 0)
    if type(citations) is not int or citations < 0:
        raise LiteratureFailed("retrieved citation count is invalid")
    return Paper(
        title=record.title,
        abstract=record.abstract or "",
        year=record.year,
        doi=record.doi,
        authors=[Author(name) for name in record.authors],
        venue=record.venue,
        citation_count=citations,
        references=[
            "doi:" + row["DOI"].lower()
            for row in record.raw.get("reference", [])
            if isinstance(row, dict) and isinstance(row.get("DOI"), str)
        ],
    )


def independent_analysis(
    session: LiveSession, papers: list[Paper], *, config_source_bytes: bytes | None = None
) -> dict[str, Any]:
    """Run the real analysis producer and independently reconcile its corpus counts."""
    corpus_path = session.directory / "corpus.jsonl"
    Corpus(papers=papers).save(corpus_path)
    session.consume(corpus_path)
    directory = session.directory / "analysis"
    args = argparse.Namespace(
        output_dir=str(directory), corpus=str(corpus_path), min_year=1800, max_features=100, n_topics=1
    )
    run_meta_analysis_pipeline(args, project_root=session.directory / "inputs", config_source_bytes=config_source_bytes)
    raw = session.consume(directory / "data/descriptive_stats.json")
    report = exact_json(raw)["descriptive_stats"]
    expected_years = {str(year): count for year, count in Counter(paper.year for paper in papers).items()}
    actual_years = {str(year): count for year, count in report["counts_by_year"].items()}
    if report["total"] != len(papers) or actual_years != expected_years:
        raise LiteratureFailed("independent corpus/year accounting disagrees with analysis producer")
    if report["citation_count_total"] != sum(paper.citation_count for paper in papers):
        raise LiteratureFailed("independent citation accounting disagrees with analysis producer")
    for path in sorted((directory / "data").glob("*.json")):
        value = exact_json(session.consume(path))
        if isinstance(value, dict) and "error" in value:
            raise LiteratureFailed(f"required analysis producer failed: {path.name}")
    return {
        "status": "passed",
        "paper_count": len(papers),
        "independent_counts_match": True,
        "scope": "retrieved acceptance sample bibliometrics/NLP, not clinical efficacy meta-analysis",
    }


def run_live(
    project_root: Path,
    directory: Path,
    settings: LiveSettings,
    *,
    crossref_endpoint: str = CROSSREF_URL,
    europepmc_endpoint: str = EUROPEPMC_URL,
) -> Path:
    session = LiveSession(
        project_root, directory, settings, CAPABILITIES, active_source_root=Path(__file__).absolute().parents[1]
    )
    generator = LocalGenerator(session, max_calls=2)
    try:
        config_bytes = session.freeze_project_input_bytes("manuscript/config.yaml")
        config_path = session.directory / "inputs/manuscript/config.yaml"
        require_valid_config(config_path, categories=("search_config", "hypothesis_config"), source_bytes=config_bytes)
        config = load_project_config(config_path, source_bytes=config_bytes)
        records = retrieve_crossref(session, config["search"]["query"], endpoint=crossref_endpoint)
        keys = export_citations(session, records)
        papers = [domain_paper(record) for record in records]
        analysis = independent_analysis(session, papers, config_source_bytes=config_bytes)
        session.receipt["producer_results"]["retrieval"] = {
            "status": "passed",
            "paper_count": len(records),
            "bibtex_count": len(keys),
            "analysis": analysis,
        }
        selected, text, fulltext_receipt = licensed_fulltext(session, records, europepmc_endpoint=europepmc_endpoint)
        session.receipt["producer_results"]["fulltext"] = fulltext_receipt
        selected_domain = domain_paper(selected)
        source = text[:6000]
        raw = generator.generate(
            annotation_prompt(
                source,
                "Extract one to three concrete workflow nodes described by this excerpt. Return a nodes object; "
                "assign IDs n0, n1, n2, source/method/experiment/sink types, 1-4 information sufficiency ratings "
                "and upstream dependencies. Copy every source_quote exactly. Partial workflows are acceptable.",
            ),
            workflow_schema(),
        )
        workflow = parse_workflow(raw, source, selected_domain.canonical_id)
        write_json(session.directory / "workflow.json", workflow.to_dict())
        score = composite_score(workflow)
        if not math.isclose(
            score.composite_score**2, score.content_score * score.structural_score, rel_tol=1e-12, abs_tol=1e-12
        ):
            raise LiteratureFailed("independent geometric-mean score identity failed")
        write_json(session.directory / "workflow_score.json", asdict(score))
        session.receipt["producer_results"]["extraction"] = {
            "status": "passed",
            "paper_id": selected_domain.canonical_id,
            "n_nodes": len(workflow.nodes),
            "n_dangling_references": workflow.dangling_reference_count,
            "scope": "one explicitly partial full-text workflow; ratings remain uncalibrated model annotations",
        }
        hypotheses.configure_hypotheses(config_path, source_bytes=config_bytes)
        hypothesis = hypotheses.HYPOTHESES[0]
        labels = ["supports", "contradicts", "neutral"]
        annotation = validate_annotation(
            generator.generate(
                annotation_prompt(
                    source,
                    "Classify the source's relation to hypothesis: "
                    + hypothesis.description
                    + ". Return label supports, contradicts, or neutral plus an exact source_quote. "
                    "Use neutral when the excerpt is insufficient.",
                ),
                annotation_schema(labels=labels),
            ),
            source,
            labels=labels,
        )
        assertion = Assertion(
            "live_" + selected_domain.canonical_id,
            selected_domain.canonical_id,
            annotation["source_quote"],
            annotation["label"],
            hypothesis.hypothesis_id,
            confidence=1.0,
            citation_count=selected_domain.citation_count,
        )
        graph = KnowledgeGraph(use_rdflib=True)
        graph.add_paper(selected_domain)
        graph.add_assertion(assertion)
        nanopub_path = session.directory / "nanopublications.jsonl"
        append_nanopubs(
            [create_nanopub(assertion, attribution="bounded-local-model; unit weighting, not calibrated confidence")],
            nanopub_path,
        )
        persisted = deserialize_nanopubs(nanopub_path)
        if (
            len(persisted) != 1
            or persisted[0].assertion != assertion
            or graph.get_assertions_for_paper(assertion.paper_id) != [assertion.assertion_id]
        ):
            raise LiteratureFailed("knowledge graph/nanopublication roundtrip lost source assertion identity")
        session.consume(nanopub_path)
        write_json(
            session.directory / "kg_annotation.json",
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                **annotation,
                "score": hypotheses.score_hypothesis([assertion], hypothesis.hypothesis_id),
                "claim_boundary": "source quote custody and graph execution; relation/entailment not independently validated",
            },
        )
        session.receipt["producer_results"]["kg"] = {
            "status": "passed",
            "assertion_count": 1,
            "triples": graph.num_triples,
            "scope": "one selected configured hypothesis; unit weight is not calibrated confidence",
        }
        session.receipt["producer_results"]["local-model"] = {
            "status": "passed",
            "model_sha256": generator.model_sha256,
            "calls": generator.calls,
        }
        return session.finalize("passed")
    except LiteratureBlocked as exc:
        return session.finalize("blocked", issue=str(exc))
    except (LiteratureFailed, OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
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
        print(json.dumps(read_core_reference(project_root, project_root / "data/fixtures/modafinil_corpus.jsonl")))
        return 0
    if args.model is None or args.output_dir is None:
        parser.error("live mode requires --model and a fresh --output-dir")
    path = run_live(
        project_root, args.output_dir, LiveSettings(args.model, args.endpoint, max_results=args.max_results)
    )
    print(path)
    return {"passed": 0, "blocked": 75, "failed": 1}[json.loads(path.read_text())["status"]]

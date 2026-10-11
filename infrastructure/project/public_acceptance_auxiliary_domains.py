"""Concrete deterministic domain computations and independent raw-value admission."""

from __future__ import annotations

import ast
import io
import json
import math
import tempfile
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_auxiliary_native import project_module
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

DOMAIN_SCHEMA = "template-auxiliary-source-domain-v1"
SCOPES = frozenset(
    "templates/" + name
    for name in (
        "template_textbook",
        "template_code_project",
        "template_gold_refinement",
        "template_registered_report",
        "template_template",
        "template_sia",
        "template_experiment_tree",
        "template_madlib",
        "template_prose_project",
        "template_autoresearch_project",
        "template_search_project",
        "template_literature_meta_analysis",
        "template_advanced_literature_review",
    )
)


def _json(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Path):
        return value.name
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"unsupported actual domain value: {type(value).__name__}")


def _constants(path: Path, names: tuple[str, ...]) -> dict[str, Any]:
    """Read literal inputs from the actual declared public producer, without execution."""
    result = {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    result[target.id] = ast.literal_eval(node.value)
    if set(result) != set(names):
        raise ValueError("source producer's required domain inputs changed")
    return result


def execute_domain(root: Path, scope: str, directory: Path, budget: int) -> dict[str, Any] | None:
    """Run the existing public scientific API and retain source-consumed measurements."""
    if scope not in SCOPES:
        return None
    project = root / "projects" / scope
    reader = SnapshotReader(root)
    bindings: list[dict[str, str]] = []

    def input_file(relative: str) -> Path:
        snapshot = reader.read(f"projects/{scope}/{relative}")
        bindings.append({"path": snapshot.relative, "sha256": snapshot.sha256})
        return snapshot.path

    observed: dict[str, Any]
    if scope.endswith("template_textbook"):
        analysis = project_module(root, scope, "textbook.analysis")
        dataset = input_file("manuscript/assets/data/sample_dataset.csv")
        observed = analysis.build_worked_model_summary(
            dataset, source_label="manuscript/assets/data/sample_dataset.csv"
        )
    elif scope.endswith("template_code_project"):
        config_module = project_module(root, scope, "template_code_project.core.experiment_config")
        experiment = project_module(root, scope, "template_code_project.analysis.experiments")
        optimizer = project_module(root, scope, "template_code_project.core.optimizer")
        input_file("manuscript/config.yaml")
        config = config_module.load_experiment_config(project)
        results = experiment.run_convergence_experiment(config=config)
        optimum, objective = optimizer.quadratic_optimum(config.A_array(), config.b_array())
        observed = {
            "matrix": config.A_array(),
            "linear": config.b_array(),
            "optimum": optimum,
            "optimal_objective": objective,
            "runs": {str(step): asdict(value) for step, value in results.items()},
        }
    elif scope.endswith("template_gold_refinement"):
        refinery = project_module(root, scope, "template_gold_refinement.refinery")
        boundary = project_module(root, scope, "template_gold_refinement.analogy_boundary")
        adapter = project_module(root, scope, "template_gold_refinement.domain_adapter")
        input_file("domain_profile.yaml")
        result = refinery.run_refinery()
        observed = {
            "refinery": asdict(result),
            "purities": result.purity_sequence,
            "boundary": boundary.validate_analogy_boundary(adapter.load_domain_profile(project)),
        }
    elif scope.endswith("template_registered_report"):
        protocol = project_module(root, scope, "registered_report.protocol")
        registration = json.loads(input_file("data/example_registration.json").read_text())
        source = input_file("scripts/generate_review_artifacts.py")
        constants = _constants(source, ("DEFAULT_EXECUTED", "DEFAULT_DEVIATIONS"))
        frozen = protocol.freeze_registration(registration)
        findings = protocol.validate_registration(frozen)
        if any(finding.severity == "error" for finding in findings):
            raise ValueError("actual frozen registration completeness/hash validation failed")
        observed = {
            "frozen": frozen,
            "findings": findings,
            "packet": protocol.build_review_packet(
                frozen,
                constants["DEFAULT_EXECUTED"],
                constants["DEFAULT_DEVIATIONS"],
                frozen.get("sensitivity_analyses", []),
            ),
        }
    elif scope.endswith("template_template"):
        metrics = project_module(root, scope, "template_template.metrics.metrics")
        contract = project_module(root, scope, "template_template.core.contracts")
        measured = metrics.build_manuscript_metrics_dict(root)
        contract.validate_metrics_payload(measured)
        receipt = contract.build_metrics_receipt(measured)
        contract.validate_metrics_receipt(measured, receipt)
        observed = {"metrics": measured, "receipt": receipt}
    elif scope.endswith("template_sia"):
        import csv
        import subprocess
        import sys
        from infrastructure.project.installed_acceptance_artifacts import write_binary

        domain = project_module(root, scope, "template_sia.loop.proposal_domain")
        source = input_file("tasks/mini_classify/reference/reference_target_agent.py")
        dataset = input_file("tasks/mini_classify/data/public/train.csv")
        rows = domain.read_dataset(dataset)
        original = source.read_text()
        mutated = domain.mutate_threshold(original, 0.55)
        if original == mutated or domain.threshold_assignment(mutated).value != 0.55:
            raise ValueError("actual numeric threshold mutation failed")
        with tempfile.TemporaryDirectory(prefix="template-sia-domain-") as temporary:
            temporary_root = Path(temporary)
            data = temporary_root / "data"
            work = temporary_root / "work"
            data.mkdir()
            with (data / "train.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["id", "feature_0"])
                writer.writeheader()
                writer.writerows({key: row[key] for key in ("id", "feature_0")} for row in rows)
            process = subprocess.run(
                [sys.executable, "-I", str(source), "--dataset_dir", str(data), "--working_dir", str(work)],
                capture_output=True,
                text=True,
                timeout=min(budget, 30),
                check=False,
            )
            if process.returncode != 0:
                raise ValueError("actual fixed public classifier process failed: " + process.stderr)
            predictions = work / "predictions.csv"
            observed = {
                "score": domain.score_predictions(rows, predictions),
                "stdout": process.stdout,
                "original_exit_code": process.returncode,
                "prediction_artifact": write_binary(
                    root, directory / "domain-predictions.csv", predictions.read_bytes()
                ),
                "mutated_threshold": domain.threshold_assignment(mutated).value,
                "mutated_source": mutated,
                "original_source": original,
            }
    else:
        observed = remaining_domain(root, scope, directory, budget, reader, bindings)
    if not reader.unchanged():
        raise ValueError("actual domain inputs changed during execution")
    result = {
        "schema_version": DOMAIN_SCHEMA,
        "status": "passed",
        "scope": scope,
        "execution_mode": "deterministic-source-domain",
        "paid": False,
        "input_artifacts": bindings,
        "measurements": json.loads(json.dumps(observed, default=_json, allow_nan=False)),
    }
    validate_domain(result, SnapshotReader(root))
    return result


def validate_domain(native: dict[str, Any], reader: SnapshotReader) -> None:
    """Independently reconstruct numerical/schema obligations from exact retained bytes."""
    scope = native.get("scope")
    if (
        native.get("schema_version") != DOMAIN_SCHEMA
        or scope not in SCOPES
        or native.get("status") != "passed"
        or native.get("paid") is not False
        or native.get("execution_mode") != "deterministic-source-domain"
    ):
        raise ValueError("actual source domain omitted its exact scope/schema/execution boundary")
    inputs = {}
    for binding in native.get("input_artifacts", []):
        snapshot = reader.read(binding["path"])
        if snapshot.sha256 != binding["sha256"] or not snapshot.relative.startswith(f"projects/{scope}/"):
            raise ValueError("actual consumed domain input differs or belongs to another scope")
        inputs[snapshot.relative.removeprefix(f"projects/{scope}/")] = snapshot.content
    measured = native.get("measurements", {})
    if scope.endswith("template_textbook"):
        growth, decay = measured["logistic_growth"], measured["exponential_decay"]
        parameters = growth["parameters"]
        expected = [
            parameters["carrying_capacity"]
            / (1 + (parameters["carrying_capacity"] / parameters["initial"] - 1) * math.exp(-parameters["r"] * time))
            for time in growth["t"]
        ]
        if (
            len(expected) != len(growth["N"])
            or any(
                not math.isclose(actual, reference, abs_tol=1e-10)
                for actual, reference in zip(growth["N"], expected, strict=True)
            )
            or any(
                not math.isclose(
                    actual,
                    decay["parameters"]["initial"] * math.exp(-decay["parameters"]["rate"] * time),
                    abs_tol=1e-10,
                )
                for time, actual in zip(decay["t"], decay["y"], strict=True)
            )
        ):
            raise ValueError("actual textbook time-series differ from independent analytic equations")
        import csv
        import statistics

        rows = list(csv.DictReader(io.StringIO(inputs["manuscript/assets/data/sample_dataset.csv"].decode())))
        groups = {row["condition"] for row in rows}
        means = {
            group: statistics.mean(float(row["measurement"]) for row in rows if row["condition"] == group)
            for group in groups
        }
        if measured["case_study"]["condition_means"] != means:
            raise ValueError("actual textbook condition means differ from retained source observations")
    elif scope.endswith("template_code_project"):
        import numpy as np

        matrix, linear, optimum = (np.asarray(measured[key], dtype=float) for key in ("matrix", "linear", "optimum"))
        reference = np.linalg.solve(matrix, linear)
        if (
            not np.allclose(optimum, reference, rtol=0, atol=1e-10)
            or not math.isclose(
                measured["optimal_objective"], float(0.5 * optimum @ matrix @ optimum - linear @ optimum), abs_tol=1e-10
            )
            or not measured.get("runs")
        ):
            raise ValueError("actual quadratic optimizer differs from independent stationary-point solution")
        for run in measured["runs"].values():
            solution = np.asarray(run["solution"], dtype=float)
            objective = float(0.5 * solution @ matrix @ solution - linear @ solution)
            gradient = matrix @ solution - linear
            scale = float(np.max(np.abs(gradient)))
            norm = scale * float(np.linalg.norm(gradient / scale)) if scale else 0.0
            if (
                solution.shape != optimum.shape
                or not np.isfinite(solution).all()
                or not math.isclose(objective, run["objective_value"], rel_tol=1e-12, abs_tol=1e-10)
                or not math.isclose(norm, run["gradient_norm"], rel_tol=1e-12, abs_tol=1e-10)
                or len(run["objective_history"]) != run["iterations"] + 1
                or run["objective_history"][-1] != run["objective_value"]
            ):
                raise ValueError("actual optimizer run differs from independent objective/gradient/trace")
    elif scope.endswith("template_gold_refinement"):
        values = measured["purities"]
        refinery = measured["refinery"]
        if (
            not values
            or any(not 0 <= value <= 1 for value in values)
            or any(first > second for first, second in zip(values, values[1:]))
            or refinery["final_purity"] != values[-1]
            or not math.isclose(refinery["total_purity_gain"], values[-1] - values[0], abs_tol=1e-15)
            or measured["boundary"].get("status") != "pass"
        ):
            raise ValueError("actual refinery gain/monotonicity or source analogy boundary failed")
    elif scope.endswith("template_registered_report"):
        import hashlib

        frozen = dict(measured["frozen"])
        digest = frozen.pop("registration_hash")
        expected_digest = hashlib.sha256(json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if (
            digest != expected_digest
            or measured["packet"].get("registration_hash") != digest
            or any(finding.get("severity") == "error" for finding in measured["findings"])
        ):
            raise ValueError("actual registration freeze hash or analysis packet binding differs")
    elif scope.endswith("template_template"):
        module = project_module(reader.root, scope, "template_template.core.contracts")
        module.validate_metrics_receipt(measured["metrics"], measured["receipt"])
        from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

        if measured["receipt"]["public_exemplar_count"] != len(PUBLIC_PROJECT_NAMES):
            raise ValueError("actual repository metrics omitted canonical public exemplars")
    elif scope.endswith("template_sia"):
        import csv

        binding = measured["prediction_artifact"]
        predictions = reader.read(binding["path"])
        rows = list(csv.DictReader(io.StringIO(inputs["tasks/mini_classify/data/public/train.csv"].decode())))
        actual = list(csv.DictReader(io.StringIO(predictions.content.decode())))
        predicted = {row["id"]: row["label"] for row in actual}
        if (
            predictions.sha256 != binding["sha256"]
            or len(predicted) != len(rows)
            or len(actual) != len(rows)
            or any(predicted.get(row["id"]) != row["label"] for row in rows)
            or measured["score"] != 1.0
            or measured["original_exit_code"] != 0
            or measured["mutated_threshold"] != 0.55
            or measured["original_source"] == measured["mutated_source"]
        ):
            raise ValueError("actual numeric classifier/mutation differs from retained independent labels")
    else:
        validate_remaining(scope, measured, inputs, reader)


def _normal(value: Any) -> Any:
    return json.loads(json.dumps(value, default=_json, allow_nan=False))


def _invariant_valid(record: dict[str, Any]) -> bool:
    actual, expected, tolerance = record["actual"], record.get("expected"), record.get("tol", 0)
    kind = record["kind"]
    if kind == "equal":
        return bool(abs(actual - expected) <= tolerance)
    if kind == "le":
        return bool(actual <= expected + tolerance)
    if kind == "ge":
        return bool(actual >= expected - tolerance)
    if kind == "finite":
        return math.isfinite(actual)
    if kind == "nonneg":
        return bool(actual >= -tolerance)
    raise ValueError(f"unsupported source search witness relation: {kind}")


def remaining_domain(
    root: Path, scope: str, directory: Path, budget: int, reader: SnapshotReader, bindings: list[dict[str, str]]
) -> dict[str, Any]:
    project = root / "projects" / scope

    def consumed(relative: str) -> Path:
        snapshot = reader.read(f"projects/{scope}/{relative}")
        bindings.append({"path": snapshot.relative, "sha256": snapshot.sha256})
        return snapshot.path

    if scope.endswith("template_experiment_tree"):
        import runpy

        script = consumed("scripts/init_tree.py")
        project_module(root, scope, "template_experiment_tree")
        tree = runpy.run_path(str(script))["build_seed_tree"]()
        tree.validate()
        store = project_module(root, scope, "template_experiment_tree.store")
        report = project_module(root, scope, "template_experiment_tree.report")
        return {"tree": store.tree_to_payload(tree), "summary": report.summarize(tree)}
    if scope.endswith("template_madlib"):
        consumed("manuscript/config.yaml")
        module = project_module(root, scope, "template_madlib.run")
        run = module.build_run(project)
        return {
            "plan": asdict(run.plan),
            "sections": run.sections,
            "field_inventory": run.field_inventory,
            "field_counts": run.field_counts,
        }
    if scope.endswith("template_prose_project"):
        from infrastructure.prose import analyze_manuscript

        config_module = project_module(root, scope, "template_prose_project.pipeline.config")
        pipeline = project_module(root, scope, "template_prose_project.pipeline")
        config = config_module.load_project_config(consumed("manuscript/config.yaml"))
        consumed(config.bibliography.references_path)
        for path in sorted((project / config.manuscript_dir).rglob("*.md")):
            consumed(path.relative_to(project).as_posix())
        report = analyze_manuscript(
            project / config.manuscript_dir, long_sentence_threshold=config.prose.long_sentence_threshold
        )
        return dict(
            pipeline.run_prose_pipeline(
                config, project_root=project, manuscript_report=report, write_outputs=False
            ).to_dict()
        )
    if scope.endswith("template_search_project"):
        papers = json.loads(consumed("data/corpus.json").read_text())["papers"]
        module = project_module(root, scope, "template_search_project.search.search_invariants")
        return {"papers": papers, "invariants": [asdict(item) for item in module.all_invariants(papers)]}
    if scope.endswith("template_literature_meta_analysis"):
        corpus_module = project_module(root, scope, "literature.corpus")
        corpus = corpus_module.Corpus.load(consumed("data/fixtures/modafinil_corpus.jsonl"))
        stats = project_module(root, scope, "analysis.descriptive_stats")
        temporal = project_module(root, scope, "analysis.temporal_analysis")
        return {
            "evidence_mode": "source-fixture-bibliometrics",
            "statistics": stats.descriptive_stats(corpus.papers),
            "citations": stats.citation_distribution(corpus.papers),
            "temporal": temporal.compute_temporal_metrics(corpus.papers),
        }
    if scope.endswith("template_advanced_literature_review"):
        fixture = project_module(root, scope, "literature.fixture_corpus")
        search = project_module(root, scope, "multi_phase.search")
        config_path = consumed("manuscript/config.yaml")
        consumed("src/literature/fixture_corpus.py")
        with tempfile.TemporaryDirectory(prefix="actual-phase-replay-") as temporary:
            output = Path(temporary)
            corpus = fixture.build_synthetic_corpus()
            corpus.save(output / "source_fixture.jsonl")
            runner = search.MultiPhaseSearchRunner(config_path, project_root=project, output_dir=output / "phases")
            runner.replay_fixture(output / "source_fixture.jsonl")
            return {
                "evidence_mode": "source-fixture-phase-replay",
                "model_calls": 0,
                "source_records": [paper.to_dict() for paper in corpus.papers],
                "artifacts": {
                    path.name: json.loads(path.read_text()) for path in sorted((output / "phases").glob("*.json"))
                },
                "phase_corpora": {
                    path.name: [json.loads(line) for line in path.read_text().splitlines()]
                    for path in sorted((output / "phases").glob("*.jsonl"))
                },
            }
    if scope.endswith("template_autoresearch_project"):
        from infrastructure.autoresearch import BudgetPolicy

        task = project_module(root, scope, "template_autoresearch_project.ml.task")
        consumed("mnist_task.yaml")
        config = task.load_mnist_task_config(project)
        consumed(str(config.dataset_path))
        consumed(str(config.provenance_path))
        result = task.run_bounded_ml_task(
            project,
            BudgetPolicy(max_iterations=config.max_candidates, max_wall_clock_minutes=max(1, math.ceil(budget / 60))),
        )
        return {
            "result": asdict(result),
            "transformer_evaluated": result.transformer_evaluated,
            "best_accuracy": result.best_accuracy,
            "accuracy_delta": result.accuracy_delta,
        }
    raise ValueError(f"undeclared deterministic domain scope: {scope}")


def validate_remaining(scope: str, measured: dict[str, Any], inputs: dict[str, bytes], reader: SnapshotReader) -> None:
    from collections import Counter

    root = reader.root
    project = root / "projects" / scope
    if scope.endswith("template_autoresearch_project"):
        import numpy as np

        with np.load(io.BytesIO(inputs["data/mnist_small.npz"]), allow_pickle=False) as dataset:
            labels = np.asarray(dataset["y_test"], dtype=int)
        result = measured["result"]
        candidates = result["candidates"]
        accepted = [candidate for candidate in candidates if candidate["identifier"] == result["accepted_candidate_id"]]
        if (
            len(accepted) != 1
            or accepted[0]["status"] != "accepted"
            or result["llm_calls_used"] != 0
            or result["cost_usd_used"] != 0
            or result["budget_exhausted"] != (len(candidates) > result["evaluated_candidate_count"])
            or result["evaluated_candidate_count"] != result["task_config"]["max_candidates"]
            or measured["transformer_evaluated"] is not True
        ):
            raise ValueError("actual bounded neural search omitted source candidates or unpaid budget")
        if result["candidate_count"] != len(candidates):
            raise ValueError("actual candidate census differs")
        for candidate in [result["baseline"], *candidates]:
            if candidate.get("status") == "deferred":
                if (
                    candidate["test_predictions"]
                    or candidate["test_accuracy"] is not None
                    or candidate["training_history"]
                ):
                    raise ValueError("deferred candidate cannot claim evaluated measurements")
                continue
            prediction = np.asarray(candidate["test_predictions"], dtype=int)
            if prediction.shape != labels.shape or np.any((prediction < 0) | (prediction > 9)):
                raise ValueError("actual MNIST predictions differ from dataset dimensions")
            confusion = np.zeros((10, 10), dtype=int)
            np.add.at(confusion, (labels, prediction), 1)
            if (
                not np.array_equal(confusion, candidate["confusion_matrix"])
                or round(float(np.mean(prediction == labels)), 6) != candidate["test_accuracy"]
            ):
                raise ValueError("actual MNIST confusion/accuracy differs from independent retained labels")
            if "test_probabilities" in candidate:
                probabilities = np.asarray(candidate["test_probabilities"], dtype=float)
                if (
                    probabilities.shape != (len(labels), 10)
                    or not np.isfinite(probabilities).all()
                    or np.any(probabilities < 0)
                    or np.any(probabilities > 1)
                    or not np.allclose(probabilities.sum(axis=1), 1, atol=1e-5)
                    or not np.array_equal(np.argmax(probabilities, axis=1), prediction)
                    or len(candidate["training_history"]) != candidate["epochs"]
                ):
                    raise ValueError("actual neural probability/training trace is incomplete")
        if measured["best_accuracy"] != accepted[0]["test_accuracy"] or not math.isclose(
            measured["accuracy_delta"], accepted[0]["test_accuracy"] - result["baseline"]["test_accuracy"]
        ):
            raise ValueError("actual neural selection improvement differs from measured baseline")
        return
    if scope.endswith("template_search_project"):
        papers = json.loads(inputs["data/corpus.json"])["papers"]
        module = project_module(root, scope, "template_search_project.search.search_invariants")
        expected = _normal([asdict(item) for item in module.all_invariants(papers)])
        if (
            measured["papers"] != papers
            or measured["invariants"] != expected
            or not all(map(_invariant_valid, expected))
        ):
            raise ValueError("actual search metadata/coverage witnesses fail independent relations")
        return
    if scope.endswith("template_experiment_tree"):
        import runpy

        store = project_module(root, scope, "template_experiment_tree.store")
        report = project_module(root, scope, "template_experiment_tree.report")
        tree = store.tree_from_payload(measured["tree"])
        expected_tree = runpy.run_path(str(project / "scripts/init_tree.py"))["build_seed_tree"]()
        if measured["tree"] != store.tree_to_payload(expected_tree) or measured["summary"] != report.summarize(tree):
            raise ValueError("actual preregistered source tree/projection differs")
        return
    if scope.endswith("template_madlib"):
        run = project_module(root, scope, "template_madlib.run").build_run(project)
        expected = _normal(
            {
                "plan": asdict(run.plan),
                "sections": run.sections,
                "field_inventory": run.field_inventory,
                "field_counts": run.field_counts,
            }
        )
        if measured != expected or len(measured["plan"]["choices"]) == 0:
            raise ValueError("actual seeded token choices/field inventory differ from source config")
        return
    if scope.endswith("template_prose_project"):
        from infrastructure.prose import analyze_manuscript

        config = project_module(root, scope, "template_prose_project.pipeline.config").load_project_config(
            project / "manuscript/config.yaml"
        )
        report = analyze_manuscript(
            project / config.manuscript_dir, long_sentence_threshold=config.prose.long_sentence_threshold
        )
        expected = (
            project_module(root, scope, "template_prose_project.pipeline")
            .run_prose_pipeline(config, project_root=project, manuscript_report=report, write_outputs=False)
            .to_dict()
        )
        if measured != _normal(expected) or measured["all_passed"] is not True or measured["total_words"] <= 0:
            raise ValueError("actual manuscript measurements/configured prose checks fail source reanalysis")
        return
    if scope.endswith("template_literature_meta_analysis"):
        corpus_module = project_module(root, scope, "literature.corpus")
        corpus = corpus_module.Corpus.load(project / "data/fixtures/modafinil_corpus.jsonl")
        stats = project_module(root, scope, "analysis.descriptive_stats")
        temporal = project_module(root, scope, "analysis.temporal_analysis")
        expected = _normal(
            {
                "evidence_mode": "source-fixture-bibliometrics",
                "statistics": stats.descriptive_stats(corpus.papers),
                "citations": stats.citation_distribution(corpus.papers),
                "temporal": temporal.compute_temporal_metrics(corpus.papers),
            }
        )
        years = {str(key): value for key, value in Counter(p.year for p in corpus.papers if p.year is not None).items()}
        if (
            measured != expected
            or measured["statistics"]["counts_by_year"] != years
            or measured["statistics"]["total"] != len(corpus.papers)
        ):
            raise ValueError("actual fixture bibliometrics differ from independent record counts/source algorithms")
        return
    if scope.endswith("template_advanced_literature_review"):
        fixture = project_module(root, scope, "literature.fixture_corpus")
        source_records = _normal([paper.to_dict() for paper in fixture.build_synthetic_corpus().papers])
        metadata = measured["artifacts"]["phase_metadata.json"]
        combined = measured["phase_corpora"]["combined_corpus.jsonl"]
        if (
            measured["source_records"] != source_records
            or measured["evidence_mode"] != "source-fixture-phase-replay"
            or measured["model_calls"] != 0
            or metadata["replay_mode"] != "fixture"
            or metadata["total_unique_papers"] != len(combined)
        ):
            raise ValueError("actual replay must preserve source fixture boundary and unique corpus counts")
        for phase, values in metadata["phases"].items():
            rows = measured["phase_corpora"][f"{phase}_corpus.jsonl"]
            if values["papers_final"] != len(rows) or values["llm_filter_status"] != "skipped_fixture_replay":
                raise ValueError("actual replay phase count/source boundary differs")
        # Re-execute only deterministic fixture filters in a confined temporary output.
        with tempfile.TemporaryDirectory(prefix="phase-readback-") as temporary:
            scratch = Path(temporary)
            corpus = fixture.build_synthetic_corpus()
            corpus.save(scratch / "source_fixture.jsonl")
            runner = project_module(root, scope, "multi_phase.search").MultiPhaseSearchRunner(
                project / "manuscript/config.yaml", project_root=project, output_dir=scratch / "phases"
            )
            runner.replay_fixture(scratch / "source_fixture.jsonl")
            actual = {path.name: json.loads(path.read_text()) for path in sorted((scratch / "phases").glob("*.json"))}
            actual_corpora = {
                path.name: [json.loads(line) for line in path.read_text().splitlines()]
                for path in sorted((scratch / "phases").glob("*.jsonl"))
            }
            if measured["artifacts"] != actual or measured["phase_corpora"] != actual_corpora:
                raise ValueError("actual phase provenance/conflict/manifest/corpus readback differs")
        return
    raise ValueError(f"unimplemented deterministic scientific readback: {scope}")


def domain_negative(root: Path, scope: str) -> int | None:
    """Call the actual scientific/intent checker with an independently corrupt input."""
    if scope not in SCOPES:
        return None
    try:
        if scope.endswith("template_textbook"):
            import numpy as np

            models = project_module(root, scope, "textbook.models")
            models.linear_fit(np.array([1.0]), np.array([1.0, 2.0]))
        elif scope.endswith("template_code_project"):
            import numpy as np

            optimizer = project_module(root, scope, "template_code_project.core.optimizer")
            optimizer.quadratic_optimum(np.array([[0.0]]), np.zeros(1))
        elif scope.endswith("template_gold_refinement"):
            from dataclasses import replace

            module = project_module(root, scope, "template_gold_refinement.refinery")
            stages = list(module.CANONICAL_STAGES)
            stages[1] = replace(stages[1], input_purity=0.001)
            module.run_refinery(stages)
        elif scope.endswith("template_registered_report"):
            module = project_module(root, scope, "registered_report.protocol")
            raw = json.loads((root / "projects" / scope / "data/example_registration.json").read_text())
            frozen = module.freeze_registration(raw)
            frozen["registration_hash"] = "0" * 64
            module.freeze_registration(frozen)
        elif scope.endswith("template_template"):
            module = project_module(root, scope, "template_template.core.contracts")
            module.validate_metrics_payload({"metrics_schema_version": "foreign", "project_count": 0})
        elif scope.endswith("template_sia"):
            module = project_module(root, scope, "template_sia.loop.proposal_domain")
            module.validated_threshold(float("nan"))
        elif scope.endswith("template_experiment_tree"):
            project_module(root, scope, "template_experiment_tree.store").tree_from_payload(
                {"schema_version": "foreign", "nodes": []}
            )
        elif scope.endswith("template_madlib"):
            project_module(root, scope, "template_madlib.config")._load_lexicon({"noun": []})
        elif scope.endswith("template_prose_project"):
            project_module(root, scope, "template_prose_project.pipeline.config").ProjectConfig.from_dict(
                {"foreign_key": True}
            )
        elif scope.endswith("template_autoresearch_project"):
            project_module(root, scope, "template_autoresearch_project.ml.data")._probability_float(
                1.5, "invalid_probability"
            )
        elif scope.endswith("template_literature_meta_analysis"):
            project_module(root, scope, "analysis.descriptive_stats")._resolve_buckets([5, 1])
        elif scope.endswith("template_search_project"):
            module = project_module(root, scope, "template_search_project.search.search_invariants")
            records = module.uniqueness_invariants([{"id": "duplicate"}, {"id": "duplicate"}])
            return 23 if any(not _invariant_valid(asdict(record)) for record in records) else 0
        elif scope.endswith("template_advanced_literature_review"):
            module = project_module(root, scope, "multi_phase.contracts")
            return 23 if module.validate_phase_provenance([{"phase": "foreign"}], ["phase1"]) else 0
        else:
            return None
    except ValueError:
        return 23
    return 0

"""SIA generation loop state machine."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from infrastructure.core.exceptions import BuildError, ValidationError
from infrastructure.core.logging.utils import get_logger

from .context_ledger import append_generation, init_context
from .evaluation_runner import read_results_json, run_evaluation
from .execution_logs import load_agent_execution
from .models import EvaluationResult, GenerationArtifacts, GenerationState, RunConfig
from .task_layout import validate_task_dir

logger = get_logger(__name__)


def run_sia_loop(config: RunConfig) -> list[GenerationArtifacts]:
    """Execute the SIA Meta → Target → Feedback loop.

    Args:
        config: Run configuration including task_dir, output_dir, and live flag.

    Returns:
        Artifact records for each completed generation.
    """
    if config.max_generations < 1:
        # Fail closed: a zero/negative generation count would skip the loop body
        # entirely, returning an empty (vacuously "successful") run without ever
        # reading a fixture or executing an agent.
        raise ValidationError(f"max_generations must be >= 1, got {config.max_generations}")
    layout = validate_task_dir(config.task_dir)
    state = GenerationState(config=config, layout=layout)
    state.config.run_root().mkdir(parents=True, exist_ok=True)
    state.context_path = init_context(
        state.config.run_root() / "context.md",
        task_name=layout.task_dir.name,
    )

    meta_fn = _live_meta if config.live else _fixture_meta
    target_fn = _live_target if config.live else _fixture_target
    feedback_fn = _live_feedback if config.live else _fixture_feedback

    all_artifacts: list[GenerationArtifacts] = []
    for generation in range(1, config.max_generations + 1):
        state.current_generation = generation
        gen_dir = state.gen_dir()
        gen_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "SIA run_id=%s generation=%s/%s live=%s dir=%s",
            config.run_id,
            generation,
            config.max_generations,
            config.live,
            gen_dir,
        )

        if generation == 1:
            meta_fn(state)

        improvement_excerpt = ""
        if generation > 1:
            prior = all_artifacts[-1]
            _, improvement_excerpt = feedback_fn(state, prior)

        target_agent, execution_path = target_fn(state, gen_dir)
        evaluation = _maybe_evaluate(state, gen_dir)
        artifacts = GenerationArtifacts(
            generation=generation,
            gen_dir=gen_dir,
            target_agent=target_agent,
            agent_execution=execution_path,
            improvement=gen_dir / "improvement.md" if generation > 1 else None,
            results=gen_dir / "results.json" if evaluation else None,
            evaluation=evaluation,
        )
        append_generation(
            state.context_path,
            artifacts=artifacts,
            improvement_excerpt=improvement_excerpt,
        )
        all_artifacts.append(artifacts)

    _write_run_summary(state, all_artifacts)
    return all_artifacts


def _maybe_evaluate(state: GenerationState, gen_dir: Path) -> EvaluationResult | None:
    if state.layout.evaluate_script is None:
        return None
    results_path = gen_dir / "results.json"
    if results_path.is_file():
        return read_results_json(results_path)
    return run_evaluation(
        state.layout.evaluate_script,
        gen_dir=gen_dir,
        task_dir=state.layout.task_dir,
        timeout_sec=state.config.target_timeout_sec,
    )


def _fixture_root(state: GenerationState) -> Path:
    if state.config.fixtures_dir is None:
        raise ValidationError("fixtures_dir is required when live=False")
    root = state.config.fixtures_dir / f"gen_{state.current_generation}"
    if not root.is_dir():
        raise ValidationError(f"Missing fixture directory: {root}")
    return root


def _copy_fixture_file(fixture_root: Path, name: str, dest: Path) -> Path:
    source = fixture_root / name
    if not source.is_file():
        raise ValidationError(f"Fixture missing {name}: {source}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest


def _fixture_meta(state: GenerationState) -> Path:
    fixture_root = _fixture_root(state)
    gen_dir = state.gen_dir()
    return _copy_fixture_file(fixture_root, "target_agent.py", gen_dir / "target_agent.py")


def _fixture_target(state: GenerationState, gen_dir: Path) -> tuple[Path, Path]:
    fixture_root = _fixture_root(state)
    target = gen_dir / "target_agent.py"
    if not target.is_file():
        _copy_fixture_file(fixture_root, "target_agent.py", target)
    execution = _copy_fixture_file(fixture_root, "agent_execution.json", gen_dir / "agent_execution.json")
    if (fixture_root / "results.json").is_file():
        _copy_fixture_file(fixture_root, "results.json", gen_dir / "results.json")
    return target, execution


def _fixture_feedback(state: GenerationState, prior: GenerationArtifacts) -> tuple[Path, str]:
    fixture_root = _fixture_root(state)
    gen_dir = state.gen_dir()
    improvement = _copy_fixture_file(fixture_root, "improvement.md", gen_dir / "improvement.md")
    if (fixture_root / "target_agent.py").is_file():
        _copy_fixture_file(fixture_root, "target_agent.py", gen_dir / "target_agent.py")
    excerpt = improvement.read_text(encoding="utf-8")
    return improvement, excerpt


def _live_meta(state: GenerationState) -> Path:
    """Generate generation-1 target agent via reference scaffold (deterministic seed)."""
    gen_dir = state.gen_dir()
    reference = state.layout.reference_dir / "reference_target_agent.py"
    target = gen_dir / "target_agent.py"
    shutil.copy2(reference, target)
    return target


def _live_target(state: GenerationState, gen_dir: Path) -> tuple[Path, Path]:
    """Run target agent as bounded subprocess."""
    target = gen_dir / "target_agent.py"
    if not target.is_file():
        raise ValidationError(f"Missing target agent: {target}")

    working_dir = gen_dir / "working"
    working_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir = state.layout.public_dir
    cmd = [
        sys.executable,
        str(target.resolve()),
        "--dataset_dir",
        str(dataset_dir),
        "--working_dir",
        str(working_dir),
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(gen_dir),
        capture_output=True,
        text=True,
        timeout=state.config.target_timeout_sec,
        check=False,
    )
    execution_path = gen_dir / "agent_execution.json"
    payload = {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "dataset_dir": str(dataset_dir),
        "working_dir": str(working_dir),
    }
    execution_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if proc.returncode != 0:
        raise BuildError(f"Target agent failed (exit {proc.returncode}): {proc.stderr.strip()}")
    load_agent_execution(execution_path)
    return target, execution_path


def _live_feedback(state: GenerationState, prior: GenerationArtifacts) -> tuple[Path, str]:
    """Write improvement text from Ollama when configured, else a deterministic stub."""
    from .live_llm import generate_improvement_markdown

    gen_dir = state.gen_dir()
    prior_metric = prior.evaluation.metric_value if prior.evaluation else 0.0
    metric_name = prior.evaluation.metric_name if prior.evaluation else "accuracy"
    text = generate_improvement_markdown(
        generation=state.current_generation,
        metric_name=metric_name,
        metric_value=prior_metric,
        llm_model=state.config.llm_model,
    )
    if text is None:
        text = (
            f"# Improvement gen {state.current_generation}\n\n"
            f"Prior {metric_name}={prior_metric:.4f}. "
            "Tune threshold on feature_0 for better separation.\n"
        )
    improvement = gen_dir / "improvement.md"
    improvement.write_text(text, encoding="utf-8")
    reference = state.layout.reference_dir / "reference_target_agent.py"
    target = gen_dir / "target_agent.py"
    shutil.copy2(reference, target)
    return improvement, text


def _write_run_summary(state: GenerationState, artifacts: list[GenerationArtifacts]) -> Path:
    summary_path = state.config.run_root() / "run_summary.json"
    payload = {
        "run_id": state.config.run_id,
        "live": state.config.live,
        "max_generations": state.config.max_generations,
        "task_dir": str(state.layout.task_dir),
        "generations": [item.to_dict() for item in artifacts],
    }
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return summary_path


__all__ = ["run_sia_loop"]

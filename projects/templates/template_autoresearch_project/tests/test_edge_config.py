"""Edge-case tests for config and ML task YAML loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import (
    load_experiment_candidates,
    load_human_review,
    load_loop_config,
    load_seed_ideas,
)


def test_load_human_review_rejects_wrong_schema(tmp_path: Path) -> None:
    path = tmp_path / "human_review.yaml"

    path.write_text(
        "schema: wrong-schema-v0\npublication_approved: false\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="schema must be"):
        load_human_review(path)


def test_load_human_review_rejects_non_bool_approved(tmp_path: Path) -> None:
    path = tmp_path / "human_review.yaml"

    path.write_text(
        "schema: template-autoresearch-human-review-v1\npublication_approved: maybe\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be a boolean"):
        load_human_review(path)


def test_load_human_review_rejects_non_mapping_decisions(tmp_path: Path) -> None:
    path = tmp_path / "human_review.yaml"

    path.write_text(
        "schema: template-autoresearch-human-review-v1\npublication_approved: false\ndecisions:\n  - deferred\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be a mapping"):
        load_human_review(path)


def test_load_human_review_rejects_unknown_decision(tmp_path: Path) -> None:
    path = tmp_path / "human_review.yaml"

    path.write_text(
        "schema: template-autoresearch-human-review-v1\n"
        "publication_approved: false\n"
        "decisions:\n  proposal_review: pending\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be one of"):
        load_human_review(path)


# ---------------------------------------------------------------------------

# config.py — load_seed_ideas and load_experiment_candidates

# ---------------------------------------------------------------------------


def test_load_seed_ideas_rejects_non_list_ideas(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text("ideas: not_a_list\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a list"):
        load_seed_ideas(tmp_path)


def test_load_seed_ideas_rejects_non_mapping_entry(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text("ideas:\n  - just_a_string\n", encoding="utf-8")

    with pytest.raises(ValueError, match="entries must be mappings"):
        load_seed_ideas(tmp_path)


def test_load_seed_ideas_rejects_incomplete_entry(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n  - id: idea1\n    title: No Rationale\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must declare id, title, rationale, and status"):
        load_seed_ideas(tmp_path)


def test_load_experiment_candidates_returns_empty_for_non_list_ideas(tmp_path: Path) -> None:
    # ideas must be non-list → return ()

    (tmp_path / "seed_ideas.yaml").write_text("ideas: not_a_list\n", encoding="utf-8")

    result = load_experiment_candidates(tmp_path)

    assert result == ()


def test_load_experiment_candidates_skips_non_mapping_ideas(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text("ideas:\n  - just_a_string\n", encoding="utf-8")

    result = load_experiment_candidates(tmp_path)

    assert result == ()


def test_load_experiment_candidates_skips_non_list_candidates(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n  - id: idea1\n    candidates: not_a_list\n",
        encoding="utf-8",
    )

    result = load_experiment_candidates(tmp_path)

    assert result == ()


def test_load_experiment_candidates_skips_non_mapping_candidate_entries(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n  - id: idea1\n    candidates:\n      - just_a_string\n",
        encoding="utf-8",
    )

    result = load_experiment_candidates(tmp_path)

    assert result == ()


def test_load_experiment_candidates_skips_empty_identifier(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        'ideas:\n  - id: idea1\n    candidates:\n      - id: ""\n        status: proposed\n',
        encoding="utf-8",
    )

    # Empty identifier → filtered out by `candidate.identifier`

    result = load_experiment_candidates(tmp_path)

    assert result == ()


def test_load_seed_ideas_evidence_links_rejects_non_list(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n  - id: idea1\n    title: T\n    rationale: R\n    status: accepted\n    evidence_links: not_a_list\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="evidence_links must be a list"):
        load_seed_ideas(tmp_path)


def test_load_seed_ideas_evidence_links_rejects_non_mapping_entry(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n"
        "  - id: idea1\n"
        "    title: T\n"
        "    rationale: R\n"
        "    status: accepted\n"
        "    evidence_links:\n"
        "      - not_a_mapping\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="evidence link entries must be mappings"):
        load_seed_ideas(tmp_path)


def test_load_seed_ideas_evidence_links_skips_empty_evidence_path(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n"
        "  - id: idea1\n"
        "    title: T\n"
        "    rationale: R\n"
        "    status: accepted\n"
        "    evidence_links:\n"
        '      - evidence_path: ""\n',
        encoding="utf-8",
    )

    ideas = load_seed_ideas(tmp_path)

    assert len(ideas) == 1

    # Empty evidence_path is silently skipped

    assert ideas[0].evidence_links == ()


# ---------------------------------------------------------------------------

# config.py — load_loop_config without an explicit plan

# ---------------------------------------------------------------------------


def test_load_loop_config_without_explicit_plan(project_root: Path) -> None:
    """load_loop_config(project_root) resolves the plan internally."""

    config = load_loop_config(project_root)

    assert config.topic.startswith("Deterministic bounded AutoResearch")

    assert config.human_review.source_exists is True


def test_load_mnist_task_config_rejects_bad_model_type(tmp_path: Path, project_root: Path) -> None:
    """A candidate with an unsupported model_type should raise ValueError."""

    import yaml

    from src.ml.data import load_mnist_task_config

    # Load real config and inject a bad candidate

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")

    config_dict = yaml.safe_load(real_config_text)

    # Replace first candidate's model_type with an invalid one

    config_dict["candidate_configs"][0]["model_type"] = "unsupported_model"

    bad_config_path = tmp_path / "mnist_task.yaml"

    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported model_type"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


def test_load_mnist_task_config_rejects_bad_training_key(tmp_path: Path, project_root: Path) -> None:
    """An unsupported training key in a candidate config should raise ValueError."""

    import yaml

    from src.ml.data import load_mnist_task_config

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")

    config_dict = yaml.safe_load(real_config_text)

    # Add an unsupported training key

    config_dict["candidate_configs"][0].setdefault("training", {})["unsupported_key"] = 1

    bad_config_path = tmp_path / "mnist_task.yaml"

    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported training key"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


def test_load_mnist_task_config_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    """A non-mapping YAML root should raise ValueError."""

    from src.ml.data import load_mnist_task_config

    (tmp_path / "mnist_task.yaml").write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a mapping"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


def test_load_mnist_task_config_rejects_unsupported_normalization(tmp_path: Path, project_root: Path) -> None:
    """An unsupported normalization mode should raise ValueError at array-load time."""

    import yaml

    from src.ml.data import load_mnist_task_config, load_mnist_arrays

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")

    config_dict = yaml.safe_load(real_config_text)

    config_dict["task"]["normalization"] = "minmax"

    bad_config_path = tmp_path / "mnist_task.yaml"

    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    config = load_mnist_task_config(tmp_path, "mnist_task.yaml")

    # Need to point dataset_path to the real fixture

    import dataclasses

    config = dataclasses.replace(config, dataset_path=str(project_root / "data" / "mnist_small.npz"))

    with pytest.raises(ValueError, match="unsupported normalization"):
        load_mnist_arrays(tmp_path, config)


def test_load_mnist_task_config_rejects_robustness_bad_type(tmp_path: Path, project_root: Path) -> None:
    """An unsupported robustness transform type should raise ValueError."""

    import yaml

    from src.ml.data import load_mnist_task_config

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")

    config_dict = yaml.safe_load(real_config_text)

    config_dict["robustness_transforms"] = [{"id": "bad", "type": "unsupported_transform"}]

    bad_config_path = tmp_path / "mnist_task.yaml"

    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported robustness transform type"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


def test_load_mnist_task_config_rejects_robustness_empty_id(tmp_path: Path, project_root: Path) -> None:
    """A robustness transform with empty id should raise ValueError."""

    import yaml

    from src.ml.data import load_mnist_task_config

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")

    config_dict = yaml.safe_load(real_config_text)

    config_dict["robustness_transforms"] = [{"id": "", "type": "identity"}]

    bad_config_path = tmp_path / "mnist_task.yaml"

    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="id must not be empty"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")

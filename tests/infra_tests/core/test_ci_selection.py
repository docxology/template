"""Real Git changes and source-owned dependency declarations select functional work."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from infrastructure.core.testing.ci_selection import (
    _parse_changed_paths,
    affected_projects,
    changed_git_paths,
    documentation_only,
    functional_selection,
    infrastructure_selection,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def _metadata(root: Path) -> None:
    for scope in PUBLIC_PROJECT_NAMES:
        base = root / "projects" / scope
        base.mkdir(parents=True)
        package = Path(scope).name.replace("_", "-")
        (base / "pyproject.toml").write_text(f'[project]\nname="{package}"\ndependencies=[]\n')
    consumer = root / "projects/templates/template_advanced_literature_review/pyproject.toml"
    consumer.write_text(
        '[project]\nname="template-advanced-literature-review"\n'
        'dependencies=["template-literature-meta-analysis==0.2.0"]\n'
        '[tool.uv.sources]\ntemplate-literature-meta-analysis={path="../template_literature_meta_analysis"}\n'
    )


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.name=Owned selection", "-c", "user.email=selection@example.invalid", *args],
        cwd=root,
        env={"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return result.stdout.strip()


def test_meta_change_includes_real_declared_reverse_consumer(tmp_path: Path) -> None:
    _metadata(tmp_path)
    selected, reason = affected_projects(
        tmp_path, ("projects/templates/template_literature_meta_analysis/src/data.py",)
    )
    assert selected == ("templates/template_advanced_literature_review", "templates/template_literature_meta_analysis")
    assert "reverse" in reason
    selected, _ = affected_projects(tmp_path, ("projects/templates/template_code_project/tests/test_actual.py",))
    assert selected == ("templates/template_code_project",)


@pytest.mark.parametrize(
    "name",
    [
        "uv.lock",
        ".github/workflows/ci.yml",
        "infrastructure/core/actual.py",
        "tests/infra_tests/core/test_actual.py",
        "fonds/templates/actual/data.json",
        "projects/templates/unknown/src/model.py",
        "projects/working/private/src/model.py",
    ],
)
def test_global_controls_and_unknown_paths_cannot_reduce_roster(tmp_path: Path, name: str) -> None:
    selected, _ = affected_projects(tmp_path, (name,))
    assert set(selected) == set(PUBLIC_PROJECT_NAMES)


@pytest.mark.parametrize("change", ["modify", "add", "rename", "delete", "missing-base"])
def test_real_git_change_boundaries_fail_closed(tmp_path: Path, change: str) -> None:
    _git(tmp_path, "init", "-q")
    original = tmp_path / "owned.txt"
    original.write_text("owned source\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "Owned base")
    base = _git(tmp_path, "rev-parse", "HEAD")
    if change == "modify":
        original.write_text("changed source\n")
    elif change == "add":
        (tmp_path / "new.txt").write_text("new source\n")
    elif change == "rename":
        original.rename(tmp_path / "renamed.txt")
    elif change == "delete":
        original.unlink()
    else:
        base = "0" * 40
        original.write_text("changed source\n")
    _git(tmp_path, "add", "--all")
    _git(tmp_path, "commit", "-qm", "Owned change")
    paths, full = changed_git_paths(tmp_path, base)
    assert full is (change in {"rename", "delete", "missing-base"})
    if not full:
        assert paths == (("owned.txt",) if change == "modify" else ("new.txt",))
    elif change == "rename":
        assert paths == ("owned.txt", "renamed.txt")
    elif change == "delete":
        assert paths == ("owned.txt",)


def test_real_git_rename_does_not_drop_later_new_infrastructure_test(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("original unchanged content\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "Owned base")
    base = _git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "a.txt").rename(tmp_path / "b.txt")
    added = tmp_path / "tests/infra_tests/core/test_new.py"
    added.parent.mkdir(parents=True)
    added.write_text("def test_actual():\n    assert True\n")
    _git(tmp_path, "add", "--all")
    _git(tmp_path, "commit", "-qm", "Rename then add genuine test")
    paths, full = changed_git_paths(tmp_path, base)
    assert full
    assert paths == ("a.txt", "b.txt", "tests/infra_tests/core/test_new.py")


def test_non_pr_and_invalid_base_events_always_run_full(tmp_path: Path) -> None:
    for event in ("push", "workflow_dispatch", "unknown", "pull_request"):
        plan = functional_selection(tmp_path, event, "not-a-commit")
        assert plan["full"] and set(plan["projects"]) == set(PUBLIC_PROJECT_NAMES)
        assert plan["change_roster_available"] is (event not in {"pull_request", "push"})


@pytest.mark.parametrize(
    "output", [b"M\0a.py\0A\0z-invalid-\xff.py\0", b"R100\0old.py\0", b"M\0a.py\0X-invalid\0z.py\0", b"M\0a.py"]
)
def test_malformed_change_data_refuses_any_partial_change_roster(output: bytes) -> None:
    assert _parse_changed_paths(output) == ((), True)


def test_documentation_paths_select_no_roster_entry(tmp_path: Path) -> None:
    _metadata(tmp_path)
    selected, reason = affected_projects(tmp_path, ("docs/version.md",))
    assert selected == ()
    assert "documentation-only" in reason


def test_documentation_only_change_runs_no_exemplar_suite(tmp_path: Path) -> None:
    _metadata(tmp_path)
    test = tmp_path / "tests/infra_tests/documentation/test_guide.py"
    test.parent.mkdir(parents=True)
    test.write_text("def test_guide():\n    assert 1 + 1 == 2\n")
    paths = ("AGENTS.md", "docs/guides/new-project-setup.md", "infrastructure/core/testing/AGENTS.md")
    assert documentation_only(paths)
    projects, reason = affected_projects(tmp_path, paths)
    assert projects == ()
    assert "documentation-only" in reason
    plan: dict[str, object] = {"changed_paths": list(paths), "projects": [], "reason": reason}
    infrastructure_selection(tmp_path, plan)
    assert plan["documentation_only"] is True
    assert plan["infra_shards"] == [["tests/infra_tests/documentation/test_guide.py"]]
    from infrastructure.core.testing.ci_infra import validate_plan

    validate_plan(tmp_path, plan)


@pytest.mark.parametrize(
    "paths",
    [
        ("infrastructure/project/git_guards.py",),
        ("AGENTS.md", "pyproject.toml"),
        ("uv.lock",),
        (),
    ],
)
def test_non_documentation_changes_keep_normal_routing(paths: tuple[str, ...]) -> None:
    assert not documentation_only(paths)


@pytest.mark.parametrize(
    "path",
    [
        "requirements.txt",
        "infrastructure/llm/prompts/review.md",
        "docs/prompts/research.md",
        "docs/manuscript/01_intro.md",
        "projects/templates/template_code_project/manuscript/01_intro.md",
        "projects/templates/template_code_project/manuscript/figures/plot.png",
        "infrastructure/rendering/assets/background.svg",
        "unknown/README.md",
        "../docs/guide.md",
        "/docs/guide.md",
    ],
)
def test_runtime_text_artwork_and_unknown_paths_keep_functional_tests(path: str) -> None:
    assert not documentation_only((path,))


def test_full_run_does_not_apply_pull_request_documentation_reduction() -> None:
    from infrastructure.core.testing.ci_infra import infrastructure_files, validate_plan

    root = Path(__file__).resolve().parents[3]
    plan = {"changed_paths": ["README.md"], "full": True}
    infrastructure_selection(root, plan)
    assert plan["documentation_only"] is False
    validate_plan(root, plan)
    assert set(infrastructure_files(root)) <= {name for shard in plan["infra_shards"] for name in shard}


@pytest.mark.timeout(90)
def test_documentation_plan_executes_real_modules_and_retains_prepared_contracts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from infrastructure.core.testing.ci_infra import run_shard, validate_plan, verify_shard_receipts

    root = tmp_path / "source"
    directory = root / "tests/infra_tests/documentation"
    directory.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts=[]\n")
    for name in ("test_guide", "test_counts_refresh"):
        (directory / (name + ".py")).write_text(
            "from pathlib import Path\n"
            f"def test_real_file():\n    Path({str(tmp_path / name)!r}).write_text('executed')\n"
        )
    plan = {"changed_paths": ["docs/guide.md"]}
    infrastructure_selection(root, plan)
    validate_plan(root, plan)
    assert plan["contract_modules"] == ["tests/infra_tests/documentation/test_counts_refresh.py"]
    assert plan["infra_shards"] == [["tests/infra_tests/documentation/test_guide.py"]]
    monkeypatch.setenv("PYTEST_ADDOPTS", "")
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[3]))
    receipts = tmp_path / "receipts"
    for shard in range(2):
        assert run_shard(root, plan, shard, receipts / str(shard)) == 0
    assert verify_shard_receipts(plan, receipts, root=root)["members"] == 2
    assert all((tmp_path / name).read_text() == "executed" for name in ("test_guide", "test_counts_refresh"))
    plan["documentation_only"] = False
    with pytest.raises(ValueError, match="documentation lane"):
        validate_plan(root, plan)

import re
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_experiment_plan_figures_are_referenced_by_the_manuscript() -> None:
    plan = yaml.safe_load((PROJECT_ROOT / "experiment_plan.yaml").read_text(encoding="utf-8"))
    expected = set(plan["expected_figures"])
    manuscript = (PROJECT_ROOT / "manuscript" / "05_results_discussion.md").read_text(encoding="utf-8")
    referenced = set(re.findall(r"\{#(fig:[^}]+)\}", manuscript))
    assert expected == referenced == {"fig:demo-convergence", "fig:convergence-tick-distribution"}


def test_live_fixture_and_documentation_surfaces_are_synchronized() -> None:
    bad_fixtures = sorted((PROJECT_ROOT / "tests" / "mypy_fixtures").glob("bad_*.py"))
    good_fixtures = sorted((PROJECT_ROOT / "tests" / "mypy_fixtures").glob("good_*.py"))
    assert len(bad_fixtures) == 6
    assert len(good_fixtures) == 3

    abstract = (PROJECT_ROOT / "manuscript" / "00_abstract.md").read_text(encoding="utf-8")
    tests_readme = (PROJECT_ROOT / "tests" / "README.md").read_text(encoding="utf-8")
    results = (PROJECT_ROOT / "manuscript" / "05_results_discussion.md").read_text(encoding="utf-8")
    assert "six known-bad" in abstract
    assert "eight pre-registered analyses" in abstract
    assert "278 tests" in tests_readme
    assert "95.91%" in tests_readme
    assert "three pre-registered" not in results.lower()


def test_authoritative_mypy_command_is_synchronized_across_fork_surfaces() -> None:
    expected_prefix = "MYPYPATH=projects/templates/template_formal/src"
    for relative_path in ("README.md", "STANDALONE.md", ".agents/skills/template-formal/SKILL.md"):
        surface = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
        assert expected_prefix in surface, relative_path
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "Success: no issues found in 27 source files" in readme


def test_generated_figure_registry_is_complete_when_outputs_exist() -> None:
    registry_path = PROJECT_ROOT / "output" / "figures" / "figure_registry.json"
    if not registry_path.exists():
        return
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    assert set(registry) == {"fig:demo-convergence", "fig:convergence-tick-distribution"}


def test_claim_ledger_rows_have_resolvable_source_and_artifact_paths() -> None:
    ledger = yaml.safe_load((PROJECT_ROOT / "data" / "claim_ledger.yaml").read_text(encoding="utf-8"))
    claims = ledger["claims"]
    assert len(claims) == 101
    assert len({claim["claim_id"] for claim in claims}) == len(claims)
    for claim in claims:
        source_path = claim["source"].split(" ", 1)[0]
        assert (PROJECT_ROOT / source_path).exists(), source_path
        artifact_parent = (PROJECT_ROOT / claim["artifact_path"]).parent
        if claim["artifact_path"].startswith("output/") and not (PROJECT_ROOT / "output").exists():
            # output/ is gitignored (disposable render tree): rows binding to
            # render artifacts are checkable only after a pipeline run, not on
            # a clean checkout.
            continue
        assert artifact_parent.exists(), claim["artifact_path"]

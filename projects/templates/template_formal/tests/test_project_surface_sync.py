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
    assert "95.28%" in tests_readme
    assert "three pre-registered" not in results.lower()

    # The collected-test total used to be pinned in prose here ("279 tests"), which
    # meant adding a single test reddened a doc gate in nine places. The total now
    # lives in the regenerated docs/_generated/COUNTS.md, so the assertions below
    # bind to what still has to be true of tests/README.md: it points at that
    # generated doc, it does not re-pin a total, and the module-per-subpackage
    # layout it describes matches the real tree.
    assert "docs/_generated/COUNTS.md" in tests_readme
    hardcoded_totals = [line for line in tests_readme.splitlines() if re.search(r"\b\d{2,5}\s+tests\b", line)]
    assert not hardcoded_totals, f"tests/README.md re-pinned a test total: {hardcoded_totals}"

    src_subpackages = {
        entry.name
        for entry in (PROJECT_ROOT / "src" / "template_formal").iterdir()
        if entry.is_dir() and (entry / "__init__.py").is_file()
    }
    test_subdirs = {
        entry.name
        for entry in (PROJECT_ROOT / "tests").iterdir()
        if entry.is_dir() and entry.name not in {"__pycache__", "mypy_fixtures"}
    }
    assert src_subpackages, "src subpackage probe found nothing — the layout changed"
    # `types/` is the one documented exception: its two leaf modules are covered by
    # top-level test_types_*.py files rather than a test directory of their own.
    assert src_subpackages - test_subdirs == {"types"}
    assert not test_subdirs - src_subpackages
    assert sorted(path.name for path in (PROJECT_ROOT / "tests").glob("test_types_*.py")) == [
        "test_types_ids.py",
        "test_types_result.py",
    ]
    for name in sorted(test_subdirs):
        assert f"[`{name}/`]({name}/)" in tests_readme, name

    root_readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert root_readme.count("95.28%") == 2
    assert "95.91%" not in root_readme


def test_authoritative_mypy_command_is_synchronized_across_fork_surfaces() -> None:
    expected_prefix = "MYPYPATH=projects/templates/template_formal/src"
    for relative_path in ("README.md", "STANDALONE.md", ".agents/skills/template-formal/SKILL.md"):
        surface = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
        assert expected_prefix in surface, relative_path
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "Success: no issues found in 27 source files" in readme


def test_documented_project_script_paths_resolve_on_disk() -> None:
    """Every `scripts/<name>.py` a fork-facing surface names must actually exist.

    Regression guard: these surfaces once documented the shared repo-root runner
    `scripts/pipeline/stage_02_analysis.py` as this project's analysis command,
    which does not exist inside the exemplar, so a forker following the README hit
    a missing file. Repo-root runners are addressed as
    `scripts/pipeline/...` with an explicit `--project` flag and are excluded here;
    a bare `scripts/<name>.py` is a claim about THIS project's scripts/ directory.
    """
    surfaces = ("README.md", "AGENTS.md", "STANDALONE.md", ".agents/skills/template-formal/SKILL.md")
    pattern = re.compile(r"(?<![\w/.])scripts/([A-Za-z0-9_]+\.py)")
    missing: list[str] = []
    checked = 0
    for relative_path in surfaces:
        text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
        for script_name in set(pattern.findall(text)):
            checked += 1
            if not (PROJECT_ROOT / "scripts" / script_name).is_file():
                missing.append(f"{relative_path} -> scripts/{script_name}")
    assert checked > 0, "no project-local script paths found — the pattern stopped matching"
    assert not missing, f"documented project scripts do not exist: {missing}"


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

"""Tests for src/analysis.py review-stage helpers (temp dirs + subprocess CLI; no mocks)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.analysis import (
    StageResult,
    audit_infrastructure_imports,
    check_determinism_artifacts,
    run_project_tests,
    validate_bibliography_completeness,
    validate_variables_resolved,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_stage_result_as_dict() -> None:
    r = StageResult(name="t", status="passed", message="ok", details={"a": 1}, exit_code=0)
    d = r.as_dict()
    assert d["name"] == "t"
    assert d["details"] == {"a": 1}


def test_validate_bibliography_completeness_missing_bib(tmp_path: Path) -> None:
    (tmp_path / "manuscript").mkdir()
    res = validate_bibliography_completeness(tmp_path)
    assert res.exit_code == 2
    assert res.status == "error"


def test_validate_bibliography_completeness_pass(tmp_path: Path) -> None:
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "references.bib").write_text("@article{k1,\n title={x}\n}\n", encoding="utf-8")
    (md / "01_intro.md").write_text("Ref [@k1].", encoding="utf-8")
    res = validate_bibliography_completeness(tmp_path)
    assert res.status == "passed"
    assert res.exit_code == 0


def test_validate_bibliography_completeness_missing_key(tmp_path: Path) -> None:
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "references.bib").write_text("@article{k1,\n title={x}\n}\n", encoding="utf-8")
    (md / "01_intro.md").write_text("Missing [@ghost].", encoding="utf-8")
    res = validate_bibliography_completeness(tmp_path)
    assert res.status == "failed"
    assert "ghost" in res.details["missing_keys"]


def test_validate_bibliography_completeness_key_in_second_bib(tmp_path: Path) -> None:
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "references.bib").write_text("@article{k1,\n title={x}\n}\n", encoding="utf-8")
    (md / "references_deep.bib").write_text("@article{deep1,\n title={y}\n}\n", encoding="utf-8")
    (md / "01_intro.md").write_text("Ref [@k1] and [@deep1].", encoding="utf-8")
    res = validate_bibliography_completeness(tmp_path)
    assert res.status == "passed"
    assert res.exit_code == 0


def test_validate_variables_resolved_pass(tmp_path: Path) -> None:
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "body.md").write_text("No templates here.", encoding="utf-8")
    res = validate_variables_resolved(tmp_path)
    assert res.status == "passed"


def test_validate_variables_resolved_fail(tmp_path: Path) -> None:
    out_m = tmp_path / "output" / "manuscript"
    out_m.mkdir(parents=True)
    (out_m / "body.md").write_text("Bad {{TOKEN}}.", encoding="utf-8")
    res = validate_variables_resolved(tmp_path)
    assert res.status == "failed"
    assert res.exit_code == 1


def test_validate_variables_resolved_prefers_output_manuscript(tmp_path: Path) -> None:
    """Templates under manuscript/ may keep placeholders; resolved tree must be clean."""
    src = tmp_path / "manuscript"
    src.mkdir()
    (src / "body.md").write_text("Keep {{TOKEN}} here.", encoding="utf-8")
    out_m = tmp_path / "output" / "manuscript"
    out_m.mkdir(parents=True)
    (out_m / "body.md").write_text("Substituted, no markers.", encoding="utf-8")
    res = validate_variables_resolved(tmp_path)
    assert res.status == "passed"


def test_audit_infrastructure_imports_on_project() -> None:
    res = audit_infrastructure_imports(PROJECT_ROOT)
    assert res.status == "passed"
    assert "infrastructure_imports" in res.details


def test_check_determinism_artifacts_pass(tmp_path: Path) -> None:
    out = tmp_path / "output"
    (out / "search" / "cache").mkdir(parents=True)
    (out / "search" / "cache" / "search_fake.json").write_text("{}", encoding="utf-8")
    # ``run_search_pipeline.py`` writes ``papers`` (not ``num_papers``).
    # The check must read the field the pipeline actually writes.
    (out / "run_summary.json").write_text('{"papers": 3}', encoding="utf-8")
    mdir = tmp_path / "manuscript"
    mdir.mkdir()
    (mdir / "config.yaml").write_text(
        "llm:\n  seed: 42\n  temperature: 0\n",
        encoding="utf-8",
    )
    res = check_determinism_artifacts(tmp_path)
    assert res.status == "passed"
    # Regression: papers_found must reflect the actual papers count, not
    # "unknown" — the historic bug was reading ``num_papers`` (never
    # written) instead of ``papers`` (what the pipeline actually writes).
    assert res.details["findings"]["papers_found"] == 3


def test_check_determinism_artifacts_reads_total_papers(tmp_path: Path) -> None:
    """Deep-search writes ``total_papers``; the check must accept that key too."""
    out = tmp_path / "output"
    (out / "search" / "cache").mkdir(parents=True)
    (out / "search" / "cache" / "x.json").write_text("{}", encoding="utf-8")
    (out / "run_summary.json").write_text('{"total_papers": 17}', encoding="utf-8")
    mdir = tmp_path / "manuscript"
    mdir.mkdir()
    (mdir / "config.yaml").write_text("llm:\n  seed: 1\n  temperature: 0\n", encoding="utf-8")
    res = check_determinism_artifacts(tmp_path)
    assert res.status == "passed"
    assert res.details["findings"]["papers_found"] == 17


def test_check_determinism_artifacts_missing_run_summary(tmp_path: Path) -> None:
    out = tmp_path / "output"
    (out / "search" / "cache").mkdir(parents=True)
    (out / "search" / "cache" / "x.json").write_text("{}", encoding="utf-8")
    mdir = tmp_path / "manuscript"
    mdir.mkdir()
    (mdir / "config.yaml").write_text(
        "llm:\n  seed: 1\n  temperature: 0\n",
        encoding="utf-8",
    )
    res = check_determinism_artifacts(tmp_path)
    assert res.status == "failed"
    assert any("run_summary" in i for i in res.details["issues"])


def test_check_determinism_artifacts_temperature_high(tmp_path: Path) -> None:
    out = tmp_path / "output"
    (out / "search" / "cache").mkdir(parents=True)
    (out / "search" / "cache" / "x.json").write_text("{}", encoding="utf-8")
    (out / "run_summary.json").write_text("{}", encoding="utf-8")
    mdir = tmp_path / "manuscript"
    mdir.mkdir()
    (mdir / "config.yaml").write_text(
        "llm:\n  seed: 1\n  temperature: 0.9\n",
        encoding="utf-8",
    )
    res = check_determinism_artifacts(tmp_path)
    assert res.status == "failed"


def test_run_project_tests_missing_tests_dir(tmp_path: Path) -> None:
    res = run_project_tests(tmp_path)
    assert res.status == "error"
    assert res.exit_code == 2


def _build_isolated_project(tmp_path: Path, *, test_body: str = "def test_ok():\n    assert 1 + 1 == 2\n") -> Path:
    """Lay out a tiny project root with src/ + tests/ so run_project_tests
    can invoke pytest under it without the parent test runner colliding."""
    proj = tmp_path / "iso_project"
    src = proj / "src"
    tests = proj / "tests"
    src.mkdir(parents=True)
    tests.mkdir(parents=True)
    (src / "__init__.py").write_text("def two(): return 2\n", encoding="utf-8")
    (tests / "__init__.py").write_text("", encoding="utf-8")
    (tests / "conftest.py").write_text(
        "import sys, pathlib\nsys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))\n",
        encoding="utf-8",
    )
    (tests / "test_local.py").write_text(test_body, encoding="utf-8")
    # Avoid inheriting the repo-level pyproject coverage settings that would
    # require additional plugins to be loaded under the isolated subprocess.
    (proj / "pyproject.toml").write_text("[tool.pytest.ini_options]\nminversion='7.0'\n", encoding="utf-8")
    return proj


def test_run_project_tests_pass(tmp_path: Path) -> None:
    """Happy path: real subprocess run of pytest with sufficient coverage."""
    proj = _build_isolated_project(tmp_path, test_body="from src import two\n\ndef test_ok():\n    assert two() == 2\n")
    res = run_project_tests(proj, min_coverage=10.0)
    assert res.status == "passed", res.details
    assert res.exit_code == 0
    assert res.details.get("coverage") is not None


def test_run_project_tests_fail_when_pytest_errors(tmp_path: Path) -> None:
    """Failure path: a failing test triggers status=failed and exit_code=1."""
    proj = _build_isolated_project(
        tmp_path,
        test_body="def test_will_fail():\n    assert False, 'intentional'\n",
    )
    res = run_project_tests(proj, min_coverage=1.0)
    assert res.status == "failed"
    assert res.exit_code == 1


def test_analysis_cli_infrastructure_usage(tmp_path: Path) -> None:
    """CLI dispatch covers the infrastructure_usage stage."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text(
        "from infrastructure.search.literature import Paper  # noqa: F401\n", encoding="utf-8"
    )
    (tmp_path / "manuscript").mkdir()
    # Project lives at projects/templates/<name>/; repo root is three levels up.
    repo_root = PROJECT_ROOT.parents[2]
    proc = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "src" / "analysis.py"),
            "--stage",
            "infrastructure_usage",
            "--project-root",
            str(tmp_path),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "passed"


def test_analysis_cli_determinism_check_failed(tmp_path: Path) -> None:
    """CLI dispatch covers the determinism_check stage on an empty project."""
    # Project lives at projects/templates/<name>/; repo root is three levels up.
    repo_root = PROJECT_ROOT.parents[2]
    proc = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "src" / "analysis.py"),
            "--stage",
            "determinism_check",
            "--project-root",
            str(tmp_path),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["status"] == "failed"


def test_analysis_cli_test_suite_health_missing_tests(tmp_path: Path) -> None:
    """CLI dispatch covers the test_suite_health stage when tests/ is absent."""
    # Project lives at projects/templates/<name>/; repo root is three levels up.
    repo_root = PROJECT_ROOT.parents[2]
    proc = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "src" / "analysis.py"),
            "--stage",
            "test_suite_health",
            "--project-root",
            str(tmp_path),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "error"


def test_audit_infrastructure_imports_flags_missing_module(tmp_path: Path) -> None:
    """A non-existent infrastructure import is reported as an issue."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "bad.py").write_text(
        "from infrastructure.this_module_definitely_does_not_exist import Foo\n",
        encoding="utf-8",
    )
    res = audit_infrastructure_imports(tmp_path)
    assert res.status == "failed", res.details
    assert res.exit_code == 1
    joined = "\n".join(res.details["issues"])
    assert "this_module_definitely_does_not_exist" in joined


def test_audit_infrastructure_imports_skips_private_modules(tmp_path: Path) -> None:
    """Private helpers (leading underscore) are excluded from the audit."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "_helpers.py").write_text("from infrastructure.never.never import x\n", encoding="utf-8")
    res = audit_infrastructure_imports(tmp_path)
    assert res.status == "passed", res.details


def test_audit_infrastructure_imports_reports_syntax_error(tmp_path: Path) -> None:
    """A file with a SyntaxError must surface in the issues list and the
    rest of the audit must continue rather than abort."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "broken.py").write_text("def bad(:\n    pass\n", encoding="utf-8")
    (src / "ok.py").write_text(
        "from infrastructure.search.literature import Paper  # noqa: F401\n",
        encoding="utf-8",
    )
    res = audit_infrastructure_imports(tmp_path)
    assert res.status == "failed"
    assert any("syntax error" in m for m in res.details["issues"])
    # The good file's import was still counted.
    assert "infrastructure.search.literature" in res.details["infrastructure_imports"]


def test_extract_citation_keys_handles_empty_brackets() -> None:
    """Pathological input: ``[@]`` and ``[@; @]`` must produce no keys
    rather than emitting empty strings into the cited-key set."""
    from src.analysis import _extract_citation_keys

    assert _extract_citation_keys("[@]") == set()
    assert _extract_citation_keys("[@; @]") == set()
    assert _extract_citation_keys("[@; @real]") == {"real"}
    # Whitespace-only token after split must also be dropped.
    assert _extract_citation_keys("[@  ;@k]") == {"k"}


def test_extract_citation_keys_handles_multicite_and_crossref() -> None:
    """The citation extractor must:

    * split multi-cite ``[@a; @b]`` into two keys,
    * drop pandoc-crossref labels (``[@sec:foo]``, ``[@fig:bar]``,
      ``[@tbl:t1]``, ``[@eq:e]``, ``[@lst:l]``),
    * strip locators (``[@key, p. 5]``) and author/suppression
      markers (``[-@k]``, ``[+@k]``),
    * leave plain single citations untouched.
    """
    from src.analysis import _extract_citation_keys

    text = (
        "See [@boyd2004convex; @nocedal2006numerical] and a single [@kingma2014adam]. "
        "Cross-refs [@sec:methodology], [@fig:papers_per_source], [@tbl:determinism], "
        "[@eq:foo], [@lst:bar] must be excluded. "
        "Locator: [@peng2011reproducible, p. 1226]. "
        "Suppression: [-@reddi2018convergence]. "
        "Multi with author-only: [@nesterov2013gradient; -@kingma2014adam]."
    )
    keys = _extract_citation_keys(text)
    assert keys == {
        "boyd2004convex",
        "nocedal2006numerical",
        "kingma2014adam",
        "peng2011reproducible",
        "reddi2018convergence",
        "nesterov2013gradient",
    }


def test_validate_bibliography_completeness_handles_multicite(tmp_path: Path) -> None:
    """A multi-cite ``[@a; @b]`` must resolve every key, not be treated
    as a single composite key."""
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "references.bib").write_text(
        "@article{a,\n title={A}\n}\n@article{b,\n title={B}\n}\n",
        encoding="utf-8",
    )
    (md / "01_intro.md").write_text("Multi [@a; @b].", encoding="utf-8")
    res = validate_bibliography_completeness(tmp_path)
    assert res.status == "passed", res.details
    assert {"a", "b"}.issubset(set(res.details["cited_keys"]))


def test_validate_bibliography_completeness_excludes_crossref_labels(tmp_path: Path) -> None:
    """``[@sec:foo]`` etc. are pandoc-crossref refs, not BibTeX keys —
    they must not be reported as missing."""
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "references.bib").write_text("@article{k,\n title={x}\n}\n", encoding="utf-8")
    (md / "01_intro.md").write_text(
        "See [@sec:methodology], [@fig:foo], [@tbl:t1] and the real cite [@k].",
        encoding="utf-8",
    )
    res = validate_bibliography_completeness(tmp_path)
    assert res.status == "passed", res.details
    assert "sec:methodology" not in res.details["cited_keys"]
    assert "fig:foo" not in res.details["cited_keys"]
    assert "tbl:t1" not in res.details["cited_keys"]


def test_validate_bibliography_completeness_skips_doc_files(tmp_path: Path) -> None:
    """``SYNTAX.md`` / ``AGENTS.md`` / ``README.md`` carry illustrative
    ``[@key]`` examples that must not be treated as real citations."""
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "references.bib").write_text("@article{real,\n title={x}\n}\n", encoding="utf-8")
    (md / "01_intro.md").write_text("Use [@real].", encoding="utf-8")
    (md / "SYNTAX.md").write_text("Example syntax: [@key].", encoding="utf-8")
    (md / "AGENTS.md").write_text("Agents see [@example_key] and [@another].", encoding="utf-8")
    (md / "README.md").write_text("Readme cites [@foo_bar].", encoding="utf-8")
    res = validate_bibliography_completeness(tmp_path)
    assert res.status == "passed", res.details


def test_validate_bibliography_completeness_skips_references_section(tmp_path: Path) -> None:
    """References-section markdown (`99_*`) is intentionally skipped — those
    files reference every key by design and would always trip the check."""
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "references.bib").write_text("@article{k1,\n title={x}\n}\n", encoding="utf-8")
    # Body cites k1 → present in bib.
    (md / "01_intro.md").write_text("Body cites [@k1].", encoding="utf-8")
    # 99_references.md mentions a key that does NOT exist; this must be
    # ignored because the file itself is the bibliography pointer.
    (md / "99_references.md").write_text("Pointer: [@k1] [@absent_key_only_listed_here]", encoding="utf-8")
    res = validate_bibliography_completeness(tmp_path)
    assert res.status == "passed"
    assert "absent_key_only_listed_here" not in res.details["cited_keys"]


def test_check_determinism_missing_search_cache_dir(tmp_path: Path) -> None:
    """When output/search/cache does not exist, the issue is surfaced."""
    out = tmp_path / "output"
    out.mkdir()
    (out / "run_summary.json").write_text("{}", encoding="utf-8")
    mdir = tmp_path / "manuscript"
    mdir.mkdir()
    (mdir / "config.yaml").write_text("llm:\n  seed: 1\n  temperature: 0\n", encoding="utf-8")
    res = check_determinism_artifacts(tmp_path)
    assert res.status == "failed"
    assert any("cache directory not present" in i for i in res.details["issues"])


def test_check_determinism_temperature_missing(tmp_path: Path) -> None:
    """Missing temperature in config must be flagged as non-deterministic."""
    out = tmp_path / "output"
    (out / "search" / "cache").mkdir(parents=True)
    (out / "search" / "cache" / "x.json").write_text("{}", encoding="utf-8")
    (out / "run_summary.json").write_text("{}", encoding="utf-8")
    mdir = tmp_path / "manuscript"
    mdir.mkdir()
    (mdir / "config.yaml").write_text(
        # temperature absent on purpose
        "llm:\n  seed: 1\n",
        encoding="utf-8",
    )
    res = check_determinism_artifacts(tmp_path)
    assert res.status == "failed"
    assert any("temperature" in i for i in res.details["issues"])


def test_analysis_cli_bibliography_completeness(tmp_path: Path) -> None:
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "references.bib").write_text("@article{a,\ntitle={t}\n}\n", encoding="utf-8")
    (md / "x.md").write_text("", encoding="utf-8")
    # Project lives at projects/templates/<name>/; repo root is three levels up.
    repo_root = PROJECT_ROOT.parents[2]
    proc = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "src" / "analysis.py"),
            "--stage",
            "bibliography_completeness",
            "--project-root",
            str(tmp_path),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "passed"


def test_analysis_cli_variables_resolved(tmp_path: Path) -> None:
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "x.md").write_text("{{BAD}}", encoding="utf-8")
    # Project lives at projects/templates/<name>/; repo root is three levels up.
    repo_root = PROJECT_ROOT.parents[2]
    proc = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "src" / "analysis.py"),
            "--stage",
            "variables_resolved",
            "--project-root",
            str(tmp_path),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["status"] == "failed"

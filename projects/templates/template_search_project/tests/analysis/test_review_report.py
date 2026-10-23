"""Direct-call tests for src.review_report (no mocks; real files).

Uses an isolated project tree with a pre-materialised ``output/review/summary.json``
so ``ensure_review_summary`` short-circuits without spawning the real
``scripts/review`` subprocess (that flow is exercised separately by the
review-orchestrator's own tests).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from template_search_project.analysis.review_report import (
    H,
    check_anchors,
    collect_infra_imports,
    ensure_review_summary,
    generate_review_report,
    project_paths,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_project_paths_resolve_real_layout() -> None:
    project_root, review_dir = project_paths(PROJECT_ROOT)
    assert project_root.name == "template_search_project"
    assert (project_root / "AGENTS.md").exists()
    assert review_dir == project_root / "output" / "review"


def test_H_builds_markdown_header():
    assert H("Title") == "# Title"
    assert H("Sub", level=2) == "## Sub"


def test_check_anchors_finds_broken_and_valid():
    # check_anchors does a literal (non-slugified) substring search for the
    # anchor text within a heading line, so the heading must contain the
    # anchor text verbatim to count as defined.
    text = "## section-one\n\nSee [link](#section-one) for details.\nSee [broken](#does-not-exist) too.\n"
    broken = check_anchors(text)
    assert "does-not-exist" in broken
    assert "section-one" not in broken


def test_check_anchors_html_id_anchor_counts_as_defined():
    text = '<a id="my-anchor"></a>\n\nLink to [it](#my-anchor).\n'
    assert check_anchors(text) == []


def _write_fake_src_module(project_root: Path) -> None:
    (project_root / "src").mkdir(parents=True, exist_ok=True)
    (project_root / "src" / "widget.py").write_text(
        "from infrastructure.core.logging.utils import get_logger\nlogger = get_logger(__name__)\n",
        encoding="utf-8",
    )
    (project_root / "src" / "_private.py").write_text(
        "from infrastructure.core.logging.utils import get_logger\n",
        encoding="utf-8",
    )
    (project_root / "src" / "no_infra.py").write_text("x = 1\n", encoding="utf-8")


def test_collect_infra_imports_finds_real_and_skips_underscore(tmp_path: Path):
    _write_fake_src_module(tmp_path)
    result = collect_infra_imports(tmp_path)
    assert "infrastructure.core.logging.utils" in result
    assert result["infrastructure.core.logging.utils"] == {"widget.py"}


def test_collect_infra_imports_ignores_nonexistent_infra_module(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "fake.py").write_text(
        "from infrastructure.totally_made_up_module import thing\n", encoding="utf-8"
    )
    result = collect_infra_imports(tmp_path)
    assert result == {}


def test_ensure_review_summary_reads_existing_summary(tmp_path: Path):
    review_dir = tmp_path / "output" / ".pipeline" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "summary.json").write_text(
        json.dumps({"total": 3, "passed": 3, "failed": 0, "skipped": 0, "overall_exit_code": 0}),
        encoding="utf-8",
    )
    summary, exit_code, notes = ensure_review_summary(tmp_path, review_dir)
    assert exit_code == 0
    assert notes == ""
    assert summary["total"] == 3


def test_ensure_review_summary_missing_review_script(tmp_path: Path):
    review_dir = tmp_path / "output" / ".pipeline" / "review"
    (tmp_path / "scripts").mkdir(parents=True)
    summary, exit_code, notes = ensure_review_summary(tmp_path, review_dir)
    assert exit_code == 1
    assert "missing" in notes
    assert summary["overall_exit_code"] == 1


def _make_isolated_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "AGENTS.md").write_text(
        "# Agent guide\n\n### Purpose\n\nStuff.\n\n### Layout\n\nMore stuff.\n",
        encoding="utf-8",
    )
    (project_root / "README.md").write_text("# Project\n\n## Purpose\n\nStuff.\n", encoding="utf-8")
    (project_root / "manuscript").mkdir()
    (project_root / "manuscript" / "references.bib").write_text(
        "@article{a2020,\n  title={T},\n}\n@article{b2021,\n  title={U},\n}\n",
        encoding="utf-8",
    )
    (project_root / "manuscript" / "01_intro.md").write_text("Intro citing [@a2020] and [@b2021].\n", encoding="utf-8")
    (project_root / "manuscript" / "99_references.md").write_text("See bib.\n", encoding="utf-8")
    _write_fake_src_module(project_root)
    (project_root / "tests").mkdir()
    (project_root / "tests" / "test_x.py").write_text("", encoding="utf-8")
    (project_root / "scripts").mkdir()
    (project_root / "scripts" / "review").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    review_dir = project_root / "output" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "summary.json").write_text(
        json.dumps({"total": 2, "passed": 2, "failed": 0, "skipped": 0, "overall_exit_code": 0}),
        encoding="utf-8",
    )
    (review_dir / "stage_bibtex_validation.json").write_text(
        json.dumps({"status": "ok", "success": True}), encoding="utf-8"
    )
    (review_dir / "stage_bibliography_completeness.json").write_text(
        json.dumps({"status": "ok", "success": False}), encoding="utf-8"
    )

    (project_root / "review_config.yaml").write_text(
        "review:\n"
        "  stages:\n"
        "  - name: bibtex_validation\n"
        "    enabled: true\n"
        "  - name: bibliography_completeness\n"
        "    enabled: true\n"
        "  - name: skipped_stage\n"
        "    enabled: false\n",
        encoding="utf-8",
    )
    return project_root


def test_generate_review_report_writes_markdown_and_prints_summary(tmp_path: Path, capsys):
    project_root = _make_isolated_project(tmp_path)
    exit_code = generate_review_report(project_root, project_root / "output" / "review")
    assert exit_code == 0

    out = project_root / "output" / "review" / "REVIEW_REPORT.md"
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "DEEP REVIEW REPORT" in text
    assert "informational current-source findings" in text
    assert "Overall status:" not in text
    assert "a2020" in text and "b2021" in text
    assert "ENABLED  bibtex_validation" in text
    assert "Bibliography completeness:** passed" in text
    assert "DISABLED  skipped_stage" in text

    captured = capsys.readouterr()
    assert "REPORT →" in captured.out
    assert "DEEP REVIEW SUMMARY" in captured.out
    assert str(project_root / "output/.pipeline/review") in captured.out
    assert "search-report-inputs-" not in captured.out


def test_generate_review_report_is_byte_stable_and_path_portable(tmp_path: Path, monkeypatch):
    """The offline report must not embed wall-clock or checkout-specific paths."""
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    project_root = _make_isolated_project(tmp_path)
    review_dir = project_root / "output" / "review"
    assert generate_review_report(project_root, review_dir) == 0
    first = (review_dir / "REVIEW_REPORT.md").read_bytes()
    assert generate_review_report(project_root, review_dir) == 0
    second = (review_dir / "REVIEW_REPORT.md").read_bytes()
    assert first == second
    report = second.decode("utf-8")
    assert str(tmp_path) not in report
    assert "SOURCE_DATE_EPOCH unset" in report


def _cite_count_in_report(text: str) -> int:
    """Extract the ``## 3.`` section's live-computed inline-citation count."""
    match = re.search(r"\*\*Manuscript inline citations:\*\* (\d+) unique keys", text)
    assert match is not None, "section 3 citation count not found in report"
    return int(match.group(1))


def test_gaps_section_reflects_live_citation_count_not_hardcoded_zero(tmp_path: Path):
    """Regression test: section 7 (GAPS) must report the *same* citation
    count that section 3 (BIBLIOGRAPHY AUDIT) computes from the live
    ``cite_keys`` set, not a separately hardcoded narrative string.

    Before this fix, section 7 always printed the literal string "0 inline
    citations in manuscript" regardless of input, which directly
    contradicted section 3's live count whenever the fixture had real
    citations (e.g. the 2-citation fixture used by the test above, which
    simultaneously claimed "0" in section 7 and "2 unique keys" in section
    3). This test seeds a *different* nonzero citation count (3) than that
    other fixture's count (2) to prove the GAPS section tracks whatever
    ``cite_keys`` actually is, rather than a fixed number.
    """
    project_root = _make_isolated_project(tmp_path)
    # Extend the bib + manuscript with a third, distinct citation key so the
    # live count (3) differs from both "0" (the old hardcoded literal) and
    # "2" (the other test fixture's count) — any residual hardcoding would
    # be caught by either assertion below.
    bib_path = project_root / "manuscript" / "references.bib"
    bib_path.write_text(
        bib_path.read_text(encoding="utf-8") + "@article{c2022,\n  title={V},\n}\n",
        encoding="utf-8",
    )
    (project_root / "manuscript" / "02_extra.md").write_text("Further discussion citing [@c2022].\n", encoding="utf-8")

    exit_code = generate_review_report(project_root, project_root / "output" / "review")
    assert exit_code == 0

    text = (project_root / "output" / "review" / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    live_count = _cite_count_in_report(text)
    assert live_count == 3

    # Section 7's bibliography row must cite the SAME live count, not "0".
    assert f"{live_count} inline citation(s) present in manuscript" in text
    assert "0 inline citations in manuscript" not in text


def test_gaps_section_reports_zero_citations_when_manuscript_has_none(tmp_path: Path):
    """The zero-citation branch is still exercised (and still correct) when
    the live count really is zero — this pins the other half of the
    now-conditional bibliography row.
    """
    project_root = _make_isolated_project(tmp_path)
    for md in (project_root / "manuscript").glob("*.md"):
        if md.name != "99_references.md":
            md.write_text("No citations here.\n", encoding="utf-8")

    exit_code = generate_review_report(project_root, project_root / "output" / "review")
    assert exit_code == 0

    text = (project_root / "output" / "review" / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert _cite_count_in_report(text) == 0
    assert "0 inline citations in manuscript" in text
    assert "inline citation(s) present in manuscript" not in text


def test_section_9_infra_usage_matches_section_4_live_computation(tmp_path: Path):
    """Section 9's "Infra usage" bullet must list the same modules
    ``infra_imports_used`` (section 4) actually found — not a separately
    hardcoded module list that can drift out of sync with the real scan.
    """
    project_root = _make_isolated_project(tmp_path)
    exit_code = generate_review_report(project_root, project_root / "output" / "review")
    assert exit_code == 0

    text = (project_root / "output" / "review" / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    section_9 = text.split("9.  INTELLIGENCE AUGMENTATION", 1)[1]
    # _write_fake_src_module (used by _make_isolated_project) only imports
    # infrastructure.core.logging.utils — the old hardcoded section-9 list
    # named unrelated modules (infrastructure.search.literature,
    # infrastructure.reference.citation, infrastructure.llm) that this
    # fixture never imports at all. Scope the check to section 9's own text
    # since "infrastructure.reference" also appears (legitimately) in
    # section 5's static description of the review-system's stage list.
    assert "Infra usage (1 module(s)): infrastructure.core.logging.utils" in section_9
    assert "infrastructure.search.literature" not in section_9
    assert "infrastructure.reference.citation" not in section_9
    assert "infrastructure.llm" not in section_9


def test_public_report_recomputes_findings_despite_forged_historical_claims(tmp_path: Path):
    project = _make_isolated_project(tmp_path)
    historical = project / "output/review/summary.json"
    original = historical.read_bytes()
    assert generate_review_report(project, project / "output/review") == 0
    before = (project / "output/review/REVIEW_REPORT.md").read_text()
    assert "Bibliography completeness:** passed" in before
    # A different existing own bibliography provides real invalid source bytes;
    # an old all-green completion claim cannot bless their current citation gap.
    wrong_existing = project / "wrong-existing-source.bib"
    wrong_existing.write_text("@article{z2099, title={Different source},}\n")
    (project / "manuscript/references.bib").write_bytes(wrong_existing.read_bytes())
    assert generate_review_report(project, project / "output/review") == 0
    after = (project / "output/review/REVIEW_REPORT.md").read_text()
    assert "Bibliography completeness:** failed" in after
    assert "Missing bibliography keys:** 2" in after and after != before
    assert "all enabled stages passed" not in after and "Overall status:" not in after
    assert historical.read_bytes() == original


def test_public_report_validates_actual_import_source_despite_historical_green_receipt(tmp_path: Path):
    project = _make_isolated_project(tmp_path)
    (project / "src/widget.py").write_text("import infrastructure.actual_nonexistent_owned_control\n")
    assert generate_review_report(project, project / "output/review") == 0
    text = (project / "output/review/REVIEW_REPORT.md").read_text()
    assert "Infrastructure import validity:** failed" in text
    assert "Infrastructure import issues:** 1" in text


def test_public_report_bytes_ignore_operational_history_and_private_transcript_data(tmp_path: Path):
    project = _make_isolated_project(tmp_path)
    assert generate_review_report(project, project / "output/review") == 0
    report = project / "output/review/REVIEW_REPORT.md"
    original = report.read_bytes()
    for relative in (
        "output/review/summary.json",
        "output/review/stage_bibtex_validation.json",
        "output/.pipeline/review/summary.json",
    ):
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '{"complete":"true","run_id":"volatile-owned-nonce",'
            '"stdout":"/Users/invented-private-fixture/credential-location"}'
        )
        assert generate_review_report(project, project / "output/review") == 0
        assert report.read_bytes() == original
        path.write_text("malformed old/runtime bytes")
        assert generate_review_report(project, project / "output/review") == 0
        assert report.read_bytes() == original
    text = report.read_text()
    assert "volatile-owned-nonce" not in text and "/Users/" not in text
    assert "Overall status:" not in text and "Review subprocess notes:" not in text


def test_public_report_source_redirect_is_refused_without_reading_or_overwriting_external_data(tmp_path: Path):
    import pytest

    project = _make_isolated_project(tmp_path)
    outside = tmp_path / "invented-external-source.bib"
    original = b"@article{private_invented_key, title={Owned negative fixture},}\n"
    outside.write_bytes(original)
    canonical = project / "manuscript/references.bib"
    canonical.unlink()
    canonical.symlink_to(outside)
    with pytest.raises((OSError, ValueError), match="symlink|regular|directory"):
        generate_review_report(project, project / "output/review")
    assert outside.read_bytes() == original
    assert not (project / "output/review/REVIEW_REPORT.md").exists()


def test_receipt_reader_respects_actual_configured_local_path_and_filename(tmp_path: Path):
    from template_search_project.analysis.review_report import configured_review_paths

    project = _make_isolated_project(tmp_path)
    config = project / "review_config.yaml"
    config.write_text(
        "review:\n  stages: []\n  output:\n"
        "    dir: output/.pipeline/owned-review\n    summary_json: owned-summary.json\n"
    )
    directory, filename = configured_review_paths(project)
    assert directory == project / "output/.pipeline/owned-review" and filename == "owned-summary.json"
    directory.mkdir(parents=True)
    actual = {"total": 0, "overall_exit_code": 75}
    (directory / filename).write_text(json.dumps(actual))
    # Historical and similarly named local files are real conflicting controls.
    (directory / "summary.json").write_text('{"total":99,"overall_exit_code":0}')
    summary, code, _ = ensure_review_summary(project)
    assert summary == actual and code == 75


def test_operational_output_rejects_public_directory_before_execution(tmp_path: Path):
    import pytest
    from template_search_project.analysis.review_report import configured_review_paths

    project = _make_isolated_project(tmp_path)
    (project / "review_config.yaml").write_text("review:\n  output: {dir: output/review}\n")
    with pytest.raises(ValueError, match="output/.pipeline"):
        configured_review_paths(project)
    original = (project / "output/review/summary.json").read_bytes()
    with pytest.raises(ValueError, match="output/.pipeline"):
        ensure_review_summary(project)
    assert (project / "output/review/summary.json").read_bytes() == original


def test_actual_git_guard_refuses_forced_runtime_receipts_and_inventory_excludes_them(tmp_path: Path):
    import subprocess
    from infrastructure.project.git_guards import tracked_generated_artifacts
    from infrastructure.core.pipeline.artifacts import collect_stable_output_inventory

    root = tmp_path / "owned-public-git"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=10)
    project = root / "projects/templates/template_search_project"
    runtime = project / "output/.pipeline/review/summary.json"
    runtime.parent.mkdir(parents=True)
    runtime.write_text('{"run_id":"owned-volatile-runtime"}\n')
    public = project / "output/review/REVIEW_REPORT.md"
    public.parent.mkdir(parents=True)
    public.write_text("# Deterministic owned public finding\n")
    runtime_relative = runtime.relative_to(root).as_posix()
    public_relative = public.relative_to(root).as_posix()
    subprocess.run(
        ["git", "-C", str(root), "add", "-f", "--", runtime_relative, public_relative], check=True, timeout=10
    )
    offenders = tracked_generated_artifacts(root)
    assert runtime_relative in offenders and public_relative not in offenders
    inventory = collect_stable_output_inventory(project / "output")
    assert public.absolute() in inventory.files and runtime.absolute() not in inventory.files


def test_public_report_refuses_invalid_current_stage_identity_before_writing(tmp_path: Path):
    import pytest

    project = _make_isolated_project(tmp_path)
    config = project / "review_config.yaml"
    for stages in (
        [{"name": "/invented-private-path"}],
        [{"name": "same"}, {"name": "same"}],
        [{"name": "valid", "enabled": "true"}],
    ):
        config.write_text(json.dumps({"review": {"stages": stages}}))
        with pytest.raises(ValueError, match="stable|boolean"):
            generate_review_report(project, project / "output/review")
        assert not (project / "output/review/REVIEW_REPORT.md").exists()


def test_local_receipt_reader_refuses_ancestor_and_leaf_links_before_launch(tmp_path: Path):
    import errno
    import pytest

    project = _make_isolated_project(tmp_path)
    marker = project / "worker-executed"
    (project / "scripts/review").write_text(
        "from pathlib import Path\nPath(" + repr(str(marker)) + ').write_text("ran")\n'
    )
    outside = tmp_path / "invented-owned-external"
    outside.mkdir()
    original = b"owned external data\n"
    (outside / "preserve").write_bytes(original)
    pipeline = project / "output/.pipeline"
    pipeline.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="confined|real directories"):
        ensure_review_summary(project)
    assert not marker.exists() and (outside / "preserve").read_bytes() == original
    assert not (outside / "review").exists()
    pipeline.unlink()
    directory = pipeline / "review"
    directory.mkdir(parents=True)
    leaf = directory / "summary.json"
    for target in (outside / "preserve", outside / "genuinely-missing-summary"):
        leaf.symlink_to(target)
        with pytest.raises(OSError) as refusal:
            ensure_review_summary(project)
        assert refusal.value.errno == errno.ELOOP
        assert not marker.exists() and (outside / "preserve").read_bytes() == original
        assert not (outside / "genuinely-missing-summary").exists()
        leaf.unlink()


def test_public_report_binds_consumed_regular_output_presence(tmp_path: Path):
    project = _make_isolated_project(tmp_path)
    public = project / "output/review"
    assert generate_review_report(project, public) == 0
    original = (public / "REVIEW_REPORT.md").read_bytes()
    (project / "output/reading_report.md").write_text("# Actual owned reading output\n")
    assert generate_review_report(project, public) == 0
    reading = (public / "REVIEW_REPORT.md").read_bytes()
    assert reading != original
    pdf = project / "output/pdf"
    pdf.mkdir()
    (pdf / "owned_combined.pdf").write_bytes(b"owned presence fixture, not valid PDF acceptance")
    assert generate_review_report(project, public) == 0
    assert (public / "REVIEW_REPORT.md").read_bytes() != reading
    assert b"not run or release acceptance" in (public / "REVIEW_REPORT.md").read_bytes()


def test_public_report_refuses_redirected_output_presence_before_public_write(tmp_path: Path):
    import pytest
    import shutil

    project = _make_isolated_project(tmp_path)
    outside = tmp_path / "invented-owned-output"
    outside.mkdir()
    original = b"owned outside presence data\n"
    (outside / "reading_report.md").write_bytes(original)
    shutil.rmtree(project / "output")
    (project / "output").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="confined|symlink"):
        generate_review_report(project, project / "output/review")
    assert (outside / "reading_report.md").read_bytes() == original
    assert not (outside / "review").exists()


def test_public_report_refuses_directory_as_reading_report_presence(tmp_path: Path):
    import pytest

    project = _make_isolated_project(tmp_path)
    (project / "output/reading_report.md").mkdir()
    with pytest.raises(ValueError, match="regular file"):
        generate_review_report(project, project / "output/review")
    assert not (project / "output/review/REVIEW_REPORT.md").exists()


def test_actual_source_aba_cannot_authorize_findings_under_original_snapshot(tmp_path: Path):
    import subprocess
    import sys
    import template_search_project

    source = Path(template_search_project.__file__).resolve()
    # Nominate the same ordinary isolated SDK that the genuine ABA child loads.
    # The project implementation and test fixture remain the explicit Source copy below.
    provider = Path(
        subprocess.check_output(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                "from pathlib import Path;import infrastructure;print(Path(infrastructure.__file__).resolve(strict=True))",
            ],
            text=True,
            timeout=30,
        ).strip()
    )
    test_source = Path(__file__).resolve()
    program = f"""
import importlib.util,json,sys,hashlib
from pathlib import Path
import infrastructure
assert Path(infrastructure.__file__).resolve()==Path({str(provider)!r})
spec=importlib.util.spec_from_file_location('template_search_project',{str(source)!r},submodule_search_locations=[{str(source.parent)!r}])
assert spec is not None and spec.loader is not None
package=importlib.util.module_from_spec(spec);sys.modules[spec.name]=package;spec.loader.exec_module(package)
test_spec=importlib.util.spec_from_file_location('owned_source_aba_fixture',{str(test_source)!r})
assert test_spec is not None and test_spec.loader is not None
fixture=importlib.util.module_from_spec(test_spec);test_spec.loader.exec_module(fixture)
project=fixture._make_isolated_project(Path({str(tmp_path)!r}))
report=project/'output/review/REVIEW_REPORT.md'
assert fixture.generate_review_report(project,report.parent)==0
baseline=report.read_bytes(); assert b'Bibliography completeness:** passed' in baseline
bib=project/'manuscript/references.bib';original=bib.read_bytes()
events=[]
def actual_open_control(event,args):
    if event!='open' or not isinstance(args[0],(str,bytes)):return
    path=Path(args[0]); frozen=any(part.startswith('search-report-inputs-') for part in path.parts)
    if not frozen:return
    if path.name=='references.bib' and not events:
        bib.write_bytes(b'@article{{wrong_existing_source,title={{Owned wrong bibliography}},}}\\n')
        assert bib.read_bytes()!=original
        events.append('actual-source-mutated-before-frozen-validator-bib-read')
    elif path.name=='01_intro.md' and len(events)==1:
        bib.write_bytes(original);assert bib.read_bytes()==original
        events.append('actual-source-restored-before-final-original-source-capture')
sys.addaudithook(actual_open_control)
try:fixture.generate_review_report(project,report.parent)
except ValueError as error:assert 'source/data changed' in str(error)
else:raise AssertionError('actual source ABA must not authorize a current report')
assert len(events)==2 and bib.read_bytes()==original and report.read_bytes()==baseline
print(json.dumps({{'events':events,'original_sha256':hashlib.sha256(original).hexdigest(),
                 'final_sha256':hashlib.sha256(bib.read_bytes()).hexdigest(),'report_preserved':True}}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", program], cwd=tmp_path, capture_output=True, text=True, timeout=90, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    observations = json.loads(result.stdout.splitlines()[-1])
    assert len(observations["events"]) == 2
    assert observations["original_sha256"] == observations["final_sha256"]
    assert observations["report_preserved"] is True


def test_current_source_named_output_subdirectory_is_captured_and_audited(tmp_path: Path):
    project = _make_isolated_project(tmp_path)
    public = project / "output/review"
    nested = project / "src/output"
    nested.mkdir()
    source = nested / "owned_source.py"
    source.write_text("from infrastructure.core.logging.utils import get_logger\n")
    assert generate_review_report(project, public) == 0
    admitted = (public / "REVIEW_REPORT.md").read_bytes()
    assert b"Infrastructure import validity:** passed" in admitted
    source.write_text("import infrastructure.actual_nonexistent_nested_output_control\n")
    assert generate_review_report(project, public) == 0
    changed = (public / "REVIEW_REPORT.md").read_bytes()
    assert b"Infrastructure import validity:** failed" in changed and changed != admitted
    before_digest = re.search(rb"snapshot SHA-256:\*\* `([0-9a-f]{64})`", admitted).group(1)
    after_digest = re.search(rb"snapshot SHA-256:\*\* `([0-9a-f]{64})`", changed).group(1)
    assert before_digest != after_digest

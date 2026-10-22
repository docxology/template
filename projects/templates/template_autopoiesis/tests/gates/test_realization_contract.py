"""Actual bounded child producers, source/export custody, and fail-closed controls."""

from __future__ import annotations

import json
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
import numpy as np

from template_autopoiesis.core.grammar import KNOWN_DOMAINS
from template_autopoiesis.gates.child_execution import execute_child
from template_autopoiesis.gates.child_results import verify_analysis_results
from template_autopoiesis.gates.materialize import materialize
from template_autopoiesis.gates.realization_contract import realize_selected_children, selected_specs
from template_autopoiesis.gates.sealing import seal_verified_child

PROJECT = Path(__file__).resolve().parents[2]


@pytest.fixture
def source_project(tmp_path: Path) -> Path:
    project = tmp_path / "source_project"
    shutil.copytree(
        PROJECT,
        project,
        ignore=shutil.ignore_patterns("output", ".venv", "__pycache__", ".pytest_cache", ".coverage*", "*.egg-info"),
    )
    return project


def test_manifest_selects_one_exact_cell_per_declared_domain_and_honors_filters(source_project: Path) -> None:
    selected = selected_specs(source_project)
    assert tuple(spec.primitive_domain for spec in selected) == KNOWN_DOMAINS
    config = source_project / "manuscript/config.yaml"
    payload = yaml.safe_load(config.read_text())
    payload["project_config"]["autopoiesis"]["archetype_filters"] = {
        "primitive_domain": ["graph", "optimization"],
        "track": ["empirical"],
        "section_set": ["minimal"],
    }
    config.write_text(yaml.safe_dump(payload, sort_keys=False))
    selected = selected_specs(source_project)
    assert tuple(spec.primitive_domain for spec in selected) == ("optimization", "graph")
    assert all(
        dict(spec.selections)["track"] == "empirical" and dict(spec.selections)["section_set"] == "minimal"
        for spec in selected
    )
    assert len(selected_specs(source_project, single=True)) == 1


def test_unknown_selected_domains_and_unbounded_grammar_cells_fail_closed(source_project: Path) -> None:
    config = source_project / "manuscript/config.yaml"
    payload = yaml.safe_load(config.read_text())
    grammar = payload["project_config"]["autopoiesis"]
    grammar["slots"][0]["options"].append("unsupported")
    config.write_text(yaml.safe_dump(payload, sort_keys=False))
    with pytest.raises(ValueError, match="unsupported primitive domain"):
        selected_specs(source_project)
    grammar["slots"][0]["options"].pop()
    grammar["slots"].append({"name": "large_dimension", "options": [str(index) for index in range(100)]})
    config.write_text(yaml.safe_dump(payload, sort_keys=False))
    with pytest.raises(ValueError, match="at most 10000"):
        selected_specs(source_project)


def test_standalone_materialization_is_real_and_missing_platform_execution_blocks_75(
    source_project: Path, tmp_path: Path
) -> None:
    script = (
        "import sys,runpy,importlib.util\nfrom pathlib import Path\n"
        "def load_package(name,origin):\n"
        "    spec=importlib.util.spec_from_file_location(name,origin,submodule_search_locations=[str(Path(origin).parent)])\n"
        "    assert spec is not None and spec.loader is not None\n"
        "    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)\n"
        f"load_package('numpy',{str(Path(np.__file__).resolve())!r})\n"
        f"load_package('yaml',{str(Path(yaml.__file__).resolve())!r})\n"
        f"load_package('template_autopoiesis',{str(source_project / 'src/template_autopoiesis/__init__.py')!r})\n"
        "assert importlib.util.find_spec('infrastructure') is None; "
        "from template_autopoiesis.gates.materialize import materialize; "
        "from template_autopoiesis.gates.realization_contract import selected_specs; "
        f"project=Path({str(source_project)!r}); "
        f"result=materialize(selected_specs(project,single=True)[0],Path({str(tmp_path / 'standalone_children')!r}),project); "
        "assert (result.root/'analysis.py').is_file(); "
        "sys.argv=['realize_child_full.py','--project-root',str(project)]; "
        f"runpy.run_path({str(source_project / 'scripts/realize_child_full.py')!r},run_name='__main__')"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 75, result.stderr
    assert "platform 4.1.0" in result.stderr
    receipt = json.loads((source_project / "output/.pipeline/child_realization/single.json").read_text())
    assert receipt["schema_version"] == "autopoiesis/selected-child-execution/2"
    assert receipt["status"] == "blocked" and receipt["executed_children"] == []
    assert not (source_project / "output/.pipeline/child_realization/workspaces").exists()


def test_every_selected_child_really_runs_and_exports_verified_domain_results(source_project: Path) -> None:
    history = source_project / "output/children/historical.txt"
    history.parent.mkdir(parents=True)
    history.write_bytes(b"preserve published evidence exactly\n")
    receipt_path = realize_selected_children(source_project)
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "passed" and receipt["mode"] == "core"
    assert receipt["selected_count"] == 5 and receipt["declared_filtered_cells"] == 360
    assert receipt["selection_scope"] == "one-per-selected-domain" and receipt["child_pdf_rendering"] == "unsupported"
    assert {record["domain"] for record in receipt["executed_children"]} == set(KNOWN_DOMAINS)
    assert receipt["schema_version"] == "autopoiesis/selected-child-execution/2"
    assert receipt["honesty"]["source_sha256"] and receipt["source_sha256"]
    generator = receipt["active_generator_custody"]
    assert generator["schema_version"] == "autopoiesis/active-generator-custody/1"
    assert generator["binding_kind"] == "source-checkout" and generator["files"]
    assert generator["bytecode_binding"] == "loaded-baseline"
    assert receipt["platform_custody"]["files"]
    for record in receipt["executed_children"]:
        assert record["status"] == "passed"
        assert record["tests"]["returncode"] == record["analysis"]["returncode"] == 0
        assert not record["tests"]["timed_out"] and not record["analysis"]["timed_out"]
        assert record["source_sha256"] == record["export_source_sha256"]
        exported = receipt_path.parent / "exports" / record["export_name"]
        assert verify_analysis_results(exported, record["domain"])["status"] == "passed"
        coverage = json.loads((exported / "coverage.json").read_text())
        assert coverage["totals"]["percent_covered"] >= 90
        assert '"resource_limits"' in record["analysis"]["stdout"]
    assert history.read_bytes() == b"preserve published evidence exactly\n"


def test_single_child_entrypoint_runs_its_selected_child_and_current_sealing_only(source_project: Path) -> None:
    realized = subprocess.run(
        [sys.executable, str(PROJECT / "scripts/realize_child_full.py"), "--project-root", str(source_project)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert realized.returncode == 0, realized.stderr
    receipt_path = source_project / "output/.pipeline/child_realization/single.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "passed" and receipt["selected_count"] == 1
    assert receipt["selection_scope"] == "one-selected-child"
    sealed = subprocess.run(
        [sys.executable, str(PROJECT / "scripts/04_seal.py"), "--project-root", str(source_project)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert sealed.returncode == 0, sealed.stderr
    exported = receipt_path.parent / "exports" / receipt["executed_children"][0]["export_name"]
    assert (exported / "seal.json").is_file()
    assert not (source_project / "output/children").exists()


def test_real_child_analysis_failure_fails_parent_after_real_child_tests_pass(source_project: Path) -> None:
    kernel = source_project / "src/template_autopoiesis/primitives/optimization.py"
    kernel.write_text(
        kernel.read_text()
        + '\nimport sys\nif sys.argv[0] == "analysis.py":\n    raise RuntimeError("required analysis negative control")\n'
    )
    result = subprocess.run(
        [sys.executable, str(PROJECT / "scripts/realize_archetypes.py"), "--project-root", str(source_project)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 1
    receipt = json.loads((source_project / "output/.pipeline/child_realization/archetypes.json").read_text())
    record = receipt["executed_children"][0]
    assert receipt["status"] == "failed" and "analysis producer failed" in receipt["diagnostic"]
    assert record["tests"]["returncode"] == 0 and record["analysis"]["returncode"] != 0
    assert "required analysis negative control" in record["analysis"]["stderr"]
    assert not (
        source_project / "output/.pipeline/child_realization/exports" / record.get("export_name", "absent")
    ).exists()


def test_real_child_domain_test_failure_fails_parent_and_preserves_diagnostics(source_project: Path) -> None:
    oracle = source_project / "tests/primitives/test_primitives_optimization.py"
    oracle.write_text(
        oracle.read_text()
        + '\ndef test_required_domain_negative_control():\n    assert False, "required domain negative control"\n'
    )
    with pytest.raises(ValueError, match="tests producer failed"):
        realize_selected_children(source_project)
    receipt = json.loads((source_project / "output/.pipeline/child_realization/archetypes.json").read_text())
    assert receipt["status"] == "failed"
    record = receipt["executed_children"][0]
    assert record["tests"]["returncode"] != 0 and "required domain negative control" in record["tests"]["stdout"]
    assert "analysis" not in record


def test_missing_required_oracle_does_not_produce_a_passing_empty_child(source_project: Path) -> None:
    (source_project / "tests/primitives/test_primitives_optimization.py").unlink()
    with pytest.raises(ValueError, match="regular existing"):
        realize_selected_children(source_project)
    receipt = json.loads((source_project / "output/.pipeline/child_realization/archetypes.json").read_text())
    assert receipt["status"] == "failed"


def test_independent_results_reject_tampered_actual_child_output(tmp_path: Path) -> None:
    result = materialize(selected_specs(PROJECT, single=True)[0], tmp_path, PROJECT)
    outcome = execute_child(result.root, "analysis.py")
    assert outcome.returncode == 0
    verify_analysis_results(result.root, result.files and selected_specs(PROJECT, single=True)[0].primitive_domain)
    path = result.root / "output/data/analysis_results.json"
    payload = json.loads(path.read_text())
    first = next(iter(payload["results"]))
    payload["results"][first] = {"invented": 0}
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="computation mismatch"):
        verify_analysis_results(result.root, payload["domain"])


def test_actual_child_timeout_and_file_resource_caps_are_enforced(tmp_path: Path) -> None:
    started = tmp_path / "cpu-body-started"
    (tmp_path / "infinite.py").write_text(
        "from pathlib import Path\nPath('cpu-body-started').write_text('body ran')\nwhile True: pass\n"
    )
    timeout = execute_child(tmp_path, "infinite.py", 60, cpu_seconds=1)
    assert started.read_text() == "body ran"
    assert timeout.original_returncode == -signal.SIGXCPU
    assert not timeout.timed_out and not timeout.custody_refused
    assert '"cpu_seconds": 1' in timeout.stdout
    (tmp_path / "oversize.py").write_text(
        "from pathlib import Path\nPath('oversize.bin').write_bytes(b'x' * 16777217)\n"
    )
    outcome = execute_child(tmp_path, "oversize.py")
    assert outcome.returncode != 0 and (tmp_path / "oversize.bin").stat().st_size <= 16777216


def test_actual_child_receives_only_the_explicit_credential_free_environment(tmp_path: Path) -> None:
    (tmp_path / "environment.py").write_text("import os,json\nprint(json.dumps(sorted(os.environ)))\n")
    outcome = execute_child(tmp_path, "environment.py")
    assert outcome.returncode == 0
    names = json.loads(outcome.stdout.splitlines()[-1])
    assert set(names) <= {
        "PATH",
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "LC_CTYPE",
        "TEMPLATE_BOUNDED_RUN_IDS",
        "__CF_USER_TEXT_ENCODING",  # macOS Python adds this runtime encoding hint.
    }


@pytest.mark.parametrize("script", ["../outside.py", "/absolute.py", "nested/../../outside.py"])
def test_execution_rejects_unconfined_script_paths(tmp_path: Path, script: str) -> None:
    with pytest.raises(ValueError, match="confined"):
        execute_child(tmp_path, script)


def test_runtime_export_and_artifact_symlink_components_are_rejected(source_project: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    output = source_project / "output"
    output.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        realize_selected_children(source_project)
    assert not list(outside.iterdir())


def test_seal_binds_actual_spec_hash_and_refuses_changed_source(tmp_path: Path) -> None:
    spec = selected_specs(PROJECT, single=True)[0]
    result = materialize(spec, tmp_path, PROJECT)
    seal_path = seal_verified_child(result.root)
    seal = json.loads(seal_path.read_text())
    assert seal["spec_hash"] == spec.spec_hash and seal["tree_hash"] == result.tree_hash
    seal_path.unlink()
    (result.root / "analysis.py").write_text("raise RuntimeError('changed source')\n")
    with pytest.raises(ValueError, match="refusing to seal"):
        seal_verified_child(result.root)
    assert not seal_path.exists()


@pytest.mark.parametrize("cpu_seconds", [0, -1, 61, True, 1.5])
def test_child_cpu_budget_refuses_invalid_invocations_before_launch(tmp_path: Path, cpu_seconds: Any) -> None:
    marker = tmp_path / "executed"
    (tmp_path / "marker.py").write_text("from pathlib import Path\nPath('executed').write_text('body ran')\n")
    with pytest.raises(ValueError, match="child CPU seconds"):
        execute_child(tmp_path, "marker.py", cpu_seconds=cpu_seconds)
    assert not marker.exists()


def test_one_second_whole_deadline_does_not_claim_unlaunched_cpu_acceptance(tmp_path: Path) -> None:
    started = tmp_path / "whole-body-started"
    (tmp_path / "infinite.py").write_text(
        "from pathlib import Path\nPath('whole-body-started').write_text('body ran')\nwhile True: pass\n"
    )
    result = execute_child(tmp_path, "infinite.py", 1)
    assert result.timed_out or result.returncode != 0
    if result.original_returncode is None:
        assert result.timed_out and not result.stdout and not started.exists()
    if started.exists():
        assert started.read_text() == "body ran"
    # A launched child may expire before its bootstrap/banner or actual body.
    # Only the separate original -SIGXCPU + body proof accepts the CPU limit.


def test_figure_package_exports_keep_the_actual_implementation_identity() -> None:
    import importlib

    package = importlib.import_module("template_autopoiesis.manuscript")
    figures = importlib.import_module("template_autopoiesis.manuscript.manuscript_figures")
    for name in package._FIGURE_EXPORTS:
        assert getattr(package, name) is getattr(figures, name)
    with pytest.raises(AttributeError):
        getattr(package, "invented_figure_api")
    assert set(package.__all__) <= set(dir(package))

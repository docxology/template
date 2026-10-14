"""Real selected-provider, shadow-package, and isolated review child controls."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import infrastructure
import pytest

from template_search_project.analysis.analysis import audit_infrastructure_imports
from template_search_project.analysis.provider_paths import platform_package_root
from template_search_project.analysis.review_report import collect_infra_imports, ensure_review_summary

PROJECT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.timeout(420)


def _provider_identity() -> dict[str, str]:
    origin = Path(infrastructure.__file__).resolve(strict=True)
    return {
        "origin": str(origin),
        "version": importlib.metadata.version("research-project-template"),
        "init_sha256": hashlib.sha256(origin.read_bytes()).hexdigest(),
    }


def _ambient_startup_control(directory: Path) -> tuple[dict[str, str], Path]:
    directory.mkdir()
    marker = directory / "startup-executed"
    (directory / "sitecustomize.py").write_text(
        f"from pathlib import Path; Path({str(marker)!r}).write_text('startup executed')\n"
    )
    environment = dict(os.environ, PYTHONPATH=str(directory))
    ordinary = subprocess.run(
        [sys.executable, "-c", "pass"],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert ordinary.returncode == 0, ordinary.stdout + ordinary.stderr
    assert marker.read_text() == "startup executed", "ordinary-child startup control was not live"
    marker.unlink()
    return environment, marker


def _standalone_project(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "standalone"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    for filename in ("review", "zz_generate_review_report.py", "_search_sdk_bootstrap.py"):
        shutil.copy2(PROJECT / "scripts" / filename, scripts / filename)
    shutil.copytree(
        PROJECT / "src/template_search_project",
        project / "src/template_search_project",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    # Observe the real selected provider inside the genuine own-package import.
    # Append observation only; preserve the actual initializer and domain modules.
    initializer = project / "src/template_search_project/__init__.py"
    with initializer.open("a") as stream:
        stream.write(
            "\nimport hashlib as _probe_hashlib, importlib.metadata as _probe_metadata\n"
            "import json as _probe_json, os as _probe_os, infrastructure as _probe_infra\n"
            "from pathlib import Path as _ProbePath\n"
            "_probe_origin = _ProbePath(_probe_infra.__file__).resolve(strict=True)\n"
            "_probe_directory = _ProbePath(__file__).resolve().parents[2] / 'provider-observations'\n"
            "_probe_directory.mkdir(exist_ok=True)\n"
            "(_probe_directory / f'{_probe_os.getpid()}.json').write_text(_probe_json.dumps({"
            "'origin': str(_probe_origin),"
            "'version': _probe_metadata.version('research-project-template'),"
            "'init_sha256': _probe_hashlib.sha256(_probe_origin.read_bytes()).hexdigest()}))\n"
        )
    marker = tmp_path / "own-src-provider-substituted"
    shadow = project / "src/infrastructure"
    shadow.mkdir()
    (shadow / "__init__.py").write_text(
        f"from pathlib import Path; Path({str(marker)!r}).write_text('shadow executed')\nraise SystemExit(78)\n"
    )
    # This owned shadow really substitutes the provider if preload is removed.
    control = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);import infrastructure",
            str(project / "src"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert control.returncode == 78, control.stdout + control.stderr
    assert marker.read_text() == "shadow executed", "shadow-package control was not live"
    marker.unlink()
    return project, marker


def _assert_provider_observations(project: Path, *, minimum: int) -> None:
    observations = sorted((project / "provider-observations").glob("*.json"))
    assert len(observations) >= minimum
    expected = _provider_identity()
    assert expected["version"] == "4.0.1"
    assert all(json.loads(path.read_text()) == expected for path in observations)


def test_inventories_use_selected_provider_for_both_import_forms_and_reject_missing_modules(tmp_path):
    assert platform_package_root() == Path(infrastructure.__file__).resolve(strict=True).parent
    src = tmp_path / "src"
    src.mkdir()
    fixtures = {
        "valid_from.py": "from infrastructure.core.logging.utils import get_logger\n",
        "valid_plain.py": "import os, infrastructure.core.logging.utils as logging\n",
        "valid_root.py": "import infrastructure\n",
        "missing_from.py": "from infrastructure.missing_portability_control import value\n",
        "missing_plain.py": "import infrastructure.missing_plain_control as missing\n",
        "relative.py": "from .infrastructure.core.logging.utils import get_logger\n",
    }
    for filename, source in fixtures.items():
        (src / filename).write_text(source)
    inventory = collect_infra_imports(tmp_path)
    assert inventory == {
        "infrastructure.core.logging.utils": {"valid_from.py", "valid_plain.py"},
        "infrastructure": {"valid_root.py"},
    }
    result = audit_infrastructure_imports(tmp_path)
    assert result.exit_code == 1
    assert result.details["issues"] == [
        "missing_from.py imports non-existent infra module: infrastructure.missing_portability_control",
        "missing_plain.py imports non-existent infra module: infrastructure.missing_plain_control",
    ]
    assert result.details["infrastructure_imports"]["infrastructure.core.logging.utils"] == [
        "valid_from.py",
        "valid_plain.py",
    ]
    assert "relative.py" not in str(result.details)


@pytest.mark.parametrize("script", ["review", "zz_generate_review_report.py"])
def test_direct_review_shims_preload_selected_provider_before_own_src(tmp_path, script):
    project, shadow_marker = _standalone_project(tmp_path)
    environment, startup_marker = _ambient_startup_control(tmp_path / "ambient")
    command = [
        sys.executable,
        "-I",
        "-c",
        "import runpy,sys;runpy.run_path(sys.argv[1],run_name='provider_portability_probe')",
        str(project / "scripts" / script),
    ]
    result = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_provider_observations(project, minimum=1)
    assert not shadow_marker.exists() and not startup_marker.exists()


def test_review_child_uses_selected_provider_without_ambient_startup_code(tmp_path, monkeypatch):
    project = tmp_path / "standalone"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    review = scripts / "review"
    review.write_text(
        "import hashlib,importlib.metadata,json\n"
        "from pathlib import Path\n"
        "import infrastructure\n"
        "origin=Path(infrastructure.__file__).resolve(strict=True)\n"
        "directory=Path.cwd()/'output/.pipeline/review'\n"
        "directory.mkdir(parents=True,exist_ok=True)\n"
        "summary={'total':1,'passed':1,'failed':0,'skipped':0,'overall_exit_code':0,"
        "'provider':{'origin':str(origin),"
        "'version':importlib.metadata.version('research-project-template'),"
        "'init_sha256':hashlib.sha256(origin.read_bytes()).hexdigest()}}\n"
        "(directory/'summary.json').write_text(json.dumps(summary))\n"
    )
    environment, marker = _ambient_startup_control(tmp_path / "ambient")
    monkeypatch.setenv("PYTHONPATH", environment["PYTHONPATH"])
    summary, exit_code, _ = ensure_review_summary(project, project / "output/.pipeline/review")
    assert exit_code == 0 and not marker.exists()
    assert summary["provider"] == _provider_identity()
    assert summary["provider"]["version"] == "4.0.1"


def test_real_standalone_review_runs_infra_and_custom_stages_and_rejects_domain_fault(tmp_path):
    project, shadow_marker = _standalone_project(tmp_path)
    (project / "src/valid.py").write_text("import infrastructure.core.logging.utils as logging\n")
    manuscript = project / "manuscript"
    manuscript.mkdir()
    (manuscript / "references.bib").write_text(
        "@article{example,author={Example, Ada},title={Public fixture},journal={Example Journal},year={2024}}\n"
    )
    (project / "review_config.yaml").write_text(
        "review:\n  stages:\n"
        "  - name: bibtex_validation\n    enabled: true\n"
        "    infra_module: infrastructure.reference.citation.cli\n"
        "    command: validate\n    args: [manuscript/references.bib, --strict]\n"
        "  - name: infrastructure_usage\n    enabled: true\n    stage_type: custom\n"
        "  output: {dir: output/.pipeline/review, summary_json: summary.json}\n"
    )
    environment, startup_marker = _ambient_startup_control(tmp_path / "ambient")
    command = [
        sys.executable,
        "-I",
        str(project / "scripts/review"),
        "--project-root",
        str(project),
        "--timeout",
        "150",
        "--stage-timeout",
        "60",
    ]
    positive = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=180)
    assert positive.returncode == 0, positive.stdout + positive.stderr
    summary = json.loads((project / "output/.pipeline/review/summary.json").read_text())
    assert {key: summary[key] for key in ("total", "passed", "failed", "skipped", "overall_exit_code")} == {
        "total": 2,
        "passed": 2,
        "failed": 0,
        "skipped": 0,
        "overall_exit_code": 0,
    }
    assert summary["complete"] and summary["expected_stages"] == ["bibtex_validation", "infrastructure_usage"]
    assert summary["execution"]["original_exit_code"] == 0 and not summary["execution"]["timed_out"]
    # Direct shim and the actual custom bootstrap both imported the own package.
    _assert_provider_observations(project, minimum=2)
    assert not shadow_marker.exists() and not startup_marker.exists()
    (project / "src/missing.py").write_text("import infrastructure.missing_portability_control\n")
    negative = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=180)
    assert negative.returncode == 1, negative.stdout + negative.stderr
    failed = json.loads((project / "output/.pipeline/review/stage_infrastructure_usage.json").read_text())
    assert failed["exit_code"] == 1 and not failed["success"]
    assert any("missing_portability_control" in issue for issue in failed["result"]["details"]["issues"])
    _assert_provider_observations(project, minimum=4)
    assert not shadow_marker.exists() and not startup_marker.exists()

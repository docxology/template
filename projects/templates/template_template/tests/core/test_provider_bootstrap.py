"""Actual SDK selection and real own-domain execution in native isolated children."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import infrastructure
import pytest
import yaml

PROJECT = Path(__file__).resolve().parents[2]
PACKAGE = "template_template"
SDK_ORIGIN = Path(infrastructure.__file__).resolve(strict=True)
SDK_DIGEST = hashlib.sha256(SDK_ORIGIN.read_bytes()).hexdigest()


_testing = yaml.safe_load((PROJECT / "manuscript/config.yaml").read_text()).get("testing", {})
DOMAIN_EXPECTATION = {
    key: _testing.get(key, 0) for key in ("max_test_failures", "max_infra_test_failures", "max_project_test_failures")
}
DOMAIN_PROGRAM = (
    "from template_template import analyze_test_coverage_config;"
    "config=analyze_test_coverage_config(project);assert config is not None and config.project_name==project.name;"
    "print(json.dumps({'provider_origin':str(Path(sdk.__file__).resolve()),'provider_version':sdk.__version__,"
    "'domain':{key:getattr(config,key) for key in "
    "('max_test_failures','max_infra_test_failures','max_project_test_failures')}}));"
)
WRONG_MODULE = "template_template.core.paths"
ALIASED_MODULE = "template_template.core.introspection"


def _copy_project(tmp_path: Path) -> Path:
    project = tmp_path / PACKAGE
    for name in ("src", "scripts", "manuscript"):
        shutil.copytree(PROJECT / name, project / name, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(PROJECT / "pyproject.toml", project / "pyproject.toml")
    return project


def _native(project: Path, program: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-c", program],
        cwd=project.parent,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


def _bootstrap_program(project: Path) -> str:
    return (
        "import sys,importlib,importlib.util,hashlib,json;from pathlib import Path;"
        f"project=Path({str(project)!r});"
        "sys.path[:0]=[str(project),str(project/'src'),str(project/'scripts')];"
        "before=sys.path[:];"
        "spec=importlib.util.spec_from_file_location('owned_bootstrap',project/'scripts/_bootstrap.py');"
        "assert spec is not None and spec.loader is not None;"
        "bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap);"
        "sdk=bootstrap.bootstrap_project(project);"
        f"assert Path(sdk.__file__).resolve()==Path({str(SDK_ORIGIN)!r});"
        "assert sdk.__version__=='4.0.2';"
        "assert hashlib.sha256(Path(sdk.__file__).read_bytes()).hexdigest()=="
        f"{SDK_DIGEST!r};"
        "assert sys.path==before;"
        f"own=importlib.import_module({PACKAGE!r});"
        f"assert Path(own.__file__).resolve()==project/'src'/{PACKAGE!r}/'__init__.py';"
    )


def test_canonical_project_bootstrap_keeps_genuine_selected_runtime_sdk() -> None:
    """A prepared project-local environment must retain its real installed SDK."""
    actual = _native(PROJECT, _bootstrap_program(PROJECT) + DOMAIN_PROGRAM)
    assert actual.returncode == 0, actual.stderr or actual.stdout
    rows = [json.loads(line) for line in actual.stdout.splitlines() if line.startswith("{")]
    assert len(rows) == 1 and rows[0]["provider_origin"] == str(SDK_ORIGIN)
    assert rows[0]["provider_version"] == "4.0.2"
    assert rows[0]["domain"] == DOMAIN_EXPECTATION


def test_cached_authored_own_namespace_cannot_supply_platform_sdk(tmp_path: Path) -> None:
    """A real own module cached under the provider fullname must be refused."""
    project = _copy_project(tmp_path)
    program = (
        _bootstrap_program(project)
        + f"sys.modules['infrastructure']=importlib.import_module({PACKAGE!r});"
        + "\ntry:\n"
        + "    bootstrap.bootstrap_project(project)\n"
        + "except ImportError as error:\n"
        + "    assert 'own project source' in str(error)\n"
        + "    print('actual authored cached provider refused')\n"
        + "else:\n"
        + "    raise AssertionError('authored own namespace admitted as platform SDK')\n"
    )
    actual = _native(project, program)
    assert actual.returncode == 0, actual.stderr or actual.stdout
    assert "actual authored cached provider refused" in actual.stdout


@pytest.mark.parametrize("shadow_location", ["own-root", "own-src"])
def test_selected_sdk_precedes_actual_own_shadow_and_executes_domain(tmp_path: Path, shadow_location: str) -> None:
    project = _copy_project(tmp_path)
    marker = tmp_path / "actual-shadow-started"
    location = project if shadow_location == "own-root" else project / "src"
    shadow = location / "infrastructure"
    shadow.mkdir()
    shadow.joinpath("__init__.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('owned startup observed')\n"
        "raise RuntimeError('owned shadow executed')\n",
        encoding="utf-8",
    )
    # First prove the original owned package executes under ordinary selected import.
    positive = _native(project, f"import sys;sys.path.insert(0,{str(location)!r});import infrastructure")
    assert positive.returncode == 1 and "owned shadow executed" in positive.stderr
    assert marker.read_text() == "owned startup observed"
    marker.unlink()
    actual = _native(project, _bootstrap_program(project) + DOMAIN_PROGRAM)
    assert actual.returncode == 0, actual.stderr or actual.stdout
    rows = [json.loads(line) for line in actual.stdout.splitlines() if line.startswith("{")]
    assert len(rows) == 1 and rows[0]["provider_origin"] == str(SDK_ORIGIN)
    assert rows[0]["provider_version"] == "4.0.2"
    assert rows[0]["domain"] == DOMAIN_EXPECTATION
    assert not marker.exists()


def test_cached_canonical_modules_remain_valid_but_real_wrong_own_alias_is_refused(tmp_path: Path) -> None:
    project = _copy_project(tmp_path)
    program = (
        _bootstrap_program(project)
        + DOMAIN_PROGRAM
        + (
            "bootstrap.bootstrap_project(project);"
            f"wrong=importlib.import_module({WRONG_MODULE!r});"
            f"sys.modules[{ALIASED_MODULE!r}]=wrong;"
            "try:\n"
            "    bootstrap.bootstrap_project(project)\n"
            "except ImportError as error:\n"
            "    assert 'canonical own' in str(error)\n"
            "    print('actual wrong own alias refused')\n"
            "else:\n"
            "    raise AssertionError('actual wrong own alias admitted')\n"
        )
    )
    # Start multiline exception syntax on a fresh line after the actual original calls.
    program = program.replace("try:\n", "\ntry:\n")
    actual = _native(project, program)
    assert actual.returncode == 0, actual.stderr or actual.stdout
    assert "actual wrong own alias refused" in actual.stdout

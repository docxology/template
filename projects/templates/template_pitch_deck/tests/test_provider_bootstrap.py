"""Actual SDK selection and real own-domain execution in native isolated children."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tomllib
from functools import cache
from pathlib import Path

import pytest
import yaml

PROJECT = Path(__file__).resolve().parents[1]
PLATFORM_VERSION = tomllib.loads((PROJECT / "pyproject.toml").read_text())["tool"]["template"]["platform_version"]
PACKAGE = "template_pitch_deck"


_raw = yaml.safe_load((PROJECT / "manuscript/deck_content_short.yaml").read_text())
DOMAIN_EXPECTATION = {"title": _raw.get("title", ""), "slides": len(_raw["slides"])}
DOMAIN_PROGRAM = (
    "from template_pitch_deck.content_loader import load_deck_yaml,raw_deck_texts;"
    "raw=load_deck_yaml(project/'manuscript/deck_content_short.yaml');texts=raw_deck_texts(raw);"
    "assert texts['title']==raw.get('title','') and len(raw['slides'])>0;"
    "print(json.dumps({'provider_origin':str(Path(sdk.__file__).resolve()),'provider_version':sdk.__version__,"
    "'domain':{'title':texts['title'],'slides':len(raw['slides'])}}));"
)
WRONG_MODULE = "template_pitch_deck.token_resolution"
ALIASED_MODULE = "template_pitch_deck.content_loader"


def _copy_project(tmp_path: Path) -> Path:
    project = tmp_path / PACKAGE
    for name in ("src", "scripts", "manuscript"):
        shutil.copytree(PROJECT / name, project / name, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(PROJECT / "pyproject.toml", project / "pyproject.toml")
    return project


def _native(project: Path, program: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", program],
        cwd=project.parent,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


@cache
def _selected_sdk_identity() -> tuple[Path, str]:
    """Observe the isolated interpreter SDK during a test, never collection."""
    # A pipeline parent can import frozen Source; its cached module is not the
    # provider selected by a new isolated child of the same interpreter.
    observation = _native(
        PROJECT,
        "import hashlib,json,infrastructure;from pathlib import Path;"
        "origin=Path(infrastructure.__file__).resolve(strict=True);"
        "print(json.dumps({'origin':str(origin),'version':infrastructure.__version__,"
        "'sha256':hashlib.sha256(origin.read_bytes()).hexdigest()}))",
    )
    assert observation.returncode == 0, observation.stderr or observation.stdout
    identity = json.loads(observation.stdout)
    assert identity["version"] == PLATFORM_VERSION
    return Path(identity["origin"]), identity["sha256"]


def _bootstrap_program(project: Path) -> str:
    sdk_origin, sdk_digest = _selected_sdk_identity()
    return (
        "import sys,importlib,importlib.util,hashlib,json;from pathlib import Path;"
        f"project=Path({str(project)!r});"
        "sys.path[:0]=[str(project),str(project/'src'),str(project/'scripts')];"
        "before=sys.path[:];"
        "spec=importlib.util.spec_from_file_location('owned_bootstrap',project/'scripts/_bootstrap.py');"
        "assert spec is not None and spec.loader is not None;"
        "bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap);"
        "sdk=bootstrap.bootstrap_project(project);"
        f"assert Path(sdk.__file__).resolve()==Path({str(sdk_origin)!r});"
        f"assert sdk.__version__=={PLATFORM_VERSION!r};"
        "assert hashlib.sha256(Path(sdk.__file__).read_bytes()).hexdigest()=="
        f"{sdk_digest!r};"
        "assert sys.path==before;"
        f"own=importlib.import_module({PACKAGE!r});"
        f"assert Path(own.__file__).resolve()==project/'src'/{PACKAGE!r}/'__init__.py';"
    )


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
    assert len(rows) == 1 and rows[0]["provider_origin"] == str(_selected_sdk_identity()[0])
    assert rows[0]["provider_version"] == PLATFORM_VERSION
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


@pytest.mark.parametrize("declaration", ['"0.0.0"', "false"])
def test_bootstrap_refuses_a_different_or_malformed_declared_sdk(tmp_path: Path, declaration: str) -> None:
    project = _copy_project(tmp_path)
    metadata = project / "pyproject.toml"
    original = metadata.read_text()
    changed = original.replace(f'platform_version = "{PLATFORM_VERSION}"', f"platform_version = {declaration}")
    assert changed != original
    metadata.write_text(changed)
    program = (
        "import importlib.util,sys;from pathlib import Path;"
        f"project=Path({str(project)!r});"
        "spec=importlib.util.spec_from_file_location('owned_bootstrap',project/'scripts/_bootstrap.py');"
        "assert spec is not None and spec.loader is not None;"
        "bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap);"
        "before=sys.path[:];\n"
        "try:\n"
        "    bootstrap.bootstrap_project(project)\n"
        "except ImportError as error:\n"
        "    assert 'declared platform' in str(error)\n"
        "    assert sys.path == before\n"
        "    print('declared SDK refused')\n"
        "else:\n"
        "    raise AssertionError('different or malformed SDK declaration admitted')\n"
    )
    actual = _native(project, program)
    assert actual.returncode == 0, actual.stderr or actual.stdout
    assert actual.stdout.strip() == "declared SDK refused"

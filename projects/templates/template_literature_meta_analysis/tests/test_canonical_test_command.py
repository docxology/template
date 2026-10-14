"""Bind checkout-specific test guidance to genuine standalone source execution."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import sys
from pathlib import Path

import pytest
from defusedxml import ElementTree as ET

import infrastructure

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MONOREPO_TEST_COMMAND = (
    "uv run python scripts/pipeline/stage_01_test.py "
    "--project templates/template_literature_meta_analysis --project-only"
)
STANDALONE_TEST_COMMAND = "python -I -m pytest tests/ --cov=src --cov-fail-under=90"
PRIMARY_DOCS = (
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "AGENTS.md",
    PROJECT_ROOT / ".agents" / "skills" / "template-literature-meta-analysis" / "SKILL.md",
    PROJECT_ROOT / "STANDALONE.md",
    PROJECT_ROOT / "tests" / "README.md",
    PROJECT_ROOT / "tests" / "AGENTS.md",
)


@pytest.mark.parametrize("document", PRIMARY_DOCS, ids=lambda path: str(path.relative_to(PROJECT_ROOT)))
def test_primary_docs_declare_monorepo_and_standalone_test_commands(document: Path) -> None:
    """Each entry point explains the command appropriate to its checkout."""
    guidance = document.read_text(encoding="utf-8")
    assert MONOREPO_TEST_COMMAND in guidance
    assert STANDALONE_TEST_COMMAND in guidance


def test_standalone_test_command_uses_local_configuration() -> None:
    """The independent source command selects the real own tests and coverage gate."""
    assert shlex.split(STANDALONE_TEST_COMMAND) == [
        "python",
        "-I",
        "-m",
        "pytest",
        "tests/",
        "--cov=src",
        "--cov-fail-under=90",
    ]
    assert (PROJECT_ROOT / "pyproject.toml").is_file()
    assert (PROJECT_ROOT / "tests" / "conftest.py").is_file()


def _standalone_source_copy(destination: Path) -> Path:
    """Copy genuine source/configuration and selected oracles, without a Root tree."""
    destination.mkdir(parents=True)
    shutil.copy2(PROJECT_ROOT / "pyproject.toml", destination / "pyproject.toml")
    shutil.copytree(
        PROJECT_ROOT / "src",
        destination / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    for relative in (
        "tests/conftest.py",
        "tests/literature/test_corpus.py",
        "tests/knowledge_graph/llm_extraction_fixtures.py",
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / relative, target)
    assert not (destination / "infrastructure").exists()
    assert not (destination / "scripts" / "pipeline" / "stage_01_test.py").exists()
    return destination


def _conftest_child_program() -> str:
    """Load the actual canonical startup with pytest's authored paths present."""
    assert infrastructure.__file__ is not None
    sdk_origin = Path(infrastructure.__file__).resolve(strict=True)
    return (
        "import importlib,importlib.util,json,sys;from pathlib import Path;"
        f"project=Path({str(PROJECT_ROOT)!r});"
        "sys.path[:0]=[str(project),str(project/'src'),str(project/'tests')];before=sys.path[:];"
        "spec=importlib.util.spec_from_file_location('actual_project_conftest',project/'tests/conftest.py');"
        "assert spec is not None and spec.loader is not None;"
        "startup=importlib.util.module_from_spec(spec);spec.loader.exec_module(startup);"
        "assert sys.path==before;import infrastructure;"
        f"assert Path(infrastructure.__file__).resolve()==Path({str(sdk_origin)!r});"
        f"assert infrastructure.__version__=={infrastructure.__version__!r};"
    )


def _run_conftest_child(program: str):
    environment = build_bounded_env(dict(os.environ))
    for name in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        environment.pop(name, None)
    return run_bounded_subprocess([sys.executable, "-I", "-c", program], cwd=PROJECT_ROOT, env=environment, timeout=90)


def test_canonical_startup_preserves_genuine_selected_environment_and_domain() -> None:
    """The real project-local SDK survives filtering and runs actual corpus logic."""
    program = _conftest_child_program() + (
        "from template_literature_meta_analysis.literature.corpus import Corpus;"
        "from template_literature_meta_analysis.literature.models import Paper;"
        "corpus=Corpus([Paper(title='One',doi='10.5555/same'),Paper(title='One again',doi='10.5555/same')]);"
        "assert len(corpus)==1;"
        "print(json.dumps({'origin':str(Path(infrastructure.__file__).resolve()),"
        "'version':infrastructure.__version__,'deduplicated':len(corpus)}));"
    )
    actual = _run_conftest_child(program)
    assert actual.returncode == actual.original_returncode == 0, actual.stdout + actual.stderr + actual.command_error
    assert not actual.timed_out and not actual.custody_refused
    receipts = [json.loads(line) for line in actual.stdout.splitlines() if line.startswith("{")]
    assert infrastructure.__file__ is not None
    assert receipts == [
        {
            "origin": str(Path(infrastructure.__file__).resolve(strict=True)),
            "version": infrastructure.__version__,
            "deduplicated": 1,
        }
    ]


def test_canonical_startup_rejects_actual_authored_namespace_cached_as_sdk() -> None:
    """A genuine own module under the SDK fullname cannot gain provider authority."""
    program = _conftest_child_program() + (
        "sys.modules['infrastructure']=importlib.import_module('template_literature_meta_analysis');\n"
        "try:\n"
        "    spec.loader.exec_module(startup)\n"
        "except ImportError as error:\n"
        "    assert 'own project source cannot provide' in str(error)\n"
        "    assert sys.path==before\n"
        "    print('actual authored cached provider refused')\n"
        "else:\n"
        "    raise AssertionError('actual own namespace admitted as SDK')\n"
    )
    actual = _run_conftest_child(program)
    assert actual.returncode == actual.original_returncode == 0, actual.stdout + actual.stderr + actual.command_error
    assert not actual.timed_out and not actual.custody_refused
    assert actual.stdout.strip() == "actual authored cached provider refused"


@pytest.mark.timeout(120)
@pytest.mark.parametrize("case", ("corpus-oracles", "sdk-shadows", "wrong-domain-result", "empty-scope"))
def test_configured_pytest_runs_in_standalone_source_copy(tmp_path: Path, case: str) -> None:
    """Real pytest admits copied domain oracles and refuses false/empty evidence.

    The selected interpreter already provides the declared SDK and dev packages.
    These focused source tests make no full-suite or installed-wheel claim.
    """
    owned_context = tmp_path / "owned-context"
    standalone = _standalone_source_copy(owned_context / "ancestors" / "middle" / "standalone-meta")
    origin = standalone / "tests" / "test_owned_domain.py"
    provider_receipt = standalone / "actual-sdk-provider.json"
    assert infrastructure.__file__ is not None
    sdk_origin = Path(infrastructure.__file__).resolve(strict=True)
    sdk_version = infrastructure.__version__
    shadow_markers: list[Path] = []
    if case == "sdk-shadows":
        # All three invalid providers are disposable actual package files.
        # The ancestor is owned; no ambient pytest/user directory is touched.
        for index, directory in enumerate(
            (
                standalone / "infrastructure",
                standalone / "src" / "infrastructure",
                owned_context / "infrastructure",
            )
        ):
            directory.mkdir()
            marker = standalone / f"shadow-executed-{index}"
            shadow_markers.append(marker)
            (directory / "__init__.py").write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('invalid SDK executed')\n"
                "raise RuntimeError('own or guessed-ancestor source cannot select the SDK')\n",
                encoding="utf-8",
            )
    if case in {"corpus-oracles", "sdk-shadows"}:
        origin.write_text(
            "import json\nfrom pathlib import Path\nimport infrastructure\n"
            "from template_literature_meta_analysis.literature import models\n"
            "def test_actual_source_origin():\n"
            "    expected = Path(__file__).resolve().parents[1] / 'src/literature/models.py'\n"
            "    assert Path(models.__file__).resolve() == expected\n"
            f"    assert Path(infrastructure.__file__).resolve() == Path({str(sdk_origin)!r})\n"
            f"    assert infrastructure.__version__ == {sdk_version!r}\n"
            f"    Path({str(provider_receipt)!r}).write_text(json.dumps("
            "{'origin':str(Path(infrastructure.__file__).resolve()),"
            "'version':infrastructure.__version__}),encoding='utf-8')\n",
            encoding="utf-8",
        )
        selected = [
            "tests/literature/test_corpus.py::TestCorpusAdd::test_dedup_keeps_more_complete",
            "tests/literature/test_corpus.py::TestCorpusPersistence::test_save_and_load_round_trip",
            "tests/test_owned_domain.py",
        ]
        expected_exit, expected_count, expected_failures = 0, 3, 0
    elif case == "wrong-domain-result":
        origin.write_text(
            "from template_literature_meta_analysis.literature.corpus import Corpus\n"
            "from template_literature_meta_analysis.literature.models import Paper\n"
            "def test_wrong_deduplication_expectation():\n"
            "    corpus = Corpus([Paper(title='One', doi='10.5555/same'), "
            "Paper(title='One again', doi='10.5555/same')])\n"
            "    assert len(corpus) == 2\n",
            encoding="utf-8",
        )
        selected = ["tests/test_owned_domain.py"]
        expected_exit, expected_count, expected_failures = 1, 1, 1
    else:
        (standalone / "tests" / "empty").mkdir()
        selected = ["tests/empty"]
        expected_exit, expected_count, expected_failures = 5, 0, 0

    receipt = standalone / "pytest-results.xml"
    env = build_bounded_env(dict(os.environ))
    for name in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        env.pop(name, None)
    # The focused oracles need no third-party auto-loaded plugins. Admit the
    # actual declared timeout plugin explicitly; the full coverage gate is above.
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["MPLCONFIGDIR"] = str(standalone / "matplotlib-config")
    result = run_bounded_subprocess(
        [
            sys.executable,
            "-I",
            "-m",
            "pytest",
            "-p",
            "pytest_timeout",
            "-c",
            "pyproject.toml",
            "--confcutdir",
            str(standalone),
            "--basetemp",
            str(standalone / "pytest-tmp"),
            "--override-ini",
            f"cache_dir={standalone / 'pytest-cache'}",
            f"--junitxml={receipt}",
            "-q",
            *selected,
        ],
        cwd=standalone,
        env=env,
        timeout=90,
    )
    diagnostic = result.command_error + result.stdout + result.stderr
    assert not result.timed_out, diagnostic
    assert not result.custody_refused, diagnostic
    assert result.returncode == result.original_returncode == expected_exit, diagnostic
    suites = list(ET.parse(receipt).getroot().iter("testsuite"))
    assert sum(int(suite.attrib["tests"]) for suite in suites) == expected_count
    assert sum(int(suite.attrib["failures"]) for suite in suites) == expected_failures
    assert sum(int(suite.attrib["errors"]) for suite in suites) == 0
    assert sum(int(suite.attrib["skipped"]) for suite in suites) == 0
    assert all(not marker.exists() for marker in shadow_markers)
    if case in {"corpus-oracles", "sdk-shadows"}:
        assert json.loads(provider_receipt.read_text(encoding="utf-8")) == {
            "origin": str(sdk_origin),
            "version": sdk_version,
        }
    if case == "wrong-domain-result":
        failures = list(ET.parse(receipt).getroot().iter("failure"))
        assert len(failures) == 1
        assert "assert 1 == 2" in (failures[0].text or ""), diagnostic

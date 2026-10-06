"""Actual isolated imports preserve optional providers without eager plotting."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

SDK_ROOT = Path(__file__).resolve().parents[3]


def _native(program: str, cwd: Path, *, without_site: bool = False):
    command = [sys.executable, "-I", "-B"]
    if without_site:
        command.append("-S")
    command.extend(["-c", "import sys\n" + f"sys.path.insert(0, {str(SDK_ROOT)!r})\n" + program])
    return run_with_policy(
        command,
        cwd=cwd,
        env=build_bounded_env(),
        policy=SubprocessPolicy(
            policy_id="actual-reporting-optional-imports",
            source_path="tests/infra_tests/reporting/test_optional_plotting_imports.py",
            timeout_seconds=60,
            credential_free=True,
        ),
    )


@pytest.mark.timeout(120)
def test_actual_pipeline_and_interactive_imports_leave_plotting_unloaded(tmp_path: Path) -> None:
    result = _native(
        "import infrastructure.reporting as reporting\n"
        "from infrastructure.reporting import collect_output_statistics, generate_pipeline_report, save_pipeline_report, InteractiveDashboard\n"
        "from infrastructure.reporting.output_statistics import collect_output_statistics as actual_statistics\n"
        "from infrastructure.reporting.pipeline_report_model import generate_pipeline_report as actual_report\n"
        "from infrastructure.reporting.pipeline_io import save_pipeline_report as actual_save\n"
        "from infrastructure.reporting.interactive_dashboard import InteractiveDashboard as actual_dashboard\n"
        "assert collect_output_statistics is actual_statistics and generate_pipeline_report is actual_report\n"
        "assert save_pipeline_report is actual_save and InteractiveDashboard is actual_dashboard\n"
        "assert not any(name == 'matplotlib' or name.startswith('matplotlib.') for name in sys.modules)\n"
        "assert 'infrastructure.reporting._dashboard_matplotlib' not in sys.modules\n"
        "assert 'infrastructure.reporting._dashboard_charts' not in sys.modules\n"
        "print('actual-ordinary-providers-without-plotting')\n",
        tmp_path,
    )
    assert result.returncode == result.original_returncode == 0, result.stderr
    assert not result.timed_out and not result.custody_refused
    assert "actual-ordinary-providers-without-plotting" in result.stdout


@pytest.mark.timeout(120)
def test_actual_optional_exports_and_enumeration_retain_original_function_identity(tmp_path: Path) -> None:
    result = _native(
        "import infrastructure.reporting as reporting\n"
        "assert reporting.DASHBOARD_AVAILABLE is True\n"
        "from infrastructure.reporting._dashboard_matplotlib import generate_all_dashboards, generate_plotly_dashboard\n"
        "from infrastructure.reporting._dashboard_charts import generate_matplotlib_dashboard\n"
        "assert reporting.generate_all_dashboards is generate_all_dashboards\n"
        "assert reporting.generate_plotly_dashboard is generate_plotly_dashboard\n"
        "assert reporting.generate_matplotlib_dashboard is generate_matplotlib_dashboard\n"
        "assert set(reporting.__all__) <= set(dir(reporting))\n"
        "assert {'generate_all_dashboards','generate_plotly_dashboard','generate_matplotlib_dashboard'} <= set(dir(reporting))\n"
        "try: reporting.actual_nonexistent_owned_attribute\n"
        "except AttributeError: pass\n"
        "else: raise AssertionError('unknown export was accepted')\n"
        "print('actual-optional-export-identity')\n",
        tmp_path,
    )
    assert result.returncode == result.original_returncode == 0, result.stderr
    assert not result.timed_out and not result.custody_refused
    assert "actual-optional-export-identity" in result.stdout


@pytest.mark.timeout(120)
def test_genuine_no_site_environment_retains_optional_import_failure(tmp_path: Path) -> None:
    # Use actual PyYAML source in a restricted, otherwise empty import directory;
    # no import finder, synthetic module or replacement plotting producer exists.
    spec = importlib.util.find_spec("yaml")
    assert spec is not None and spec.origin is not None
    minimal = tmp_path / "actual-minimal-site"
    shutil.copytree(Path(spec.origin).parent, minimal / "yaml", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    result = _native(
        f"sys.path.insert(0, {str(minimal)!r})\n"
        "import json\nimport infrastructure.reporting as reporting\n"
        "assert 'matplotlib' not in sys.modules\n"
        "assert reporting.DASHBOARD_AVAILABLE is False\n"
        "for name in ('generate_all_dashboards','generate_plotly_dashboard','generate_matplotlib_dashboard'):\n"
        "    try: getattr(reporting,name)\n"
        "    except AttributeError: pass\n"
        "    else: raise AssertionError('absent plotting provider accepted')\n"
        "assert 'DASHBOARD_AVAILABLE' in dir(reporting)\n"
        "print(json.dumps({'available':reporting.DASHBOARD_AVAILABLE,'actual_missing_optional':True}))\n",
        tmp_path,
        without_site=True,
    )
    assert result.returncode == result.original_returncode == 0, result.stderr
    assert not result.timed_out and not result.custody_refused
    payload = json.loads(result.stdout)
    assert payload == {"available": False, "actual_missing_optional": True}

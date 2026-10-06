"""Real executor-owned logging, in pytest and an ordinary isolated Python child."""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline


def _exercise_logging(root: Path) -> None:
    import logging
    import time
    from dataclasses import replace

    from infrastructure.core.pipeline import observability
    from infrastructure.core.pipeline.executor import PipelineExecutor
    from infrastructure.core.pipeline.plan import compile_execution_plan
    from infrastructure.core.pipeline.types import PipelineConfig

    root_logger = logging.getLogger()
    module_logger = observability.logger
    root_before = tuple(root_logger.handlers)
    module_before = tuple(module_logger.handlers)
    module_level_before = module_logger.level
    foreign_root = logging.FileHandler(root / "observer-root.log")
    foreign_module = logging.FileHandler(root / "observer-module.log")
    root_logger.addHandler(foreign_root)
    module_logger.addHandler(foreign_module)
    outsider = logging.getLogger("actual_logging_observer")
    outsider_level, outsider_propagate = outsider.level, outsider.propagate
    outsider.setLevel(logging.INFO)
    outsider.propagate = True
    executors = []
    try:
        first = PipelineExecutor(PipelineConfig("first", root, clean=False, skip_infra=True))
        executors.append(first)
        observability.log_stage_start(first, stage_num=1, stage_name="FIRST_PROGRESS", pipeline_start=None)
        outsider.info("FIRST_ROOT_RECORD")
        assert first.log_file.read_text().count("FIRST_PROGRESS") == 1
        assert first.log_file.read_text().count("FIRST_ROOT_RECORD") == 1
        initial_root, initial_module = first._log_handler, first._module_log_handler
        assert initial_root is not None and initial_module is not None

        # The real clean method deletes the owned output and reinstalls its sinks.
        assert first._run_clean_outputs()
        assert initial_root not in root_logger.handlers and initial_root.stream is None
        assert initial_module not in module_logger.handlers and initial_module.stream is None
        observability.log_stage_start(first, stage_num=1, stage_name="FIRST_AFTER_CLEAN", pipeline_start=None)
        assert first.log_file.read_text().count("FIRST_AFTER_CLEAN") == 1
        plan = compile_execution_plan(first.config)
        expired = first.execute_plan(plan, deadline_monotonic=time.monotonic() - 1)
        assert first.run_result(expired).exit_code == 124
        assert expired[0].outcome is not None and expired[0].outcome.child_exit_code is None
        assert first._log_handler is first._module_log_handler is None
        first_bytes = first.log_file.read_bytes()

        second = PipelineExecutor(PipelineConfig("second", root, clean=False, skip_infra=True))
        executors.append(second)
        observability.log_stage_start(second, stage_num=1, stage_name="SECOND_PROGRESS", pipeline_start=None)
        outsider.info("SECOND_ROOT_RECORD")
        second_plan = compile_execution_plan(second.config)
        try:
            second.execute_plan(replace(second_plan, project="first"))
        except ValueError as exc:
            assert "does not match" in str(exc)
        else:
            raise AssertionError("actual foreign plan was accepted")
        assert second._log_handler is second._module_log_handler is None
        assert second.log_file.read_text().count("SECOND_PROGRESS") == 1
        assert second.log_file.read_text().count("SECOND_ROOT_RECORD") == 1
        assert first.log_file.read_bytes() == first_bytes

        # Reusing the actual closed executor must reattach, then detach on refusal.
        repeated = first.execute_plan(plan, deadline_monotonic=time.monotonic() - 1)
        assert first.run_result(repeated).exit_code == 124
        assert first._log_handler is first._module_log_handler is None
        assert not (root / "process_order.log").exists()
        assert foreign_root in root_logger.handlers and foreign_root.stream is not None
        assert foreign_module in module_logger.handlers and foreign_module.stream is not None
        outsider.info("OBSERVER_AFTER_CLOSE")
        module_logger.warning("MODULE_OBSERVER_AFTER_CLOSE")
        foreign_root.flush()
        foreign_module.flush()
        assert "OBSERVER_AFTER_CLOSE" in (root / "observer-root.log").read_text()
        assert "MODULE_OBSERVER_AFTER_CLOSE" in (root / "observer-module.log").read_text()
    finally:
        for executor in executors:
            executor.close()
        root_logger.removeHandler(foreign_root)
        module_logger.removeHandler(foreign_module)
        foreign_root.close()
        foreign_module.close()
        outsider.setLevel(outsider_level)
        outsider.propagate = outsider_propagate
    assert tuple(root_logger.handlers) == root_before
    assert tuple(module_logger.handlers) == module_before
    assert module_logger.level == module_level_before


@pytest.mark.timeout(120)
def test_executor_logging_has_exact_owned_sinks_and_preserves_pytest_observers(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("first", "second"))
    _exercise_logging(tmp_path)


@pytest.mark.timeout(120)
def test_executor_logging_preserves_ordinary_python_progress(tmp_path: Path) -> None:
    import infrastructure

    scaffold_pipeline(tmp_path, ("first", "second"))
    assert infrastructure.__file__ is not None
    provider = Path(infrastructure.__file__).resolve().parent.parent
    # Reuse the same actual test-harness function without importing this pytest module.
    control = textwrap.dedent(inspect.getsource(_exercise_logging))
    assert "pytest" not in control
    code = (
        "import os, sys\nfrom pathlib import Path\n"
        "os.environ.pop('PYTEST_CURRENT_TEST', None)\n"
        "sys.dont_write_bytecode = True\n"
        "sys.pycache_prefix = str(Path(sys.argv[2]) / 'owned-bytecode')\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "import infrastructure\n"
        "assert Path(infrastructure.__file__).resolve() == Path(sys.argv[1]) / 'infrastructure/__init__.py'\n"
        + control
        + "\n_exercise_logging(Path(sys.argv[2]))\n"
        "assert 'pytest' not in sys.modules\n"
        "from infrastructure.core.pipeline.observability import logger\n"
        "assert logger.propagate is False\n"
    )
    environment = dict(os.environ)
    environment.pop("PYTEST_CURRENT_TEST", None)
    child = subprocess.run(
        [sys.executable, "-I", "-c", code, str(provider), str(tmp_path)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=100,
    )
    assert child.returncode == 0, child.stdout + child.stderr


def test_actual_telemetry_constructor_failure_detaches_owned_logging(tmp_path: Path) -> None:
    import logging
    import yaml

    from infrastructure.core.pipeline import observability
    from infrastructure.core.pipeline.executor import PipelineExecutor
    from infrastructure.core.pipeline.types import PipelineConfig

    scaffold_pipeline(tmp_path)
    declaration = tmp_path / "infrastructure/core/pipeline/pipeline.yaml"
    payload = yaml.safe_load(declaration.read_text())
    payload["telemetry"] = {"output_formats": None}
    declaration.write_text(yaml.safe_dump(payload))
    before_root = tuple(logging.getLogger().handlers)
    before_module = tuple(observability.logger.handlers)
    level_before = observability.logger.level
    with pytest.raises(TypeError):
        PipelineExecutor(PipelineConfig("demo", tmp_path, clean=False))
    assert tuple(logging.getLogger().handlers) == before_root
    assert tuple(observability.logger.handlers) == before_module
    assert observability.logger.level == level_before


def test_actual_closed_banner_stream_releases_constructed_executor(tmp_path: Path) -> None:
    import logging

    from infrastructure.core.pipeline import observability
    from infrastructure.orchestration.pipeline_runner import PipelineInvocation, PipelineRunner

    scaffold_pipeline(tmp_path)
    root_handlers = tuple(logging.getLogger().handlers)
    module_handlers = tuple(observability.logger.handlers)
    module_level = observability.logger.level
    stream = (tmp_path / "closed-banner.txt").open("w")
    stream.close()
    runner = PipelineRunner(tmp_path, stream=stream)
    with pytest.raises(ValueError, match="closed file"):
        runner.run(PipelineInvocation("demo", skip_infra=True))
    # The setup marker proves actual executor construction preceded the stream failure.
    log = tmp_path / "projects/demo/output/logs/pipeline.log"
    assert "Set up log file handler" in log.read_text()
    assert not (tmp_path / "process_order.log").exists()
    assert tuple(logging.getLogger().handlers) == root_handlers
    assert tuple(observability.logger.handlers) == module_handlers
    assert observability.logger.level == module_level

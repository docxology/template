"""Real imported checkout custody and admission failures, without substitutions."""

from __future__ import annotations

import hashlib
import importlib.metadata
import infrastructure
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from template_autopoiesis.gates.generator_custody import capture_execution_custody
from template_autopoiesis.gates.realization_contract import selected_specs, source_custody

PROJECT = Path(__file__).resolve().parents[2]
SDK_PACKAGE = Path(infrastructure.__file__).resolve(strict=True).parent


def _isolated_sdk_package() -> Path:
    """Select the real -I environment provider, separately from this test's Source SDK."""
    observed = subprocess.run(
        [sys.executable, "-I", "-c", "import infrastructure; print(infrastructure.__file__)"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert observed.returncode == 0, observed.stdout + observed.stderr
    return Path(observed.stdout.strip()).resolve(strict=True).parent


ISOLATED_SDK_PACKAGE = _isolated_sdk_package()


def _copy_project(destination: Path) -> Path:
    shutil.copytree(
        PROJECT,
        destination,
        ignore=shutil.ignore_patterns("output", ".venv", "__pycache__", ".pytest_cache", ".coverage*", "*.egg-info"),
    )
    return destination


def _run(generator: Path, reference: Path, *, bootstrap: bool = False) -> subprocess.CompletedProcess[str]:
    """Run actual copied generator with the current selected environment SDK."""
    if bootstrap:
        registration = (
            f"spec=importlib.util.spec_from_file_location('auto_bootstrap',{str(generator / 'scripts/_bootstrap.py')!r});"
            "assert spec is not None and spec.loader is not None;"
            "selected=importlib.util.module_from_spec(spec);spec.loader.exec_module(selected);"
            f"selected.bootstrap_project(Path({str(generator)!r}));"
        )
    else:
        # Explicitly selected own SOURCE fixture exercises producer custody,
        # independently from the stricter script startup admission controls.
        registration = (
            f"spec=importlib.util.spec_from_file_location('template_autopoiesis',{str(generator / 'src/template_autopoiesis/__init__.py')!r},submodule_search_locations=[{str(generator / 'src/template_autopoiesis')!r}]);"
            "assert spec is not None and spec.loader is not None;"
            "selected=importlib.util.module_from_spec(spec);sys.modules[spec.name]=selected;spec.loader.exec_module(selected);"
        )
    script = (
        "import sys,importlib.util;from pathlib import Path;import infrastructure;"
        f"assert Path(infrastructure.__file__).resolve()==Path({str(ISOLATED_SDK_PACKAGE / '__init__.py')!r});"
        "assert infrastructure.__version__=='4.0.2';"
        + registration
        + "from template_autopoiesis.gates.realization_contract import realize_selected_children;"
        f"realize_selected_children(Path({str(reference)!r}),single=True)"
    )
    return subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=reference.parent,
        capture_output=True,
        text=True,
        timeout=150,
        check=False,
    )


def test_fresh_own_bootstrap_accepts_actual_environment_sdk_and_executes_primitive(tmp_path: Path) -> None:
    """An installed SDK inside the own environment is a provider, not authored source."""
    script = (
        "import importlib.util,json,sys,sysconfig;from pathlib import Path;"
        "assert 'infrastructure' not in sys.modules;"
        f"project=Path({str(PROJECT)!r});"
        "original=sys.path[:];"
        "spec=importlib.util.spec_from_file_location('actual_own_bootstrap',project/'scripts/_bootstrap.py');"
        "assert spec is not None and spec.loader is not None;"
        "bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap);"
        "sdk=bootstrap.bootstrap_project(project);"
        f"assert Path(sdk.__file__).resolve()==Path({str(ISOLATED_SDK_PACKAGE / '__init__.py')!r});"
        "assert sdk.__version__=='4.0.2';assert sys.path==original;"
        "origin=Path(sdk.__file__).resolve();"
        "providers=[Path(sysconfig.get_path(kind)).resolve() for kind in ('purelib','platlib')];"
        "assert not origin.is_relative_to(project) or any(origin.is_relative_to(path) for path in providers);"
        "from template_autopoiesis.primitives.optimization import gradient_descent;"
        "assert gradient_descent.__module__=='template_autopoiesis.primitives.optimization';"
        "result=gradient_descent({'A':[[2.0]],'c':[3.0],'x0':[0.0],'lr':0.5,'steps':1});"
        "assert result['x_final'].tolist()==[3.0];"
        "print(json.dumps({'provider':str(origin),'result':result['x_final'].tolist()}))"
    )
    observed = subprocess.run(
        [sys.executable, "-I", "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False
    )
    assert observed.returncode == 0, observed.stdout + observed.stderr
    result = json.loads(observed.stdout)
    assert result == {"provider": str(ISOLATED_SDK_PACKAGE / "__init__.py"), "result": [3.0]}


@pytest.mark.parametrize("shadow_location", ["own-root", "own-src"])
def test_actual_cached_authored_sdk_is_refused_outside_active_provider_roots(
    tmp_path: Path, shadow_location: str
) -> None:
    """The provider exception must not admit an already executed authored shadow."""
    generator = _copy_project(tmp_path / "generator")
    location = generator if shadow_location == "own-root" else generator / "src"
    shadow = location / "infrastructure"
    shadow.mkdir()
    marker = tmp_path / "authored-sdk-executed"
    (shadow / "__init__.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('actual authored provider ran')\n"
        "__version__='4.0.2'\n",
        encoding="utf-8",
    )
    script = (
        "import importlib.util,sys;from pathlib import Path;"
        f"project=Path({str(generator)!r});sys.path.insert(0,{str(location)!r});"
        "import infrastructure;"
        f"assert Path(infrastructure.__file__).resolve()==Path({str(shadow / '__init__.py')!r});"
        "spec=importlib.util.spec_from_file_location('actual_own_bootstrap',project/'scripts/_bootstrap.py');"
        "assert spec is not None and spec.loader is not None;"
        "bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap);"
        "original=sys.path[:];\n"
        "try:\n"
        "    bootstrap.bootstrap_project(project)\n"
        "except ImportError as error:\n"
        "    assert 'own project source cannot provide' in str(error)\n"
        "else:\n"
        "    raise AssertionError('authored SDK was accepted as active provider')\n"
        "assert sys.path==original\n"
    )
    observed = subprocess.run(
        [sys.executable, "-I", "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False
    )
    assert observed.returncode == 0, observed.stdout + observed.stderr
    assert marker.read_text() == "actual authored provider ran"
    assert not (generator / "output").exists()


def test_actual_loaded_sdk_missing_origin_is_refused_and_paths_are_restored(tmp_path: Path) -> None:
    """A genuine cached provider must retain an existing source origin."""
    missing = tmp_path / "absent-provider" / "__init__.py"
    script = (
        "import importlib.util,sys;from pathlib import Path;import infrastructure;"
        f"assert Path(infrastructure.__file__).resolve(strict=True)==Path({str(ISOLATED_SDK_PACKAGE / '__init__.py')!r});"
        "assert infrastructure.__version__=='4.0.2';"
        f"project=Path({str(PROJECT)!r});"
        "spec=importlib.util.spec_from_file_location('actual_own_bootstrap',project/'scripts/_bootstrap.py');"
        "assert spec is not None and spec.loader is not None;"
        "bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap);"
        f"infrastructure.__file__={str(missing)!r};assert not Path(infrastructure.__file__).exists();"
        "original=sys.path[:];\n"
        "try:\n"
        "    bootstrap.bootstrap_project(project)\n"
        "except FileNotFoundError:\n"
        "    pass\n"
        "else:\n"
        "    raise AssertionError('missing genuine SDK source origin was accepted')\n"
        "assert sys.path==original\n"
        "assert sys.modules['infrastructure'] is infrastructure\n"
        "print('missing genuine SDK origin refused')\n"
    )
    observed = subprocess.run(
        [sys.executable, "-I", "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False
    )
    assert observed.returncode == 0, observed.stdout + observed.stderr
    assert observed.stdout.strip() == "missing genuine SDK origin refused"
    assert not missing.parent.exists()


def test_loaded_generator_custody_is_distinct_from_supplied_reference_inputs(tmp_path: Path) -> None:
    reference = _copy_project(tmp_path / "reference")
    generator, platform = capture_execution_custody()
    assert generator["schema_version"] == "autopoiesis/active-generator-custody/1"
    assert generator["binding_kind"] == "source-checkout"
    assert (
        generator["files"]["checkout/pyproject.toml"]
        == hashlib.sha256((PROJECT / "pyproject.toml").read_bytes()).hexdigest()
    )
    assert generator["files"]["checkout/uv.lock"] == hashlib.sha256((PROJECT / "uv.lock").read_bytes()).hexdigest()
    assert platform["files"] and generator["bytecode_binding"] == "loaded-baseline"
    assert infrastructure.__version__ == "4.0.2"
    assert (
        platform["files"]["infrastructure/__init__.py"]
        == hashlib.sha256((SDK_PACKAGE / "__init__.py").read_bytes()).hexdigest()
    )
    sdk_checkout = SDK_PACKAGE.parent
    if all((sdk_checkout / name).is_file() for name in ("pyproject.toml", "uv.lock", ".python-version")):
        assert platform["binding_kind"] == "source-checkout"
        for filename in ("pyproject.toml", "uv.lock", ".python-version"):
            assert platform["files"][filename] == hashlib.sha256((sdk_checkout / filename).read_bytes()).hexdigest()
    else:
        assert platform["binding_kind"] == "installed-distribution"
        selected = importlib.metadata.distribution("research-project-template")
        assert selected.version == "4.0.2" and selected.files is not None
        records = [path for path in selected.files if str(path).endswith(".dist-info/RECORD")]
        assert len(records) == 1
        for field, relative in (("record_sha256", records[0]), ("metadata_sha256", records[0].parent / "METADATA")):
            assert (
                platform["distribution"][field]
                == hashlib.sha256(Path(selected.locate_file(relative)).read_bytes()).hexdigest()
            )
        assert {
            "infrastructure/" + relative: digest
            for relative, digest in platform["distribution"]["public_python"].items()
        } == platform["files"]

    reference_before = source_custody(reference)
    config = reference / "manuscript/config.yaml"
    config.write_text(config.read_text() + "\n# separate supplied reference fixture\n")
    assert source_custody(reference) != reference_before
    assert capture_execution_custody() == (generator, platform)


@pytest.mark.parametrize("fault", ["identity", "missing-lock", "symlink"])
def test_generator_admission_faults_fail_before_materialization(tmp_path: Path, fault: str) -> None:
    generator = _copy_project(tmp_path / "generator")
    reference = _copy_project(tmp_path / "reference")
    if fault == "identity":
        metadata = generator / "pyproject.toml"
        metadata.write_text(metadata.read_text().replace('name = "template_autopoiesis"', 'name = "wrong-generator"'))
    elif fault == "missing-lock":
        (generator / "uv.lock").unlink()
    else:
        package = generator / "src/template_autopoiesis"
        original = tmp_path / "package"
        package.rename(original)
        package.symlink_to(original, target_is_directory=True)
    result = _run(generator, reference)
    assert result.returncode != 0, result.stdout
    assert "ValueError" in result.stderr or "OSError" in result.stderr
    receipt = json.loads((reference / "output/.pipeline/child_realization/single.json").read_text())
    assert receipt["status"] == "failed" and receipt["executed_children"] == []
    assert not (reference / "output/.pipeline/child_realization/workspaces").exists()


def test_generator_source_change_during_real_child_tests_prevents_success(tmp_path: Path) -> None:
    generator = _copy_project(tmp_path / "generator")
    reference = _copy_project(tmp_path / "reference")
    domain = selected_specs(reference, single=True)[0].primitive_domain
    oracle = reference / f"tests/primitives/test_primitives_{domain}.py"
    target = generator / "src/template_autopoiesis/gates/generator_custody.py"
    oracle.write_text(
        oracle.read_text()
        + "\ndef test_actual_parent_generator_mutation_negative_control():\n"
        + "    from pathlib import Path\n"
        + f"    source = Path({str(target)!r})\n"
        + "    source.write_text(source.read_text() + '\\n# generator mutation negative control\\n')\n"
        + "    assert source.is_file()\n"
    )
    result = _run(generator, reference)
    assert result.returncode != 0
    receipt = json.loads((reference / "output/.pipeline/child_realization/single.json").read_text())
    assert receipt["status"] == "failed" and "changed during child execution" in receipt["diagnostic"]
    record = receipt["executed_children"][0]
    assert record["tests"]["returncode"] == record["analysis"]["returncode"] == 0
    assert target.read_text().endswith("# generator mutation negative control\n")


@pytest.mark.timeout(180)
def test_actual_own_bootstrap_preloads_selected_sdk_before_local_shadow_candidates(tmp_path: Path) -> None:
    generator = _copy_project(tmp_path / "generator")
    reference = _copy_project(tmp_path / "reference")
    shadow = generator / "src/infrastructure"
    shadow.mkdir()
    marker = generator / "shadow-executed"
    (shadow / "__init__.py").write_text(
        f'from pathlib import Path\nPath({str(marker)!r}).write_text("actual shadow ran")\n'
        'raise RuntimeError("owned invalid provider")\n'
    )
    # Prove this exact owned package is executable in an ordinary explicit import.
    positive = subprocess.run(
        [sys.executable, "-I", "-c", f"import sys;sys.path.insert(0,{str(shadow.parent)!r});import infrastructure"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert positive.returncode == 1 and "owned invalid provider" in positive.stderr
    assert marker.read_text() == "actual shadow ran"
    marker.unlink()
    result = _run(generator, reference, bootstrap=True)
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads((reference / "output/.pipeline/child_realization/single.json").read_text())
    assert receipt["status"] == "passed" and receipt["selected_count"] == 1
    assert receipt["active_generator_custody"]["binding_kind"] == "source-checkout"
    assert (
        receipt["platform_custody"]["files"]["infrastructure/__init__.py"]
        == hashlib.sha256((SDK_PACKAGE / "__init__.py").read_bytes()).hexdigest()
    )
    record = receipt["executed_children"][0]
    assert record["tests"]["returncode"] == record["analysis"]["returncode"] == 0
    assert not record["tests"]["timed_out"] and not record["analysis"]["timed_out"]
    assert not marker.exists()


@pytest.mark.timeout(90)
@pytest.mark.parametrize("mode", ["canonical-cache", "wrong-own-alias", "foreign-search-path"])
def test_actual_cached_own_namespace_preserves_canonical_modules_and_refuses_wrong_origins(
    tmp_path: Path,
    mode: str,
) -> None:
    generator = _copy_project(tmp_path / "generator")
    foreign = tmp_path / "foreign-search"
    foreign.mkdir()
    marker = tmp_path / "foreign-module-executed"
    (foreign / "foreign_cache_probe.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('actual foreign search path executed')\n",
        encoding="utf-8",
    )
    script = (
        "import importlib,importlib.util,sys;from pathlib import Path;import infrastructure;"
        f"assert Path(infrastructure.__file__).resolve()==Path({str(ISOLATED_SDK_PACKAGE / '__init__.py')!r});"
        "assert infrastructure.__version__=='4.0.2';"
        f"spec=importlib.util.spec_from_file_location('actual_auto_bootstrap',{str(generator / 'scripts/_bootstrap.py')!r});"
        "assert spec is not None and spec.loader is not None;bootstrap=importlib.util.module_from_spec(spec);"
        "spec.loader.exec_module(bootstrap);"
        f"project=Path({str(generator)!r});bootstrap.bootstrap_project(project);"
        "package=importlib.import_module('template_autopoiesis');"
        "actual=importlib.import_module('template_autopoiesis.core.project_paths');"
        "assert Path(actual.__file__).resolve()==project/'src/template_autopoiesis/core/project_paths.py';"
        "assert actual.project_output_dirs.__module__=='template_autopoiesis.core.project_paths';"
        f"mode={mode!r};foreign=Path({str(foreign)!r});marker=Path({str(marker)!r});\n"
        "if mode=='wrong-own-alias':\n"
        "    actual_grammar=importlib.import_module('template_autopoiesis.core.grammar')\n"
        "    assert Path(actual_grammar.__file__).resolve()==project/'src/template_autopoiesis/core/grammar.py'\n"
        "    assert actual_grammar.__name__=='template_autopoiesis.core.grammar'\n"
        "    sys.modules['template_autopoiesis.core.project_paths']=actual_grammar\n"
        "elif mode=='foreign-search-path':\n"
        "    package.__path__.append(str(foreign))\n"
        "    imported=importlib.import_module('template_autopoiesis.foreign_cache_probe')\n"
        "    assert Path(imported.__file__).resolve()==foreign/'foreign_cache_probe.py'\n"
        "    assert marker.read_text()=='actual foreign search path executed'\n"
        "    del sys.modules['template_autopoiesis.foreign_cache_probe']\n"
        "    delattr(package,'foreign_cache_probe')\n"
        "    marker.unlink()\n"
        "try:\n"
        "    selected=bootstrap.bootstrap_project(project)\n"
        "except ImportError as error:\n"
        "    assert mode!='canonical-cache'\n"
        "    assert 'canonical own source' in str(error) or 'canonical own module' in str(error)\n"
        "else:\n"
        "    assert mode=='canonical-cache', 'actual wrong cached namespace was accepted'\n"
        "    assert selected is infrastructure\n"
        "    assert importlib.import_module('template_autopoiesis.core.project_paths') is actual\n"
        "    assert actual.project_output_dirs.__module__=='template_autopoiesis.core.project_paths'\n"
        "assert not marker.exists()\n"
        "print('actual cached namespace checked: '+mode)\n"
    )
    observed = subprocess.run(
        [sys.executable, "-I", "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=60, check=False
    )
    assert observed.returncode == 0, observed.stdout + observed.stderr
    assert observed.stdout.strip() == "actual cached namespace checked: " + mode


@pytest.mark.timeout(90)
def test_actual_redirected_own_initializer_is_refused_before_execution(tmp_path: Path) -> None:
    generator = _copy_project(tmp_path / "generator")
    canonical = generator / "src/template_autopoiesis"
    foreign = tmp_path / "owned-foreign-initializer"
    canonical.rename(foreign)
    marker = tmp_path / "initializer-executed"
    initializer = foreign / "__init__.py"
    initializer.write_text(
        initializer.read_text()
        + f'\nfrom pathlib import Path\nPath({str(marker)!r}).write_text("actual initializer ran")\n'
    )
    canonical.symlink_to(foreign, target_is_directory=True)
    positive = subprocess.run(
        [sys.executable, "-I", "-c", f"import runpy;runpy.run_path({str(initializer)!r})"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert positive.returncode == 0, positive.stderr
    assert marker.read_text() == "actual initializer ran"
    marker.unlink()
    script = (
        "import importlib.util;from pathlib import Path;import infrastructure;"
        f"assert Path(infrastructure.__file__).resolve()==Path({str(ISOLATED_SDK_PACKAGE / '__init__.py')!r});"
        f'spec=importlib.util.spec_from_file_location("actual_auto_bootstrap",{str(generator / "scripts/_bootstrap.py")!r});'
        "assert spec is not None and spec.loader is not None;bootstrap=importlib.util.module_from_spec(spec);"
        "spec.loader.exec_module(bootstrap);"
        f"bootstrap.bootstrap_project(Path({str(generator)!r}))"
    )
    rejected = subprocess.run(
        [sys.executable, "-I", "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False
    )
    assert rejected.returncode == 1 and "canonical own source" in rejected.stderr
    assert not marker.exists()
    assert not (generator / "output/.pipeline/child_realization/workspaces").exists()

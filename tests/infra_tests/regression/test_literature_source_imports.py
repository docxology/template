"""Real isolated import controls for Literature's canonical regression bindings."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

_ROOT = Path(__file__).resolve().parents[3]
_SOURCE = _ROOT / "projects/templates/template_literature_meta_analysis/src"
_REGRESSION = _ROOT / "tests/regression/projects/template_literature_meta_analysis/tables/test_field_overview_claims.py"
pytestmark = pytest.mark.timeout(120)

_PROBE = r"""
import importlib
import importlib.util
import json
import sys
from pathlib import Path

root, shadow, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(root))
import infrastructure
from infrastructure.core.implementation_custody import verify_fresh_module_bytecode
sys.path.insert(0, str(shadow))
source = root / 'projects/templates/template_literature_meta_analysis/src'
regression = root / 'tests/regression/projects/template_literature_meta_analysis/tables/test_field_overview_claims.py'
if mode == 'siblings':
    # These ordinary imports prove every competing sibling fixture is live.
    siblings = {name: importlib.import_module(name) for name in ('analysis', 'literature', 'config')}
elif mode == 'wrong-own-alias':
    canonical = 'template_literature_meta_analysis'
    source_spec = importlib.util.spec_from_file_location(canonical, source / '__init__.py', submodule_search_locations=[str(source)])
    package = importlib.util.module_from_spec(source_spec)
    sys.modules[canonical] = package
    source_spec.loader.exec_module(package)
    real_models = importlib.import_module(canonical + '.literature.models')
    assert Path(real_models.__file__).resolve() == source.resolve() / 'literature/models.py'
    assert real_models.Paper.__module__ == canonical + '.literature.models'
    # Actual own model code is cached under the different corpus fullname.
    sys.modules[canonical + '.literature.corpus'] = real_models
else:
    importlib.import_module('template_literature_meta_analysis.literature.models')
    if mode == 'cached-descendant':
        sys.modules.pop('template_literature_meta_analysis')
        sys.modules.pop('template_literature_meta_analysis.literature')
paths_before, finders_before = list(sys.path), list(sys.meta_path)
spec = importlib.util.spec_from_file_location('_owned_literature_regression', regression)
module = importlib.util.module_from_spec(spec)
if mode != 'siblings':
    try:
        spec.loader.exec_module(module)
    except ValueError as error:
        assert 'canonical Literature source origin differs' in str(error), str(error)
    else:
        raise AssertionError('canonical cached shadow source was accepted')
    if mode != 'wrong-own-alias':
        assert (shadow / 'canonical-marker.txt').read_text() == 'actual canonical shadow executed'
    else:
        assert sys.modules['template_literature_meta_analysis.literature.corpus'] is real_models
        assert not (shadow / 'canonical-marker.txt').exists()
    assert not hasattr(module, 'Corpus'), 'refusal must precede domain bindings'
    print('canonical cached shadow refused: ' + mode)
else:
    spec.loader.exec_module(module)
    for name, sibling in siblings.items():
        assert sys.modules[name] is sibling
        assert (shadow / (name + '-marker.txt')).read_text() == 'actual sibling executed'
    assert sys.path == paths_before and sys.meta_path == finders_before
    assert '_literature_meta_analysis_src' not in sys.modules
    for value in (module.Corpus, module.Paper, module.descriptive_stats, module.citation_distribution, module.compute_temporal_metrics):
        imported = sys.modules[value.__module__]
        assert Path(imported.__file__).resolve().is_relative_to(source.resolve()), imported.__file__
        assert value.__module__.startswith('template_literature_meta_analysis.')
    pins = json.loads((root / 'tests/regression/pinned_values/template_literature_meta_analysis.json').read_text())
    papers = module.Corpus.load(module._FIXTURE_CORPUS).papers
    stats = module.descriptive_stats(papers)
    load_pins = lambda name: pins if name == 'template_literature_meta_analysis' else None
    module.test_field_overview_size_and_identifier_claims_rederive_from_source(load_pins, papers, stats)
    module.test_descriptive_bibliometrics_citation_claims_rederive_from_source(load_pins, papers, stats)
    module.test_field_overview_peak_year_claim_rederives_from_source(load_pins, papers)
    module.test_pin_mutation_negative_control_fails(load_pins)
    print('canonical real source and original numerical pins accepted with live sibling shadows')
verify_fresh_module_bytecode(root / 'infrastructure', Path(sys.pycache_prefix))
verify_fresh_module_bytecode(source, Path(sys.pycache_prefix))
verify_fresh_module_bytecode(regression, Path(sys.pycache_prefix))
verify_fresh_module_bytecode(shadow, Path(sys.pycache_prefix))
"""


def _run_probe(tmp_path: Path, mode: str) -> str:
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    for name in ("analysis", "literature", "config"):
        module = shadow / (name + ".py")
        module.write_text(
            "from pathlib import Path\n"
            f"Path({str(shadow / (name + '-marker.txt'))!r}).write_text('actual sibling executed')\n",
            encoding="utf-8",
        )
    package = shadow / "template_literature_meta_analysis"
    (package / "literature").mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "literature/__init__.py").write_text("", encoding="utf-8")
    (package / "literature/models.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(shadow / 'canonical-marker.txt')!r}).write_text('actual canonical shadow executed')\n",
        encoding="utf-8",
    )
    prefix = tmp_path / "cache"
    prefix.mkdir()
    bootstrap = bytecode_audit_bootstrap((_ROOT / "infrastructure", _SOURCE, _REGRESSION, shadow), prefix)
    observed = run_with_policy(
        [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={prefix}",
            "-c",
            bootstrap + _PROBE,
            str(_ROOT),
            str(shadow),
            mode,
        ],
        cwd=tmp_path,
        env=None,
        policy=SubprocessPolicy(
            policy_id="literature-regression-source-import-control",
            source_path="tests/infra_tests/regression/test_literature_source_imports.py",
            timeout_seconds=90,
            credential_free=True,
        ),
    )
    assert not observed.timed_out, observed
    assert observed.returncode == 0, observed.stdout + observed.stderr
    return observed.stdout.strip()


def test_canonical_source_numerical_bindings_ignore_live_generic_sibling_shadows(tmp_path: Path) -> None:
    assert _run_probe(tmp_path, "siblings") == (
        "canonical real source and original numerical pins accepted with live sibling shadows"
    )


@pytest.mark.parametrize("mode", ["cached-package", "cached-descendant", "wrong-own-alias"])
def test_canonical_cached_source_from_actual_shadow_tree_is_refused(tmp_path: Path, mode: str) -> None:
    assert _run_probe(tmp_path, mode) == "canonical cached shadow refused: " + mode

"""Select the environment SDK and register only this genuine own namespace.

No inferred repository or own src directory is added to global import paths.
The declared platform 4.0.1 SDK must be available before own package execution.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import sysconfig
from pathlib import Path
from types import ModuleType

_PACKAGE = "template_template"


def _verify_cached_namespace(source: Path) -> ModuleType | None:
    """Bind each cached canonical fullname to its actual source and search path."""
    selected = sys.modules.get(_PACKAGE)
    for name, loaded in tuple(sys.modules.items()):
        if name != _PACKAGE and not name.startswith(_PACKAGE + "."):
            continue
        if not isinstance(loaded, ModuleType) or (name != _PACKAGE and selected is None):
            raise ImportError("canonical own namespace has an unsupported or orphan cached module")
        suffix = name.removeprefix(_PACKAGE).lstrip(".")
        parts = suffix.split(".") if suffix else []
        if any(not part.isidentifier() for part in parts):
            raise ImportError("canonical own module identity differs")
        location = source.joinpath(*parts)
        package_init = location / "__init__.py"
        is_package = package_init.is_file()
        expected_origin = package_init if is_package else location.with_suffix(".py")
        origin, spec = getattr(loaded, "__file__", None), getattr(loaded, "__spec__", None)
        if (
            not isinstance(origin, str)
            or not expected_origin.is_file()
            or Path(origin).resolve(strict=True) != expected_origin
            or getattr(spec, "origin", None) != origin
        ):
            raise ImportError("canonical own source origin differs")
        if (
            loaded.__name__ != name
            or getattr(spec, "name", None) != name
            or loaded.__package__ != (name if is_package else name.rsplit(".", 1)[0])
        ):
            raise ImportError("canonical own module identity differs")
        paths, spec_paths = getattr(loaded, "__path__", None), getattr(spec, "submodule_search_locations", None)
        if is_package:
            if (
                paths is None
                or spec_paths is None
                or any(
                    [Path(path).resolve(strict=True) for path in actual] != [location] for actual in (paths, spec_paths)
                )
            ):
                raise ImportError("canonical own source search path differs")
        elif paths is not None or spec_paths is not None:
            raise ImportError("canonical own module search path differs")
    return selected


def bootstrap_project(project: Path) -> ModuleType:
    project = project.resolve(strict=True)
    owner = Path(__file__).resolve(strict=True).parent.parent
    own_roots = (project, owner)
    # The selected own environment can live under project/.venv. Keep only its
    # actual runtime site roots when filtering authored project import paths.
    runtime_paths = sysconfig.get_paths()
    runtime_sites = {Path(runtime_paths[key]).resolve(strict=True) for key in ("purelib", "platlib")}
    original = sys.path[:]
    try:
        sys.path[:] = [
            entry
            for entry in original
            if Path(entry or os.getcwd()).resolve() in runtime_sites
            or not any(Path(entry or os.getcwd()).resolve().is_relative_to(own) for own in own_roots)
        ]
        sdk = importlib.import_module("infrastructure")
        if not isinstance(sdk.__file__, str):
            raise ImportError("declared platform SDK requires its actual source origin")
        sdk_origin = Path(sdk.__file__).resolve(strict=True)
        if any(sdk_origin.is_relative_to(own) for own in own_roots) and not any(
            sdk_origin.is_relative_to(site) for site in runtime_sites
        ):
            raise ImportError("own project source cannot provide the declared platform SDK")
        if sdk.__version__ != "4.0.1":
            raise ImportError("the own project requires its declared platform 4.0.1 SDK")
    finally:
        sys.path[:] = original
    source = project / "src" / _PACKAGE
    for candidate in (project / "src", source, source / "__init__.py"):
        if candidate.is_symlink() or not candidate.exists():
            raise ImportError("canonical own source cannot be missing or redirected")
    if not source.is_dir() or not (source / "__init__.py").is_file():
        raise ImportError("canonical own source requires its real package directory and initializer")
    if _verify_cached_namespace(source) is not None:
        return sdk
    origin = source / "__init__.py"
    spec = importlib.util.spec_from_file_location(_PACKAGE, origin, submodule_search_locations=[str(source)])
    if spec is None or spec.loader is None:
        raise ImportError("actual own package cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(_PACKAGE, None)
        raise
    _verify_cached_namespace(source)
    return sdk

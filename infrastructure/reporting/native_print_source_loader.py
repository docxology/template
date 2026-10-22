"""Load only held current print-source Python; existing pyc cannot substitute.

The enclosing native owner admits source body/mode/origin before and after
rendering. This confined loader compiles those actual bodies for every selected
project import; its own execution belongs to the admitted SDK Code closure.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import CodeType, ModuleType
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined

MAX_SOURCE_BYTES = 512 * 1024


class PrintSourceLoader(importlib.machinery.SourceFileLoader):
    """Compile confined actual source bytes without reading or writing pyc."""

    def __init__(self, name: str, path: Path, root: Path) -> None:
        super().__init__(name, str(path))
        self.root = root

    def exec_module(self, module: ModuleType) -> None:
        """Describe actual cacheless execution before compiling held Source.

        Importlib's location-based spec supplies a cache pathname even though
        this loader neither consumes nor writes it. The executed-code audit
        must see the actual cacheless module rather than that phantom cache.
        """
        spec = getattr(module, "__spec__", None)
        if isinstance(spec, importlib.machinery.ModuleSpec):
            # A location-based spec lazily recreates cached even after assigning
            # None. Keep the actual origin/__file__, but declare this loader's
            # cacheless execution explicitly on both metadata surfaces.
            spec.has_location = False
            spec.cached = None
        setattr(module, "__cached__", None)
        super().exec_module(module)

    def get_code(self, fullname: str) -> CodeType:
        path = Path(self.get_filename(fullname))
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(self.root):
            raise ValueError("print source Python body escaped its admitted project package")
        content = read_bytes_confined(self.root, path, max_bytes=MAX_SOURCE_BYTES)
        return compile(content, str(path), "exec", dont_inherit=True)


class _PrintSourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, label: str, source: Path) -> None:
        self.label, self.source = label, source

    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> Any:
        del path, target
        if fullname != self.label and not fullname.startswith(self.label + "."):
            return None
        relative = fullname.removeprefix(self.label).lstrip(".").split(".") if fullname != self.label else []
        candidate = self.source.joinpath(*relative)
        package = candidate / "__init__.py"
        module = candidate.with_suffix(".py")
        if package.is_file():
            return importlib.util.spec_from_file_location(
                fullname,
                package,
                loader=PrintSourceLoader(fullname, package, self.source),
                submodule_search_locations=[str(candidate)],
            )
        if module.is_file() and relative:
            return importlib.util.spec_from_file_location(
                fullname,
                module,
                loader=PrintSourceLoader(fullname, module, self.source),
            )
        raise ImportError("print source import is not an admitted Python module/package")


def load_print_source(project: Path, name: str, identity: str) -> Any:
    """Keep each real project source namespace separate and source-byte bound."""
    if name not in {"storybook", "newspaper"}:
        raise ValueError("unknown admitted print source provider")
    source = project.resolve(strict=True) / "src" / name
    if source.is_symlink() or source.resolve(strict=True) != source:
        raise ValueError("print source package is an unadmitted alias")
    label = "_native_print_" + hashlib.sha256((str(source) + identity).encode()).hexdigest()
    if not any(isinstance(finder, _PrintSourceFinder) and finder.label == label for finder in sys.meta_path):
        sys.meta_path.insert(0, _PrintSourceFinder(label, source))
    return importlib.import_module(label + (".rendering" if name == "storybook" else ".engine"))

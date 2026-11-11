"""Runtime version from the distribution's canonical package metadata."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib

try:
    __version__ = version("research-project-template")
except PackageNotFoundError:
    __version__ = tomllib.loads((Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]

if not isinstance(__version__, str) or not __version__.strip():
    raise ValueError("Package metadata must declare a non-empty version")

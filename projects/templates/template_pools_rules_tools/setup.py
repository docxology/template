"""Setuptools orchestration for the exemplar's declared public resource bundle."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

project = Path(__file__).parent.resolve()
spec = spec_from_file_location(
    "_resource_bundle", project / "src/template_pools_rules_tools/resource_paths.py"
)
assert spec is not None and spec.loader is not None
resource_bundle = module_from_spec(spec)
spec.loader.exec_module(resource_bundle)


class BuildPublicResources(build_py):
    """Delegate public admission/copy policy to the package's tested implementation."""

    def run(self):
        super().run()
        resource_bundle.bundle_public_resources(
            project, Path(self.build_lib) / "template_pools_rules_tools/_template_resources"
        )


setup(cmdclass={"build_py": BuildPublicResources})

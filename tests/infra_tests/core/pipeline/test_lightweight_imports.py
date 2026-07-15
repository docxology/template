"""Import-budget regression tests for the pipeline package."""

from __future__ import annotations

import json
import subprocess
import sys


def test_importing_pipeline_types_does_not_load_scientific_stack() -> None:
    """Leaf type imports stay independent of reporting and plotting packages."""
    code = "import json, sys; import infrastructure.core.pipeline.types; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(  # nosec B603
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    modules = set(json.loads(result.stdout.strip().splitlines()[-1]))
    prohibited = {"matplotlib", "numpy", "PIL", "infrastructure.reporting"}
    assert not {root for root in prohibited if any(name == root or name.startswith(f"{root}.") for name in modules)}

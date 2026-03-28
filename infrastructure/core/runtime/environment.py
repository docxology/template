"""Environment setup and validation utilities.

Validates dependencies, build tools, and directory structure for the research template.
Use this module to check or install requirements before running the pipeline.

Implementation is split across focused submodules:
- ``_python_env``: Python version, interpreter, uv, subprocess env
- ``_directories``: Directory setup, validation, structure verification
- ``_packages``: Package installation, env vars, build tools
"""

from __future__ import annotations

# Re-export from _python_env
from infrastructure.core.runtime._python_env import (  # noqa: F401
    check_python_version,
    check_uv_available,
    get_python_command,
    get_subprocess_env,
    validate_interpreter,
)

# Re-export from _directories
from infrastructure.core.runtime._directories import (  # noqa: F401
    setup_directories,
    validate_directory_structure,
    verify_source_structure,
)

# Re-export from _packages
from infrastructure.core.runtime._packages import (  # noqa: F401
    check_build_tools,
    install_missing_packages,
    set_environment_variables,
    validate_uv_sync_result,
)

# Re-export from env_deps (was already here)
from infrastructure.core.runtime.env_deps import check_dependencies  # noqa: F401

"""OS-appropriate installation command generation.

Standalone module with no infrastructure dependencies — safe to import from
exceptions.py without creating circular import cycles.
"""

from __future__ import annotations

import shutil


def build_install_commands(dependency: str) -> list[str]:
    """Return OS-appropriate installation commands for a dependency."""
    import platform

    commands: list[str] = []
    system = platform.system().lower()

    if system == "linux":
        if shutil.which("apt-get"):
            commands.append(f"sudo apt-get update && sudo apt-get install -y {dependency}")
        elif shutil.which("yum"):
            commands.append(f"sudo yum install -y {dependency}")
        elif shutil.which("dnf"):
            commands.append(f"sudo dnf install -y {dependency}")
        elif shutil.which("pacman"):
            commands.append(f"sudo pacman -S {dependency}")
        else:
            commands.append(f"# Install {dependency} using your package manager")
    elif system == "darwin":
        if shutil.which("brew"):
            commands.append(f"brew install {dependency}")
        else:
            commands.append(f"# Install {dependency} using Homebrew: brew install {dependency}")
    else:
        commands.append(f"# Install {dependency} using your system's package manager")

    commands.append(f"which {dependency}  # Verify installation")
    return commands

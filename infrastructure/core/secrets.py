"""Shared credential-name classification for bounded subprocess environments."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence

_SECRET_ENV_NAME = re.compile(
    r"(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|PRIVATE[_-]?KEY|CREDENTIAL)",
    re.IGNORECASE,
)

# These names contain security-adjacent words in some CI/tooling environments
# but are not credentials and must remain available to child processes.
_KNOWN_BENIGN = frozenset({"MPLCONFIGDIR", "CI", "CIRCLECI", "GITHUB_ACTIONS"})


def is_secret_env_name(name: str) -> bool:
    """Return whether *name* conventionally identifies a credential."""
    return bool(_SECRET_ENV_NAME.search(name)) and name not in _KNOWN_BENIGN


def strip_secret_env(
    base_env: Mapping[str, str] | None = None,
    *,
    allow_secret_names: Sequence[str] = (),
    passthrough: Sequence[str] = (),
) -> dict[str, str]:
    """Copy an environment while removing credential-like variable names."""
    env = dict(os.environ if base_env is None else base_env)
    allowed = set(allow_secret_names) | set(passthrough)
    for key in tuple(env):
        if key not in allowed and is_secret_env_name(key):
            env.pop(key, None)
    return env


__all__ = ["is_secret_env_name", "strip_secret_env"]

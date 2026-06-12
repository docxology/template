"""Deterministic build-time resolution — one source of truth for reproducibility.

Research outputs that claim to be *reproducible* must be byte-stable across runs
with identical inputs. The enemy is the wall clock: xelatex stamps a
``/CreationDate`` into every PDF, manuscripts render a ``GENERATION_TIMESTAMP``,
and data writers default to ``datetime.now()`` — so two runs of the same project
produce different bytes and the repro-bundle hashes churn.

This module centralizes the fix around the cross-ecosystem
`SOURCE_DATE_EPOCH <https://reproducible-builds.org/specs/source-date-epoch/>`_
standard (which xelatex/LuaTeX honor natively for ``/CreationDate``):

- :func:`resolve_source_date_epoch` — the canonical epoch (int seconds) or
  ``None`` for wall-clock mode.
- :func:`resolve_build_timestamp` — an ISO-8601 string derived from that epoch
  (for ``GENERATION_TIMESTAMP``, title-page dates, ``generated_at`` fields).
- :func:`deterministic_subprocess_env` — a subprocess ``env`` mapping with
  ``SOURCE_DATE_EPOCH`` injected, to pass to xelatex/biber.

**Precedence** (highest first):

1. An already-set ``SOURCE_DATE_EPOCH`` environment variable (honored verbatim —
   lets a CI or an outer build pin the value).
2. Deterministic mode (``deterministic=True`` or ``TEMPLATE_DETERMINISTIC`` truthy):
   the author-date epoch of ``HEAD`` (``git log -1 --format=%ct``).
3. Otherwise wall-clock (non-deterministic) — the historical behavior.

If deterministic mode is requested but git is unavailable, the functions fall
back to wall-clock and emit a single warning, so the degradation is auditable.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

__all__ = [
    "TEMPLATE_DETERMINISTIC_ENV",
    "deterministic_subprocess_env",
    "is_deterministic_requested",
    "resolve_build_timestamp",
    "resolve_source_date_epoch",
]

TEMPLATE_DETERMINISTIC_ENV = "TEMPLATE_DETERMINISTIC"
_SOURCE_DATE_EPOCH_ENV = "SOURCE_DATE_EPOCH"
_TRUTHY = {"1", "true", "yes", "on"}
_ISO_Z = "%Y-%m-%dT%H:%M:%SZ"


def is_deterministic_requested(deterministic: bool | None = None) -> bool:
    """Resolve the tri-state determinism flag against the environment.

    ``True``/``False`` force the mode; ``None`` consults ``TEMPLATE_DETERMINISTIC``.
    A pre-set ``SOURCE_DATE_EPOCH`` also implies deterministic mode.
    """
    if deterministic is not None:
        return deterministic
    if os.environ.get(_SOURCE_DATE_EPOCH_ENV, "").strip():
        return True
    return os.environ.get(TEMPLATE_DETERMINISTIC_ENV, "").strip().lower() in _TRUTHY


def _git_head_epoch(repo_root: Path) -> int | None:
    try:
        result = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "log", "-1", "--format=%ct"],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError) as exc:
        logger.warning("Deterministic build requested but git invocation failed (%s); using wall-clock.", exc)
        return None
    if result.returncode != 0:
        logger.warning("Deterministic build requested but 'git log' returned %s; using wall-clock.", result.returncode)
        return None
    raw = result.stdout.strip()
    try:
        return int(raw)
    except ValueError:
        logger.warning("Deterministic build: unparseable git epoch %r; using wall-clock.", raw)
        return None


def resolve_source_date_epoch(
    *,
    deterministic: bool | None = None,
    repo_root: Path | None = None,
) -> int | None:
    """Return the deterministic epoch (UTC seconds), or ``None`` for wall-clock.

    A pre-set ``SOURCE_DATE_EPOCH`` wins outright. Otherwise, in deterministic
    mode, the ``HEAD`` commit epoch is used. Returns ``None`` when not in
    deterministic mode (or when git lookup fails).
    """
    preset = os.environ.get(_SOURCE_DATE_EPOCH_ENV, "").strip()
    if preset:
        try:
            return int(preset)
        except ValueError:
            logger.warning("Ignoring non-integer SOURCE_DATE_EPOCH=%r.", preset)
    if not is_deterministic_requested(deterministic):
        return None
    return _git_head_epoch(Path(repo_root) if repo_root is not None else Path.cwd())


def resolve_build_timestamp(
    *,
    deterministic: bool | None = None,
    repo_root: Path | None = None,
    fmt: str = _ISO_Z,
) -> str:
    """Return a build timestamp string (default strict-ISO8601 ``Z``).

    Deterministic mode renders the ``SOURCE_DATE_EPOCH`` / ``HEAD`` epoch in UTC;
    otherwise the current wall-clock UTC time. Pass ``fmt`` (e.g. ``"%Y-%m-%d"``)
    for a date-only value such as a title page.
    """
    epoch = resolve_source_date_epoch(deterministic=deterministic, repo_root=repo_root)
    moment = datetime.fromtimestamp(epoch, tz=timezone.utc) if epoch is not None else datetime.now(timezone.utc)
    return moment.strftime(fmt)


def deterministic_subprocess_env(
    base_env: dict[str, str] | None = None,
    *,
    deterministic: bool | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Return a subprocess ``env`` with ``SOURCE_DATE_EPOCH`` set when deterministic.

    Pass the result as ``subprocess.run(..., env=...)`` for xelatex/biber so the
    embedded ``/CreationDate`` is pinned. In wall-clock mode this is a faithful
    copy of ``base_env`` (default ``os.environ``) with nothing added — a safe
    no-op, so call sites can always route through it.
    """
    env = dict(base_env if base_env is not None else os.environ)
    epoch = resolve_source_date_epoch(deterministic=deterministic, repo_root=repo_root)
    if epoch is not None:
        env[_SOURCE_DATE_EPOCH_ENV] = str(epoch)
    return env

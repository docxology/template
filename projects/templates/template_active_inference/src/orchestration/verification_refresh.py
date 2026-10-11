"""In-session fixed-point refresh bookkeeping for verification generators.

This cache is local to one verification workflow; it does not authorize
persistent analysis reuse or replace the enclosing execution/source guards.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from pathlib import Path

_REFRESHABLE_GENERATORS = frozenset(
    {
        "compose_manuscript.py",
        "z_generate_manuscript_variables.py",
        "generate_figures.py",
        "generate_method_inventory.py",
    }
)

_GENERATOR_OBSERVER_FLAGS = frozenset({"--check", "--list-tracks", "--validate-only"})

_FINGERPRINT_EXCLUDED_PARTS = frozenset({".git", ".pytest_cache", ".venv", "htmlcov", "__pycache__"})


def _project_state_fingerprint(project_root: Path) -> str:
    """Return a deterministic source/output fingerprint for refresh caching.

    The fingerprint intentionally includes both inputs and generated contract
    outputs. A refresh is skipped only when the exact same generator already
    observed this byte state after a successful run, so a downstream producer
    changing any contract artifact naturally invalidates the cache.
    """
    digest = hashlib.sha256()
    for path in sorted(project_root.rglob("*")):
        if not path.is_file() or _FINGERPRINT_EXCLUDED_PARTS.intersection(path.parts):
            continue
        if path.name.startswith(".coverage"):
            continue
        relative = path.relative_to(project_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        try:
            digest.update(path.read_bytes())
        except OSError:
            # A concurrently written disposable output will be reflected by
            # the next fingerprint; never turn cache bookkeeping into a gate.
            continue
        digest.update(b"\0")
    return digest.hexdigest()


def _generator_name(command: list[str]) -> str | None:
    """Return the refreshable script name in a command, if any."""
    if _GENERATOR_OBSERVER_FLAGS.intersection(command):
        return None
    for part in command:
        name = Path(part).name
        if name in _REFRESHABLE_GENERATORS:
            return name
    return None


class RefreshCache:
    """In-run fixed-point cache for idempotent generator commands."""

    def __init__(self, *, clock: Callable[[], float] = time.perf_counter) -> None:
        """Initialize an empty in-run refresh cache."""
        self._last_outputs: dict[str, str] = {}
        self._clock = clock
        self._events: list[dict[str, object]] = []

    def run(
        self,
        project_root: Path,
        command: list[str],
        label: str,
        command_runner: Callable[..., None],
    ) -> None:
        """Run a generator command, skipping it when the project state is unchanged.

        If the command's generator is refreshable and the project fingerprint
        matches the last observed state for that generator, the command is
        skipped.  Otherwise the command is executed and the new fingerprint
        is cached.
        """
        generator = _generator_name(command)
        if generator is None:
            started = self._clock()
            command_runner(project_root, command, label)
            self._events.append(
                {
                    "label": label,
                    "generator": None,
                    "action": "ran",
                    "elapsed_seconds": round(self._clock() - started, 6),
                }
            )
            return
        before = _project_state_fingerprint(project_root)
        if self._last_outputs.get(generator) == before:
            print(f"\n==> {label}\n    fixed point unchanged; skipped {generator}")
            self._events.append({"label": label, "generator": generator, "action": "skipped", "elapsed_seconds": 0.0})
            return
        started = self._clock()
        command_runner(project_root, command, label)
        self._last_outputs[generator] = _project_state_fingerprint(project_root)
        self._events.append(
            {
                "label": label,
                "generator": generator,
                "action": "ran",
                "elapsed_seconds": round(self._clock() - started, 6),
            }
        )

    def receipt(self, *, baseline_seconds: float | None = None) -> dict[str, object]:
        """Return timing/cache evidence without making a performance claim."""
        elapsed_values: list[float] = []
        for event in self._events:
            elapsed = event.get("elapsed_seconds")
            if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool):
                raise ValueError("refresh receipt elapsed_seconds must be numeric")
            elapsed_values.append(float(elapsed))
        observed = round(sum(elapsed_values), 6)
        reduction = None
        target_met = None
        if baseline_seconds is not None and baseline_seconds > 0:
            reduction = round(1.0 - observed / baseline_seconds, 6)
            target_met = reduction >= 0.30
        return {
            "schema_version": "template-active-inference/refresh-receipt/1",
            "events": tuple(self._events),
            "observed_seconds": observed,
            "baseline_seconds": baseline_seconds,
            "reduction_fraction": reduction,
            "target_reduction_fraction": 0.30,
            "target_met": target_met,
        }


__all__ = ["RefreshCache"]

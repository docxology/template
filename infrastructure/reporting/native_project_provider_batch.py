"""Fixed preimport project-provider selection under one closed Source boundary.

The batch returns no observations before every selection and the original
Source/SDK/fixture closing checks pass. Worker and reader use-time guards remain
independent; this factory does not cache Source verification across operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_dependencies import (
    admit_runtime_providers,
    runtime_provider_roots,
)
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_preparation_progress import preparation_progress
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile


def admitted_native_provider_batch(
    context: NativeSourceContext,
    scopes: tuple[str, ...],
    wheels: Mapping[str, Path],
    interpreter: Path,
    *,
    deadline: float,
) -> dict[str, tuple[dict[str, Any], tuple[Path, ...]]]:
    """Admit a complete fixed public selection before any payload is executed."""
    remaining(deadline)
    if (
        not isinstance(context, NativeSourceContext)
        or not isinstance(scopes, tuple)
        or not scopes
        or any(not isinstance(scope, str) or scope not in PUBLIC_PROJECT_NAMES for scope in scopes)
        or len(set(scopes)) != len(scopes)
        or not isinstance(interpreter, Path)
    ):
        raise ValueError("native provider batch requires genuine Source and distinct public scopes")
    root = context.bindings.current_root
    reader = context.current_source_reader
    preparation_progress("project-providers", "source-opening", deadline)
    # One lexical guard brackets this fixed synchronous DATA batch.
    # No result/capability escapes before its complete closing checks.
    with context._correspondence_guard(context.reference, root, reader, deadline):
        preparation_progress("project-providers", "profile", deadline)
        requirements, faults = required_profile(root, reader, source_fingerprint(root))
        if faults:
            raise ValueError("native provider batch needs the complete current source profile")
        lookup = {row.id: row for row in requirements}
        # Freeze the nominated mapping itself, without interpreting receipt DATA as
        # provider authority. Every actual wheel is still inspected by the factory.
        nominations = dict(wheels)
        result: dict[str, tuple[dict[str, Any], tuple[Path, ...]]] = {}
        for scope in scopes:
            remaining(deadline)
            preparation_progress("project-providers", "selection", deadline, scope)
            providers = admit_runtime_providers(root, scope, nominations, lookup, reader)
            result[scope] = providers, runtime_provider_roots(root, providers, interpreter)
        # Re-observe earlier items after the last selection. Source reader retains
        # wheel/source snapshots, including physical identity and ancestor guards.
        for scope in scopes:
            remaining(deadline)
            preparation_progress("project-providers", "selection-closing", deadline, scope)
            providers = admit_runtime_providers(root, scope, nominations, lookup, reader)
            if result[scope] != (providers, runtime_provider_roots(root, providers, interpreter)):
                raise ValueError("native project provider selection changed during batch admission")
        preparation_progress("project-providers", "source-closing", deadline)
    remaining(deadline)
    preparation_progress("project-providers", "completed", deadline)
    return result

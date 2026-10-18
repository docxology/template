"""Exact selected, bounded and audited Popen environment commitments.

Only an authenticated original ToolAPI gives these records authority. Values
are hashed; the only retained raw identifiers are ephemeral guardian run IDs.
The selected Source map is distinct from each actual injected environment.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, TYPE_CHECKING

from infrastructure.core._bounded_kill import _RUN_IDS_ENV
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.core.secrets import strip_secret_env, is_secret_env_name
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_loader_observation import NativeLoaderObservation

SCHEMA = "template-native-actual-environment-custody-v1"
_LOADER_KEYS = frozenset(
    {
        "LD_AUDIT",
        "TEMPLATE_LOADER_TOKEN",
        "TEMPLATE_LOADER_SOCKET",
        "TEMPLATE_LOADER_DEADLINE_NS",
        "TEMPLATE_LOADER_OWNER_PID",
    }
)


def value_commitment(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _commitments(env: dict[str, str]) -> dict[str, str]:
    if len(env) > 4096 or sum(len(key.encode()) + len(value.encode()) for key, value in env.items()) > 1024 * 1024:
        raise ValueError("actual native environment exceeds its finite commitment ceiling")
    if any(not key or "=" in key or "\0" in key or "\0" in value for key, value in env.items()):
        raise ValueError("native environment contains an invalid actual Popen member")
    return {key: value_commitment(env[key]) for key in sorted(env)}


def loader_environment_injections(loader: NativeLoaderObservation) -> dict[str, str]:
    """The exact overlay selected by the concrete Source consuming observer."""
    return {
        "LD_AUDIT": str(loader.compiled.library),
        "TEMPLATE_LOADER_TOKEN": loader.token.decode("ascii"),
        "TEMPLATE_LOADER_SOCKET": loader.address,
        "TEMPLATE_LOADER_DEADLINE_NS": str(int(loader.deadline * 1_000_000_000)),
        "TEMPLATE_LOADER_OWNER_PID": str(loader.owner_pid),
    }


def capture_native_environment(
    source: dict[str, str],
    selected: dict[str, str],
    bounded: dict[str, str],
    actual: dict[str, str],
    token: str,
    loader: NativeLoaderObservation | None,
) -> dict[str, Any]:
    """Called immediately before the genuine supervisor passes this map to Popen."""
    if selected != strip_secret_env(source) or any(is_secret_env_name(key) for key in selected):
        raise ValueError("native selected environment differs from the Source credential-name policy")
    inherited_raw = selected.get(_RUN_IDS_ENV, "")
    inherited = inherited_raw.strip()
    expected = {**selected, _RUN_IDS_ENV: inherited + ":" + token if inherited else token}
    if re.fullmatch(r"[0-9a-f]{32}", token) is None or bounded != expected:
        raise ValueError("native guardian environment is not this exact unique inherited run chain")
    injections = None
    if loader is not None:
        injections = loader_environment_injections(loader)
        if _LOADER_KEYS & set(expected) or "LD_PRELOAD" in expected or any(key.startswith("DYLD_") for key in expected):
            raise ValueError("native loader environment contains preexisting ambient instrumentation")
        expected.update(injections)
    if actual != expected:
        raise ValueError("actual Popen environment differs from its exact Source bounded/audited transformation")
    return {
        "schema_version": SCHEMA,
        "source_selected_digest": canonical_digest(source),
        "source_allowed_commitments": _commitments(selected),
        "source_allowed_digest": canonical_digest(selected),
        "bounded_digest": canonical_digest(bounded),
        "actual_digest": canonical_digest(actual),
        "actual_commitments": _commitments(actual),
        "guardian_inherited_ids": inherited_raw,
        "guardian_run_token": token,
        "loader_injections": None if injections is None else _commitments(injections),
    }


def validate_native_environment(native: dict[str, Any], tool: dict[str, Any], reader: SnapshotReader) -> None:
    """Reconstruct the transformation after separately authenticating the OS owner."""
    from infrastructure.reporting.native_format_acceptance_validation import _file

    environment_digest = tool.get("environment_digest")
    if not isinstance(environment_digest, str) or re.fullmatch(r"[0-9a-f]{64}", environment_digest) is None:
        raise ValueError("native ToolAPI lacks its original Source-selected environment commitment")
    raw = native.get("environment_custody")
    fields = {
        "schema_version",
        "source_selected_digest",
        "source_allowed_commitments",
        "source_allowed_digest",
        "bounded_digest",
        "actual_digest",
        "actual_commitments",
        "guardian_inherited_ids",
        "guardian_run_token",
        "loader_injections",
    }
    if (
        not isinstance(raw, dict)
        or set(raw) != fields
        or raw["schema_version"] != SCHEMA
        or raw["source_selected_digest"] != environment_digest
    ):
        raise ValueError("native actual environment lacks its original Source-selected commitment")
    for name in ("source_selected_digest", "source_allowed_digest", "bounded_digest", "actual_digest"):
        if not isinstance(raw[name], str) or re.fullmatch(r"[0-9a-f]{64}", raw[name]) is None:
            raise ValueError("native whole-environment commitment is invalid")
    for name in ("source_allowed_commitments", "actual_commitments"):
        values = raw[name]
        if (
            not isinstance(values, dict)
            or len(values) > 4096
            or any(
                not isinstance(key, str)
                or not key
                or "=" in key
                or "\0" in key
                or not isinstance(value, str)
                or re.fullmatch(r"[0-9a-f]{64}", value) is None
                for key, value in values.items()
            )
        ):
            raise ValueError("native per-variable environment commitment is invalid")
    selected = raw["source_allowed_commitments"]
    if any(is_secret_env_name(key) for key in selected):
        raise ValueError("native Source allowlist retained a credential-like variable")
    inherited, token = raw["guardian_inherited_ids"], raw["guardian_run_token"]
    if (
        not isinstance(inherited, str)
        or len(inherited) > 4096
        or not isinstance(token, str)
        or re.fullmatch(r"[0-9a-f]{32}", token) is None
    ):
        raise ValueError("native guardian injection lacks its bounded ephemeral identity")
    if inherited.strip() and any(re.fullmatch(r"[0-9a-f]{32}", item) is None for item in inherited.strip().split(":")):
        raise ValueError("native guardian inherited identity chain is malformed")
    if _RUN_IDS_ENV in selected and selected[_RUN_IDS_ENV] != value_commitment(inherited):
        raise ValueError("native guardian inherited chain differs from selected Source environment")
    if _RUN_IDS_ENV not in selected and inherited:
        raise ValueError("native guardian claimed an absent inherited Source identity")
    inherited = inherited.strip()
    expected = {**selected, _RUN_IDS_ENV: value_commitment(inherited + ":" + token if inherited else token)}
    injections = raw["loader_injections"]
    if native.get("loader_lifecycle") is None:
        if injections is not None or expected != raw["actual_commitments"]:
            raise ValueError("ordinary actual native environment carries unqualified loader injections")
    else:
        lifecycle = _file(native["loader_lifecycle"], reader).json_object()
        compilation = _file(lifecycle["compiler"], reader).json_object()
        compiler = _file(compilation["compiler"], reader).json_object()
        library = str(Path(compiler["cwd"]) / Path(compilation["library"]["path"]).name)
        if (
            not isinstance(injections, dict)
            or set(injections) != _LOADER_KEYS
            or injections != lifecycle.get("environment_injections")
        ):
            raise ValueError("actual native audit injection differs from its original consuming loader owner")
        if any(key in selected for key in _LOADER_KEYS | {"LD_PRELOAD"}) or any(
            key.startswith("DYLD_") for key in selected
        ):
            raise ValueError("selected Source environment contained ambient loader instrumentation")
        if any(
            injections[key] != expected_value
            for key, expected_value in {
                "LD_AUDIT": value_commitment(library),
                "TEMPLATE_LOADER_TOKEN": lifecycle["token_sha256"],
                "TEMPLATE_LOADER_OWNER_PID": value_commitment(str(native["owner_pid"])),
                "TEMPLATE_LOADER_DEADLINE_NS": value_commitment(
                    str(int(native["original_deadline_monotonic"] * 1_000_000_000))
                ),
            }.items()
        ):
            raise ValueError("actual audit variables differ from their Source compiler/peer/token/owner/clock")
        if any(
            not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None for value in injections.values()
        ):
            raise ValueError("actual audit variable commitment is malformed")
        expected.update(injections)
        if expected != raw["actual_commitments"]:
            raise ValueError("actual audited Popen environment is not the exact committed bounded transformation")


HOSTED_READER_SCHEMA = "template-fixed-hosted-reader-environment-v1"


def _capture_hosted_reader_environment(
    source: dict[str, str],
    selected: dict[str, str],
    bounded: dict[str, str],
    actual: dict[str, str],
    token: str,
) -> dict[str, Any]:
    """Private fixed-reader overlay; ordinary native custody remains credential-free."""
    from infrastructure.reporting.native_source_provider_bootstrap import NATIVE_READER_MODULE

    ordinary = capture_native_environment(source, selected, bounded, bounded, token, None)
    credentials = {"GH_TOKEN": source["GH_TOKEN"]} if source.get("GH_TOKEN") else {}
    if actual != {**bounded, **credentials}:
        raise ValueError("fixed hosted reader differs from its exact nominated credential transformation")
    return {
        "schema_version": HOSTED_READER_SCHEMA,
        "reader_role": NATIVE_READER_MODULE,
        "ordinary": ordinary,
        "credential_commitments": _commitments(credentials),
        "actual_commitments": _commitments(actual),
        "actual_digest": canonical_digest(actual),
    }


def _validate_hosted_reader_environment(raw: dict[str, Any], source: dict[str, str]) -> None:
    """Check this actual parent's launch, never compare a later job's credentials."""
    selected = strip_secret_env(source)
    ordinary = raw.get("ordinary")
    if not isinstance(ordinary, dict) or not isinstance(ordinary.get("guardian_run_token"), str):
        raise ValueError("fixed hosted reader lacks its actual guardian environment")
    token = ordinary["guardian_run_token"]
    inherited = selected.get(_RUN_IDS_ENV, "").strip()
    bounded = {**selected, _RUN_IDS_ENV: inherited + ":" + token if inherited else token}
    actual = {**bounded, **({"GH_TOKEN": source["GH_TOKEN"]} if source.get("GH_TOKEN") else {})}
    if raw != _capture_hosted_reader_environment(source, selected, bounded, actual, token):
        raise ValueError("fixed hosted reader environment commitment changed")

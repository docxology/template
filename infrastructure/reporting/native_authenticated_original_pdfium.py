"""Authenticated hosted original PDFium inputs, distinct from live execution.

Only the actual exact-run authenticated hosted custodian composes this factory.
Retained original wheel/body/Code labels never select or open producer paths.
Current native execution uses its separate actual independently selected wheel.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_pdfium_source_wheel import (
    inspect_pdfium_source_wheel,
)
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)

if TYPE_CHECKING:
    from infrastructure.reporting.native_hosted_original_custody import (
        NativeHostedArtifactCustodian,
    )
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumSelection

_AUTHENTICATED = object()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True)
class NativeAuthenticatedOriginalPDFium:
    """Source-listed original byte capability held by the real hosted custodian."""

    source: NativeSourceContext
    scope: str
    selection: NativePDFiumSelection
    members: MappingProxyType[str, bytes]
    wheel: dict[str, Any]
    installed: dict[str, Any]
    inputs: dict[str, Any]
    custodian: NativeHostedArtifactCustodian
    seal: str
    deadline: float
    _key: object

    def held_inputs(self) -> dict[str, Any]:
        """Recheck genuine external Source/clock/membership; read no original path."""
        from infrastructure.reporting.native_hosted_original_custody import (
            NativeHostedArtifactCustodian,
        )

        remaining(self.deadline)
        if self._key is not _AUTHENTICATED or not isinstance(self.custodian, NativeHostedArtifactCustodian):
            raise ValueError("PDFium original inputs require the actual authenticated hosted collector factory")
        if self.deadline != self.custodian.deadline:
            raise ValueError("PDFium original input capability lost its exact collector clock")
        self.custodian.verify_source(self.source, scope=self.scope)
        current = self.custodian.original_pdfium_inputs(self.scope)
        hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in self.members.items()}
        if (
            current != self.inputs
            or _digest(self.inputs) != self.seal
            or self.wheel != self.inputs["wheel"]
            or self.installed != self.inputs["installed"]
            or self.inputs["member_hashes"] != hashes
            or self.inputs["site"] != str(self.selection.site)
            or self.inputs["wheel_path"] != str(self.selection.wheel)
        ):
            raise ValueError("PDFium original retained Source/provider inputs changed after genuine collection")
        remaining(self.deadline)
        value: dict[str, Any] = json.loads(json.dumps(self.inputs, allow_nan=False))
        return value

    @property
    def audit_roots(self) -> tuple[Path, ...]:
        """Original compilation labels only, never current execution selections."""
        from infrastructure.reporting.native_office_pdfium_provider import PROVIDERS

        self.held_inputs()
        return tuple(self.selection.site / name for name in PROVIDERS)


def admit_authenticated_original_pdfium(
    custodian: NativeHostedArtifactCustodian,
    source: NativeSourceContext,
    *,
    scope: str,
    deadline: float,
) -> NativeAuthenticatedOriginalPDFium:
    """Compose solely from actual authenticated origin and genuine current Source."""
    from infrastructure.reporting.native_hosted_original_custody import (
        NativeHostedArtifactCustodian,
    )
    from infrastructure.reporting.native_full_worker_pdfium import (
        NativePDFiumSelection,
        SCHEMA,
    )
    from infrastructure.reporting.native_office_pdfium_provider import (
        PROVIDERS,
        SCHEMA as INSTALLED_SCHEMA,
    )

    remaining(deadline)
    if not isinstance(custodian, NativeHostedArtifactCustodian) or not isinstance(source, NativeSourceContext):
        raise ValueError("PDFium hosted original factory requires its actual typed collector and Source admission")
    if deadline != custodian.deadline:
        raise ValueError("PDFium original input factory cannot renew or replace the genuine external reader clock")
    custodian.verify_source(source, scope=scope)
    original_binding = custodian.original_source_binding(scope)
    if original_binding[1:] != (
        source.reference.commit,
        source.reference.source_identity,
    ):
        raise ValueError("PDFium hosted original Source differs from independently admitted current Source")
    inputs = custodian.original_pdfium_inputs(scope)
    if not isinstance(inputs, dict) or set(inputs) != {
        "schema_version",
        "scope",
        "site",
        "wheel_path",
        "wheel",
        "installed",
        "source_commit",
        "source_identity",
        "member_hashes",
    }:
        raise ValueError("PDFium authenticated original input fields differ")
    if (
        inputs["schema_version"] != SCHEMA
        or inputs["scope"] != scope
        or (inputs["source_commit"], inputs["source_identity"]) != original_binding[1:]
    ):
        raise ValueError("PDFium authenticated original Source/scope identity differs")
    selection = NativePDFiumSelection(Path(inputs["site"]), Path(inputs["wheel_path"]))
    filename, body = custodian.read_original_pdfium_wheel(scope)
    if filename != selection.wheel.name:
        raise ValueError(
            "PDFium retained original wheel filename differs from authenticated independent original selection"
        )
    members, observed = inspect_pdfium_source_wheel(source, filename, body, deadline=deadline)
    wheel = inputs["wheel"]
    if (
        not isinstance(wheel, dict)
        or set(wheel) != {"path", "sha256", "bytes", "identity", "source_lock_sha256", "version"}
        or wheel["path"] != str(selection.wheel)
    ):
        raise ValueError("PDFium authenticated original wheel observation fields differ")
    if any(wheel[key] != value for key, value in observed.items()) or inputs["member_hashes"] != {
        name: hashlib.sha256(raw).hexdigest() for name, raw in members.items()
    }:
        raise ValueError("PDFium authenticated retained original body/Code differs from actual Source-listed wheel")
    installed = inputs["installed"]
    if installed["schema_version"] != INSTALLED_SCHEMA or installed["selection"] != {
        "site": str(selection.site),
        "version": wheel["version"],
        "origins": {name: str(selection.site / name / "__init__.py") for name in PROVIDERS},
    }:
        raise ValueError("PDFium genuine original installed selection differs from retained Source platform wheel")
    for label, raw in members.items():
        if label.endswith(".dist-info/RECORD"):
            continue
        file = installed["files"].get(label)
        if not isinstance(file, dict) or file["sha256"] != hashlib.sha256(raw).hexdigest() or file["bytes"] != len(raw):
            raise ValueError("PDFium original installed body differs from authenticated Source wheel")
    captured = json.loads(json.dumps(inputs, allow_nan=False))
    result = NativeAuthenticatedOriginalPDFium(
        source,
        scope,
        selection,
        MappingProxyType(members),
        captured["wheel"],
        captured["installed"],
        captured,
        custodian,
        _digest(captured),
        deadline,
        _AUTHENTICATED,
    )
    result.held_inputs()
    custodian.verify_source(source, scope=scope)
    remaining(deadline)
    return result

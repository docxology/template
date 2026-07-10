"""Optional adapter for the upstream Kmyth TPM sealing tools.

The bundled ``kmyth/`` directory is a git submodule that provides C
executables, not an importable Python package. This adapter keeps secure-run
integration optional: it can validate whether the submodule has been built or
whether Kmyth is installed on ``PATH``, and it can seal selected output
artifacts only when a project explicitly opts in.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

KMYTH_REPOSITORY_URL = "https://github.com/NationalSecurityAgency/kmyth"
KMYTH_SUBMODULE_DIRNAME = "kmyth"
KMYTH_SEAL = "kmyth-seal"
KMYTH_UNSEAL = "kmyth-unseal"
SUPPORTED_SEAL_ARTIFACTS = frozenset({"pdf", "hash_manifest"})
KMYTH_PREFIX = Path.home() / ".kmyth-prefix"


class KmythError(RuntimeError):
    """Base class for Kmyth integration failures."""


class KmythUnavailableError(KmythError):
    """Raised when Kmyth is requested but usable tools are unavailable."""


class KmythCommandError(KmythError):
    """Raised when a Kmyth command exits unsuccessfully."""


@dataclass(frozen=True)
class KmythAvailability:
    """Validation result for the optional Kmyth command-line tools."""

    source_dir: Path
    seal_path: Path | None
    unseal_path: Path | None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        """Return ``True`` when both seal and unseal executables are usable."""
        return self.seal_path is not None and self.unseal_path is not None and not self.errors

    def summary(self) -> str:
        """Return a concise human-readable validation summary."""
        if self.available:
            return f"Kmyth available: seal={self.seal_path}, unseal={self.unseal_path}"
        details = [*self.errors, *self.warnings]
        suffix = "; ".join(details) if details else "unknown validation failure"
        return f"Kmyth unavailable: {suffix}"


@dataclass(frozen=True)
class KmythSealOptions:
    """Runtime options for invoking ``kmyth-seal``."""

    binary_dir: Path | None = None
    source_dir: Path | None = None
    pcrs: tuple[int, ...] = ()
    cipher: str | None = None
    output_suffix: str = ".ski"
    overwrite: bool = True
    timeout_seconds: int = 120
    tcti_config: str | None = None
    """TCTI connection string for the TPM (e.g., ``mssim:host=127.0.0.1,port=2321``).

    When set, the adapter passes ``TSS2_TCTI_DEFAULT`` to the kmyth-seal
    subprocess so it connects to the specified TPM backend instead of
    attempting hardware TCTI auto-discovery.
    """

    @classmethod
    def from_config(cls, config: Any) -> "KmythSealOptions":
        """Build options from a :class:`SteganographyConfig`-like object."""
        binary_dir = _optional_path(getattr(config, "kmyth_binary_dir", None))
        source_dir = _optional_path(getattr(config, "kmyth_source_dir", None))
        return cls(
            binary_dir=binary_dir,
            source_dir=source_dir,
            pcrs=tuple(getattr(config, "kmyth_pcrs", ()) or ()),
            cipher=getattr(config, "kmyth_cipher", None) or None,
            output_suffix=getattr(config, "kmyth_output_suffix", ".ski") or ".ski",
            overwrite=bool(getattr(config, "kmyth_overwrite", True)),
            timeout_seconds=int(getattr(config, "kmyth_timeout_seconds", 120) or 120),
            tcti_config=getattr(config, "kmyth_tcti_config", None) or None,
        )


def default_kmyth_source_dir() -> Path:
    """Return the expected checkout path for the Kmyth git submodule."""
    return Path(__file__).resolve().parent / KMYTH_SUBMODULE_DIRNAME


def validate_kmyth_installation(
    *,
    binary_dir: str | Path | None = None,
    source_dir: str | Path | None = None,
) -> KmythAvailability:
    """Validate that Kmyth source and command-line tools are available.

    The adapter accepts either a built submodule at
    ``infrastructure/steganography/kmyth/bin`` or an installation on ``PATH``.
    The source checkout is reported because clean clones must initialize the
    submodule before building, but a system install can still be used if the
    checkout is absent.
    """
    bin_dir = _optional_path(binary_dir)
    src_dir = _optional_path(source_dir) or default_kmyth_source_dir()
    warnings: list[str] = []
    errors: list[str] = []

    if not src_dir.exists():
        warnings.append(
            f"Kmyth submodule source directory is missing at {src_dir}; run "
            "`git submodule update --init --recursive` or install kmyth on PATH."
        )
    elif not (src_dir / "README.md").exists() or not (src_dir / "Makefile").exists():
        warnings.append(f"Kmyth source directory does not look like an initialized checkout: {src_dir}")

    seal_path = _resolve_tool(KMYTH_SEAL, binary_dir=bin_dir, source_dir=src_dir)
    unseal_path = _resolve_tool(KMYTH_UNSEAL, binary_dir=bin_dir, source_dir=src_dir)

    if seal_path is None:
        errors.append(
            "kmyth-seal executable not found. Build the submodule with `make`, "
            "set kmyth_binary_dir, or install kmyth on PATH."
        )
    if unseal_path is None:
        errors.append(
            "kmyth-unseal executable not found. Build the submodule with `make`, "
            "set kmyth_binary_dir, or install kmyth on PATH."
        )

    return KmythAvailability(
        source_dir=src_dir,
        seal_path=seal_path,
        unseal_path=unseal_path,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def seal_file_with_kmyth(
    input_path: Path,
    output_path: Path | None = None,
    *,
    options: KmythSealOptions | None = None,
) -> Path:
    """Seal *input_path* with ``kmyth-seal`` and return the ``.ski`` path."""
    opts = options or KmythSealOptions()
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Kmyth input artifact does not exist: {source}")

    destination = output_path or Path(str(source) + opts.output_suffix)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not opts.overwrite:
            raise FileExistsError(f"Kmyth output already exists: {destination}")
        destination.unlink()

    availability = validate_kmyth_installation(binary_dir=opts.binary_dir, source_dir=opts.source_dir)
    if not availability.available or availability.seal_path is None:
        raise KmythUnavailableError(availability.summary())

    argv = [
        str(availability.seal_path),
        "--input",
        str(source),
        "--output",
        str(destination),
    ]
    if opts.pcrs:
        argv.extend(["--pcrs_list", ", ".join(str(pcr) for pcr in opts.pcrs)])
    if opts.cipher:
        argv.extend(["--cipher", opts.cipher])

    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, shell=False
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=opts.timeout_seconds,
            env=_build_subprocess_env(opts),
        )
    except subprocess.TimeoutExpired as exc:
        raise KmythCommandError(f"kmyth-seal timed out after {opts.timeout_seconds} seconds") from exc
    except OSError as exc:
        raise KmythCommandError(f"kmyth-seal invocation failed: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or f"exit status {result.returncode}"
        raise KmythCommandError(f"kmyth-seal failed for {source.name}: {detail}")

    if not destination.exists():
        raise KmythCommandError(f"kmyth-seal completed but did not create {destination}")
    return destination


def normalize_kmyth_pcrs(value: Any) -> list[int]:
    """Normalize YAML PCR config into a list of integer PCR indexes."""
    if value in (None, ""):
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        raw_items: list[Any] = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, (list, tuple)):
        raw_items = list(value)
    else:
        raise ValueError("kmyth_pcrs must be an integer, comma-separated string, or list of integers")

    pcrs: list[int] = []
    for item in raw_items:
        try:
            pcr = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"kmyth_pcrs entry is not an integer: {item!r}") from exc
        if pcr < 0:
            raise ValueError(f"kmyth_pcrs entry must be non-negative: {pcr}")
        pcrs.append(pcr)
    return pcrs


def normalize_kmyth_seal_artifacts(value: Any) -> list[str]:
    """Normalize and validate the artifact list sealed by Kmyth."""
    if value in (None, ""):
        return ["hash_manifest"]
    if isinstance(value, str):
        artifacts = [value]
    elif isinstance(value, (list, tuple)):
        artifacts = [str(item) for item in value]
    else:
        raise ValueError("kmyth_seal_artifacts must be a string or list of strings")

    normalized = [artifact.strip() for artifact in artifacts if artifact.strip()]
    unknown = sorted(set(normalized) - SUPPORTED_SEAL_ARTIFACTS)
    if unknown:
        expected = ", ".join(sorted(SUPPORTED_SEAL_ARTIFACTS))
        raise ValueError(f"Unsupported kmyth_seal_artifacts values: {unknown}; expected one of: {expected}")
    return normalized or ["hash_manifest"]


def _build_subprocess_env(options: KmythSealOptions) -> dict[str, str]:
    """Build the environment for the kmyth-seal subprocess.

    Inherits the current process environment and adds:
    - ``TSS2_TCTI_DEFAULT``: if ``options.tcti_config`` is set
    - ``DYLD_LIBRARY_PATH``: ensures TPM2-TSS and OpenSSL libs are found
    """
    env = dict(os.environ)
    if options.tcti_config:
        env["TSS2_TCTI_DEFAULT"] = options.tcti_config
    # Ensure .so symlinks exist for dlopen
    kmyth_lib = KMYTH_PREFIX / "lib"
    if kmyth_lib.exists():
        existing = env.get("DYLD_LIBRARY_PATH", "")
        parts = [str(kmyth_lib)] + ([existing] if existing else [])
        env["DYLD_LIBRARY_PATH"] = ":".join(parts)
    return env


def _optional_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return Path(text).expanduser()


def _resolve_tool(name: str, *, binary_dir: Path | None, source_dir: Path) -> Path | None:
    candidates: list[Path] = []
    if binary_dir is not None:
        candidates.append(binary_dir / name)
    candidates.append(source_dir / "bin" / name)

    which_result = shutil.which(name)
    if which_result:
        candidates.append(Path(which_result))

    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    return None


__all__ = [
    "KMYTH_PREFIX",
    "KMYTH_REPOSITORY_URL",
    "KMYTH_SEAL",
    "KMYTH_SUBMODULE_DIRNAME",
    "KMYTH_UNSEAL",
    "SUPPORTED_SEAL_ARTIFACTS",
    "KmythAvailability",
    "KmythCommandError",
    "KmythError",
    "KmythSealOptions",
    "KmythUnavailableError",
    "default_kmyth_source_dir",
    "normalize_kmyth_pcrs",
    "normalize_kmyth_seal_artifacts",
    "seal_file_with_kmyth",
    "validate_kmyth_installation",
]

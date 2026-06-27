"""infrastructure.publishing.archival — multi-target archival publishing subpackage.

Re-exports the full public surface so callers can import from either the flat
``infrastructure.publishing.archival`` module (backwards-compat) or this
subpackage with identical import paths:

    from infrastructure.publishing.archival import (
        ArchivalProvider,
        ArchivalReceipt,
        ArchivalRun,
        ArchivalCredentials,
        ArchivalError,
        DEFAULT_CREDENTIALS_PATH,
        ZenodoProvider,
        IPFSPinataProvider,
        IPFSWeb3StorageProvider,
        SoftwareHeritageProvider,
        archive_publication,
        load_credentials,
    )

Sub-module layout
-----------------
- ``models``      — dataclasses, ArchivalError, DEFAULT_CREDENTIALS_PATH, private helpers
- ``providers``   — ArchivalProvider protocol + all 4 concrete provider classes
- ``orchestrate`` — load_credentials(), archive_publication()
"""

from __future__ import annotations

from .models import (
    ArchivalCredentials,
    ArchivalError,
    ArchivalReceipt,
    ArchivalRun,
    DEFAULT_CREDENTIALS_PATH,
)
from .orchestrate import archive_publication, load_credentials
from .providers import (
    ArchivalProvider,
    IPFSPinataProvider,
    IPFSWeb3StorageProvider,
    SoftwareHeritageProvider,
    ZenodoProvider,
)

__all__ = [
    "ArchivalError",
    "ArchivalReceipt",
    "ArchivalRun",
    "ArchivalProvider",
    "ZenodoProvider",
    "IPFSPinataProvider",
    "IPFSWeb3StorageProvider",
    "SoftwareHeritageProvider",
    "ArchivalCredentials",
    "archive_publication",
    "load_credentials",
    "DEFAULT_CREDENTIALS_PATH",
]

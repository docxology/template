"""Data models for the Open Science Framework (OSF) publishing adapter."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OSFConfig:
    """Configuration for an OSF publish.

    Parameters
    ----------
    title:
        Project (node) title used when creating a new node.
    token:
        OSF personal access token. When ``None`` the adapter reads ``OSF_TOKEN``
        from the environment.
    node_id:
        Existing OSF node (5-char GUID, e.g. ``ab12c``) to upload into. When
        ``None`` a new node is created from ``title``.
    category:
        OSF node category (``project``, ``data``, ``software``, ...).
    public:
        Make the node public. OSF nodes are private by default; this adapter
        defaults to public to match a publication workflow.
    description:
        Optional node description.
    api_base:
        OSF JSON:API base. Overridable for ``pytest-httpserver``.
    files_base:
        Waterbutler file-storage base. Overridable for tests. OSF separates
        metadata (api.osf.io) from file I/O (files.osf.io).
    storage_provider:
        Waterbutler storage provider (default ``osfstorage``).
    timeout:
        Per-request timeout (seconds).
    """

    title: str = "Untitled deposit"
    token: str | None = None
    node_id: str | None = None
    category: str = "project"
    public: bool = True
    description: str = ""
    api_base: str = "https://api.osf.io/v2"
    files_base: str = "https://files.osf.io/v1"
    storage_provider: str = "osfstorage"
    timeout: float = 30.0


@dataclass(frozen=True)
class OSFResult:
    """Result of an OSF publish attempt. Never raised — inspected by callers."""

    status: str  # "ok" | "error" | "dry-run"
    node_id: str | None = None
    url: str | None = None
    uploaded: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None
    timestamp_utc: str | None = None
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "ok"

"""Data models for the HuggingFace Hub publishing adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class HFRepoType(str, Enum):
    """HuggingFace Hub repository types."""

    MODEL = "model"
    DATASET = "dataset"
    SPACE = "space"


@dataclass(frozen=True)
class HuggingFaceConfig:
    """Configuration for a HuggingFace Hub publish.

    Parameters
    ----------
    repo_id:
        Target repository in ``namespace/name`` form (e.g. ``docxology/my-paper``).
    repo_type:
        One of ``model`` / ``dataset`` / ``space``. Research artifacts and
        reproducibility bundles are usually published as ``dataset``.
    token:
        HuggingFace access token (``hf_...``). When ``None`` the adapter reads
        ``HUGGINGFACE_TOKEN`` (then ``HF_TOKEN``) from the environment.
    private:
        Create the repo as private. Defaults to public.
    base_url:
        Hub API base. Overridable so tests can target a local
        ``pytest-httpserver`` instance.
    commit_message:
        Commit message used for the upload.
    timeout:
        Per-request timeout (seconds).
    """

    repo_id: str
    repo_type: HFRepoType = HFRepoType.DATASET
    token: str | None = None
    private: bool = False
    base_url: str = "https://huggingface.co"
    commit_message: str = "Publish via template/ publishing pipeline"
    timeout: float = 30.0


@dataclass(frozen=True)
class HuggingFaceResult:
    """Result of a HuggingFace Hub publish attempt. Never raised — inspected."""

    status: str  # "ok" | "error" | "dry-run"
    repo_id: str
    repo_type: str
    url: str | None = None
    commit_url: str | None = None
    uploaded: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None
    timestamp_utc: str | None = None
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "ok"

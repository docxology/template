"""Backwards-compat shim: the module moved to ``infrastructure.metadata``.

Historical import paths keep resolving; new code imports
``infrastructure.metadata.repository_metadata`` directly.
"""

from infrastructure.metadata.repository_metadata import normalized_repository_url

__all__ = ["normalized_repository_url"]
